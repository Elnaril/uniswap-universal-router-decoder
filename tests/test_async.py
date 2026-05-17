from pprint import pp

import pytest
from web3 import AsyncWeb3
from web3.types import Wei

from tests.resources.transactions import transactions
from uniswap_universal_router_decoder import (
    AsyncRouterCodec,
    FunctionRecipient,
    V4Constants,
)
from uniswap_universal_router_decoder._constants import ur_address


def test_get_max_expiration(async_codec):
    assert async_codec.get_max_expiration() == 2**48 - 1


# Test Decode Trx + Input
@pytest.mark.parametrize(
    "trx_hash, use_w3, expected_decoded_input",
    (
        (transactions[0]["trx_hash"], True, transactions[0]["decoded_input"]),
        (transactions[1]["trx_hash"], False, transactions[1]["decoded_input"]),
        (transactions[2]["trx_hash"], True, transactions[2]["decoded_input"]),
        (transactions[3]["trx_hash"], False, transactions[3]["decoded_input"]),
        (transactions[4]["trx_hash"], True, transactions[4]["decoded_input"]),
        (transactions[5]["trx_hash"], False, transactions[5]["decoded_input"]),
        (transactions[6]["trx_hash"], True, transactions[6]["decoded_input"]),
    )
)
async def test_decode_transaction(trx_hash, use_w3, expected_decoded_input, async_w3, rpc_url):
    if use_w3:
        codec_w3 = AsyncRouterCodec(async_w3=async_w3)
    else:
        codec_w3 = AsyncRouterCodec(rpc_endpoint=rpc_url)

    decoded_trx = await codec_w3.decode.transaction(trx_hash)
    assert decoded_trx["hash"] == AsyncWeb3.to_bytes(hexstr=trx_hash)
    assert str(decoded_trx["decoded_input"]) == expected_decoded_input

    decoded_input = codec_w3.decode.function_input(decoded_trx["input"])
    assert str(decoded_input) == expected_decoded_input


async def test_build_transaction(async_w3):
    async_codec = AsyncRouterCodec(async_w3=async_w3)
    sender = "0x1AB4973a48dc892Cd9971ECE8e01DcC7688f8F23"
    balance = await async_codec._w3.eth.get_balance(
        "0x52d7Bb619F6E37A038e522eDF755008d9EfdD695",
        block_identifier=19876107
    )
    assert balance > AsyncWeb3.to_wei(4, "ether")

    amount_in = Wei(2 * 10**18)
    builder = (
        async_codec
        .encode
        .chain()
        .wrap_eth(FunctionRecipient.ROUTER, amount_in)
        .v2_swap_exact_in_from_balance(
            FunctionRecipient.SENDER,
            Wei(0),
            [
                '0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2',
                '0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48',
            ],
        )
    )

    # transaction 1 - all defaults except value
    trx_1 = await builder.build_transaction(
        sender=sender,
        value=amount_in,
        block_identifier=19876107
    )
    assert trx_1.get("from") == sender
    assert trx_1.get("value") == amount_in
    assert trx_1.get("to") == ur_address
    assert trx_1.get("chainId") == 1
    assert trx_1.get("nonce") == 397356
    assert trx_1.get("type") == "0x2"
    assert trx_1.get("maxPriorityFeePerGas") == 2500000000
    assert trx_1.get("maxFeePerGas") == 20479961920
    assert len(trx_1.get("data")) > 100
    assert trx_1.get("gas", 0) > 0

    # transaction 3 - no call to rpc and custom fields
    trx_3 = await builder.build_transaction(
        sender=sender,
        value=amount_in,
        trx_speed=None,
        priority_fee=Wei(1900000000),
        max_fee_per_gas=Wei(22222222222),
        gas_limit=500_000,
        chain_id=2,
        nonce=100,
        block_identifier=19876107
    )

    assert trx_3.get("chainId") == 2
    assert trx_3.get("nonce") == 100
    assert trx_3.get("maxPriorityFeePerGas") == 1900000000
    assert trx_3.get("maxFeePerGas") == 22222222222
    assert trx_3.get("gas") == 500_000

    # transaction 4, 5, 6 - incompatible arguments
    with pytest.raises(ValueError):
        _ = await builder.build_transaction(
            sender=sender,
            value=amount_in,
            priority_fee=Wei(1900000000),
            block_identifier=19876107
        )

    with pytest.raises(ValueError):
        _ = await builder.build_transaction(
            sender=sender,
            value=amount_in,
            max_fee_per_gas=Wei(22222222222),
            block_identifier=19876107
        )

    with pytest.raises(ValueError):
        _ = await builder.build_transaction(
            sender=sender,
            value=amount_in,
            trx_speed=None,
            block_identifier=19876107
        )

    # transaction 7 - computed gas too high
    with pytest.raises(ValueError):
        _ = await builder.build_transaction(
            sender=sender,
            value=amount_in,
            max_fee_per_gas_limit=Wei(1 * 10 ** 9),
            block_identifier=19876107
        )


