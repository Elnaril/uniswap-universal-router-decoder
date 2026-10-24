"""
Discoverable description of the UR commands, in the decoded format that Encoder.function_input() consumes.

The description is derived from the Universal Router ABIs (see _abi_builder), so it matches the decoded format and
follows the ABIs when they change. The parameters whose meaning is not obvious from their ABI type carry a
hand-written description.
"""
from __future__ import annotations

from typing import (
    Any,
    cast,
    Optional,
    Union,
)

from uniswap_universal_router_decoder._abi_builder import (
    ABIFunction,
    ABIMap,
    ABIMapWrapper,
    ABIParam,
    ABIStruct,
)
from uniswap_universal_router_decoder._enums import (
    NO_REVERT_COMMANDS,
    RouterFunction,
    STRUCTURED_COMMANDS,
    V3_POSITION_MANAGER_ACTIONS,
)
from uniswap_universal_router_decoder.router_codec import (
    AsyncRouterCodec,
    RouterCodec,
)


# The envelope of a decoded call, ie the shape Encoder.function_input() expects.
_FORMAT: dict[str, Any] = {
    "function": {
        "type": "string",
        "required": False,
        "default": "execute",
        "description": "the UR function to call; only 'execute' can be rebuilt from data",
    },
    "params": {
        "inputs": {
            "type": "list",
            "required": True,
            "description": (
                "one entry per command, in execution order: {'command': <name>, 'params': {...}} plus an optional "
                "'revert_on_fail' for the commands that support it"
            ),
        },
        "deadline": {
            "type": "integer",
            "required": False,
            "description": (
                "unix timestamp; omit it to build execute(bytes,bytes[]) instead of execute(bytes,bytes[],uint256)"
            ),
        },
    },
}

_NOT_REBUILDABLE_REASON = (
    "the decoder expands its arguments into decoded structures (V4 actions, nested commands) instead of ABI "
    "values, so it cannot be rebuilt from a decoded call"
)

_RECIPIENT = (
    "the recipient of the command output, or one of the UR sentinels: 0x0000000000000000000000000000000000000001 "
    "for the transaction sender, 0x0000000000000000000000000000000000000002 for the router"
)
_V2_PATH = "the token sequence: the first token is the one sold, the last one is the one bought"
_V3_PATH = (
    "the packed V3 path: token address + pool fee (3 bytes) + token address + ...; "
    "see 'ur-decode v3-path' / 'ur-encode v3-path'"
)
_PAYER_IS_SENDER = "True if the input tokens come from the sender, False if they are already held by the router"
_MIN_HOP_PRICE = "the minimum price (output / input x 1e36) expected for each hop; an empty list disables the check"
_BIPS = "the share to pay, in basis points (1/10000)"
_PORTION = "the share to pay, in 1e18 precision"
_POOL_KEY = "the V4 pool key: currency0, currency1, fee, tickSpacing, hooks"
_SQRT_PRICE = "the initial pool price; the encoder computes it from the amount_0 / amount_1 ratio"
_ALLOWANCE_DETAILS = "the transfers to perform: from, to, amount, token"
_PERMIT_STRUCT = "the permit: details (token, amount, expiration, nonce), spender, sigDeadline"
_PERMIT_BATCH_STRUCT = "the permit batch: a list of details (token, amount, expiration, nonce), spender, sigDeadline"
_PERMIT_SIGNATURE = "the signature of the permit, as returned by sign_message()"
_V3_PERMIT_V = "the v component of the permit signature"
_V3_PERMIT_R = "the r component of the permit signature"
_V3_PERMIT_S = "the s component of the permit signature"

# The parameters whose meaning is not obvious from their ABI type, keyed by command name then parameter name.
_PARAM_DESCRIPTIONS: dict[str, dict[str, str]] = {
    "WRAP_ETH": {"recipient": _RECIPIENT},
    "UNWRAP_WETH": {"recipient": _RECIPIENT},
    "SWEEP": {"recipient": _RECIPIENT},
    "TRANSFER": {"recipient": _RECIPIENT},
    "PAY_PORTION": {"recipient": _RECIPIENT, "bips": _BIPS},
    "PAY_PORTION_FULL_PRECISION": {"recipient": _RECIPIENT, "portion": _PORTION},
    "PERMIT2_TRANSFER_FROM": {"recipient": _RECIPIENT},
    "PERMIT2_TRANSFER_FROM_BATCH": {"AllowanceTransferDetails": _ALLOWANCE_DETAILS},
    "PERMIT2_PERMIT": {"struct": _PERMIT_STRUCT, "data": _PERMIT_SIGNATURE},
    "PERMIT2_PERMIT_BATCH": {"struct": _PERMIT_BATCH_STRUCT, "data": _PERMIT_SIGNATURE},
    "V2_SWAP_EXACT_IN": {
        "recipient": _RECIPIENT,
        "path": _V2_PATH,
        "payerIsSender": _PAYER_IS_SENDER,
        "minHopPriceX36": _MIN_HOP_PRICE,
    },
    "V2_SWAP_EXACT_OUT": {
        "recipient": _RECIPIENT,
        "path": _V2_PATH,
        "payerIsSender": _PAYER_IS_SENDER,
        "minHopPriceX36": _MIN_HOP_PRICE,
    },
    "V3_SWAP_EXACT_IN": {
        "recipient": _RECIPIENT,
        "path": _V3_PATH,
        "payerIsSender": _PAYER_IS_SENDER,
        "minHopPriceX36": _MIN_HOP_PRICE,
    },
    "V3_SWAP_EXACT_OUT": {
        "recipient": _RECIPIENT,
        "path": _V3_PATH,
        "payerIsSender": _PAYER_IS_SENDER,
        "minHopPriceX36": _MIN_HOP_PRICE,
    },
    "V4_INITIALIZE_POOL": {"PoolKey": _POOL_KEY, "sqrtPriceX96": _SQRT_PRICE},
    "permit": {"v": _V3_PERMIT_V, "r": _V3_PERMIT_R, "s": _V3_PERMIT_S},
    "decreaseLiquidity": {"params": "the position to decrease: tokenId, liquidity, amount0Min, amount1Min, deadline"},
    "collect": {"params": "the position to collect from: tokenId, recipient, amount0Max, amount1Max"},
}


