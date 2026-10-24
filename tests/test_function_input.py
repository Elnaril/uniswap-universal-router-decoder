from typing import (
    Any,
    Callable,
    Optional,
)

import pytest
from web3 import Web3

from uniswap_universal_router_decoder import (
    AsyncRouterCodec,
    decoded_input_to_dict,
    FunctionRecipient,
    RouterCodec,
)


TOKEN_IN = Web3.to_checksum_address("0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2")
TOKEN_OUT = Web3.to_checksum_address("0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48")
TOKEN_MID = Web3.to_checksum_address("0x6B175474E89094C44Da98b954EedeAC495271d0F")
CUSTOM_RECIPIENT = Web3.to_checksum_address("0x247B1d8Efc8b39D4b6c6179CbfBfA420c31217a8")

V2_PATH = [TOKEN_IN, TOKEN_OUT]
V3_PATH = [TOKEN_IN, 3000, TOKEN_OUT]
V3_LONG_PATH = [TOKEN_IN, 3000, TOKEN_OUT, 500, TOKEN_MID]


@pytest.fixture
def codec():
    return RouterCodec()


def _decoded(codec: RouterCodec, build: Callable[[Any], Any], deadline: Optional[int] = 1234) -> dict[str, Any]:
    """Encode a chain, then return its JSON-friendly decoded form."""
    return decoded_input_to_dict(codec.decode.function_input(build(codec.encode.chain()).build(deadline)))


def _round_trip(codec: RouterCodec, build: Callable[[Any], Any]) -> None:
    """Encode a chain, decode it, then rebuild the calldata from the decoded form."""
    calldata = build(codec.encode.chain()).build(deadline=1234)
    plan = decoded_input_to_dict(codec.decode.function_input(calldata))

    assert codec.encode.function_input(plan) == calldata


def test_round_trip_simple_commands(codec):
    _round_trip(codec, lambda b: b.wrap_eth(FunctionRecipient.ROUTER, 10))
    _round_trip(codec, lambda b: b.unwrap_weth(FunctionRecipient.SENDER, 10))
    _round_trip(codec, lambda b: b.sweep(FunctionRecipient.CUSTOM, TOKEN_IN, 5, CUSTOM_RECIPIENT))
    _round_trip(codec, lambda b: b.transfer(FunctionRecipient.SENDER, TOKEN_IN, 7))
    _round_trip(codec, lambda b: b.pay_portion(FunctionRecipient.SENDER, TOKEN_IN, 24))
    _round_trip(
        codec,
        lambda b: b.pay_portion_full_precision(FunctionRecipient.SENDER, TOKEN_IN, 4000000000000000),
    )
    _round_trip(codec, lambda b: b.balance_check_erc20(CUSTOM_RECIPIENT, TOKEN_IN, 3))
    _round_trip(codec, lambda b: b.permit2_transfer_from(FunctionRecipient.SENDER, TOKEN_IN, 9))
    _round_trip(
        codec,
        lambda b: b.permit2_transfer_from_batch(
            [{"from": TOKEN_IN, "to": TOKEN_OUT, "amount": 5, "token": TOKEN_IN}],
        ),
    )


def test_round_trip_swaps(codec):
    _round_trip(codec, lambda b: b.v2_swap_exact_in(FunctionRecipient.SENDER, 100, 1, V2_PATH))
    _round_trip(codec, lambda b: b.v2_swap_exact_out(FunctionRecipient.SENDER, 100, 200, V2_PATH))
    _round_trip(codec, lambda b: b.v3_swap_exact_in(FunctionRecipient.ROUTER, 100, 1, V3_PATH))
    _round_trip(codec, lambda b: b.v3_swap_exact_out(FunctionRecipient.SENDER, 100, 200, V3_PATH))
    _round_trip(codec, lambda b: b.v3_swap_exact_in(FunctionRecipient.SENDER, 100, 1, V3_LONG_PATH))


def test_round_trip_v3_position_manager_call(codec):
    _round_trip(codec, lambda b: b.v3_decrease_liquidity(123, 100, 0, 0, 999))
    _round_trip(codec, lambda b: b.v3_collect(123, CUSTOM_RECIPIENT, 10, 20))
    _round_trip(codec, lambda b: b.v3_burn(123))


