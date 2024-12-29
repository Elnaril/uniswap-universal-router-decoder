from eth_account import Account
from eth_account.datastructures import SignedMessage
from eth_account.signers.local import LocalAccount
from eth_utils import keccak
import pytest
from web3 import Web3
from web3.types import (
    HexBytes,
    HexStr,
    Wei,
)

from uniswap_universal_router_decoder import (
    FunctionRecipient,
    TransactionSpeed,
)
from uniswap_universal_router_decoder._constants import _ur_address  # noqa
from uniswap_universal_router_decoder._encoder import _ChainedFunctionBuilder  # noqa
from uniswap_universal_router_decoder._enums import _RouterFunction  # noqa


@pytest.mark.parametrize(
    "function_recipient, custom_recipient, expected_recipient, expected_exception",
    (
        (FunctionRecipient.SENDER, None, Web3.to_checksum_address("0x0000000000000000000000000000000000000001"), None),
        (FunctionRecipient.ROUTER, None, Web3.to_checksum_address("0x0000000000000000000000000000000000000002"), None),
        (FunctionRecipient.CUSTOM, Web3.to_checksum_address("0xB4FBF271143F4FBf7B91A5ded31805e42b2208d6"), Web3.to_checksum_address("0xB4FBF271143F4FBf7B91A5ded31805e42b2208d6"), None),  # noqa E501
        (FunctionRecipient.CUSTOM, None, None, ValueError),
        (FunctionRecipient.CUSTOM, "moo", None, ValueError),
    )
)
def test_get_recipient(function_recipient, custom_recipient, expected_recipient, expected_exception):
    if expected_exception:
        with pytest.raises(expected_exception):
            _ChainedFunctionBuilder._get_recipient(function_recipient, custom_recipient)
    else:
        assert expected_recipient == _ChainedFunctionBuilder._get_recipient(function_recipient, custom_recipient)


def test_chain_wrap_eth(codec):
    encoded_input = codec.encode.chain().wrap_eth(FunctionRecipient.SENDER, Wei(10**17), None).build(1676825611)
    assert encoded_input == HexStr("0x3593564c000000000000000000000000000000000000000000000000000000000000006000000000000000000000000000000000000000000000000000000000000000a00000000000000000000000000000000000000000000000000000000063f2540b00000000000000000000000000000000000000000000000000000000000000010b000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000001000000000000000000000000000000000000000000000000000000000000002000000000000000000000000000000000000000000000000000000000000000400000000000000000000000000000000000000000000000000000000000000001000000000000000000000000000000000000000000000000016345785d8a0000")  # noqa E501


def test_chain_unwrap_weth(codec):
    encoded_input = codec.encode.chain().unwrap_weth(FunctionRecipient.SENDER, Wei(10**17), None).build(1676825611)
    assert encoded_input == HexStr("0x3593564c000000000000000000000000000000000000000000000000000000000000006000000000000000000000000000000000000000000000000000000000000000a00000000000000000000000000000000000000000000000000000000063f2540b00000000000000000000000000000000000000000000000000000000000000010c000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000001000000000000000000000000000000000000000000000000000000000000002000000000000000000000000000000000000000000000000000000000000000400000000000000000000000000000000000000000000000000000000000000001000000000000000000000000000000000000000000000000016345785d8a0000")  # noqa E501


def test_chain_v2_swap_exact_in(codec):
    encoded_input = codec.encode.chain().v2_swap_exact_in(
        FunctionRecipient.SENDER,
        Wei(10**17),
        Wei(0),
        [
            Web3.to_checksum_address("0xB4FBF271143F4FBf7B91A5ded31805e42b2208d6"),
            Web3.to_checksum_address("0x326C977E6efc84E512bB9C30f76E30c160eD06FB"),
        ],
        payer_is_sender=True,
    ).build(1676919287)
    assert encoded_input == HexStr("0x3593564c000000000000000000000000000000000000000000000000000000000000006000000000000000000000000000000000000000000000000000000000000000a00000000000000000000000000000000000000000000000000000000063f3c1f7000000000000000000000000000000000000000000000000000000000000000108000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000001000000000000000000000000000000000000000000000000000000000000002000000000000000000000000000000000000000000000000000000000000001000000000000000000000000000000000000000000000000000000000000000001000000000000000000000000000000000000000000000000016345785d8a0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000a000000000000000000000000000000000000000000000000000000000000000010000000000000000000000000000000000000000000000000000000000000002000000000000000000000000b4fbf271143f4fbf7b91a5ded31805e42b2208d6000000000000000000000000326c977e6efc84e512bb9c30f76e30c160ed06fb")  # noqa E501


