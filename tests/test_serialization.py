from uniswap_universal_router_decoder import (
    decoded_input_to_dict,
    FunctionRecipient,
    transaction_to_dict,
)
from uniswap_universal_router_decoder._serialization import (
    _to_jsonable,
    to_json_primitives,
)


TOKEN_IN = "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2"
TOKEN_OUT = "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48"
RECIPIENT = "0x247B1d8Efc8b39D4b6c6179CbfBfA420c31217a8"


def test_serialization_helpers_are_exported():
    import uniswap_universal_router_decoder as sdk

    assert {"decoded_input_to_dict", "transaction_to_dict"} <= set(sdk.__all__)
    assert sdk.decoded_input_to_dict is decoded_input_to_dict
    assert sdk.transaction_to_dict is transaction_to_dict


def test_to_json_primitives():
    assert to_json_primitives(b"\x01\x02") == "0x0102"
    assert to_json_primitives(bytearray(b"\xff")) == "0xff"
    assert to_json_primitives({"a": (1, b"\xff")}) == {"a": [1, "0xff"]}
    assert to_json_primitives(123) == 123
    assert to_json_primitives(True) is True
    assert to_json_primitives(None) is None


def test_to_jsonable_renders_a_decoded_command(codec):
    calldata = (
        codec.encode()
        .v3_swap_exact_in(FunctionRecipient.SENDER, 1000, 0, [TOKEN_IN, 3000, TOKEN_OUT])
        .build(deadline=1234)
    )
    params = codec.decode.function_input(calldata)[1]

    structured = _to_jsonable(params)

    assert structured["commands"] == "0x00"
    assert structured["deadline"] == 1234
    command = structured["inputs"][0]
    assert command["command"] == "V3_SWAP_EXACT_IN"
    assert command["revert_on_fail"] is True


def test_decoded_input_to_dict_round_trip(codec):
    calldata = (
        codec.encode()
        .v3_swap_exact_in(FunctionRecipient.SENDER, 1000, 0, [TOKEN_IN, 3000, TOKEN_OUT])
        .build(deadline=1234)
    )
    structured = decoded_input_to_dict(codec.decode.function_input(calldata))

    assert structured["function"] == "execute"
    assert structured["params"]["deadline"] == 1234
    command = structured["params"]["inputs"][0]
    assert command["command"] == "V3_SWAP_EXACT_IN"
    assert command["revert_on_fail"] is True
    assert command["params"]["amountIn"] == 1000
    assert command["params"]["path"].startswith("0x")


def test_decoded_input_to_dict_chained_commands(codec):
    calldata = (
        codec.encode()
        .v3_decrease_liquidity(1, 100, 0, 0, 1234)
        .v3_collect(1, RECIPIENT, 0, 0)
        .build(deadline=1234)
    )
    structured = decoded_input_to_dict(codec.decode.function_input(calldata))

    commands = structured["params"]["inputs"]
    # 0x12 decodes to the actual V3 position manager function names.
    assert [command["command"] for command in commands] == ["decreaseLiquidity", "collect"]
    assert all(command["revert_on_fail"] is True for command in commands)


def test_transaction_to_dict(codec):
    calldata = (
        codec.encode()
        .v3_swap_exact_in(FunctionRecipient.SENDER, 1000, 0, [TOKEN_IN, 3000, TOKEN_OUT])
        .build(deadline=1234)
    )
    trx = {
        "hash": b"\x00\x01",
        "input": calldata,
        "decoded_input": codec.decode.function_input(calldata),
    }
    structured = transaction_to_dict(trx)

    assert structured["hash"] == "0x0001"
    assert structured["decoded_input"]["function"] == "execute"
