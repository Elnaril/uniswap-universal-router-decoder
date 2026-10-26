"""
Analyse how the Uniswap Universal Router commands are used over a block range.

The script reads one or more RPC endpoints from the environment (PROVIDER_1, PROVIDER_2, ...), each guarded by its own
rate limiter, and spreads the work of fetching the blocks (with their full transactions) across all of them.

For every transaction sent to the Universal Router it then:
* decodes the call and counts how many times each command is used;
* re-encodes the call (except the structured commands) and compares the result to the original calldata.

A transaction the codec cannot decode or rebuild is only reported as a failure if it succeeded on-chain: a
transaction that reverted may carry calldata the codec is not expected to handle, so it is counted in 'faulty_trx'
instead of the failure lists.

Usage:
    python scripts/ur_command_usage.py <block_start> <block_end> [--commands 0 2 16]

The RPC endpoints are read from the environment, or from a .env file in the current directory:
    PROVIDER_1=https://...
    PROVIDER_2=https://...
    PROVIDER_3=https://...
"""
from __future__ import annotations

import argparse
import asyncio
from collections.abc import Iterator
from contextlib import asynccontextmanager
import os
import sys
from typing import (
    Any,
    AsyncIterator,
    Optional,
    Sequence,
    Union,
)

from credit_rate_limit import (
    CountRateLimiter,
    throughput,
)
from dotenv import load_dotenv
from web3 import (
    AsyncHTTPProvider,
    AsyncWeb3,
    Web3,
)
from web3.types import (
    BlockData,
    TxData,
    TxReceipt,
)

from uniswap_universal_router_decoder import (
    AsyncRouterCodec,
    decoded_input_to_dict,
)
from uniswap_universal_router_decoder._enums import (
    RouterConstant,
    RouterFunction,
    STRUCTURED_COMMANDS,
)


UR_ADDRESS = Web3.to_checksum_address("0x23617e59A5925b2A4Bf75d73ff6711cD0b29De85")

# The number of requests each provider is allowed to make per interval.
RATE_LIMIT_MAX_COUNT = 8
RATE_LIMIT_INTERVAL = 1.0

# How often the progress and the failure lists are printed.
REPORT_BLOCK_STEP = 100
REPORT_FAILURE_STEP = 1000

# How many transaction hashes are kept per requested command.
MAX_REQUESTED_PER_COMMAND = 3

COMMAND_TYPE_MASK = RouterConstant.COMMAND_TYPE_MASK.value
STRUCTURED_COMMAND_VALUES = frozenset(command.value for command in STRUCTURED_COMMANDS)
COMMAND_NAMES = {command.value: command.name for command in RouterFunction}


class _Provider:
    """One RPC endpoint, with its own rate limiter and codec."""

    def __init__(self, name: str, rpc_url: str) -> None:
        self.name = name
        self.rate_limiter = CountRateLimiter(RATE_LIMIT_MAX_COUNT, RATE_LIMIT_INTERVAL, name=name)
        self.w3 = AsyncWeb3(AsyncHTTPProvider(rpc_url))

    @throughput(attribute_name="rate_limiter")
    async def get_block(self, block_number: int) -> BlockData:
        return await self.w3.eth.get_block(block_number, full_transactions=True)

    @throughput(attribute_name="rate_limiter")
    async def get_receipt(self, tx_hash: str) -> TxReceipt:
        return await self.w3.eth.get_transaction_receipt(tx_hash)

    async def close(self) -> None:
        await self.w3.provider.disconnect()


class _ProviderPool:
    """
    Hand out the providers so the RPC calls are spread across all of them.

    A caller borrows a provider for the duration of one call and gives it back, so whichever provider is free takes
    the next request.
    """

    def __init__(self, providers: Sequence[_Provider]) -> None:
        self._queue: asyncio.Queue[_Provider] = asyncio.Queue()
        for provider in providers:
            self._queue.put_nowait(provider)

    @asynccontextmanager
    async def acquire(self) -> AsyncIterator[_Provider]:
        provider = await self._queue.get()
        try:
            yield provider
        finally:
            self._queue.put_nowait(provider)