def test_chain_v2_swap_exact_in_from_balance(codec):
    encoded_input = codec.encode.chain().v2_swap_exact_in_from_balance(
        FunctionRecipient.SENDER,
        Wei(0),
        [
            Web3.to_checksum_address("0xB4FBF271143F4FBf7B91A5ded31805e42b2208d6"),
            Web3.to_checksum_address("0x326C977E6efc84E512bB9C30f76E30c160eD06FB"),
        ],
    ).build(1676919287)
    assert encoded_input == HexStr("0x3593564c000000000000000000000000000000000000000000000000000000000000006000000000000000000000000000000000000000000000000000000000000000a00000000000000000000000000000000000000000000000000000000063f3c1f70000000000000000000000000000000000000000000000000000000000000001080000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000010000000000000000000000000000000000000000000000000000000000000020000000000000000000000000000000000000000000000000000000000000010000000000000000000000000000000000000000000000000000000000000000018000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000a000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000002000000000000000000000000b4fbf271143f4fbf7b91a5ded31805e42b2208d6000000000000000000000000326c977e6efc84e512bb9c30f76e30c160ed06fb")  # noqa E501


def test_chain_v2_swap_exact_out(codec):
    # https://etherscan.io/tx/0xd3abc2fe01376ebaff699a944ae3fb94b00ab899e8ed845a5e22ae120e83cb9e
    encoded_input = codec.encode.chain().v2_swap_exact_out(
        FunctionRecipient.SENDER,
        Wei(5000000000000000000000000),
        Wei(1364343969533288399),
        [
            Web3.to_checksum_address("0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2"),
            Web3.to_checksum_address("0xC74B43cC61b627667a608c3F650c2558F88028a1"),
        ],
        payer_is_sender=True,
    ).build(1678369883)
    assert encoded_input == HexStr("0x3593564c000000000000000000000000000000000000000000000000000000000000006000000000000000000000000000000000000000000000000000000000000000a0000000000000000000000000000000000000000000000000000000006409e45b0000000000000000000000000000000000000000000000000000000000000001090000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000010000000000000000000000000000000000000000000000000000000000000020000000000000000000000000000000000000000000000000000000000000010000000000000000000000000000000000000000000000000000000000000000010000000000000000000000000000000000000000000422ca8b0a00a42500000000000000000000000000000000000000000000000000000012ef1f9c977a5fcf00000000000000000000000000000000000000000000000000000000000000a000000000000000000000000000000000000000000000000000000000000000010000000000000000000000000000000000000000000000000000000000000002000000000000000000000000c02aaa39b223fe8d0a0e5c4f27ead9083c756cc2000000000000000000000000c74b43cc61b627667a608c3f650c2558f88028a1")  # noqa E501


path_seq_1 = (
    Web3.to_checksum_address("0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2"),
    3000,
    Web3.to_checksum_address("0xf3dcbc6D72a4E1892f7917b7C43b74131Df8480e"),
)
expected_v3_path_1 = Web3.to_bytes(hexstr=HexStr("0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2000bb8f3dcbc6D72a4E1892f7917b7C43b74131Df8480e"))  # noqa E501

path_seq_2 = (
    Web3.to_checksum_address("0xdAC17F958D2ee523a2206206994597C13D831ec7"),
    500,
    Web3.to_checksum_address("0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2"),
    3000,
    Web3.to_checksum_address("0xABe580E7ee158dA464b51ee1a83Ac0289622e6be"),
)
expected_v3_path_2 = Web3.to_bytes(hexstr=HexStr("0xABe580E7ee158dA464b51ee1a83Ac0289622e6be000bb8C02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc20001F4dAC17F958D2ee523a2206206994597C13D831ec7"))  # noqa E501


