import pytest

from uniswap_universal_router_decoder import (
    AsyncRouterCodec,
    decoded_input_to_dict,
)
from uniswap_universal_router_decoder._command_spec import (
    describe_command,
    encode_commands,
    list_command_specs,
)
from uniswap_universal_router_decoder.encoder import resolve_command


TOKEN_IN = "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2"
TOKEN_OUT = "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48"


def _swap_commands():
    return [
        {
            "command": "v3_swap_exact_in",
            "params": {
                "function_recipient": "SENDER",
                "amount_in": 1000,
                "amount_out_min": 0,
                "path": [TOKEN_IN, 3000, TOKEN_OUT],
            },
        },
    ]


def test_list_command_specs_contains_expected_commands():
    names = {spec["command"] for spec in list_command_specs()}
    assert {"v3_swap_exact_in", "wrap_eth", "v3_decrease_liquidity", "v3_collect", "v3_burn"} <= names


def test_describe_command_reports_required_and_optional_params():
    spec = describe_command("pay_portion")
    params = {param["name"]: param for param in spec["params"]}

    assert set(params) == {"function_recipient", "token_address", "bips", "custom_recipient"}
    assert params["bips"]["required"] is True
    assert params["custom_recipient"]["required"] is False
    assert params["custom_recipient"]["default"] is None


def test_describe_command_reports_defaults():
    spec = describe_command("v3_swap_exact_in")
    params = {param["name"]: param for param in spec["params"]}

    assert params["payer_is_sender"]["default"] is True
    assert params["min_hop_price_x36"]["default"] == []


def test_resolve_command_accepts_router_function_name():
    assert resolve_command("V3_SWAP_EXACT_IN") == "v3_swap_exact_in"
    assert resolve_command("v3_swap_exact_in") == "v3_swap_exact_in"


def test_resolve_command_rejects_unknown():
    with pytest.raises(KeyError):
        resolve_command("NOT_A_COMMAND")


def test_encoder_function_input_coerces_recipient_and_builds(codec):
    calldata = codec.encode.function_input(_swap_commands(), deadline=1234)

    assert calldata.startswith("0x")
    structured = decoded_input_to_dict(codec.decode.function_input(calldata))
    assert structured["params"]["deadline"] == 1234
    assert structured["params"]["inputs"][0]["command"] == "V3_SWAP_EXACT_IN"


def test_async_encoder_function_input():
    async_codec = AsyncRouterCodec()

    assert async_codec.encode.function_input(_swap_commands(), deadline=1234).startswith("0x")


def test_encode_commands_delegates_to_encoder_function_input(codec):
    commands = _swap_commands()

    assert encode_commands(codec, commands, deadline=1234) == codec.encode.function_input(commands, 1234)


def test_encoder_function_input_rejects_unknown_parameter(codec):
    with pytest.raises(ValueError, match="Unknown parameter"):
        codec.encode.function_input([{"command": "wrap_eth", "params": {"nope": 1}}])


def test_encoder_function_input_rejects_bad_enum_value(codec):
    with pytest.raises(ValueError, match="Invalid value"):
        codec.encode.function_input([{"command": "wrap_eth", "params": {"function_recipient": "NOPE", "amount": 1}}])


def test_encoder_function_input_requires_command_key(codec):
    with pytest.raises(ValueError, match="command"):
        codec.encode.function_input([{"params": {}}])