def _param_spec(abi_param: Union[ABIParam, ABIStruct], description: Optional[str]) -> dict[str, Any]:
    spec: dict[str, Any] = {"name": abi_param.name, "type": abi_param.type}
    if isinstance(abi_param, ABIStruct):
        spec["components"] = [_param_spec(component, None) for component in abi_param.params]
    if description is not None:
        spec["description"] = description
    return spec


def _command_spec(name: str, router_function: RouterFunction, abi: ABIFunction) -> dict[str, Any]:
    descriptions = _PARAM_DESCRIPTIONS.get(name, {})
    spec: dict[str, Any] = {
        "command": name,
        "rebuildable": True,
        "params": [_param_spec(abi_param, descriptions.get(abi_param.name)) for abi_param in abi.params],
    }
    if router_function in NO_REVERT_COMMANDS:
        spec["revert_on_fail"] = {
            "type": "boolean",
            "required": False,
            "default": True,
            "description": "False to let the transaction continue if this command fails",
        }
    return spec


def _rebuildable_commands(abi_map: ABIMap) -> list[tuple[str, RouterFunction, ABIFunction]]:
    commands: list[tuple[str, RouterFunction, ABIFunction]] = []
    for router_function in RouterFunction:
        if router_function in STRUCTURED_COMMANDS or router_function is RouterFunction.V3_POSITION_MANAGER_CALL:
            continue
        commands.append((abi_map[router_function].name, router_function, abi_map[router_function]))
    # V3_POSITION_MANAGER_CALL decodes under the name of the position manager function it calls, not its own
    for name, action in V3_POSITION_MANAGER_ACTIONS.items():
        commands.append((name, RouterFunction.V3_POSITION_MANAGER_CALL, abi_map[action]))
    return sorted(commands, key=lambda command: command[0])


def _not_rebuildable_specs(abi_map: ABIMap) -> list[dict[str, Any]]:
    return [
        {"command": abi_map[router_function].name, "rebuildable": False, "reason": _NOT_REBUILDABLE_REASON}
        for router_function in sorted(STRUCTURED_COMMANDS, key=lambda router_function: router_function.value)
    ]


def _all_command_specs() -> list[dict[str, Any]]:
    abi_map = ABIMapWrapper().abi_map
    specs = [_command_spec(name, router_function, abi) for name, router_function, abi in _rebuildable_commands(abi_map)]
    specs.extend(_not_rebuildable_specs(abi_map))
    return specs


def list_command_specs() -> dict[str, Any]:
    """
    Describe the decoded call format and every UR command.

    :return: {"format": <the envelope>, "commands": [<command description>, ...]}
    """
    return {"format": _FORMAT, "commands": _all_command_specs()}


def describe_command(name: str) -> dict[str, Any]:
    """
    Describe a single UR command, as it appears in the decoded format.

    :param name: the command name, as decoded (ex: V3_SWAP_EXACT_IN, decreaseLiquidity)
    :return: the command description
    """
    specs = _all_command_specs()
    for spec in specs:
        if spec["command"] == name:
            return spec
    known = ", ".join(sorted(cast(str, spec["command"]) for spec in specs))
    raise ValueError(f"Unknown command '{name}'. Known commands: {known}")


def encode_commands(codec: Union[RouterCodec, AsyncRouterCodec], plan: dict[str, Any]) -> str:
    """
    Build UR calldata from the decoded form of an "execute" call.

    Thin wrapper around Encoder.function_input()/AsyncEncoder.function_input().

    :param codec: a RouterCodec or AsyncRouterCodec instance
    :param plan: the decoded call to rebuild (see Encoder.function_input())
    :return: the encoded calldata, as a "0x"-prefixed hex string
    """
    return codec.encode.function_input(plan)
