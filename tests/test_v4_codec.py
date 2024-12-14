from pprint import pp

from web3 import Web3
from web3.types import HexStr

from uniswap_universal_router_decoder import RouterCodec


codec = RouterCodec()


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
    # assert pool_key_1


def test_pool_id():
    pool_key = codec.encode.v4_pool_key(
        "0x0000000000000000000000000000000000000000",
        "0x4200000000000000000000000000000000000006",
        3000,
        60,
    )
    expected_pool_id = HexStr("426f60e2b0ac279b6cf8b3806d23e1d15d21aba4d6973e30d36299e81e3f01a1")
    assert codec.encode.v4_pool_id(pool_key) == Web3.to_bytes(hexstr=expected_pool_id)


def test_v4_swap():
    pool_key = codec.encode.v4_pool_key(
        "0x0000000000000000000000000000000000000000",
        "0xBf5617af623f1863c4abc900c5bebD5415a694e8",
        3000,
        50,
    )
    encoded_input = codec.encode.chain().v4_swap().swap_exact_in_single(
        pool_key=pool_key,
        zero_for_one=False,
        amount_in=100000000000000,
        amount_out_min=798750268136655870501951828,
        hook_data=b'',
    ).build_v4().build(deadline=1732612928)

    print(encoded_input)

    fct_name, decoded_input = codec.decode.function_input(encoded_input)
    print(fct_name)
    pp(decoded_input, indent=4, width=120)


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
    pp(decoded_input, indent=4, width=120)

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
