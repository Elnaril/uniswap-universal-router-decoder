from pprint import pp

import pytest
from web3 import AsyncWeb3
from web3.types import (
    HexStr,
    Wei,
)

from uniswap_universal_router_decoder import (
    AsyncRouterCodec,
    FunctionRecipient,
    V4Constants,
)
from uniswap_universal_router_decoder._constants import ur_address


def test_get_max_expiration(async_codec):
    assert async_codec.get_max_expiration() == 2**48 - 1


# Test Decode Trx + Input
trx_hash_01 = HexStr("0xd2c87626ff2ed52e922c3d0c49ca36bd6c48e31ac21d5aee2505e503ddd1e29c")
expected_function_names_01 = ("V2_SWAP_EXACT_IN", "UNWRAP_WETH")

trx_hash_02 = HexStr("0x16f416f6e808c457f88a7e0ce89892e5741c5ea7587d89eca073b5095e33c890")
expected_function_names_02 = ("PERMIT2_PERMIT", "V3_SWAP_EXACT_OUT")

trx_hash_03 = HexStr("0x93371c34a911f9b7f1a01945b373548fc17f72c6628767669151a981a33fc156")
expected_function_names_03 = ("WRAP_ETH", "V2_SWAP_EXACT_OUT", "UNWRAP_WETH")

trx_hash_05 = HexStr("0x47c0f1dd13edf9f1608f9f34bdba9ad40cb95dd081033cad69f5b88e451b4b55")
expected_function_names_05 = (None, "SWEEP")

trx_hash_06 = HexStr("0xfd25bd671e4186f360e673bee850a7ba0677bd45f1498ad400c81ffb0cef7838")
expected_function_names_06 = ("V3_SWAP_EXACT_IN", "V3_SWAP_EXACT_IN", "V2_SWAP_EXACT_IN")

trx_hash_07 = HexStr("0x1e869ba980b7131ca03f619cdf4a37af66eed4de2db97eed862c02c977ecce53")
expected_function_names_07 = ("PERMIT2_PERMIT", "V2_SWAP_EXACT_IN", "PAY_PORTION", "PAY_PORTION", "UNWRAP_WETH")

trx_hash_11 = HexStr("0x4b8c8940707bbcd928d00d0e369bdbe8ff65b092ba1fc8aa10891bfac7c4277b")
expected_function_names_11 = ("PERMIT2_PERMIT_BATCH", "V4_SWAP")

trx_hash_12 = HexStr("0x2ab1c28cf84f5e4b4db07e1be2e6f45f9c07e5d3b2ad80396e51c12d8db2b180")
expected_function_names_12 = ("PERMIT2_PERMIT_BATCH", "V4_SWAP", "PERMIT2_TRANSFER_FROM_BATCH", "modifyLiquidities")

trx_hash_13 = HexStr("0x19d531aaab4b8abfa3723d4d6fa5e80d8ecddafe3100992230edb9a2b02c3a80")
expected_function_names_13 = ("WRAP_ETH", "TRANSFER", "V3_SWAP_EXACT_OUT", "UNWRAP_WETH")


@pytest.mark.parametrize(
    "trx_hash, use_w3, expected_fct_names",
    (
        (trx_hash_01, False, expected_function_names_01),
        (trx_hash_02, True, expected_function_names_02),
        (trx_hash_03, True, expected_function_names_03),
        (trx_hash_05, True, expected_function_names_05),
        (trx_hash_06, True, expected_function_names_06),
        (trx_hash_07, True, expected_function_names_07),
        (trx_hash_11, True, expected_function_names_11),
        (trx_hash_12, True, expected_function_names_12),
        (trx_hash_13, True, expected_function_names_13),
    )
)
async def test_decode_transaction(trx_hash, use_w3, expected_fct_names, async_w3, rpc_url):
    if use_w3:
        codec_w3 = AsyncRouterCodec(async_w3=async_w3)
    else:
        codec_w3 = AsyncRouterCodec(rpc_endpoint=rpc_url)

    decoded_trx = await codec_w3.decode.transaction(trx_hash)
    command_inputs = decoded_trx["decoded_input"]["inputs"]
    assert len(command_inputs) == len(expected_fct_names)
    for i, expected_name in enumerate(expected_fct_names):
        if expected_name:
            assert expected_name == command_inputs[i][0].fn_name
            assert command_inputs[i][2]['revert_on_fail'] is True
        else:
            assert isinstance(command_inputs[i], str)
            int(command_inputs[i], 16)  # check the str is actually a hex


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
