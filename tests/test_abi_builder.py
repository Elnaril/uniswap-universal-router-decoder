import json

import pytest

from uniswap_universal_router_decoder._abi_builder import build_abi_type_list  # noqa
from uniswap_universal_router_decoder._enums import (  # noqa
    MiscFunctions,
    RouterFunction,
    V4Actions,
)


expected_fct_abi_08 = json.loads('{"inputs":[{"name":"recipient","type":"address"},{"name":"amountIn","type":"uint256"},{"name":"amountOutMin","type":"uint256"},{"name":"path","type":"address[]"},{"name":"payerIsSender","type":"bool"}],"name":"V2_SWAP_EXACT_IN","type":"function"}')  # noqa: E501
expected_fct_signature_08 = "V2_SWAP_EXACT_IN(address,uint256,uint256,address[],bool)"
expected_fct_abi_10 = json.loads('{"inputs":[{"name":"struct","type":"tuple","components":[{"name":"details","type":"tuple","components":[{"name":"token","type":"address"},{"name":"amount","type":"uint160"},{"name":"expiration","type":"uint48"},{"name":"nonce","type":"uint48"}]},{"name":"spender","type":"address"},{"name":"sigDeadline","type":"uint256"}]},{"name":"data","type":"bytes"}],"name":"PERMIT2_PERMIT","type":"function"}')  # noqa: E501
expected_fct_signature_10 = "PERMIT2_PERMIT(((address,uint160,uint48,uint48),address,uint256),bytes)"
expected_execute_abi = json.loads('{"inputs":[{"name":"commands","type":"bytes"},{"name":"inputs","type":"bytes[]"}],"name":"execute","type":"function"}')  # noqa: E501
expected_execute_signature = "execute(bytes,bytes[])"
expected_fct_abi_19 = json.loads('{"inputs": [{"components": [{"name": "currency0", "type": "address"}, {"name": "currency1", "type": "address"}, {"name": "fee", "type": "uint24"}, {"name": "tickSpacing", "type": "int24"}, {"name": "hooks", "type": "address"}], "name": "PoolKey", "type": "tuple"}, {"name": "sqrtPriceX96", "type": "uint256"}], "name": "V4_INITIALIZE_POOL", "type": "function"}')  # noqa E501
expected_fct_signature_19 = "V4_INITIALIZE_POOL((address,address,uint24,int24,address),uint256)"
expected_v4_swap_exact_in_abi = json.loads('{"inputs": [{"name": "params", "type": "ExactInputParams"}], "name": "SWAP_EXACT_IN", "type": "function"}')  # noqa E501
expected_v4_swap_exact_in_signature = "SWAP_EXACT_IN(ExactInputParams)"


@pytest.mark.parametrize(
    "command_id, expected_fct_abi, expected_selector, expected_signature",
    (
        (RouterFunction(8), expected_fct_abi_08, bytes.fromhex("3bd2d879"), expected_fct_signature_08),
        (RouterFunction(10), expected_fct_abi_10, b'9#\xf7\x04', expected_fct_signature_10),
        (MiscFunctions.EXECUTE, expected_execute_abi, bytes.fromhex("24856bc3"), expected_execute_signature),
        (RouterFunction.V4_INITIALIZE_POOL, expected_fct_abi_19, b'\xdb\xd4\xe4\xbd', expected_fct_signature_19),
        (V4Actions.SWAP_EXACT_IN, expected_v4_swap_exact_in_abi, b'h>~1', expected_v4_swap_exact_in_signature),  # noqa E501
    )
)
def test_build_abi_map(command_id, expected_fct_abi, expected_selector, expected_signature, codec):
    assert codec._abi_map[command_id].get_abi() == expected_fct_abi
    assert codec._abi_map[command_id].get_selector() == expected_selector
    assert codec._abi_map[command_id].get_signature() == expected_signature


abi_dict_1 = \
    {
        'inputs': [
            {
                'name': 'recipient',
                'type': 'address'
            },
            {
                'name': 'amountMin',
                'type': 'uint256'
            }
        ],
        'name': 'WRAP_ETH',
        'type': 'function'
    }

abi_dict_2 = \
    {
        'inputs': [
            {
                'name': 'struct',
                'type': 'tuple',
                'components':
                    [
                        {
                            'name': 'details',
                            'type': 'tuple',
                            'components': [
                                {
                                    'name': 'token',
                                    'type': 'address'
                                },
                                {
                                    'name': 'amount',
                                    'type': 'uint160'
                                },
                                {
                                    'name': 'expiration',
                                    'type': 'uint48'
                                },
                                {
                                    'name': 'nonce',
                                    'type': 'uint48'
                                }
                            ]
                        },
                        {
                            'name': 'spender',
                            'type': 'address'
                        },
                        {
                            'name': 'sigDeadline',
                            'type': 'uint256'
                        }
                    ]
            },
            {
                'name': 'data',
                'type': 'bytes'
            }
        ],
        'name': 'PERMIT2_PERMIT',
        'type': 'function'
    }


@pytest.mark.parametrize(
    "abi_dict, expected_abi_types",
    (
        (abi_dict_1, ["address", "uint256"]),
        (abi_dict_2, ["((address,uint160,uint48,uint48),address,uint256)", "bytes"]),
    )
)
def test_get_abi_types(abi_dict, expected_abi_types):
    assert build_abi_type_list(abi_dict) == expected_abi_types
