from pprint import pp

from web3 import Web3
from web3.types import (
    HexStr,
    Wei,
)

from uniswap_universal_router_decoder import (
    RouterCodec,
    V4Constants,
)


codec = RouterCodec()


def to_camel_case(d: dict):
    result = {}
    for k, v in d.items():
        breakdown = k.split("_")
        camel_case_key = breakdown[0] + "".join(key_bit.title() for key_bit in breakdown[1:])
        result[camel_case_key] = v
    return result


def test_pool_key():
    pool_key_1 = codec.encode.v4_pool_key(
        "0x0000000000000000000000000000000000000000",
        "0xBf5617af623f1863c4abc900c5bebD5415a694e8",
        3000,
        50,
    )
    pool_key_2 = codec.encode.v4_pool_key(
        "0xBf5617af623f1863c4abc900c5bebD5415a694e8",
        "0x0000000000000000000000000000000000000000",
        3000,
        50,
    )
    assert pool_key_1 == pool_key_2


def test_pool_id():
    pool_key = codec.encode.v4_pool_key(
        "0x0000000000000000000000000000000000000000",
        "0x4200000000000000000000000000000000000006",
        3000,
        60,
    )
    expected_pool_id = HexStr("426f60e2b0ac279b6cf8b3806d23e1d15d21aba4d6973e30d36299e81e3f01a1")
    assert codec.encode.v4_pool_id(pool_key) == Web3.to_bytes(hexstr=expected_pool_id)


def test_v4_swap_exact_in_single():
    pool_key = codec.encode.v4_pool_key(
        "0x0000000000000000000000000000000000000000",
        "0xBf5617af623f1863c4abc900c5bebD5415a694e8",
        3000,
        50,
    )
    encoded_input = (
        codec.
        encode.
        chain().
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

    fct_name, decoded_input = codec.decode.function_input(encoded_input)
    print(fct_name)
    pp(decoded_input, width=120)


"""
<Function execute(bytes,bytes[],uint256)>
{
    'commands': b'\x10',
    'inputs': [
        (
            <Function V4_SWAP(bytes,bytes[])>,
            {
                'actions': b'\x06\x0f\x0c',
                'params': [
                    (
                        <Function SWAP_EXACT_IN_SINGLE(((address,address,uint24,int24,address),bool,uint128,uint128,bytes))>,  # noqa
                        {
                            'exact_in_single_params': {
                                'PoolKey': {
                                    'currency0': '0x0000000000000000000000000000000000000000',
                                    'currency1': '0xBf5617af623f1863c4abc900c5bebD5415a694e8',
                                    'fee': 3000,
                                    'tickSpacing': 50,
                                    'hooks': '0x0000000000000000000000000000000000000000'
                                },
                                'zeroForOne': False,
                                'amountIn': 100000000000000,
                                'amountOutMinimum': 798750268136655870501951828,
                                'hookData': b''
                            }
                        }
                    ),
                    (
                        <Function TAKE_ALL(address,uint256)>,
                        {
                            'currency': '0x0000000000000000000000000000000000000000',
                            'minAmount': 0
                        }
                    ),
                    (
                        <Function SETTLE_ALL(address,uint256)>,
                        {
                            'currency': '0xBf5617af623f1863c4abc900c5bebD5415a694e8',
                            'maxAmount': 100000000000000
                        }
                    )
                ]
            },
            {
                'revert_on_fail': True
            }
        )
    ],
    'deadline': 1732612928
}
"""


def test_v4_initialize_pool():
    pool_key = codec.encode.v4_pool_key(
        "0x0000000000000000000000000000000000000000",
        "0xBf5617af623f1863c4abc900c5bebD5415a694e8",
        3000,
        50,
    )
    encoded_input = codec.encode.chain().v4_initialize_pool(pool_key, 1 * 10**18, 3800 * 10**6).build()
    print(encoded_input)
    assert encoded_input == "0x24856bc300000000000000000000000000000000000000000000000000000000000000400000000000000000000000000000000000000000000000000000000000000080000000000000000000000000000000000000000000000000000000000000000113000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000001000000000000000000000000000000000000000000000000000000000000002000000000000000000000000000000000000000000000000000000000000000c00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000bf5617af623f1863c4abc900c5bebd5415a694e80000000000000000000000000000000000000000000000000000000000000bb800000000000000000000000000000000000000000000000000000000000000320000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000040a3790bf349180000000"  # noqa

    fct_name, decoded_input = codec.decode.function_input(encoded_input)
    print(fct_name)
    pp(decoded_input, width=120)

    assert decoded_input["commands"] == b'\x13'
    assert decoded_input["inputs"][0][0].fn_name == "V4_INITIALIZE_POOL"
    expected_params = {
        'PoolKey': {
            'currency0': '0x0000000000000000000000000000000000000000',
            'currency1': '0xBf5617af623f1863c4abc900c5bebD5415a694e8',
            'fee': 3000,
            'tickSpacing': 50,
            'hooks': '0x0000000000000000000000000000000000000000'
        },
        'sqrtPriceX96': 4883951944324328712044544
    }
    assert decoded_input["inputs"][0][1] == expected_params
    assert decoded_input["inputs"][0][2] == {'revert_on_fail': True}


MIN_TICK = -887272
MAX_TICK = 887272


def test_v4_position_manager_call():
    pool_key = codec.encode.v4_pool_key(
        "0x0000000000000000000000000000000000000000",
        "0xBf5617af623f1863c4abc900c5bebD5415a694e8",
        3000,
        50,
    )
    encoded_input = (
        codec.
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
            Web3.to_checksum_address("0x29F08a27911bbCd0E01E8B1D97ec3cA187B6351D"),
            b"",
        ).
        settle("0xBf5617af623f1863c4abc900c5bebD5415a694e8", V4Constants.OPEN_DELTA.value, False).
        close_currency("0x0000000000000000000000000000000000000000").
        sweep("0xBf5617af623f1863c4abc900c5bebD5415a694e8", "0x29F08a27911bbCd0E01E8B1D97ec3cA187B6351D").
        sweep("0x0000000000000000000000000000000000000000", "0x29F08a27911bbCd0E01E8B1D97ec3cA187B6351D").
        build_v4_posm_call(codec.get_default_deadline()).
        build()
    )
    print(encoded_input)

    fct_name, decoded_input = codec.decode.function_input(encoded_input)
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


