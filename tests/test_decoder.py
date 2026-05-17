import pytest
from web3 import Web3

from tests.resources.transactions import transactions
from uniswap_universal_router_decoder import RouterCodec


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
def test_decode_transaction(trx_hash, use_w3, expected_decoded_input, w3, rpc_url):
    if use_w3:
        codec_w3 = RouterCodec(w3=w3)
    else:
        codec_w3 = RouterCodec(rpc_endpoint=rpc_url)

    decoded_trx = codec_w3.decode.transaction(trx_hash)
    assert decoded_trx["hash"] == Web3.to_bytes(hexstr=trx_hash)
    assert str(decoded_trx["decoded_input"]) == expected_decoded_input

    decoded_input = codec_w3.decode.function_input(decoded_trx["input"])
    assert str(decoded_input) == expected_decoded_input


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
        (transactions[1]["trx_hash"], "V3_SWAP_EXACT_OUT", expected_parsed_path_02, None),
        (transactions[4]["trx_hash"], "V2_SWAP_EXACT_IN", None, ValueError),
        (transactions[4]["trx_hash"], "V3_SWAP_EXACT_IN", expected_parsed_path_06, None),
        (transactions[6]["trx_hash"], "V3_SWAP_EXACT_OUT", expected_parsed_path_13, None),
    )
)
def test_decode_v3_path(trx_hash, fn_name, expected_parsed_path, expected_exception, codec_rpc):
    decoded_trx = codec_rpc.decode.transaction(trx_hash)
    command_inputs = decoded_trx["decoded_input"][1]["inputs"]
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
