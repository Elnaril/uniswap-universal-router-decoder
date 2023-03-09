import json
import os

from eth_account import Account
from eth_account.datastructures import SignedMessage
from eth_account.signers.local import LocalAccount
from eth_utils import keccak
import pytest
from web3 import Web3
from web3.types import (
    HexBytes,
    Wei,
)

from uniswap_universal_router_decoder.router_decoder import (
    _RouterFunction,
    HexStr,
    RouterDecoder,
)


# Test Build API Map

expected_fct_abi_08 = json.loads('{"inputs":[{"name":"recipient","type":"address"},{"name":"amountIn","type":"uint256"},{"name":"amountOutMin","type":"uint256"},{"name":"path","type":"address[]"},{"name":"payerIsUser","type":"bool"}],"name":"V2_SWAP_EXACT_IN","type":"function"}')  # noqa
expected_fct_abi_10 = json.loads('{"inputs":[{"name":"struct","type":"tuple","components":[{"name":"details","type":"tuple","components":[{"name":"token","type":"address"},{"name":"amount","type":"uint256"},{"name":"expiration","type":"uint256"},{"name":"nonce","type":"uint256"}]},{"name":"spender","type":"address"},{"name":"sigDeadline","type":"uint256"}]},{"name":"data","type":"bytes"}],"name":"PERMIT2_PERMIT","type":"function"}')  # noqa
decoder = RouterDecoder()


@pytest.mark.parametrize(
    "command_id, expected_fct_abi, expected_selector",
    (
        (_RouterFunction(8), expected_fct_abi_08, bytes.fromhex("3bd2d879")),
        (_RouterFunction(10), expected_fct_abi_10, b'\xe5\xa0\x93%'),
    )
)
def test_build_abi_map(command_id, expected_fct_abi, expected_selector):
    assert decoder._abi_map[command_id].fct_abi.get_abi() == expected_fct_abi
    assert decoder._abi_map[command_id].selector == expected_selector


# Test Decode Trx + Input

rpc_endpoint_address = os.environ["WEB3_HTTP_PROVIDER_URL_ETHEREUM_MAINNET"]
w3_instance = Web3(Web3.HTTPProvider(rpc_endpoint_address))


trx_hash_01 = HexStr("0x52e63b75f41a352ad9182f9e0f923c8557064c3b1047d1778c1ea5b11b979dd9")
expected_function_names_01 = ("PERMIT2_PERMIT", "V2_SWAP_EXACT_IN")

trx_hash_02 = HexStr("0x3247555a5dbc877ade17c4b49362bc981af5fb5064e0b3cbd91411e085fe3093")
expected_function_names_02 = ("V3_SWAP_EXACT_IN", "UNWRAP_WETH")

trx_hash_03 = HexStr("0x889b34a27b730dd664cd71579b4310522c3b495fb34f17f08d1131c0cec651fa")
expected_function_names_03 = ("WRAP_ETH", "V2_SWAP_EXACT_OUT", "UNWRAP_WETH")

trx_hash_04 = HexStr("0xf99ac4237df313794747759550db919b37d7c8a67d4a7e12be8f5cbaacd51376")
expected_function_names_04 = ("WRAP_ETH", "V2_SWAP_EXACT_OUT", "V3_SWAP_EXACT_OUT", "UNWRAP_WETH")

trx_hash_05 = HexStr("0x47c0f1dd13edf9f1608f9f34bdba9ad40cb95dd081033cad69f5b88e451b4b55")
expected_function_names_05 = (None, None)


@pytest.mark.parametrize(
    "trx_hash, w3, rpc_endpoint, expected_fct_names",
    (
        (trx_hash_01, None, rpc_endpoint_address, expected_function_names_01),
        (trx_hash_02, w3_instance, None, expected_function_names_02),
        (trx_hash_03, w3_instance, None, expected_function_names_03),
        (trx_hash_04, w3_instance, None, expected_function_names_04),
        (trx_hash_05, w3_instance, None, expected_function_names_05),
    )
)
def test_decode_transaction(trx_hash, w3, rpc_endpoint, expected_fct_names):
    if w3:
        decoder_w3 = RouterDecoder(w3=w3)
    else:
        decoder_w3 = RouterDecoder(rpc_endpoint=rpc_endpoint)

    decoded_trx = decoder_w3.decode_transaction(trx_hash)
    command_inputs = decoded_trx["decoded_input"]["inputs"]
    assert len(command_inputs) == len(expected_fct_names)
    for i, expected_name in enumerate(expected_fct_names):
        if expected_name:
            assert expected_name == command_inputs[i][0].fn_name
        else:
            assert type(command_inputs[i]) == str
            int(command_inputs[i], 16)  # check the str is actually a hex