"""
<Function execute(bytes,bytes[])>
{
    'commands': b'\x14',
    'inputs': [
        (
            <Function modifyLiquidities(bytes,uint256)>,
            {
                'unlockData': {
                    'actions': b'\x02\x0b\x12\x14\x14',
                    'params': [
                        (
                            <Function MINT_POSITION((address,address,uint24,int24,address),int24,int24,uint256,uint128,uint128,address,bytes)>,  # noqa
                            {
                                'PoolKey': {
                                    'currency0': '0x0000000000000000000000000000000000000000',
                                    'currency1': '0xBf5617af623f1863c4abc900c5bebD5415a694e8',
                                    'fee': 3000,
                                    'tickSpacing': 50,
                                    'hooks': '0x0000000000000000000000000000000000000000'
                                },
                                'tickLower': -887272,
                                'tickUpper': 887272,
                                'liquidity': 10860507277202,
                                'amount0Max': 1000000000000000000,
                                'amount1Max': 1000000000000000000,
                                'recipient': '0x29F08a27911bbCd0E01E8B1D97ec3cA187B6351D',
                                'hookData': b''
                            }
                        ),
                        (
                            <Function SETTLE(address,uint256,bool)>,
                            {
                                'currency': '0xBf5617af623f1863c4abc900c5bebD5415a694e8',
                                'amount': 0,
                                'payerIsUser': False
                            }
                        ),
                        (
                            <Function CLOSE_CURRENCY(address)>,
                            {
                                'currency': '0x0000000000000000000000000000000000000000'
                            }
                        ),
                        (
                            <Function SWEEP(address,address)>,
                            {
                                'currency': '0xBf5617af623f1863c4abc900c5bebD5415a694e8',
                                'to': '0x29F08a27911bbCd0E01E8B1D97ec3cA187B6351D'
                            }
                        ),
                        (
                            <Function SWEEP(address,address)>,
                            {
                                'currency': '0x0000000000000000000000000000000000000000',
                                'to': '0x29F08a27911bbCd0E01E8B1D97ec3cA187B6351D'
                            }
                        )
                    ]
                },
                'deadline': 1735382780
            },
            {
                'revert_on_fail': True
            }
        )
    ]
}
"""