@pytest.mark.parametrize(
    "fn_name, path_seq, expected_v3_path, expected_exception",
    (
        ("V3_SWAP_EXACT_IN", path_seq_1, expected_v3_path_1, None),
        ("V2_SWAP_EXACT_OUT", path_seq_1, expected_v3_path_1, ValueError),
        ("V3_SWAP_EXACT_IN", path_seq_1[:2], expected_v3_path_1, ValueError),
        ("V3_SWAP_EXACT_OUT", path_seq_2, expected_v3_path_2, None),
    )
)
def test_encode_v3_path(fn_name, path_seq, expected_v3_path, expected_exception, codec):
    if expected_exception:
        with pytest.raises(expected_exception):
            _ = codec.encode.v3_path(fn_name, path_seq)
    else:
        assert expected_v3_path == codec.encode.v3_path(fn_name, path_seq)


def test_chain_v3_swap_exact_in(codec):
    # https://etherscan.io/tx/0x8bc2aa83ec3749a9987415a20052afec90b8a700092d83a4d65b9e5c227403f1
    encoded_input = codec.encode.chain().v3_swap_exact_in(
        FunctionRecipient.SENDER,
        Wei(229292136388),
        Wei(943146926),
        [
            Web3.to_checksum_address("0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48"),
            500,
            Web3.to_checksum_address("0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2"),
            500,
            Web3.to_checksum_address("0x2260FAC5E5542a773Aa44fBCfeDf7C193bc2C599"),
        ],
        payer_is_sender=True,
    ).build(1677080627)
    assert encoded_input == HexStr("0x3593564c000000000000000000000000000000000000000000000000000000000000006000000000000000000000000000000000000000000000000000000000000000a00000000000000000000000000000000000000000000000000000000063f638330000000000000000000000000000000000000000000000000000000000000001000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000010000000000000000000000000000000000000000000000000000000000000020000000000000000000000000000000000000000000000000000000000000012000000000000000000000000000000000000000000000000000000000000000010000000000000000000000000000000000000000000000000000003562e057c400000000000000000000000000000000000000000000000000000000383747ae00000000000000000000000000000000000000000000000000000000000000a000000000000000000000000000000000000000000000000000000000000000010000000000000000000000000000000000000000000000000000000000000042a0b86991c6218b36c1d19d4a2e9eb0ce3606eb480001f4c02aaa39b223fe8d0a0e5c4f27ead9083c756cc20001f42260fac5e5542a773aa44fbcfedf7c193bc2c599000000000000000000000000000000000000000000000000000000000000")  # noqa E501


def test_chain_v3_swap_exact_in_from_balance(codec):
    encoded_input = codec.encode.chain().v3_swap_exact_in_from_balance(
        FunctionRecipient.SENDER,
        Wei(943146926),
        [
            Web3.to_checksum_address("0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48"),
            500,
            Web3.to_checksum_address("0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2"),
            500,
            Web3.to_checksum_address("0x2260FAC5E5542a773Aa44fBCfeDf7C193bc2C599"),
        ],
    ).build(1677080627)
    assert encoded_input == HexStr("0x3593564c000000000000000000000000000000000000000000000000000000000000006000000000000000000000000000000000000000000000000000000000000000a00000000000000000000000000000000000000000000000000000000063f63833000000000000000000000000000000000000000000000000000000000000000100000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000001000000000000000000000000000000000000000000000000000000000000002000000000000000000000000000000000000000000000000000000000000001200000000000000000000000000000000000000000000000000000000000000001800000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000383747ae00000000000000000000000000000000000000000000000000000000000000a000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000042a0b86991c6218b36c1d19d4a2e9eb0ce3606eb480001f4c02aaa39b223fe8d0a0e5c4f27ead9083c756cc20001f42260fac5e5542a773aa44fbcfedf7c193bc2c599000000000000000000000000000000000000000000000000000000000000")  # noqa E501


