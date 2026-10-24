import pytest

from uniswap_universal_router_decoder import (
    AsyncRouterCodec,
    decoded_input_to_dict,
    RouterCodec,
)
from uniswap_universal_router_decoder._command_spec import (
    describe_command,
    encode_commands,
    list_command_specs,
)


TOKEN_IN = "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2"
TOKEN_OUT = "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48"
SENDER = "0x0000000000000000000000000000000000000001"


def _swap_plan():
    # The decoded form of a V3_SWAP_EXACT_IN call, as returned by decoded_input_to_dict().
    path = RouterCodec().encode.v3_path("V3_SWAP_EXACT_IN", [TOKEN_IN, 3000, TOKEN_OUT])
    return {
        "function": "execute",
        "params": {
            "inputs": [
                {
                    "command": "V3_SWAP_EXACT_IN",
                    "params": {
                        "recipient": SENDER,
                        "amountIn": 1000,
                        "amountOutMin": 0,
                        "path": "0x" + path.hex(),
                        "payerIsSender": True,
                        "minHopPriceX36": [],
                    },
                },
            ],
            "deadline": 1234,
        },
    }


def test_list_command_specs_describes_the_format():
    result = list_command_specs()

    assert result["format"]["function"]["default"] == "execute"
    assert result["format"]["params"]["inputs"]["required"] is True
    assert result["format"]["params"]["deadline"]["required"] is False


def test_list_command_specs_lists_every_command():
    specs = list_command_specs()["commands"]
    names = {spec["command"] for spec in specs}

    assert {"WRAP_ETH", "V3_SWAP_EXACT_IN", "decreaseLiquidity", "collect", "burn", "permit"} <= names
    # V3_POSITION_MANAGER_CALL is described through the three position manager functions it can call
    assert "V3_POSITION_MANAGER_CALL" not in names
    # the commands the decoder expands into structures are listed too, flagged as not rebuildable
    assert {spec["command"] for spec in specs if not spec["rebuildable"]} == {
        "V4_SWAP", "modifyLiquidities", "EXECUTE_SUB_PLAN",
    }


def test_describe_command_reports_the_abi_params():
    spec = describe_command("PAY_PORTION")
    params = {param["name"]: param for param in spec["params"]}

    assert spec["command"] == "PAY_PORTION"
    assert spec["rebuildable"] is True
    assert set(params) == {"token", "recipient", "bips"}
    assert params["bips"]["type"] == "uint256"
    assert "basis points" in params["bips"]["description"]


def test_describe_command_reports_the_struct_components():
    spec = describe_command("V4_INITIALIZE_POOL")
    params = {param["name"]: param for param in spec["params"]}

    assert params["PoolKey"]["type"] == "tuple"
    assert [component["name"] for component in params["PoolKey"]["components"]] == [
        "currency0", "currency1", "fee", "tickSpacing", "hooks",
    ]


def test_describe_command_flags_the_commands_that_support_revert_on_fail():
    assert "revert_on_fail" in describe_command("BALANCE_CHECK_ERC20")
    assert "revert_on_fail" not in describe_command("WRAP_ETH")


def test_describe_command_reports_the_not_rebuildable_commands():
    spec = describe_command("V4_SWAP")

    assert spec["rebuildable"] is False
    assert "reason" in spec
    assert "params" not in spec


def test_describe_command_rejects_unknown():
    with pytest.raises(ValueError, match="Unknown command"):
        describe_command("NOT_A_COMMAND")


def test_encoder_function_input_builds_from_a_decoded_call(codec):
    calldata = codec.encode.function_input(_swap_plan())

    assert calldata.startswith("0x")
    structured = decoded_input_to_dict(codec.decode.function_input(calldata))
    assert structured["params"]["deadline"] == 1234
    assert structured["params"]["inputs"][0]["command"] == "V3_SWAP_EXACT_IN"


def test_async_encoder_function_input():
    async_codec = AsyncRouterCodec()

    assert async_codec.encode.function_input(_swap_plan()).startswith("0x")


def test_encode_commands_delegates_to_encoder_function_input(codec):
    plan = _swap_plan()

    assert encode_commands(codec, plan) == codec.encode.function_input(plan)


def test_encoder_function_input_rejects_an_unknown_command(codec):
    with pytest.raises(ValueError, match="Unknown command 'nope'"):
        codec.encode.function_input({"params": {"inputs": [{"command": "nope", "params": {}}]}})
