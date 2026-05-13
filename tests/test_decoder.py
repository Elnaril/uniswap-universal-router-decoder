import pytest
from web3 import Web3
from web3.types import HexStr

from uniswap_universal_router_decoder import RouterCodec


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
def test_decode_transaction(trx_hash, use_w3, expected_fct_names, w3, rpc_url):
    if use_w3:
        codec_w3 = RouterCodec(w3=w3)
    else:
        codec_w3 = RouterCodec(rpc_endpoint=rpc_url)

    decoded_trx = codec_w3.decode.transaction(trx_hash)
    print(decoded_trx)
    command_inputs = decoded_trx["decoded_input"]["inputs"]
    assert len(command_inputs) == len(expected_fct_names)
    for i, expected_name in enumerate(expected_fct_names):
        if expected_name:
            assert expected_name == command_inputs[i][0].fn_name
            assert command_inputs[i][2]['revert_on_fail'] is True
        else:
            assert isinstance(command_inputs[i], str)
            int(command_inputs[i], 16)  # check the str is actually a hex


# Test Decode V3 Path
expected_parsed_path_02 = (
    Web3.to_checksum_address("0x9E32b13ce7f2E80A01932B42553652E053D6ed8e"),
    3000,
    Web3.to_checksum_address("0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2"),
    100,
    Web3.to_checksum_address("0xdAC17F958D2ee523a2206206994597C13D831ec7"),
)

expected_parsed_path_04 = (
    Web3.to_checksum_address("0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2"),
    3000,
    Web3.to_checksum_address("0xf3dcbc6D72a4E1892f7917b7C43b74131Df8480e"),
)

expected_parsed_path_06 = (
    Web3.to_checksum_address("0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48"),
    500,
    Web3.to_checksum_address("0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2"),
    10000,
    Web3.to_checksum_address("0xAFF2565091E7207191dBe340B8528D02FA78d044"),
)

expected_parsed_path_13 = (
    Web3.to_checksum_address("0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2"),
    10000,
    Web3.to_checksum_address("0x829f4B62EEBE12Af653b4dD4fFc480966F7d7f09"),
)


@pytest.mark.parametrize(
    "trx_hash, fn_name, expected_parsed_path, expected_exception",
    (
        (trx_hash_02, "V3_SWAP_EXACT_OUT", expected_parsed_path_02, None),
        (trx_hash_06, "V2_SWAP_EXACT_IN", None, ValueError),
        (trx_hash_06, "V3_SWAP_EXACT_IN", expected_parsed_path_06, None),
        (trx_hash_13, "V3_SWAP_EXACT_OUT", expected_parsed_path_13, None),
    )
)
def test_decode_v3_path(trx_hash, fn_name, expected_parsed_path, expected_exception, codec_rpc):
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


contract_error_0 = "0x00000000"
contract_error_1 = "0x2c4029e9000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000400000000000000000000000000000000000000000000000000000000000000000"  # noqa
contract_error_2 = "0x5d1d0f9f"
contract_error_3 = "0x2c4029e9000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000400000000000000000000000000000000000000000000000000000000000000024bfb22adf000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000"  # noqa
contract_sub_error_3 = b'\xbf\xb2*\xdf\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'.hex()  # noqa
contract_error_4 = "0xf801e5250000000000000000000000000000000000000000000000000000000000000000"


@pytest.mark.parametrize(
    "contract_error, expected",
    (
        (contract_error_0, ("Unknown error", {})),
        (contract_error_1, ("ExecutionFailed(uint256,bytes)", {'commandIndex': 0, 'message': b''})),
        (contract_error_2, ("OnlyMintAllowed()", {})),
        (contract_error_3, ("ExecutionFailed(uint256,bytes)", {'commandIndex': 0, 'message': b'\xbf\xb2*\xdf\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'})),  # noqa
        (contract_sub_error_3, ("DeadlinePassed(uint256)", {'deadline': 0})),
        (contract_error_4, ("InvalidAction(bytes4)", {'action': b'\x00\x00\x00\x00'})),
    )
)
def test_contract_error(contract_error, expected):
    codec = RouterCodec()
    decoded_error = codec.decode.contract_error(contract_error)
    assert decoded_error == expected