def test_chain_v3_swap_exact_out(codec):
    # https://etherscan.io/tx/0x6aa16d2af66a8d960ce459abdd0a9018e35b2338cd3d2eb52b1280cc5a5f93ff
    encoded_input = codec.encode.chain().v3_swap_exact_out(
        FunctionRecipient.SENDER,
        Wei(40_000 * 10**18),
        Wei(2290420550308290562760),
        [
            Web3.to_checksum_address("0x0a5E677a6A24b2F1A2Bf4F3bFfC443231d2fDEc8"),
            3000,
            Web3.to_checksum_address("0x431ad2ff6a9C365805eBaD47Ee021148d6f7DBe0"),
        ],
        payer_is_sender=True,
    ).build(1678369559)
    assert encoded_input == HexStr("0x3593564c000000000000000000000000000000000000000000000000000000000000006000000000000000000000000000000000000000000000000000000000000000a0000000000000000000000000000000000000000000000000000000006409e317000000000000000000000000000000000000000000000000000000000000000101000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000001000000000000000000000000000000000000000000000000000000000000002000000000000000000000000000000000000000000000000000000000000001000000000000000000000000000000000000000000000000000000000000000001000000000000000000000000000000000000000000000878678326eac900000000000000000000000000000000000000000000000000007c29f86b56545f0ac800000000000000000000000000000000000000000000000000000000000000a00000000000000000000000000000000000000000000000000000000000000001000000000000000000000000000000000000000000000000000000000000002b431ad2ff6a9c365805ebad47ee021148d6f7dbe0000bb80a5e677a6a24b2f1a2bf4f3bffc443231d2fdec8000000000000000000000000000000000000000000")  # noqa E501


expected_permit_parameters = {
    "details": {
        "token": Web3.to_checksum_address("0x4Fabb145d64652a948d72533023f6E7A623C7C53"),
        "amount": Wei(1461501637330902918203684832716283019655932542975),
        "expiration": 1679922321,
        "nonce": 0,
    },
    "spender": Web3.to_checksum_address("0xEf1c6E67703c7BD7107eed8303Fbe6EC2554BF6B"),
    "sigDeadline": 1677332121,
}


def test_chain_permit2_permit(codec):
    params = [
        *expected_permit_parameters["details"].values(),
        expected_permit_parameters["spender"],
        expected_permit_parameters["sigDeadline"],
    ]
    permit_parameters, signable_message = codec.create_permit2_signable_message(*params)
    assert permit_parameters == expected_permit_parameters
    assert signable_message.version == b'\x01'
    assert signable_message.header == b'\x86jZ\xba!\x96j\xf9]lz\xb7\x8e\xb2\xb2\xfc\x919\x15\xc2\x8b\xe3\xb9\xaa\x07\xcc\x04\xff\x90>?('  # noqa E501
    assert signable_message.body == b'\x92U\x83n\x15\x87\x9ay\xcb\xcez\xc2B\xb6Z\xd2\xe4>\xd2n\x8b\xa8\xedl\xa9\x16\x8f\xcco\x88\xb3\xe0'  # noqa E501

    account: LocalAccount = Account.from_key(keccak(text="moo"))
    signed_message: SignedMessage = account.sign_message(signable_message)
    assert signed_message.signature == HexBytes('0xc18b2a09e7d03f38102824a401a765fe05a40753a2188520250e7ffb825f41960dd8703c82a9683c0a7a8eafb2b930aa29b3edc018cad7afc6e29781420a8ec51b')  # noqa E501

    encoded_input = codec.encode.chain().permit2_permit(permit_parameters, signed_message).build(1677332121)
    assert encoded_input == HexStr('0x3593564c000000000000000000000000000000000000000000000000000000000000006000000000000000000000000000000000000000000000000000000000000000a00000000000000000000000000000000000000000000000000000000063fa0e9900000000000000000000000000000000000000000000000000000000000000010a000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000001000000000000000000000000000000000000000000000000000000000000002000000000000000000000000000000000000000000000000000000000000001600000000000000000000000004fabb145d64652a948d72533023f6e7a623c7c53000000000000000000000000ffffffffffffffffffffffffffffffffffffffff00000000000000000000000000000000000000000000000000000000642194910000000000000000000000000000000000000000000000000000000000000000000000000000000000000000ef1c6e67703c7bd7107eed8303fbe6ec2554bf6b0000000000000000000000000000000000000000000000000000000063fa0e9900000000000000000000000000000000000000000000000000000000000000e00000000000000000000000000000000000000000000000000000000000000041c18b2a09e7d03f38102824a401a765fe05a40753a2188520250e7ffb825f41960dd8703c82a9683c0a7a8eafb2b930aa29b3edc018cad7afc6e29781420a8ec51b00000000000000000000000000000000000000000000000000000000000000')  # noqa E501