def test_v4_swap_exact_in():
    currency_in = Web3.to_checksum_address("0x0000000000000000000000000000000000000000")
    path_key_0 = codec.encode.v4_path_key(
        Web3.to_checksum_address("0xBf5617af623f1863c4abc900c5bebD5415a694e8"),
        3000,
        60,
    )
    path_key_1 = codec.encode.v4_path_key(
        Web3.to_checksum_address("0x2207B8c3d6b63675D9D14019e9F6b7f76ddF997f"),
        2500,
        55,
    )
    encoded_input = (
        codec.
        encode.
        chain().
        v4_swap().
        swap_exact_in(
            currency_in=currency_in,
            path_keys=[path_key_0, path_key_1],
            amount_in=Wei(1 * 10**18),
            amount_out_min=Wei(0),
        ).
        build_v4_swap().
        build(deadline=1735989153)
    )

    print(encoded_input)

    fct_name, decoded_input = codec.decode.function_input(encoded_input)
    print(fct_name)
    pp(decoded_input, indent=1, width=120)

    assert repr(fct_name) == "<Function execute(bytes,bytes[],uint256)>"
    assert int(decoded_input['commands'].hex(), 16) == 16
    assert repr(decoded_input['inputs'][0][0]) == "<Function V4_SWAP(bytes,bytes[])>"
    assert decoded_input['inputs'][0][1]["actions"] == b'\x07'
    assert repr(decoded_input['inputs'][0][1]["params"][0][0]) == "<Function SWAP_EXACT_IN(ExactInputParams)>"
    assert decoded_input['inputs'][0][1]["params"][0][1]["params"]["currencyIn"] == "0x0000000000000000000000000000000000000000"  # noqa E501
    path_keys = [to_camel_case(path_key_0), to_camel_case(path_key_1)]
    assert decoded_input['inputs'][0][1]["params"][0][1]["params"]["PathKeys"] == path_keys
    assert decoded_input['inputs'][0][1]["params"][0][1]["params"]["amountIn"] == 1000000000000000000
    assert decoded_input['inputs'][0][1]["params"][0][1]["params"]["amountOutMinimum"] == 0
    assert decoded_input['inputs'][0][2]["revert_on_fail"] is True
    assert decoded_input['deadline'] == 1735989153


"""
<Function execute(bytes,bytes[],uint256)>
{
    'commands': b'\x10',
    'inputs': [
        (
            <Function V4_SWAP(bytes,bytes[])>,
            {
                'actions': b'\x07',
                'params': [
                    (
                        <Function SWAP_EXACT_IN(ExactInputParams)>,
                        {
                            'params': {
                                'currencyIn': '0x0000000000000000000000000000000000000000',
                                'PathKeys': [
                                    {
                                        'intermediateCurrency': '0xBf5617af623f1863c4abc900c5bebD5415a694e8',
                                        'fee': 3000,
                                        'tickSpacing': 60,
                                        'hooks': '0x0000000000000000000000000000000000000000',
                                        'hookData': b''
                                    },
                                    {
                                        'intermediateCurrency': '0x2207B8c3d6b63675D9D14019e9F6b7f76ddF997f',
                                        'fee': 2500,
                                        'tickSpacing': 55,
                                        'hooks': '0x0000000000000000000000000000000000000000',
                                        'hookData': b''
                                    }
                                ],
                                'amountIn': 1000000000000000000,
                                'amountOutMinimum': 0
                            }
                        }
                    )
                ]
            },
            {
                'revert_on_fail': True
            }
        )
    ],
    'deadline': 1735989153
}
"""


def test_v4_swap_exact_in_2(w3):
    trx_hash = "0xa6ec9dabbd0f80bdb2d9d5f1da8006939af385ec83874363b5a85b99dde51164"
    router = RouterCodec(w3=w3)
    decoded_transaction = router.decode.transaction(trx_hash)
    print(decoded_transaction)

    currency_in = Web3.to_checksum_address("0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48")
    path_key_0 = codec.encode.v4_path_key(
        Web3.to_checksum_address("0x0000000000000000000000000000000000000000"),
        3000,
        60,
    )

    encoded_input = (
        codec.
        encode.
        chain().
        v4_swap().
        swap_exact_in(
            currency_in=currency_in,
            path_keys=[path_key_0, ],
            amount_in=Wei(1 * 10 ** 6),
            amount_out_min=Wei(0),
        ).
        build_v4_swap().
        build(deadline=1737747761)
    )

    print(encoded_input)
    assert b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00 \x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xa0\xb8i\x91\xc6!\x8b6\xc1\xd1\x9dJ.\x9e\xb0\xce6\x06\xebH\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x80\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x0fB@\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00 \x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x0b\xb8\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00<\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xa0\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'.hex() in encoded_input  # noqa

    decoded_input = codec.decode.function_input(encoded_input)
    print(decoded_input)