@pytest.mark.parametrize(
    "wallet, token, block_identifier, expected_result",
    (
        (AsyncWeb3.to_checksum_address('0x1944922D86209F7e5F3c88F2B2b4A8e737BeA9b1'), AsyncWeb3.to_checksum_address('0x1f9840a85d5aF5bf1D1762F925BDADdC4201F984'), 19881602, (1461501637330902918203684832716283019655932542975, 1718529375, 1)),  # noqa
        (AsyncWeb3.to_checksum_address('0x1944922D86209F7e5F3c88F2B2b4A8e737BeA9b1'), AsyncWeb3.to_checksum_address('0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48'), 19881602, (0, 0, 0)),  # noqa
    )
)
async def test_fetch_permit2_allowance(wallet, token, block_identifier, expected_result, async_codec_rpc):
    amount, expiration, nonce = await async_codec_rpc.fetch_permit2_allowance(
        wallet,
        token,
        spender=AsyncWeb3.to_checksum_address("0x3fC91A3afd70395Cd496C647d5a6CC9D4B2b7FAD"),  # old UR address
        block_identifier=block_identifier
    )
    assert (amount, expiration, nonce) == expected_result


async def test_v4_swap_exact_in_single(async_codec):
    pool_key = async_codec.encode.v4_pool_key(
        "0x0000000000000000000000000000000000000000",
        "0xBf5617af623f1863c4abc900c5bebD5415a694e8",
        3000,
        50,
    )
    encoded_input = (
        async_codec.
        encode().
        v4_swap().
        swap_exact_in_single(
            pool_key=pool_key,
            zero_for_one=False,
            amount_in=100000000000000,
            amount_out_min=798750268136655870501951828,
            hook_data=b'',
        ).
        take_all("0x0000000000000000000000000000000000000000", Wei(0)).
        settle_all("0xBf5617af623f1863c4abc900c5bebD5415a694e8", 100000000000000).
        build_v4_swap().
        build(deadline=1732612928)
    )

    print(encoded_input)

    fct_name, decoded_input = async_codec.decode.function_input(encoded_input)
    print(fct_name)
    pp(decoded_input, width=120)


MIN_TICK = -887272
MAX_TICK = 887272


async def test_v4_position_manager_call(async_codec_rpc):
    pool_key = async_codec_rpc.encode.v4_pool_key(
        "0x0000000000000000000000000000000000000000",
        "0xBf5617af623f1863c4abc900c5bebD5415a694e8",
        3000,
        50,
    )
    encoded_input = (
        async_codec_rpc.
        encode.
        chain().
        v4_posm_call().
        mint_position(
            pool_key,
            MIN_TICK,
            MAX_TICK,
            10860507277202,
            10**18,
            10**18,
            AsyncWeb3.to_checksum_address("0x29F08a27911bbCd0E01E8B1D97ec3cA187B6351D"),
            b"",
        ).
        settle("0xBf5617af623f1863c4abc900c5bebD5415a694e8", V4Constants.OPEN_DELTA.value, False).
        close_currency("0x0000000000000000000000000000000000000000").
        sweep("0xBf5617af623f1863c4abc900c5bebD5415a694e8", "0x29F08a27911bbCd0E01E8B1D97ec3cA187B6351D").
        sweep("0x0000000000000000000000000000000000000000", "0x29F08a27911bbCd0E01E8B1D97ec3cA187B6351D").
        build_v4_posm_call(async_codec_rpc.get_default_deadline()).
        build()
    )
    print(encoded_input)

    fct_name, decoded_input = async_codec_rpc.decode.function_input(encoded_input)
    print(fct_name)
    pp(decoded_input, indent=1, width=120)

    assert repr(fct_name) == "<Function execute(bytes,bytes[])>"
    assert int(decoded_input['commands'].hex(), 16) == 20
    assert repr(decoded_input['inputs'][0][0]) == "<Function modifyLiquidities(bytes,uint256)>"
    assert decoded_input['inputs'][0][1]['unlockData']['actions'] == b'\x02\x0b\x12\x14\x14'
    assert repr(decoded_input['inputs'][0][1]['unlockData']['params'][0][0]) == "<Function MINT_POSITION((address,address,uint24,int24,address),int24,int24,uint256,uint128,uint128,address,bytes)>"  # noqa
    assert repr(decoded_input['inputs'][0][1]['unlockData']['params'][1][0]) == "<Function SETTLE(address,uint256,bool)>"  # noqa
    assert repr(decoded_input['inputs'][0][1]['unlockData']['params'][2][0]) == "<Function CLOSE_CURRENCY(address)>"
    assert repr(decoded_input['inputs'][0][1]['unlockData']['params'][3][0]) == "<Function SWEEP(address,address)>"
    assert repr(decoded_input['inputs'][0][1]['unlockData']['params'][4][0]) == "<Function SWEEP(address,address)>"