@pytest.mark.parametrize(
    "router_function, revert_on_fail, expected_command",
    (
        # Todo: use functions that actually support the NO_REVERT_FLAG, like SUDOSWAP or another NFT function
        (_RouterFunction.V3_SWAP_EXACT_IN, True, 0x00),
        (_RouterFunction.V3_SWAP_EXACT_IN, False, 0x80),
        (_RouterFunction.V2_SWAP_EXACT_IN, True, 0x08),
        (_RouterFunction.V2_SWAP_EXACT_IN, False, 0x88),
        (_RouterFunction.PERMIT2_PERMIT, True, 0x0a),
        (_RouterFunction.PERMIT2_PERMIT, False, 0x8a),
        (_RouterFunction.WRAP_ETH, True, 0x0b),
        (_RouterFunction.WRAP_ETH, False, 0x8b),
    )
)
def test_get_command(router_function, revert_on_fail, expected_command, codec):
    assert codec.encode.chain()._get_command(router_function, revert_on_fail) == expected_command


def test_chain_v2_swap_exact_in_with_permit(codec):
    params = [
        *expected_permit_parameters["details"].values(),
        expected_permit_parameters["spender"],
        expected_permit_parameters["sigDeadline"],
    ]
    permit_parameters, signable_message = codec.create_permit2_signable_message(*params)
    assert permit_parameters == expected_permit_parameters

    account: LocalAccount = Account.from_key(keccak(text="moo"))
    signed_message: SignedMessage = account.sign_message(signable_message)

    path = [
            Web3.to_checksum_address("0x4Fabb145d64652a948d72533023f6E7A623C7C53"),
            Web3.to_checksum_address("0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2"),
        ]
    encoded_input = (
        codec
        .encode
        .chain()
        .permit2_permit(permit_parameters, signed_message)
        .v2_swap_exact_in(FunctionRecipient.SENDER, Wei(10**18), Wei(0), path, payer_is_sender=True)
        .build(1677332121)
    )

    assert encoded_input == HexStr('0x3593564c000000000000000000000000000000000000000000000000000000000000006000000000000000000000000000000000000000000000000000000000000000a00000000000000000000000000000000000000000000000000000000063fa0e9900000000000000000000000000000000000000000000000000000000000000020a080000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000002000000000000000000000000000000000000000000000000000000000000004000000000000000000000000000000000000000000000000000000000000001c000000000000000000000000000000000000000000000000000000000000001600000000000000000000000004fabb145d64652a948d72533023f6e7a623c7c53000000000000000000000000ffffffffffffffffffffffffffffffffffffffff00000000000000000000000000000000000000000000000000000000642194910000000000000000000000000000000000000000000000000000000000000000000000000000000000000000ef1c6e67703c7bd7107eed8303fbe6ec2554bf6b0000000000000000000000000000000000000000000000000000000063fa0e9900000000000000000000000000000000000000000000000000000000000000e00000000000000000000000000000000000000000000000000000000000000041c18b2a09e7d03f38102824a401a765fe05a40753a2188520250e7ffb825f41960dd8703c82a9683c0a7a8eafb2b930aa29b3edc018cad7afc6e29781420a8ec51b00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000010000000000000000000000000000000000000000000000000000000000000000010000000000000000000000000000000000000000000000000de0b6b3a7640000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000a0000000000000000000000000000000000000000000000000000000000000000100000000000000000000000000000000000000000000000000000000000000020000000000000000000000004fabb145d64652a948d72533023f6e7a623c7c53000000000000000000000000c02aaa39b223fe8d0a0e5c4f27ead9083c756cc2')  # noqa E501