def test_v4_swap_exact_out_single():
    pool_key = codec.encode.v4_pool_key(
        "0x0000000000000000000000000000000000000000",
        "0xBf5617af623f1863c4abc900c5bebD5415a694e8",
        3000,
        50,
        "0x0123456789012345678901234567890123456789"
    )
    encoded_input = (
        codec.
        encode.
        chain().
        v4_swap().
        swap_exact_out_single(
            pool_key=pool_key,
            zero_for_one=True,
            amount_out=798750268136655870501951828,
            amount_in_max=500000000000000,
            hook_data=b"hook_data",
        ).
        settle_all("0x0000000000000000000000000000000000000000", 500000000000000).
        take(
            "0xBf5617af623f1863c4abc900c5bebD5415a694e8",
            Web3.to_checksum_address("0x0000000000000000000000000000000000000001"),
            V4Constants.OPEN_DELTA.value,
        ).
        build_v4_swap().
        build(deadline=1732612928)
    )

    print(encoded_input)

    fct_name, decoded_input = codec.decode.function_input(encoded_input)
    print(fct_name)
    pp(decoded_input, width=120)

    assert repr(fct_name) == "<Function execute(bytes,bytes[],uint256)>"
    assert int(decoded_input['commands'].hex(), 16) == 16
    assert repr(decoded_input['inputs'][0][0]) == "<Function V4_SWAP(bytes,bytes[])>"
    assert decoded_input['inputs'][0][1]["actions"] == b'\x08\x0c\x0e'

    assert repr(decoded_input['inputs'][0][1]["params"][0][0]) == "<Function SWAP_EXACT_OUT_SINGLE(((address,address,uint24,int24,address),bool,uint128,uint128,bytes))>"  # noqa E501
    exact_out_single_params = decoded_input['inputs'][0][1]["params"][0][1]["exact_out_single_params"]
    assert exact_out_single_params["PoolKey"] == to_camel_case(pool_key)
    assert exact_out_single_params["zeroForOne"]
    assert exact_out_single_params["amountOut"] == 798750268136655870501951828
    assert exact_out_single_params["amountInMaximum"] == 500000000000000
    assert exact_out_single_params["hookData"] == b'hook_data'

    assert repr(decoded_input['inputs'][0][1]["params"][1][0]) == "<Function SETTLE_ALL(address,uint256)>"
    assert decoded_input['inputs'][0][1]["params"][1][1]["currency"] == "0x0000000000000000000000000000000000000000"
    assert decoded_input['inputs'][0][1]["params"][1][1]["maxAmount"] == 500000000000000

    assert repr(decoded_input['inputs'][0][1]["params"][2][0]) == "<Function TAKE(address,address,uint256)>"
    assert decoded_input['inputs'][0][1]["params"][2][1]["currency"] == "0xBf5617af623f1863c4abc900c5bebD5415a694e8"
    assert decoded_input['inputs'][0][1]["params"][2][1]["recipient"] == "0x0000000000000000000000000000000000000001"
    assert decoded_input['inputs'][0][1]["params"][2][1]["amount"] == 0

    assert decoded_input['inputs'][0][2] == {'revert_on_fail': True}
    assert decoded_input['deadline'] == 1732612928

"""
<Function execute(bytes,bytes[],uint256)>
{'commands': b'\x10',
 'inputs': [
    (
        <Function V4_SWAP(bytes,bytes[])>,
        {
            'actions': b'\x08\x0c\x0e',
            'params': [
                (
                    <Function SWAP_EXACT_OUT_SINGLE(((address,address,uint24,int24,address),bool,uint128,uint128,bytes))>,  # noqa E501
                    {
                        'exact_out_single_params': {
                            'PoolKey': {
                                'currency0': '0x0000000000000000000000000000000000000000',
                                'currency1': '0xBf5617af623f1863c4abc900c5bebD5415a694e8',
                                'fee': 3000,
                                'tickSpacing': 50,
                                'hooks': '0x0123456789012345678901234567890123456789'
                            },
                            'zeroForOne': True,
                            'amountOut': 798750268136655870501951828,
                            'amountInMaximum': 500000000000000,
                            'hookData': b'hook_data'
                        }
                    }
                ),
                (
                    <Function SETTLE_ALL(address,uint256)>,
                    {
                        'currency': '0x0000000000000000000000000000000000000000',
                        'maxAmount': 500000000000000
                    }
                ),
                (
                    <Function TAKE(address,address,uint256)>,
                    {
                        'currency': '0xBf5617af623f1863c4abc900c5bebD5415a694e8',
                        'recipient': '0x0000000000000000000000000000000000000001',
                        'amount': 0
                    }
                )
            ]
        },
        {'revert_on_fail': True}
    )
],
'deadline': 1732612928
}

"""


def test_v4_swap_exact_out(w3):
    trx_hash = "0x966a949326d0b3aba5d41c7e8fda72b585fb5f5eb4378a2ccddb82836df92711"
    router = RouterCodec(w3=w3)
    decoded_transaction = router.decode.transaction(trx_hash)
    print(decoded_transaction)

    currency_out = Web3.to_checksum_address("0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48")
    path_key_0 = codec.encode.v4_path_key(
        Web3.to_checksum_address("0x0000000000000000000000000000000000000000"),
        3000,
        60,
    )

    encoded_input = (
        codec.
        encode.
        chain().
        v4_swap().
        swap_exact_out(
            currency_out=currency_out,
            path_keys=[path_key_0, ],
            amount_out=Wei(1002500),
            amount_in_max=Wei(346005692668603),
        ).
        build_v4_swap().
        build(deadline=1737749606)
    )

    print(encoded_input)

    decoded_input = codec.decode.function_input(encoded_input)
    print(decoded_input)