# Test Decode V3 Path

expected_parsed_path_02 = (
    Web3.to_checksum_address("0x4d224452801ACEd8B2F0aebE155379bb5D594381"),
    3000,
    Web3.to_checksum_address("0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2"),
)

expected_parsed_path_04 = (
    Web3.to_checksum_address("0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2"),
    3000,
    Web3.to_checksum_address("0xf3dcbc6D72a4E1892f7917b7C43b74131Df8480e"),
)

trx_hash_06 = HexStr("0x4a23b8ca6e15be1e61554d67bc5868b2fd8e91a97124b0fb31d39ce1a921bc62")
expected_parsed_path_06 = (
    Web3.to_checksum_address("0xdAC17F958D2ee523a2206206994597C13D831ec7"),
    500,
    Web3.to_checksum_address("0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2"),
    3000,
    Web3.to_checksum_address("0xABe580E7ee158dA464b51ee1a83Ac0289622e6be"),
)


@pytest.mark.parametrize(
    "trx_hash, fn_name, rpc_endpoint, expected_parsed_path, expected_exception",
    (
        (trx_hash_02, "V3_SWAP_EXACT_IN", rpc_endpoint_address, expected_parsed_path_02, None),
        (trx_hash_04, "V3_SWAP_EXACT_OUT", rpc_endpoint_address, expected_parsed_path_04, None),
        (trx_hash_04, "V2_SWAP_EXACT_OUT", rpc_endpoint_address, None, ValueError),
        (trx_hash_06, "V3_SWAP_EXACT_OUT", rpc_endpoint_address, expected_parsed_path_06, None),
    )
)
def test_decode_v3_path(trx_hash, fn_name, rpc_endpoint, expected_parsed_path, expected_exception):
    decoder_w3 = RouterDecoder(rpc_endpoint=rpc_endpoint)
    decoded_trx = decoder_w3.decode_transaction(trx_hash)
    command_inputs = decoded_trx["decoded_input"]["inputs"]
    for command_input in command_inputs:
        if command_input[0].fn_name == fn_name:
            path_bytes = command_input[1]["path"]
            if expected_exception:
                with pytest.raises(expected_exception):
                    _ = decoder_w3.decode_v3_path(fn_name, path_bytes)
            else:
                assert decoder_w3.decode_v3_path(fn_name, path_bytes) == expected_parsed_path
                assert decoder_w3.decode_v3_path(fn_name, path_bytes.hex()) == expected_parsed_path
            break
    else:
        raise ValueError(f"No fn_name {fn_name} found in the decoded command inputs for trx {trx_hash}")


# Test encoding

def test_get_default_deadline():
    assert 79 < decoder.get_default_deadline() - decoder.get_default_deadline(100) < 81


def test_get_default_expiration():
    assert -1 < decoder.get_default_expiration() - decoder.get_default_expiration(30*24*3600) < 1


def test_encode_wrap_eth_sub_contract():
    encoded_input = decoder._encode_wrap_eth_sub_contract(
        Web3.to_checksum_address("0x0000000000000000000000000000000000000002"),
        Wei(500000000000000000)
    )
    assert encoded_input == "000000000000000000000000000000000000000000000000000000000000000200000000000000000000000000000000000000000000000006f05b59d3b20000"  # noqa


def test_encode_data_for_wrap_eth():
    encoded_data = decoder.encode_data_for_wrap_eth(Wei(10**17), 1676825611)
    assert encoded_data == HexStr("0x3593564c000000000000000000000000000000000000000000000000000000000000006000000000000000000000000000000000000000000000000000000000000000a00000000000000000000000000000000000000000000000000000000063f2540b00000000000000000000000000000000000000000000000000000000000000010b000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000001000000000000000000000000000000000000000000000000000000000000002000000000000000000000000000000000000000000000000000000000000000400000000000000000000000000000000000000000000000000000000000000001000000000000000000000000000000000000000000000000016345785d8a0000")  # noqa


