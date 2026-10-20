"""
Command line interface to encode/decode Uniswap Universal Router data.

Two entry points are installed:
* ur-decode: decode a transaction, raw calldata, a custom error or a V3 path.
* ur-encode: list/describe the encodable commands and build calldata from them.

Every subcommand prints JSON to stdout, which makes the CLI easy to consume from
a shell or by an agent (and it is the same code a future MCP server would wrap).
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from typing import (
    Any,
    cast,
    Optional,
    Sequence,
)

from uniswap_universal_router_decoder._command_spec import (
    describe_command,
    encode_commands,
    list_command_specs,
)
from uniswap_universal_router_decoder._serialization import (
    decoded_input_to_dict,
    to_json_primitives,
    transaction_to_dict,
)
from uniswap_universal_router_decoder.router_codec import RouterCodec


def _dump(data: Any) -> None:
    print(json.dumps(data, indent=2))


def _make_codec(rpc: Optional[str] = None, require_rpc: bool = False) -> RouterCodec:
    rpc_url = rpc or os.environ.get("RPC_URL") or os.environ.get("ETH_RPC_URL")
    if rpc_url:
        return RouterCodec(rpc_endpoint=rpc_url)
    if require_rpc:
        raise SystemExit("An RPC endpoint is required: pass --rpc or set RPC_URL.")
    return RouterCodec()


def _build_decode_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="ur-decode", description="Decode Uniswap Universal Router data as JSON.")
    subparsers = parser.add_subparsers(dest="subcommand", required=True)

    tx_parser = subparsers.add_parser("tx", help="Decode a transaction sent to the UR.")
    tx_parser.add_argument("tx_hash")
    tx_parser.add_argument("--rpc", default=None, help="RPC endpoint (defaults to $RPC_URL).")

    calldata_parser = subparsers.add_parser("calldata", help="Decode raw UR calldata.")
    calldata_parser.add_argument("calldata")

    error_parser = subparsers.add_parser("error", help="Decode a UR/Permit2/V4 custom error.")
    error_parser.add_argument("error_data")

    path_parser = subparsers.add_parser("v3-path", help="Decode a V3 path.")
    path_parser.add_argument("fn_name", choices=("V3_SWAP_EXACT_IN", "V3_SWAP_EXACT_OUT"))
    path_parser.add_argument("path")
    return parser


def decode_main(argv: Optional[Sequence[str]] = None) -> int:
    """
    Entry point of the ur-decode command.

    :param argv: the command line arguments (defaults to sys.argv[1:])
    :return: the process exit code
    """
    args = _build_decode_parser().parse_args(argv)
    if args.subcommand == "tx":
        trx = _make_codec(args.rpc, require_rpc=True).decode.transaction(args.tx_hash)
        _dump(transaction_to_dict(trx))
    elif args.subcommand == "calldata":
        decoded = _make_codec().decode.function_input(args.calldata)
        _dump(decoded_input_to_dict(decoded))
    elif args.subcommand == "error":
        name, params = _make_codec().decode.contract_error(args.error_data)
        _dump({"error": name, "args": to_json_primitives(params)})
    elif args.subcommand == "v3-path":
        _dump(to_json_primitives(_make_codec().decode.v3_path(args.fn_name, args.path)))
    return 0


def _build_encode_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="ur-encode", description="Encode Uniswap Universal Router commands.")
    subparsers = parser.add_subparsers(dest="subcommand", required=True)

    subparsers.add_parser("list", help="List the encodable commands.")

    describe_parser = subparsers.add_parser("describe", help="Describe one encodable command.")
    describe_parser.add_argument("command")

    build_parser = subparsers.add_parser("build", help="Build UR calldata from one or more commands.")
    build_parser.add_argument("--command", default=None, help="A single command name (see 'list').")
    build_parser.add_argument("--params", default=None, help="JSON object with the parameters of --command.")
    build_parser.add_argument("--plan", default=None, help="JSON file (or '-' for stdin) with a list of commands.")
    build_parser.add_argument("--deadline", type=int, default=None, help="Unix timestamp deadline for the tx.")
    build_parser.add_argument("--rpc", default=None, help="RPC endpoint (defaults to $RPC_URL).")
    return parser


def _load_plan(source: str) -> Any:
    if source == "-":
        return json.load(sys.stdin)
    with open(source, "r", encoding="utf-8") as plan_file:
        return json.load(plan_file)


def _commands_from_args(
        args: argparse.Namespace,
        parser: argparse.ArgumentParser) -> tuple[list[dict[str, Any]], Optional[int]]:
    if args.plan:
        plan: Any = _load_plan(args.plan)
        if isinstance(plan, dict):
            plan_dict = cast("dict[str, Any]", plan)
            deadline: Optional[int] = args.deadline if args.deadline is not None else plan_dict.get("deadline")
            return plan_dict["commands"], deadline
        return plan, args.deadline
    if args.command:
        params: dict[str, Any] = json.loads(args.params) if args.params else {}
        return [{"command": args.command, "params": params}], args.deadline
    parser.error("provide --plan or --command")


def encode_main(argv: Optional[Sequence[str]] = None) -> int:
    """
    Entry point of the ur-encode command.

    :param argv: the command line arguments (defaults to sys.argv[1:])
    :return: the process exit code
    """
    parser = _build_encode_parser()
    args = parser.parse_args(argv)
    if args.subcommand == "list":
        _dump(list_command_specs())
    elif args.subcommand == "describe":
        _dump(describe_command(args.command))
    elif args.subcommand == "build":
        commands, deadline = _commands_from_args(args, parser)
        calldata = encode_commands(_make_codec(args.rpc), commands, deadline)
        _dump({"calldata": calldata, "deadline": deadline, "commands": [entry["command"] for entry in commands]})
    return 0
