import json

import pytest

from uniswap_universal_router_decoder._enums import _RouterFunction  # noqa


expected_fct_abi_08 = json.loads('{"inputs":[{"name":"recipient","type":"address"},{"name":"amountIn","type":"uint256"},{"name":"amountOutMin","type":"uint256"},{"name":"path","type":"address[]"},{"name":"payerIsSender","type":"bool"}],"name":"V2_SWAP_EXACT_IN","type":"function"}')  # noqa
expected_fct_abi_10 = json.loads('{"inputs":[{"name":"struct","type":"tuple","components":[{"name":"details","type":"tuple","components":[{"name":"token","type":"address"},{"name":"amount","type":"uint160"},{"name":"expiration","type":"uint48"},{"name":"nonce","type":"uint48"}]},{"name":"spender","type":"address"},{"name":"sigDeadline","type":"uint256"}]},{"name":"data","type":"bytes"}],"name":"PERMIT2_PERMIT","type":"function"}')  # noqa


@pytest.mark.parametrize(
    "command_id, expected_fct_abi, expected_selector",
    (
        (_RouterFunction(8), expected_fct_abi_08, bytes.fromhex("3bd2d879")),
        (_RouterFunction(10), expected_fct_abi_10, b'9#\xf7\x04'),
    )
)
def test_build_abi_map(command_id, expected_fct_abi, expected_selector, codec):
    assert codec._abi_map[command_id].fct_abi.get_abi() == expected_fct_abi
    assert codec._abi_map[command_id].selector == expected_selector