class _Stats:
    """The counters and the failure lists, plus the periodic reporting."""

    def __init__(self, block_start: int, block_end: int, requested_commands: Sequence[int]) -> None:
        self.block_start = block_start
        self.block_end = block_end
        self.total_blocks = block_end - block_start
        self.requested_commands = list(requested_commands)
        self.blocks_done = 0
        # every command starts at 0 so the report also shows the ones that are never used
        self.command_stats: dict[Union[int, str], int] = {command.value: 0 for command in RouterFunction}
        self.command_stats["faulty_trx"] = 0
        self.command_stats["decoded_trx"] = 0
        self.command_stats["trailing_data_trx"] = 0
        self.decoding_failures: list[str] = []
        self.encoding_failures: list[str] = []
        self.requested_trx: list[dict[int, list[str]]] = (
            [{command: [] for command in self.requested_commands}] if self.requested_commands else []
        )
        self._print_lock = asyncio.Lock()

    def count_commands(self, command_values: Sequence[int]) -> None:
        for value in command_values:
            self.command_stats[value] = self.command_stats.get(value, 0) + 1

    def record_requested(self, tx_hash: str, command_values: set[int]) -> None:
        if not self.requested_commands:
            return
        bucket = self.requested_trx[0]
        for command in self.requested_commands:
            if command in command_values and len(bucket[command]) < MAX_REQUESTED_PER_COMMAND:
                bucket[command].append(tx_hash)

    def print_header(self, provider_names: Sequence[str]) -> None:
        print("=" * 70, flush=True)
        print("Universal Router command usage analysis", flush=True)
        print(f"  block_start : {self.block_start}", flush=True)
        print(f"  block_end   : {self.block_end}", flush=True)
        print(f"  blocks      : {self.total_blocks}", flush=True)
        print(f"  providers   : {', '.join(provider_names)}", flush=True)
        print(f"  commands    : {self.requested_commands if self.requested_commands else 'none'}", flush=True)
        print("=" * 70, flush=True)

    def _print_progress(self) -> None:
        used = {
            COMMAND_NAMES.get(key, key): count
            for key, count in self.command_stats.items()
            if isinstance(key, int) and count
        }
        print("-" * 70, flush=True)
        print(f"blocks analyzed: {self.blocks_done} / {self.total_blocks}", flush=True)
        print(f"command_stats  : {self.command_stats}", flush=True)
        print(f"commands used  : {used}", flush=True)

    def _print_failures(self) -> None:
        print("-" * 70, flush=True)
        print(f"decoding_failures: {self.decoding_failures}", flush=True)
        print(f"encoding_failures: {self.encoding_failures}", flush=True)
        print(f"requested_trx    : {self.requested_trx}", flush=True)

    async def block_done(self) -> None:
        self.blocks_done += 1
        if self.blocks_done % REPORT_BLOCK_STEP == 0:
            async with self._print_lock:
                self._print_progress()
        if self.blocks_done % REPORT_FAILURE_STEP == 0:
            async with self._print_lock:
                self._print_failures()

    async def print_final(self) -> None:
        async with self._print_lock:
            self._print_progress()
            self._print_failures()


def _iter_command_values(commands: bytes, inputs: Sequence[Any]) -> Iterator[int]:
    """
    Yield the command value of every command in a decoded call, including the ones nested in a sub-plan.

    :param commands: the raw command bytes of the call
    :param inputs: the decoded inputs of the call
    """
    for command_byte in commands:
        yield command_byte & COMMAND_TYPE_MASK
    for entry in inputs:
        if not isinstance(entry, tuple) or len(entry) < 2 or not isinstance(entry[1], dict):
            continue
        sub_commands = entry[1].get("commands")
        sub_inputs = entry[1].get("inputs")
        if isinstance(sub_commands, (bytes, bytearray)) and isinstance(sub_inputs, (list, tuple)):
            yield from _iter_command_values(bytes(sub_commands), sub_inputs)


async def _flag_failure(tx_hash: str, pool: _ProviderPool, stats: _Stats, failures: list[str]) -> None:
    # A transaction the codec could not process is only a real failure of the codec if it succeeded on-chain:
    # a transaction that reverted may carry calldata the codec is not expected to handle.
    try:
        async with pool.acquire() as provider:
            receipt = await provider.get_receipt(tx_hash)
    except Exception as exc:
        print(f"warning: could not fetch the receipt of {tx_hash}: {exc}", flush=True)
        failures.append(tx_hash)
        return
    if receipt.get("status") == 1:
        failures.append(tx_hash)
    else:
        stats.command_stats["faulty_trx"] += 1