def test_chain_v2_swap_exact_in_and_sweep_and_pay_portion(codec):
    # https://etherscan.io/tx/0x688f928224146be1bb99556878b72098592201d5a9024fa5e053dbb8b7f02959
    encoded_input = (
        codec
        .encode
        .chain()
        .v2_swap_exact_in(
            FunctionRecipient.ROUTER,
            Wei(2000000000000000000000000),
            Wei(986619877196212818407780752),
            [
                '0x95aD61b0a150d79219dCF64E1E6Cc01f0B64C4cE',
                '0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2',
                '0x1ce270557C1f68Cfb577b856766310Bf8B47FD9C',
            ],
            payer_is_sender=True,
        )
        .pay_portion(
            FunctionRecipient.CUSTOM,
            Web3.to_checksum_address('0x1ce270557C1f68Cfb577b856766310Bf8B47FD9C'),
            100,
            Web3.to_checksum_address('0x17CC6042605381c158D2adab487434Bde79Aa61C'),
        )
        .sweep(
            FunctionRecipient.SENDER,
            Web3.to_checksum_address('0x1ce270557C1f68Cfb577b856766310Bf8B47FD9C'),
            Wei(986619877196212818407780752),
        )
        .build(1698245843)
    )

    assert encoded_input == HexStr('0x3593564c000000000000000000000000000000000000000000000000000000000000006000000000000000000000000000000000000000000000000000000000000000a00000000000000000000000000000000000000000000000000000000065392cd3000000000000000000000000000000000000000000000000000000000000000308060400000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000003000000000000000000000000000000000000000000000000000000000000006000000000000000000000000000000000000000000000000000000000000001a000000000000000000000000000000000000000000000000000000000000002200000000000000000000000000000000000000000000000000000000000000120000000000000000000000000000000000000000000000000000000000000000200000000000000000000000000000000000000000001a784379d99db42000000000000000000000000000000000000000000000003301ce2b6b374a8a606f19000000000000000000000000000000000000000000000000000000000000000a00000000000000000000000000000000000000000000000000000000000000001000000000000000000000000000000000000000000000000000000000000000300000000000000000000000095ad61b0a150d79219dcf64e1e6cc01f0b64c4ce000000000000000000000000c02aaa39b223fe8d0a0e5c4f27ead9083c756cc20000000000000000000000001ce270557c1f68cfb577b856766310bf8b47fd9c00000000000000000000000000000000000000000000000000000000000000600000000000000000000000001ce270557c1f68cfb577b856766310bf8b47fd9c00000000000000000000000017cc6042605381c158d2adab487434bde79aa61c000000000000000000000000000000000000000000000000000000000000006400000000000000000000000000000000000000000000000000000000000000600000000000000000000000001ce270557c1f68cfb577b856766310bf8b47fd9c0000000000000000000000000000000000000000000000000000000000000001000000000000000000000000000000000000000003301ce2b6b374a8a606f190')  # noqa


@pytest.mark.parametrize(
    "function_recipient, token_address, bips, custom_recipient, expected_exception",
    (
        (FunctionRecipient.SENDER, Web3.to_checksum_address('0x1ce270557C1f68Cfb577b856766310Bf8B47FD9C'), 100, None, None),  # noqa
        (FunctionRecipient.SENDER, Web3.to_checksum_address('0x1ce270557C1f68Cfb577b856766310Bf8B47FD9C'), 100.01, None, ValueError),  # noqa
        (FunctionRecipient.SENDER, Web3.to_checksum_address('0x1ce270557C1f68Cfb577b856766310Bf8B47FD9C'), 10_001, None, ValueError),  # noqa
        (FunctionRecipient.SENDER, Web3.to_checksum_address('0x1ce270557C1f68Cfb577b856766310Bf8B47FD9C'), -1, None, ValueError),  # noqa
        (FunctionRecipient.CUSTOM, Web3.to_checksum_address('0x1ce270557C1f68Cfb577b856766310Bf8B47FD9C'), 100, None, ValueError),  # noqa
    )
)
def test_pay_portion_argument_validity(function_recipient, token_address, bips, custom_recipient, expected_exception, codec):  # noqa
    if expected_exception:
        with pytest.raises(ValueError):
            codec.encode.chain().pay_portion(function_recipient, token_address, bips, custom_recipient).build(1698245843)  # noqa
    else:
        _ = codec.encode.chain().pay_portion(function_recipient, token_address, bips, custom_recipient).build(1698245843)  # noqa