def test_encode_data_for_v2_swap_exact_in():
    encoded_input = decoder.encode_data_for_v2_swap_exact_in(
        Wei(10**17),
        Wei(0),
        [
            Web3.to_checksum_address("0xB4FBF271143F4FBf7B91A5ded31805e42b2208d6"),
            Web3.to_checksum_address("0x326C977E6efc84E512bB9C30f76E30c160eD06FB"),
        ],
        1676919287,
    )
    assert encoded_input == HexStr("0x3593564c000000000000000000000000000000000000000000000000000000000000006000000000000000000000000000000000000000000000000000000000000000a00000000000000000000000000000000000000000000000000000000063f3c1f7000000000000000000000000000000000000000000000000000000000000000108000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000001000000000000000000000000000000000000000000000000000000000000002000000000000000000000000000000000000000000000000000000000000001000000000000000000000000000000000000000000000000000000000000000001000000000000000000000000000000000000000000000000016345785d8a0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000a000000000000000000000000000000000000000000000000000000000000000010000000000000000000000000000000000000000000000000000000000000002000000000000000000000000b4fbf271143f4fbf7b91a5ded31805e42b2208d6000000000000000000000000326c977e6efc84e512bb9c30f76e30c160ed06fb")  # noqa


def test_encode_data_for_v2_swap_exact_out():
    # https://etherscan.io/tx/0xd3abc2fe01376ebaff699a944ae3fb94b00ab899e8ed845a5e22ae120e83cb9e
    encoded_input = decoder.encode_data_for_v2_swap_exact_out(
        Wei(5000000000000000000000000),
        Wei(1364343969533288399),
        [
            Web3.to_checksum_address("0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2"),
            Web3.to_checksum_address("0xC74B43cC61b627667a608c3F650c2558F88028a1"),
        ],
        1678369883,
    )
    assert encoded_input == HexStr("0x3593564c000000000000000000000000000000000000000000000000000000000000006000000000000000000000000000000000000000000000000000000000000000a0000000000000000000000000000000000000000000000000000000006409e45b0000000000000000000000000000000000000000000000000000000000000001090000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000010000000000000000000000000000000000000000000000000000000000000020000000000000000000000000000000000000000000000000000000000000010000000000000000000000000000000000000000000000000000000000000000010000000000000000000000000000000000000000000422ca8b0a00a42500000000000000000000000000000000000000000000000000000012ef1f9c977a5fcf00000000000000000000000000000000000000000000000000000000000000a000000000000000000000000000000000000000000000000000000000000000010000000000000000000000000000000000000000000000000000000000000002000000000000000000000000c02aaa39b223fe8d0a0e5c4f27ead9083c756cc2000000000000000000000000c74b43cc61b627667a608c3f650c2558f88028a1")  # noqa


path_seq_1 = expected_parsed_path_04
expected_v3_path_1 = Web3.to_bytes(hexstr=HexStr("0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2000bb8f3dcbc6D72a4E1892f7917b7C43b74131Df8480e"))  # noqa

path_seq_2 = expected_parsed_path_06
expected_v3_path_2 = Web3.to_bytes(hexstr=HexStr("0xABe580E7ee158dA464b51ee1a83Ac0289622e6be000bb8C02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc20001F4dAC17F958D2ee523a2206206994597C13D831ec7"))  # noqa


@pytest.mark.parametrize(
    "fn_name, path_seq, expected_v3_path, expected_exception",
    (
        ("V3_SWAP_EXACT_IN", path_seq_1, expected_v3_path_1, None),
        ("V2_SWAP_EXACT_OUT", path_seq_1, expected_v3_path_1, ValueError),
        ("V3_SWAP_EXACT_IN", path_seq_1[:2], expected_v3_path_1, ValueError),
        ("V3_SWAP_EXACT_OUT", path_seq_2, expected_v3_path_2, None),
    )
)
def test_encode_v3_path(fn_name, path_seq, expected_v3_path, expected_exception):
    if expected_exception:
        with pytest.raises(expected_exception):
            _ = decoder.encode_v3_path(fn_name, path_seq)
    else:
        assert expected_v3_path == decoder.encode_v3_path(fn_name, path_seq)


