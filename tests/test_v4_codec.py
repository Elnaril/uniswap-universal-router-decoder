from pprint import pp

import pytest
from web3 import Web3
from web3.types import (
    HexBytes,
    HexStr,
    Wei,
)

from uniswap_universal_router_decoder import (
    FunctionRecipient,
    PathKey,
    PoolKey,
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


# V4_SWAP - SWAP_EXACT_IN, SETTLE, TAKE
input_01 = HexBytes('0x3593564c000000000000000000000000000000000000000000000000000000000000006000000000000000000000000000000000000000000000000000000000000000a00000000000000000000000000000000000000000000000000000000069fa330c00000000000000000000000000000000000000000000000000000000000000011000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000100000000000000000000000000000000000000000000000000000000000000200000000000000000000000000000000000000000000000000000000000000400000000000000000000000000000000000000000000000000000000000000004000000000000000000000000000000000000000000000000000000000000000800000000000000000000000000000000000000000000000000000000000000003070b0e000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000030000000000000000000000000000000000000000000000000000000000000060000000000000000000000000000000000000000000000000000000000000026000000000000000000000000000000000000000000000000000000000000002e000000000000000000000000000000000000000000000000000000000000001e00000000000000000000000000000000000000000000000000000000000000020000000000000000000000000d04175024082f1490135f5d7054ade0538386fed00000000000000000000000000000000000000000000000000000000000000a000000000000000000000000000000000000000000000000000000000000001a00000000000000000000000000000000000000000000034f086ee6f2f763e3f6c0000000000000000000000000000000000000000000000000029863a7606da2a000000000000000000000000000000000000000000000000000000000000000100000000000000000000000000000000000000000000000000000000000000200000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000271000000000000000000000000000000000000000000000000000000000000000c8000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000a0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000060000000000000000000000000d04175024082f1490135f5d7054ade0538386fed00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000001000000000000000000000000000000000000000000000000000000000000006000000000000000000000000000000000000000000000000000000000000000000000000000000000000000002de9481bae36573ea2a7b949260470c6c044867c0000000000000000000000000000000000000000000000000000000000000000')  # noqa: E501
expected_decoded_input_01 = """(<Function execute(bytes,bytes[],uint256)>, {'commands': b'\\x10', 'inputs': [(<Function V4_SWAP(bytes,bytes[])>, {'actions': b'\\x07\\x0b\\x0e', 'params': [(<Function SWAP_EXACT_IN(ExactInputParams)>, {'params': {'currencyIn': '0xd04175024082F1490135F5D7054aDE0538386Fed', 'PathKeys': [{'intermediateCurrency': '0x0000000000000000000000000000000000000000', 'fee': 10000, 'tickSpacing': 200, 'hooks': '0x0000000000000000000000000000000000000000', 'hookData': b''}], 'minHopPriceX36': [], 'amountIn': 249999998517807020916588, 'amountOutMinimum': 11688059691522602}}), (<Function SETTLE(address,uint256,bool)>, {'currency': '0xd04175024082F1490135F5D7054aDE0538386Fed', 'amount': 0, 'payerIsUser': True}), (<Function TAKE(address,address,uint256)>, {'currency': '0x0000000000000000000000000000000000000000', 'recipient': '0x2De9481BAE36573Ea2A7b949260470C6C044867c', 'amount': 0})]}, {'revert_on_fail': True})], 'deadline': 1778004748})"""  # noqa: E501


def test_v4_swap_exact_in_settle_take(codec: RouterCodec):
    decoded_input = codec.decode.function_input(input_01)
    print("decoded_input:", decoded_input)
    assert expected_decoded_input_01 == repr(decoded_input)

    path_key = PathKey(
        intermediate_currency=Web3.to_checksum_address("0x0000000000000000000000000000000000000000"),
        fee=10000,
        tick_spacing=200,
        hooks=Web3.to_checksum_address("0x0000000000000000000000000000000000000000"),
        hook_data=b"",
    )
    encoded_input = (
        codec.
        encode().
        v4_swap().
        swap_exact_in(
            currency_in=Web3.to_checksum_address("0xd04175024082F1490135F5D7054aDE0538386Fed"),
            path_keys=[
                path_key,
            ],
            amount_in=249999998517807020916588,
            amount_out_min=11688059691522602,
            min_hop_price_x36=[],
        ).
        settle(
            currency=Web3.to_checksum_address("0xd04175024082F1490135F5D7054aDE0538386Fed"),
            amount=0,
            payer_is_user=True,
        ).
        take(
            currency=Web3.to_checksum_address("0x0000000000000000000000000000000000000000"),
            recipient=Web3.to_checksum_address("0x2De9481BAE36573Ea2A7b949260470C6C044867c"),
            amount=0,
        ).
        build_v4_swap().
        build(deadline=1778004748)
    )
    assert input_01 == HexBytes(Web3.to_bytes(hexstr=encoded_input))


# V4_SWAP - SWAP_EXACT_OUT, SETTLE, TAKE - SWEEP
input_02 = HexBytes('0x3593564c000000000000000000000000000000000000000000000000000000000000006000000000000000000000000000000000000000000000000000000000000000a00000000000000000000000000000000000000000000000000000000069fa5151000000000000000000000000000000000000000000000000000000000000000210040000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000002000000000000000000000000000000000000000000000000000000000000004000000000000000000000000000000000000000000000000000000000000004600000000000000000000000000000000000000000000000000000000000000400000000000000000000000000000000000000000000000000000000000000004000000000000000000000000000000000000000000000000000000000000000800000000000000000000000000000000000000000000000000000000000000003090b0e000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000030000000000000000000000000000000000000000000000000000000000000060000000000000000000000000000000000000000000000000000000000000026000000000000000000000000000000000000000000000000000000000000002e000000000000000000000000000000000000000000000000000000000000001e0000000000000000000000000000000000000000000000000000000000000002000000000000000000000000044b28991b167582f18ba0259e0173176ca12550500000000000000000000000000000000000000000000000000000000000000a000000000000000000000000000000000000000000000000000000000000001a00000000000000000000000000000000000000000000000001bc16d674ec800000000000000000000000000000000000000000000000000001026c649b068ebfb0000000000000000000000000000000000000000000000000000000000000001000000000000000000000000000000000000000000000000000000000000002000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000002710000000000000000000000000000000000000000000000000000000000000003c000000000000000000000000e54082dfbf044b6a8f584bdddb90a22d5613c44000000000000000000000000000000000000000000000000000000000000000a0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000060000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000001000000000000000000000000000000000000000000000000000000000000006000000000000000000000000044b28991b167582f18ba0259e0173176ca125505000000000000000000000000dc780bf167e46cb2de0e8db47381186dbf514831000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000600000000000000000000000000000000000000000000000000000000000000000000000000000000000000000dc780bf167e46cb2de0e8db47381186dbf5148310000000000000000000000000000000000000000000000000000000000000000')  # noqa: E501
expected_decoded_input_02 = """(<Function execute(bytes,bytes[],uint256)>, {'commands': b'\\x10\\x04', 'inputs': [(<Function V4_SWAP(bytes,bytes[])>, {'actions': b'\\t\\x0b\\x0e', 'params': [(<Function SWAP_EXACT_OUT(ExactOutputParams)>, {'params': {'currencyOut': '0x44b28991B167582F18BA0259e0173176ca125505', 'PathKeys': [{'intermediateCurrency': '0x0000000000000000000000000000000000000000', 'fee': 10000, 'tickSpacing': 60, 'hooks': '0xe54082DfBf044B6a8F584bdDdb90a22d5613C440', 'hookData': b''}], 'minHopPriceX36': [], 'amountOut': 2000000000000000000, 'amountInMaximum': 1163835573516430331}}), (<Function SETTLE(address,uint256,bool)>, {'currency': '0x0000000000000000000000000000000000000000', 'amount': 0, 'payerIsUser': True}), (<Function TAKE(address,address,uint256)>, {'currency': '0x44b28991B167582F18BA0259e0173176ca125505', 'recipient': '0xDC780BF167E46cb2dE0E8Db47381186dbF514831', 'amount': 0})]}, {'revert_on_fail': True}), (<Function SWEEP(address,address,uint256)>, {'token': '0x0000000000000000000000000000000000000000', 'recipient': '0xDC780BF167E46cb2dE0E8Db47381186dbF514831', 'amountMin': 0}, {'revert_on_fail': True})], 'deadline': 1778012497})"""  # noqa: E501


def test_v4_swap_exact_out_settle_take(codec: RouterCodec):
    decoded_input = codec.decode.function_input(input_02)
    print("decoded_input:", decoded_input)
    assert expected_decoded_input_02 == repr(decoded_input)

    path_key = PathKey(
        intermediate_currency=Web3.to_checksum_address("0x0000000000000000000000000000000000000000"),
        fee=10000,
        tick_spacing=60,
        hooks=Web3.to_checksum_address("0xe54082DfBf044B6a8F584bdDdb90a22d5613C440"),
        hook_data=b"",
    )
    encoded_input = (
        codec.
        encode().
        v4_swap().
        swap_exact_out(
            currency_out=Web3.to_checksum_address("0x44b28991B167582F18BA0259e0173176ca125505"),
            path_keys=[
                path_key,
            ],
            amount_out=2000000000000000000,
            amount_in_max=1163835573516430331,
            min_hop_price_x36=[],
        ).
        settle(
            currency=Web3.to_checksum_address("0x0000000000000000000000000000000000000000"),
            amount=0,
            payer_is_user=True,
        ).
        take(
            currency=Web3.to_checksum_address("0x44b28991B167582F18BA0259e0173176ca125505"),
            recipient=Web3.to_checksum_address("0xDC780BF167E46cb2dE0E8Db47381186dbF514831"),
            amount=0,
        ).
        build_v4_swap().
        sweep(
            function_recipient=FunctionRecipient.CUSTOM,
            token_address=Web3.to_checksum_address("0x0000000000000000000000000000000000000000"),
            amount_min=Wei(0),
            custom_recipient=Web3.to_checksum_address("0xDC780BF167E46cb2dE0E8Db47381186dbF514831"),
        ).
        build(deadline=1778012497)
    )
    assert input_02 == HexBytes(Web3.to_bytes(hexstr=encoded_input))


# V4_SWAP - SWAP_EXACT_IN_SINGLE, SETTLE_ALL, TAKE_ALL
input_03 = HexBytes('0x3593564c000000000000000000000000000000000000000000000000000000000000006000000000000000000000000000000000000000000000000000000000000000a00000000000000000000000000000000000000000000000000000000069fbf1ef00000000000000000000000000000000000000000000000000000000000000011000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000100000000000000000000000000000000000000000000000000000000000000200000000000000000000000000000000000000000000000000000000000000360000000000000000000000000000000000000000000000000000000000000004000000000000000000000000000000000000000000000000000000000000000800000000000000000000000000000000000000000000000000000000000000003060c0f00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000003000000000000000000000000000000000000000000000000000000000000006000000000000000000000000000000000000000000000000000000000000002000000000000000000000000000000000000000000000000000000000000000260000000000000000000000000000000000000000000000000000000000000018000000000000000000000000000000000000000000000000000000000000000200000000000000000000000000000000000000000000000000000000000000000000000000000000000000000be57e9c04387a1bceb89c5dfb488b99343fb9f280000000000000000000000000000000000000000000000000000000000000bb8000000000000000000000000000000000000000000000000000000000000003c000000000000000000000000d11b0ebcd58c978807aa3a438f0915a394ed20cc000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000046cbd056bca18e5260500000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000014000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000040000000000000000000000000be57e9c04387a1bceb89c5dfb488b99343fb9f2800000000000000000000000000000000000000000000046cbd056bca18e52605000000000000000000000000000000000000000000000000000000000000004000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000')  # noqa: E501
expected_decoded_input_03 = """(<Function execute(bytes,bytes[],uint256)>, {'commands': b'\\x10', 'inputs': [(<Function V4_SWAP(bytes,bytes[])>, {'actions': b'\\x06\\x0c\\x0f', 'params': [(<Function SWAP_EXACT_IN_SINGLE(((address,address,uint24,int24,address),bool,uint128,uint128,uint256,bytes))>, {'exact_in_single_params': {'PoolKey': {'currency0': '0x0000000000000000000000000000000000000000', 'currency1': '0xbE57e9c04387a1bCeB89C5Dfb488B99343FB9f28', 'fee': 3000, 'tickSpacing': 60, 'hooks': '0xD11B0eBcD58C978807aA3A438f0915A394ed20CC'}, 'zeroForOne': False, 'amountIn': 20895334702603009598981, 'amountOutMinimum': 0, 'minHopPriceX36': 0, 'hookData': b''}}), (<Function SETTLE_ALL(address,uint256)>, {'currency': '0xbE57e9c04387a1bCeB89C5Dfb488B99343FB9f28', 'maxAmount': 20895334702603009598981}), (<Function TAKE_ALL(address,uint256)>, {'currency': '0x0000000000000000000000000000000000000000', 'minAmount': 0})]}, {'revert_on_fail': True})], 'deadline': 1778119151})"""  # noqa: E501


def test_v4_swap_exact_in_single_settle_all_take_all(codec: RouterCodec):
    decoded_input = codec.decode.function_input(input_03)
    print("decoded_input:", decoded_input)
    assert expected_decoded_input_03 == repr(decoded_input)

    pool_key = PoolKey(
        currency_0=Web3.to_checksum_address("0x0000000000000000000000000000000000000000"),
        currency_1=Web3.to_checksum_address("0xbE57e9c04387a1bCeB89C5Dfb488B99343FB9f28"),
        fee=3000,
        tick_spacing=60,
        hooks=Web3.to_checksum_address("0xD11B0eBcD58C978807aA3A438f0915A394ed20CC"),
    )

    encoded_input = (
        codec.
        encode().
        v4_swap().
        swap_exact_in_single(
            pool_key=pool_key,
            zero_for_one=False,
            amount_in=Wei(20895334702603009598981),
            amount_out_min=Wei(0),
        ).
        settle_all(
            currency=Web3.to_checksum_address("0xbE57e9c04387a1bCeB89C5Dfb488B99343FB9f28"),
            max_amount=Wei(20895334702603009598981),
        ).take_all(
            currency=Web3.to_checksum_address("0x0000000000000000000000000000000000000000"),
            min_amount=Wei(0),
        ).
        build_v4_swap().
        build(deadline=1778119151)
    )
    assert input_03 == HexBytes(Web3.to_bytes(hexstr=encoded_input))


# V4_SWAP - SWAP_EXACT_IN, SETTLE, TAKE_PORTION, TAKE
input_04 = HexBytes('0x3593564c000000000000000000000000000000000000000000000000000000000000006000000000000000000000000000000000000000000000000000000000000000a00000000000000000000000000000000000000000000000000000000069f8ff4f000000000000000000000000000000000000000000000000000000000000000110000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000001000000000000000000000000000000000000000000000000000000000000002000000000000000000000000000000000000000000000000000000000000004a0000000000000000000000000000000000000000000000000000000000000004000000000000000000000000000000000000000000000000000000000000000800000000000000000000000000000000000000000000000000000000000000004070b100e000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000004000000000000000000000000000000000000000000000000000000000000008000000000000000000000000000000000000000000000000000000000000002800000000000000000000000000000000000000000000000000000000000000300000000000000000000000000000000000000000000000000000000000000038000000000000000000000000000000000000000000000000000000000000001e00000000000000000000000000000000000000000000000000000000000000020000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000a000000000000000000000000000000000000000000000000000000000000001a00000000000000000000000000000000000000000000000000001c6bf526340000000000000000000000000000000000000000000000000000000000000110a8800000000000000000000000000000000000000000000000000000000000000010000000000000000000000000000000000000000000000000000000000000020000000000000000000000000dac17f958d2ee523a2206206994597c13d831ec700000000000000000000000000000000000000000000000000000000000000640000000000000000000000000000000000000000000000000000000000000001000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000a00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000600000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000010000000000000000000000000000000000000000000000000000000000000060000000000000000000000000dac17f958d2ee523a2206206994597c13d831ec7000000000000000000000000adf72360e07ba2fa9e371b69857a3b083370f91900000000000000000000000000000000000000000000000000000000000000500000000000000000000000000000000000000000000000000000000000000060000000000000000000000000dac17f958d2ee523a2206206994597c13d831ec70000000000000000000000000add8f8b221b989245328b76d7a5c8f6b82233de0000000000000000000000000000000000000000000000000000000000000000')  # noqa: E501
expected_decoded_input_04 = """(<Function execute(bytes,bytes[],uint256)>, {'commands': b'\\x10', 'inputs': [(<Function V4_SWAP(bytes,bytes[])>, {'actions': b'\\x07\\x0b\\x10\\x0e', 'params': [(<Function SWAP_EXACT_IN(ExactInputParams)>, {'params': {'currencyIn': '0x0000000000000000000000000000000000000000', 'PathKeys': [{'intermediateCurrency': '0xdAC17F958D2ee523a2206206994597C13D831ec7', 'fee': 100, 'tickSpacing': 1, 'hooks': '0x0000000000000000000000000000000000000000', 'hookData': b''}], 'minHopPriceX36': [], 'amountIn': 500000000000000, 'amountOutMinimum': 1116808}}), (<Function SETTLE(address,uint256,bool)>, {'currency': '0x0000000000000000000000000000000000000000', 'amount': 0, 'payerIsUser': True}), (<Function TAKE_PORTION(address,address,uint256)>, {'currency': '0xdAC17F958D2ee523a2206206994597C13D831ec7', 'recipient': '0xAdF72360e07ba2FA9e371B69857A3b083370F919', 'bips': 80}), (<Function TAKE(address,address,uint256)>, {'currency': '0xdAC17F958D2ee523a2206206994597C13D831ec7', 'recipient': '0x0aDd8F8b221b989245328b76D7A5C8F6B82233de', 'amount': 0})]}, {'revert_on_fail': True})], 'deadline': 1777925967})"""  # noqa: E501


def test_v4_swap_exact_in_settle_take_portion_take(codec: RouterCodec):
    decoded_input = codec.decode.function_input(input_04)
    print("decoded_input:", decoded_input)
    assert expected_decoded_input_04 == repr(decoded_input)

    path_key = PathKey(
        intermediate_currency=Web3.to_checksum_address("0xdAC17F958D2ee523a2206206994597C13D831ec7"),
        fee=100,
        tick_spacing=1,
        hooks=Web3.to_checksum_address("0x0000000000000000000000000000000000000000"),
        hook_data=b"",
    )
    encoded_input = (
        codec.
        encode().
        v4_swap().
        swap_exact_in(
            currency_in=Web3.to_checksum_address("0x0000000000000000000000000000000000000000"),
            path_keys=[
                path_key,
            ],
            amount_in=500000000000000,
            amount_out_min=1116808,
            min_hop_price_x36=[],
        ).
        settle(
            currency=Web3.to_checksum_address("0x0000000000000000000000000000000000000000"),
            amount=0,
            payer_is_user=True,
        ).
        take_portion(
            currency=Web3.to_checksum_address("0xdAC17F958D2ee523a2206206994597C13D831ec7"),
            recipient=Web3.to_checksum_address("0xAdF72360e07ba2FA9e371B69857A3b083370F919"),
            bips=80,
        ).
        take(
            currency=Web3.to_checksum_address("0xdAC17F958D2ee523a2206206994597C13D831ec7"),
            recipient=Web3.to_checksum_address("0x0aDd8F8b221b989245328b76D7A5C8F6B82233de"),
            amount=0,
        ).
        build_v4_swap().
        build(deadline=1777925967)
    )
    assert input_04 == HexBytes(Web3.to_bytes(hexstr=encoded_input))


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


@pytest.mark.parametrize(
    'actions_input, params_input, err_msg',
    (
        (b'\x06\x0f', [b'\x00'], 'Number of actions 2 is different from number of params: 1'),
        (b'\x00', [b'\x00', b'\x06\x0f'], 'Number of actions 1 is different from number of params: 2')
    )
)
def test_decode_v4_actions_unequal_param_len(actions_input, params_input, err_msg):
    with pytest.raises(ValueError) as err:
        codec.decode._v4_decoder._decode_v4_actions(actions=actions_input, params=params_input)
    assert str(err.value) == err_msg


@pytest.mark.parametrize(
    'actions_input, params_input, expected_result',
    (
        (b'\x12\x34', [b'\x11\x22', b'\xff'], ['1122', 'ff']),
        (b'\xff', [b'\x11\x22'], ['1122']),
    )
)
def test_decode_v4_actions(actions_input, params_input, expected_result):
    result = codec.decode._v4_decoder._decode_v4_actions(actions=actions_input, params=params_input)
    assert result == expected_result


@pytest.mark.parametrize(
    'currency_0_input, currency_1_input, expected_result_func',
    (
        (
            Web3.to_checksum_address('0x0000000000000000000000000000000000000000'),
            Web3.to_checksum_address('0xBf5617af623f1863c4abc900c5bebD5415a694e8'),
            '<Function SETTLE_PAIR(address,address)>',
        ),
        (
            Web3.to_checksum_address('0xBf5617af623f1863c4abc900c5bebD5415a694e8'),
            Web3.to_checksum_address('0x0000000000000000000000000000000000000000'),
            '<Function SETTLE_PAIR(address,address)>',
        )
    )
)
def test_v4_settle_pair(currency_0_input, currency_1_input, expected_result_func):
    encoded_input = (
        codec
        .encode
        .chain()
        .v4_posm_call()
        .settle_pair(currency_0=currency_0_input, currency_1=currency_1_input)
        .build_v4_posm_call(deadline=codec.get_default_deadline())
        .build(deadline=1732612928)
    )
    result = codec.decode.function_input(input_data=encoded_input)
    assert repr(result[1]['inputs'][0][1]['unlockData']['params'][0][0]) == expected_result_func
    assert result[1]['inputs'][0][1]['unlockData']['params'][0][1]['currency0'] == currency_0_input
    assert result[1]['inputs'][0][1]['unlockData']['params'][0][1]['currency1'] == currency_1_input


@pytest.mark.parametrize(
    'amount_input, expected_result_func',
    (
        (Wei(123456789012345678), '<Function WRAP(uint256)>'),
        (Wei(0), '<Function WRAP(uint256)>')
    )
)
def test_v4_wrap_eth(amount_input, expected_result_func):
    encoded_input = (
        codec
        .encode
        .chain()
        .v4_posm_call()
        .wrap_eth(amount=amount_input)
        .build_v4_posm_call(deadline=codec.get_default_deadline())
        .build(deadline=1732612928)
    )
    result = codec.decode.function_input(input_data=encoded_input)
    assert repr(result[1]['inputs'][0][1]['unlockData']['params'][0][0]) == expected_result_func
    assert result[1]['inputs'][0][1]['unlockData']['params'][0][1]['amount'] == amount_input


@pytest.mark.parametrize(
    'amount_input, expected_result_func',
    (
        (Wei(123456789012345678), '<Function UNWRAP(uint256)>'),
        (Wei(0), '<Function UNWRAP(uint256)>')
    )
)
def test_v4_unwrap_weth(amount_input, expected_result_func):
    encoded_input = (
        codec
        .encode
        .chain()
        .v4_posm_call()
        .unwrap_weth(amount=amount_input)
        .build_v4_posm_call(deadline=codec.get_default_deadline())
        .build(deadline=1732612928)
    )
    result = codec.decode.function_input(input_data=encoded_input)
    assert repr(result[1]['inputs'][0][1]['unlockData']['params'][0][0]) == expected_result_func
    assert result[1]['inputs'][0][1]['unlockData']['params'][0][1]['amount'] == amount_input


@pytest.mark.parametrize(
    'currency_0_input, currency_1_input, recipient_input, expected_result_func',
    (
        (
            Web3.to_checksum_address('0x0000000000000000000000000000000000000000'),
            Web3.to_checksum_address('0xBf5617af623f1863c4abc900c5bebD5415a694e8'),
            Web3.to_checksum_address('0x29F08a27911bbCd0E01E8B1D97ec3cA187B6351D'),
            '<Function TAKE_PAIR(address,address,address)>'
        ),
        (
            Web3.to_checksum_address('0xBf5617af623f1863c4abc900c5bebD5415a694e8'),
            Web3.to_checksum_address('0x0000000000000000000000000000000000000000'),
            Web3.to_checksum_address('0x0000000000000000000000000000000000000000'),
            '<Function TAKE_PAIR(address,address,address)>'
        )
    )
)
def test_v4_take_pair(currency_0_input, currency_1_input, recipient_input, expected_result_func):
    encoded_input = (
        codec
        .encode
        .chain()
        .v4_posm_call()
        .take_pair(
            currency_0=currency_0_input,
            currency_1=currency_1_input,
            recipient=recipient_input
        )
        .build_v4_posm_call(deadline=codec.get_default_deadline())
        .build(deadline=1732612928)
    )
    result = codec.decode.function_input(input_data=encoded_input)
    assert repr(result[1]['inputs'][0][1]['unlockData']['params'][0][0]) == expected_result_func
    assert result[1]['inputs'][0][1]['unlockData']['params'][0][1]['currency0'] == currency_0_input
    assert result[1]['inputs'][0][1]['unlockData']['params'][0][1]['currency1'] == currency_1_input
    assert result[1]['inputs'][0][1]['unlockData']['params'][0][1]['recipient'] == recipient_input


@pytest.mark.parametrize(
    'currency_input, amount_max_input, expected_result_func',
    (
        (
            Web3.to_checksum_address('0x0000000000000000000000000000000000000000'),
            1,
            '<Function CLEAR_OR_TAKE(address,uint256)>'
        ),
        (
            Web3.to_checksum_address('0xBf5617af623f1863c4abc900c5bebD5415a694e8'),
            2,
            '<Function CLEAR_OR_TAKE(address,uint256)>'
        )
    )
)
def test_v4_clear_or_take(currency_input, amount_max_input, expected_result_func):
    encoded_input = (
        codec
        .encode
        .chain()
        .v4_posm_call()
        .clear_or_take(currency=currency_input, amount_max=amount_max_input)
        .build_v4_posm_call(deadline=codec.get_default_deadline())
        .build(deadline=1732612928)
    )
    result = codec.decode.function_input(input_data=encoded_input)
    assert repr(result[1]['inputs'][0][1]['unlockData']['params'][0][0]) == expected_result_func
    assert result[1]['inputs'][0][1]['unlockData']['params'][0][1]['currency'] == currency_input
    assert result[1]['inputs'][0][1]['unlockData']['params'][0][1]['amountMax'] == amount_max_input


@pytest.mark.parametrize(
    'currency_input, recipient_input, bips_input, expected_result_func',
    (
        (
            Web3.to_checksum_address('0x0000000000000000000000000000000000000000'),
            Web3.to_checksum_address('0xBf5617af623f1863c4abc900c5bebD5415a694e8'),
            1,
            '<Function TAKE_PORTION(address,address,uint256)>'
        ),
        (
            Web3.to_checksum_address('0xBf5617af623f1863c4abc900c5bebD5415a694e8'),
            Web3.to_checksum_address('0x0000000000000000000000000000000000000000'),
            2,
            '<Function TAKE_PORTION(address,address,uint256)>'
        )
    )
)
def test_v4_take_portion(currency_input, recipient_input, bips_input, expected_result_func):
    encoded_input = (
        codec
        .encode
        .chain()
        .v4_swap()
        .take_portion(currency=currency_input, recipient=recipient_input, bips=bips_input)
        .build_v4_swap()
        .build(deadline=1732612928)
    )
    result = codec.decode.function_input(input_data=encoded_input)
    assert repr(result[1]['inputs'][0][1]['params'][0][0]) == expected_result_func
    assert result[1]['inputs'][0][1]['params'][0][1]['currency'] == currency_input
    assert result[1]['inputs'][0][1]['params'][0][1]['recipient'] == recipient_input
    assert result[1]['inputs'][0][1]['params'][0][1]['bips'] == bips_input
