import os

import pytest
from web3 import Web3
from web3.types import HexStr

from uniswap_universal_router_decoder.router_codec import RouterCodec


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
        codec_w3 = RouterCodec(w3=w3)
    else:
        codec_w3 = RouterCodec(rpc_endpoint=rpc_endpoint)

    decoded_trx = codec_w3.decode.transaction(trx_hash)
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

trx_hash_07 = HexStr("0xe61da48803242cb323056935737e8b430025ebe20af916031c2d53a1f1b2a844")
expected_parsed_path_07 = (
    Web3.to_checksum_address("0x0f51bb10119727a7e5eA3538074fb341F56B09Ad"),
    10000,
    Web3.to_checksum_address("0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48"),
    500,
    Web3.to_checksum_address("0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2"),
)

codec_rpc = RouterCodec(rpc_endpoint=rpc_endpoint_address)


@pytest.mark.parametrize(
    "trx_hash, fn_name, expected_parsed_path, expected_exception",
    (
        (trx_hash_02, "V3_SWAP_EXACT_IN", expected_parsed_path_02, None),
        (trx_hash_04, "V3_SWAP_EXACT_OUT", expected_parsed_path_04, None),
        (trx_hash_04, "V2_SWAP_EXACT_OUT", None, ValueError),
        (trx_hash_06, "V3_SWAP_EXACT_OUT", expected_parsed_path_06, None),
        (trx_hash_07, "V3_SWAP_EXACT_IN", expected_parsed_path_07, None),
    )
)
def test_decode_v3_path(trx_hash, fn_name, expected_parsed_path, expected_exception):
    decoded_trx = codec_rpc.decode.transaction(trx_hash)
    command_inputs = decoded_trx["decoded_input"]["inputs"]
    for command_input in command_inputs:
        if command_input[0].fn_name == fn_name:
            path_bytes = command_input[1]["path"]
            if expected_exception:
                with pytest.raises(expected_exception):
                    _ = codec_rpc.decode.v3_path(fn_name, path_bytes)
            else:
                assert codec_rpc.decode.v3_path(fn_name, path_bytes) == expected_parsed_path
                assert codec_rpc.decode.v3_path(fn_name, path_bytes.hex()) == expected_parsed_path
            break
    else:
        raise ValueError(f"No fn_name {fn_name} found in the decoded command inputs for trx {trx_hash}")