def test_transfer(codec):
    encoded_input = codec.encode.chain().transfer(FunctionRecipient.CUSTOM, Web3.to_checksum_address("0x0000000000000000000000000000000000000000"), 4 * 10**15, Web3.to_checksum_address("0xaDFec019eE085a93A9e947CF3ECC5f29a36EfAc0")).build()  # noqa
    assert encoded_input == HexStr("0x24856bc300000000000000000000000000000000000000000000000000000000000000400000000000000000000000000000000000000000000000000000000000000080000000000000000000000000000000000000000000000000000000000000000105000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000001000000000000000000000000000000000000000000000000000000000000002000000000000000000000000000000000000000000000000000000000000000600000000000000000000000000000000000000000000000000000000000000000000000000000000000000000adfec019ee085a93a9e947cf3ecc5f29a36efac0000000000000000000000000000000000000000000000000000e35fa931a0000")  # noqa


def test_build_transaction(codec_rpc):
    sender = "0x52d7Bb619F6E37A038e522eDF755008d9EfdD695"
    balance = codec_rpc._w3.eth.get_balance("0x52d7Bb619F6E37A038e522eDF755008d9EfdD695", block_identifier=19876107)
    assert balance > Web3.to_wei(4, "ether")

    amount_in = Wei(2 * 10**18)
    builder = (
        codec_rpc
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
    trx_1 = builder.build_transaction(
        sender=sender,
        value=amount_in,
        block_identifier=19876107
    )
    assert trx_1["from"] == sender
    assert trx_1["value"] == amount_in
    assert trx_1["to"] == _ur_address
    assert trx_1["chainId"] == 1
    assert trx_1["nonce"] == 94
    assert trx_1["type"] == "0x2"
    assert trx_1["maxPriorityFeePerGas"] == 2500000000
    assert trx_1["maxFeePerGas"] == 20479961920
    assert len(trx_1["data"]) > 100
    assert abs(trx_1["gas"] - 192214) < 1000

    # transaction 2 - same but with FASTER speed
    trx_2 = builder.build_transaction(
        sender=sender,
        value=amount_in,
        trx_speed=TransactionSpeed.FASTER,
        block_identifier=19876107
    )

    assert trx_2["maxPriorityFeePerGas"] == 3000000000
    assert trx_2["maxFeePerGas"] == 20979961920
    assert abs(trx_2["gas"] - 192214) < 1000

    # transaction 3 - no call to rpc and custom fields
    trx_3 = builder.build_transaction(
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

    assert trx_3["chainId"] == 2
    assert trx_3["nonce"] == 100
    assert trx_3["maxPriorityFeePerGas"] == 1900000000
    assert trx_3["maxFeePerGas"] == 22222222222
    assert trx_3["gas"] == 500_000

    # transaction 4, 5, 6 - incompatible arguments
    with pytest.raises(ValueError):
        _ = builder.build_transaction(
            sender=sender,
            value=amount_in,
            priority_fee=Wei(1900000000),
            block_identifier=19876107
        )

    with pytest.raises(ValueError):
        _ = builder.build_transaction(
            sender=sender,
            value=amount_in,
            max_fee_per_gas=Wei(22222222222),
            block_identifier=19876107
        )

    with pytest.raises(ValueError):
        _ = builder.build_transaction(
            sender=sender,
            value=amount_in,
            trx_speed=None,
            block_identifier=19876107
        )

    # transaction 7 - computed gas too high
    with pytest.raises(ValueError):
        _ = builder.build_transaction(
            sender=sender,
            value=amount_in,
            max_fee_per_gas_limit=Wei(1 * 10 ** 9),
            block_identifier=19876107
        )
