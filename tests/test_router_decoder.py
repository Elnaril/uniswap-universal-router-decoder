import json
import os
import pytest

from uniswap_universal_router_decoder.router_decoder import (
    HexStr,
    RouterDecoder,
)


expected_fct_abi_08 = json.loads('{"inputs":[{"name":"sender","type":"address"},{"name":"amountIn","type":"uint256"},{"name":"amountOutMin","type":"uint256"},{"name":"path","type":"address[]"},{"name":"payerIsSender","type":"bool"}],"name":"V2_SWAP_EXACT_IN","type":"function"}')  # noqa
expected_fct_abi_10 = json.loads('{"inputs":[{"name":"struct","type":"tuple","components":[{"name":"details","type":"tuple","components":[{"name":"token","type":"address"},{"name":"amount","type":"uint256"},{"name":"expiration","type":"uint256"},{"name":"nonce","type":"uint256"}]},{"name":"spender","type":"address"},{"name":"sigDeadline","type":"uint256"}]},{"name":"data","type":"bytes"}],"name":"PERMIT2_PERMIT","type":"function"}')  # noqa
decoder = RouterDecoder()


@pytest.mark.parametrize(
    "command_id, expected_fct_abi, expected_selector",
    (
        (8, expected_fct_abi_08, bytes.fromhex("3bd2d879")),
        (10, expected_fct_abi_10, b'\xe5\xa0\x93%'),
    )
)
def test_build_abi_map(command_id, expected_fct_abi, expected_selector):
    assert decoder._abi_map[command_id].fct_abi.get_abi() == expected_fct_abi
    assert decoder._abi_map[command_id].selector == expected_selector


decoder_w3 = RouterDecoder(rpc_endpoint=os.environ["WEB3_HTTP_PROVIDER_URL_ETHEREUM_MAINNET"])


expected_function_names_01 = ("PERMIT2_PERMIT", "V2_SWAP_EXACT_IN")


@pytest.mark.parametrize(
    "trx_hash, expected_fct_names",
    (
        (HexStr("0x52e63b75f41a352ad9182f9e0f923c8557064c3b1047d1778c1ea5b11b979dd9"), expected_function_names_01),
    )
)
def test_decode_transaction(trx_hash, expected_fct_names):
    decoded_trx = decoder_w3.decode_transaction(trx_hash)
    command_input = decoded_trx["decoded_input"]["inputs"]
    assert len(command_input) == len(expected_fct_names)
    for i, expected_name in enumerate(expected_fct_names):
        assert expected_name == command_input[i][0].fn_name