async def _check_reencoding(
        tx_hash: str,
        original_input: bytes,
        decoded: Any,
        pool: _ProviderPool,
        codec: AsyncRouterCodec,
        stats: _Stats) -> None:
    try:
        rebuilt = codec.encode.function_input(decoded_input_to_dict(decoded))
        differs = rebuilt.lower() != Web3.to_hex(original_input).lower()
    except Exception:
        differs = True
    if differs:
        await _flag_failure(tx_hash, pool, stats, stats.encoding_failures)


async def _process_tx(tx: TxData, pool: _ProviderPool, codec: AsyncRouterCodec, stats: _Stats) -> None:
    tx_hash = Web3.to_hex(tx["hash"])
    try:
        decoded = codec.decode.function_input(tx["input"])
    except Exception:
        await _flag_failure(tx_hash, pool, stats, stats.decoding_failures)
        return

    _, decoded_input = decoded
    stats.command_stats["decoded_trx"] += 1
    if decoded_input.get("trailing_data"):
        stats.command_stats["trailing_data_trx"] += 1
    command_values = list(_iter_command_values(decoded_input.get("commands", b""), decoded_input.get("inputs", [])))
    stats.count_commands(command_values)
    stats.record_requested(tx_hash, set(command_values))

    if set(command_values) & STRUCTURED_COMMAND_VALUES:
        # the structured commands decode to structures, not ABI values, so they cannot be rebuilt
        return
    await _check_reencoding(tx_hash, tx["input"], decoded, pool, codec, stats)


async def _process_block(block: BlockData, pool: _ProviderPool, codec: AsyncRouterCodec, stats: _Stats) -> None:
    for tx in block.get("transactions", []):
        to = tx.get("to")
        if to is None or to.lower() != UR_ADDRESS.lower():
            continue
        await _process_tx(tx, pool, codec, stats)


async def _worker(
        pool: _ProviderPool,
        codec: AsyncRouterCodec,
        block_queue: asyncio.Queue[int],
        stats: _Stats) -> None:
    while True:
        try:
            block_number = block_queue.get_nowait()
        except asyncio.QueueEmpty:
            return
        try:
            async with pool.acquire() as provider:
                block = await provider.get_block(block_number)
        except Exception as exc:
            print(f"warning: could not fetch block {block_number}: {exc}", flush=True)
            await stats.block_done()
            continue
        if block is not None:
            await _process_block(block, pool, codec, stats)
        await stats.block_done()


def _load_providers() -> list[_Provider]:
    load_dotenv()
    providers: list[_Provider] = []
    index = 1
    while True:
        rpc_url = os.environ.get(f"PROVIDER_{index}")
        if not rpc_url:
            break
        providers.append(_Provider(f"PROVIDER_{index}", rpc_url))
        index += 1
    if not providers:
        raise SystemExit(
            "No RPC endpoint configured: set PROVIDER_1 (and optionally PROVIDER_2, PROVIDER_3, ...) "
            "in the environment or in a .env file."
        )
    return providers


async def _run(block_start: int, block_end: int, requested_commands: Sequence[int]) -> None:
    providers = _load_providers()
    pool = _ProviderPool(providers)
    # decoding and re-encoding are local, so a codec without a provider is enough
    codec = AsyncRouterCodec()
    stats = _Stats(block_start, block_end, requested_commands)
    stats.print_header([provider.name for provider in providers])

    block_queue: asyncio.Queue[int] = asyncio.Queue()
    for block_number in range(block_start, block_end):
        block_queue.put_nowait(block_number)

    workers = [
        asyncio.create_task(_worker(pool, codec, block_queue, stats))
        for _ in range(len(providers))
    ]
    try:
        await asyncio.gather(*workers)
    finally:
        await asyncio.gather(*(provider.close() for provider in providers))
    await stats.print_final()


def _parse_args(argv: Optional[Sequence[str]]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Count how the Universal Router commands are used over a block range.",
    )
    parser.add_argument("block_start", type=int, help="the first block of the range (included).")
    parser.add_argument(
        "block_end",
        type=int,
        help="the last block of the range (excluded): the range holds block_end - block_start blocks.",
    )
    parser.add_argument(
        "--commands",
        type=int,
        nargs="+",
        default=None,
        help="command values to collect example transaction hashes for (up to 3 per command).",
    )
    return parser.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = _parse_args(argv)
    if args.block_end <= args.block_start:
        raise SystemExit("block_end must be greater than block_start")
    asyncio.run(_run(args.block_start, args.block_end, args.commands or []))
    return 0


if __name__ == "__main__":
    sys.exit(main())