def test_encode_data_for_v3_swap_exact_in():
    # https://etherscan.io/tx/0x8bc2aa83ec3749a9987415a20052afec90b8a700092d83a4d65b9e5c227403f1
    encoded_input = decoder.encode_data_for_v3_swap_exact_in(
        Wei(229292136388),
        Wei(943146926),
        [
            Web3.to_checksum_address("0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48"),
            500,
            Web3.to_checksum_address("0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2"),
            500,
            Web3.to_checksum_address("0x2260FAC5E5542a773Aa44fBCfeDf7C193bc2C599"),
        ],
        1677080627,
    )
    assert encoded_input == HexStr("0x3593564c000000000000000000000000000000000000000000000000000000000000006000000000000000000000000000000000000000000000000000000000000000a00000000000000000000000000000000000000000000000000000000063f638330000000000000000000000000000000000000000000000000000000000000001000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000010000000000000000000000000000000000000000000000000000000000000020000000000000000000000000000000000000000000000000000000000000012000000000000000000000000000000000000000000000000000000000000000010000000000000000000000000000000000000000000000000000003562e057c400000000000000000000000000000000000000000000000000000000383747ae00000000000000000000000000000000000000000000000000000000000000a000000000000000000000000000000000000000000000000000000000000000010000000000000000000000000000000000000000000000000000000000000042a0b86991c6218b36c1d19d4a2e9eb0ce3606eb480001f4c02aaa39b223fe8d0a0e5c4f27ead9083c756cc20001f42260fac5e5542a773aa44fbcfedf7c193bc2c599000000000000000000000000000000000000000000000000000000000000")  # noqa


def test_encode_data_for_v3_swap_exact_out():
    # https://etherscan.io/tx/0x6aa16d2af66a8d960ce459abdd0a9018e35b2338cd3d2eb52b1280cc5a5f93ff
    encoded_input = decoder.encode_data_for_v3_swap_exact_out(
        Wei(40_000 * 10**18),
        Wei(2290420550308290562760),
        [
            Web3.to_checksum_address("0x0a5E677a6A24b2F1A2Bf4F3bFfC443231d2fDEc8"),
            3000,
            Web3.to_checksum_address("0x431ad2ff6a9C365805eBaD47Ee021148d6f7DBe0"),
        ],
        1678369559,
    )
    assert encoded_input == HexStr("0x3593564c000000000000000000000000000000000000000000000000000000000000006000000000000000000000000000000000000000000000000000000000000000a0000000000000000000000000000000000000000000000000000000006409e317000000000000000000000000000000000000000000000000000000000000000101000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000001000000000000000000000000000000000000000000000000000000000000002000000000000000000000000000000000000000000000000000000000000001000000000000000000000000000000000000000000000000000000000000000001000000000000000000000000000000000000000000000878678326eac900000000000000000000000000000000000000000000000000007c29f86b56545f0ac800000000000000000000000000000000000000000000000000000000000000a00000000000000000000000000000000000000000000000000000000000000001000000000000000000000000000000000000000000000000000000000000002b431ad2ff6a9c365805ebad47ee021148d6f7dbe0000bb80a5e677a6a24b2f1a2bf4f3bffc443231d2fdec8000000000000000000000000000000000000000000")  # noqa


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


def test_encode_data_for_permit2_permit():
    params = [
        *expected_permit_parameters["details"].values(),
        expected_permit_parameters["spender"],
        expected_permit_parameters["sigDeadline"],
    ]
    permit_parameters, signable_message = decoder.create_permit2_signable_message(*params)
    assert permit_parameters == expected_permit_parameters
    assert signable_message.version == b'\x01'
    assert signable_message.header == b'\x86jZ\xba!\x96j\xf9]lz\xb7\x8e\xb2\xb2\xfc\x919\x15\xc2\x8b\xe3\xb9\xaa\x07\xcc\x04\xff\x90>?('  # noqa
    assert signable_message.body == b'\x92U\x83n\x15\x87\x9ay\xcb\xcez\xc2B\xb6Z\xd2\xe4>\xd2n\x8b\xa8\xedl\xa9\x16\x8f\xcco\x88\xb3\xe0'  # noqa

    account: LocalAccount = Account.from_key(keccak(text="moo"))
    signed_message: SignedMessage = account.sign_message(signable_message)
    assert signed_message.signature == HexBytes('0xc18b2a09e7d03f38102824a401a765fe05a40753a2188520250e7ffb825f41960dd8703c82a9683c0a7a8eafb2b930aa29b3edc018cad7afc6e29781420a8ec51b')  # noqa

    encoded_input = decoder.encode_data_for_permit2_permit(permit_parameters, signed_message, 1677332121)
    assert encoded_input == HexStr('0x3593564c000000000000000000000000000000000000000000000000000000000000006000000000000000000000000000000000000000000000000000000000000000a00000000000000000000000000000000000000000000000000000000063fa0e9900000000000000000000000000000000000000000000000000000000000000010a000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000001000000000000000000000000000000000000000000000000000000000000002000000000000000000000000000000000000000000000000000000000000001600000000000000000000000004fabb145d64652a948d72533023f6e7a623c7c53000000000000000000000000ffffffffffffffffffffffffffffffffffffffff00000000000000000000000000000000000000000000000000000000642194910000000000000000000000000000000000000000000000000000000000000000000000000000000000000000ef1c6e67703c7bd7107eed8303fbe6ec2554bf6b0000000000000000000000000000000000000000000000000000000063fa0e9900000000000000000000000000000000000000000000000000000000000000e00000000000000000000000000000000000000000000000000000000000000041c18b2a09e7d03f38102824a401a765fe05a40753a2188520250e7ffb825f41960dd8703c82a9683c0a7a8eafb2b930aa29b3edc018cad7afc6e29781420a8ec51b00000000000000000000000000000000000000000000000000000000000000')  # noqa