def test_round_trip_v4_initialize_pool(codec):
    pool_key = codec.encode.v4_pool_key(TOKEN_IN, TOKEN_OUT, 3000, 60)

    _round_trip(codec, lambda b: b.v4_initialize_pool(pool_key, 1, 2))


def test_round_trip_multi_command_route(codec):
    _round_trip(
        codec,
        lambda b: (
            b.wrap_eth(FunctionRecipient.ROUTER, 10)
            .v3_swap_exact_in(FunctionRecipient.CUSTOM, 100, 1, V3_PATH, CUSTOM_RECIPIENT)
            .unwrap_weth(FunctionRecipient.SENDER, 5)
        ),
    )


def test_round_trip_without_deadline(codec):
    assert "deadline" not in _decoded(codec, lambda b: b.wrap_eth(FunctionRecipient.ROUTER, 10), deadline=None)

    _round_trip(codec, lambda b: b.wrap_eth(FunctionRecipient.ROUTER, 10))


def test_async_function_input():
    async_codec = AsyncRouterCodec()
    calldata = (
        async_codec
        .encode
        .chain()
        .v3_swap_exact_in(FunctionRecipient.SENDER, 100, 1, V3_PATH)
        .build(deadline=1234)
    )

    plan = decoded_input_to_dict(async_codec.decode.function_input(calldata))

    assert async_codec.encode.function_input(plan) == calldata


def test_function_input_defaults_the_function_key(codec):
    plan = _decoded(codec, lambda b: b.wrap_eth(FunctionRecipient.ROUTER, 10))
    expected = codec.encode.function_input(plan)
    del plan["function"]

    assert codec.encode.function_input(plan) == expected


def test_function_input_ignores_the_commands_bytes(codec):
    plan = _decoded(codec, lambda b: b.wrap_eth(FunctionRecipient.ROUTER, 10))
    expected = codec.encode.function_input(plan)
    plan["params"]["commands"] = "0x"

    assert codec.encode.function_input(plan) == expected


def test_function_input_rejects_a_non_execute_call(codec):
    with pytest.raises(ValueError, match="Only the 'execute' call"):
        codec.encode.function_input({"function": "executeSigned", "params": {}})


def test_function_input_rejects_an_unknown_command(codec):
    plan = {"params": {"inputs": [{"command": "NOPE", "params": {}}]}}

    with pytest.raises(ValueError, match="Unknown command 'NOPE'"):
        codec.encode.function_input(plan)


@pytest.mark.parametrize("command", ("V4_SWAP", "EXECUTE_SUB_PLAN", "modifyLiquidities"))
def test_function_input_rejects_structured_commands(codec, command):
    plan = {"params": {"inputs": [{"command": command, "params": {}}]}}

    with pytest.raises(ValueError, match="cannot be rebuilt from its decoded form"):
        codec.encode.function_input(plan)


def test_revert_on_fail_sets_the_no_revert_flag(codec):
    calldata = codec.encode.chain().v3_burn(123, revert_on_fail=False).build(deadline=1234)
    plan = decoded_input_to_dict(codec.decode.function_input(calldata))

    assert plan["params"]["commands"] == "0x92"  # 0x80 (NO_REVERT) | 0x12 (V3_POSITION_MANAGER_CALL)
    assert plan["params"]["inputs"][0]["revert_on_fail"] is False


def test_round_trip_a_no_revert_command(codec):
    pool_key = codec.encode.v4_pool_key(TOKEN_IN, TOKEN_OUT, 3000, 60)

    _round_trip(codec, lambda b: b.v3_burn(123, revert_on_fail=False))
    _round_trip(codec, lambda b: b.v3_collect(123, CUSTOM_RECIPIENT, 10, 20, revert_on_fail=False))
    _round_trip(codec, lambda b: b.balance_check_erc20(CUSTOM_RECIPIENT, TOKEN_IN, 3, revert_on_fail=False))
    _round_trip(codec, lambda b: b.v4_initialize_pool(pool_key, 1, 2, revert_on_fail=False))


def test_revert_on_fail_is_cleared_for_unsupported_commands(codec):
    calldata = codec.encode.chain().wrap_eth(FunctionRecipient.ROUTER, 10).build(deadline=1234)
    plan = decoded_input_to_dict(codec.decode.function_input(calldata))
    plan["params"]["inputs"][0]["revert_on_fail"] = False

    # WRAP_ETH does not honour the flag, so it is cleared and the calldata stays canonical
    assert codec.encode.function_input(plan) == calldata