@pytest.mark.parametrize(
    "router_functions, expected_command",
    (
        ((), ""),
        ((_RouterFunction.PERMIT2_PERMIT, ), "0a"),
        ((_RouterFunction.PERMIT2_PERMIT, _RouterFunction.V2_SWAP_EXACT_IN), "0a08"),
        ((_RouterFunction.WRAP_ETH, _RouterFunction.PERMIT2_PERMIT, _RouterFunction.V2_SWAP_EXACT_IN), "0b0a08"),
    )
)
def test_to_command(router_functions, expected_command):
    assert decoder._to_command(*router_functions).hex() == expected_command


def test_encode_data_for_v2_swap_exact_in_with_permit():
    params = [
        *expected_permit_parameters["details"].values(),
        expected_permit_parameters["spender"],
        expected_permit_parameters["sigDeadline"],
    ]
    permit_parameters, signable_message = decoder.create_permit2_signable_message(*params)
    assert permit_parameters == expected_permit_parameters

    account: LocalAccount = Account.from_key(keccak(text="moo"))
    signed_message: SignedMessage = account.sign_message(signable_message)

    encoded_input = decoder.encode_data_for_v2_swap_exact_in_with_permit(
        permit_parameters,
        signed_message,
        Wei(10**18),
        Wei(0),
        [
            Web3.to_checksum_address("0x4Fabb145d64652a948d72533023f6E7A623C7C53"),
            Web3.to_checksum_address("0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2"),
        ],
        1677332121,
    )

    assert encoded_input == HexStr('0x3593564c000000000000000000000000000000000000000000000000000000000000006000000000000000000000000000000000000000000000000000000000000000a00000000000000000000000000000000000000000000000000000000063fa0e9900000000000000000000000000000000000000000000000000000000000000020a080000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000002000000000000000000000000000000000000000000000000000000000000004000000000000000000000000000000000000000000000000000000000000001c000000000000000000000000000000000000000000000000000000000000001600000000000000000000000004fabb145d64652a948d72533023f6e7a623c7c53000000000000000000000000ffffffffffffffffffffffffffffffffffffffff00000000000000000000000000000000000000000000000000000000642194910000000000000000000000000000000000000000000000000000000000000000000000000000000000000000ef1c6e67703c7bd7107eed8303fbe6ec2554bf6b0000000000000000000000000000000000000000000000000000000063fa0e9900000000000000000000000000000000000000000000000000000000000000e00000000000000000000000000000000000000000000000000000000000000041c18b2a09e7d03f38102824a401a765fe05a40753a2188520250e7ffb825f41960dd8703c82a9683c0a7a8eafb2b930aa29b3edc018cad7afc6e29781420a8ec51b00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000010000000000000000000000000000000000000000000000000000000000000000010000000000000000000000000000000000000000000000000de0b6b3a7640000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000a0000000000000000000000000000000000000000000000000000000000000000100000000000000000000000000000000000000000000000000000000000000020000000000000000000000004fabb145d64652a948d72533023f6e7a623c7c53000000000000000000000000c02aaa39b223fe8d0a0e5c4f27ead9083c756cc2')  # noqa
