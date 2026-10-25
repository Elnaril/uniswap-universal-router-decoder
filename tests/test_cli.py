import io
import json
from typing import Any

import pytest

from uniswap_universal_router_decoder import (
    decoded_input_to_dict,
    FunctionRecipient,
    RouterCodec,
)
from uniswap_universal_router_decoder.cli import (
    _make_codec,
    decode_main,
    encode_main,
)
from uniswap_universal_router_decoder.decoder import Decoder


TOKEN_IN = "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2"
TOKEN_OUT = "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48"
TOKEN_MID = "0x6B175474E89094C44Da98b954EedeAC495271d0F"
SENDER = "0x0000000000000000000000000000000000000001"


def _swap_decoded_params():
    path = RouterCodec().encode.v3_path("V3_SWAP_EXACT_IN", [TOKEN_IN, 3000, TOKEN_OUT])
    return {
        "recipient": SENDER,
        "amountIn": 1000,
        "amountOutMin": 0,
        "path": "0x" + path.hex(),
        "payerIsSender": True,
        "minHopPriceX36": [],
    }


def test_encode_list(capsys):
    assert encode_main(["list"]) == 0
    result = json.loads(capsys.readouterr().out)

    assert result["format"]["function"]["default"] == "execute"
    assert {spec["command"] for spec in result["commands"]} >= {"V3_SWAP_EXACT_IN", "WRAP_ETH"}


def test_encode_describe(capsys):
    assert encode_main(["describe", "WRAP_ETH"]) == 0
    spec = json.loads(capsys.readouterr().out)

    assert spec["command"] == "WRAP_ETH"
    assert {param["name"] for param in spec["params"]} == {"recipient", "amountMin"}


def test_encode_build_single_command(capsys):
    assert encode_main(
        ["build", "--command", "V3_SWAP_EXACT_IN", "--params", json.dumps(_swap_decoded_params()), "--deadline", "1234"]
    ) == 0
    result = json.loads(capsys.readouterr().out)

    assert result["deadline"] == 1234
    assert result["commands"] == ["V3_SWAP_EXACT_IN"]
    structured = decoded_input_to_dict(RouterCodec().decode.function_input(result["calldata"]))
    assert structured["params"]["inputs"][0]["command"] == "V3_SWAP_EXACT_IN"


def test_encode_build_from_plan(tmp_path, capsys):
    plan = tmp_path / "plan.json"
    plan.write_text(
        json.dumps(
            {
                "function": "execute",
                "params": {
                    "inputs": [{"command": "V3_SWAP_EXACT_IN", "params": _swap_decoded_params()}],
                    "deadline": 4321,
                },
            }
        )
    )
    assert encode_main(["build", "--plan", str(plan)]) == 0
    result = json.loads(capsys.readouterr().out)

    assert result["deadline"] == 4321
    assert result["commands"] == ["V3_SWAP_EXACT_IN"]
    assert result["calldata"].startswith("0x")


def test_encode_build_deadline_flag_overrides_the_plan(tmp_path, capsys):
    plan = tmp_path / "plan.json"
    plan.write_text(
        json.dumps(
            {
                "function": "execute",
                "params": {
                    "inputs": [{"command": "WRAP_ETH", "params": {"recipient": SENDER, "amountMin": 10 ** 18}}],
                    "deadline": 4321,
                },
            }
        )
    )
    assert encode_main(["build", "--plan", str(plan), "--deadline", "1234"]) == 0
    result = json.loads(capsys.readouterr().out)

    assert result["commands"] == ["WRAP_ETH"]
    assert result["deadline"] == 1234


def test_encode_build_rejects_a_non_object_plan(tmp_path, capsys):
    plan = tmp_path / "plan.json"
    plan.write_text(json.dumps([{"command": "WRAP_ETH", "params": {}}]))

    with pytest.raises(SystemExit):
        encode_main(["build", "--plan", str(plan)])


def test_encode_build_rejects_a_plan_without_params(tmp_path, capsys):
    plan = tmp_path / "plan.json"
    plan.write_text(json.dumps({"function": "execute"}))

    with pytest.raises(SystemExit) as excinfo:
        encode_main(["build", "--plan", str(plan)])

    assert excinfo.value.code == 2
    assert "missing or invalid key: 'params'" in capsys.readouterr().err


def test_encode_build_from_plan_stdin(monkeypatch, capsys):
    plan = json.dumps(
        {
            "function": "execute",
            "params": {"inputs": [{"command": "WRAP_ETH", "params": {"recipient": SENDER, "amountMin": 10 ** 18}}]},
        }
    )
    monkeypatch.setattr("sys.stdin", io.StringIO(plan))

    assert encode_main(["build", "--plan", "-", "--deadline", "1234"]) == 0
    result = json.loads(capsys.readouterr().out)

    assert result["commands"] == ["WRAP_ETH"]
    assert result["deadline"] == 1234


def test_encode_build_round_trips_the_trailing_data(tmp_path, capsys):
    calldata = RouterCodec().encode().wrap_eth(FunctionRecipient.SENDER, 10 ** 18).build(deadline=1234)
    tagged = calldata + "756e697800000000000c"

    assert decode_main(["calldata", tagged]) == 0
    plan = json.loads(capsys.readouterr().out)
    assert plan["params"]["trailing_data"] == "0x756e697800000000000c"

    plan_file = tmp_path / "plan.json"
    plan_file.write_text(json.dumps(plan))
    assert encode_main(["build", "--plan", str(plan_file)]) == 0
    rebuilt = json.loads(capsys.readouterr().out)

    assert rebuilt["calldata"] == tagged


def test_encode_v3_path_from_arguments(capsys):
    assert encode_main(["v3-path", "V3_SWAP_EXACT_IN", TOKEN_IN, "3000", TOKEN_OUT]) == 0
    result = json.loads(capsys.readouterr().out)

    expected = RouterCodec().encode.v3_path("V3_SWAP_EXACT_IN", [TOKEN_IN, 3000, TOKEN_OUT])
    assert result == {"fn_name": "V3_SWAP_EXACT_IN", "path": "0x" + expected.hex()}


def test_encode_v3_path_multi_hop(capsys):
    assert encode_main(["v3-path", "V3_SWAP_EXACT_OUT", TOKEN_IN, "3000", TOKEN_OUT, "500", TOKEN_MID]) == 0
    result = json.loads(capsys.readouterr().out)

    expected = RouterCodec().encode.v3_path("V3_SWAP_EXACT_OUT", [TOKEN_IN, 3000, TOKEN_OUT, 500, TOKEN_MID])
    assert result["path"] == "0x" + expected.hex()


def test_encode_v3_path_from_a_json_list(capsys):
    path = json.dumps([TOKEN_IN, 3000, TOKEN_OUT, 500, TOKEN_MID])
    assert encode_main(["v3-path", "V3_SWAP_EXACT_IN", path]) == 0
    result = json.loads(capsys.readouterr().out)

    expected = RouterCodec().encode.v3_path("V3_SWAP_EXACT_IN", [TOKEN_IN, 3000, TOKEN_OUT, 500, TOKEN_MID])
    assert result["path"] == "0x" + expected.hex()


def test_encode_v3_path_matches_decode_v3_path(capsys):
    assert encode_main(["v3-path", "V3_SWAP_EXACT_IN", TOKEN_IN, "3000", TOKEN_OUT]) == 0
    encoded = json.loads(capsys.readouterr().out)["path"]

    assert decode_main(["v3-path", "V3_SWAP_EXACT_IN", encoded]) == 0
    assert json.loads(capsys.readouterr().out) == [TOKEN_IN, 3000, TOKEN_OUT]


@pytest.mark.parametrize("path", ([TOKEN_IN, TOKEN_OUT], [TOKEN_IN], ["not json"], ["3000"]))
def test_encode_v3_path_rejects_a_bad_path(path, capsys):
    with pytest.raises(SystemExit) as excinfo:
        encode_main(["v3-path", "V3_SWAP_EXACT_IN", *path])

    assert excinfo.value.code == 2
    assert capsys.readouterr().err


def test_encode_build_requires_command_or_plan(capsys):
    with pytest.raises(SystemExit):
        encode_main(["build"])


def test_encode_describe_unknown_command(capsys):
    with pytest.raises(SystemExit) as excinfo:
        encode_main(["describe", "NOPE"])

    assert excinfo.value.code == 2
    assert "Unknown command 'NOPE'" in capsys.readouterr().err


def test_encode_build_unknown_command(capsys):
    with pytest.raises(SystemExit) as excinfo:
        encode_main(["build", "--command", "NOPE", "--params", "{}"])

    assert excinfo.value.code == 2
    assert "Unknown command 'NOPE'" in capsys.readouterr().err


def test_encode_build_rejects_a_parameter_of_the_wrong_type(capsys):
    params = json.dumps({"recipient": SENDER, "amountMin": "100000000000000000"})

    with pytest.raises(SystemExit) as excinfo:
        encode_main(["build", "--command", "WRAP_ETH", "--params", params])

    assert excinfo.value.code == 2
    assert "cannot encode the parameters of 'WRAP_ETH'" in capsys.readouterr().err


def test_decode_calldata(capsys):
    calldata = (
        RouterCodec()
        .encode()
        .v3_swap_exact_in(FunctionRecipient.SENDER, 1000, 0, [TOKEN_IN, 3000, TOKEN_OUT])
        .build(deadline=1234)
    )
    assert decode_main(["calldata", calldata]) == 0
    structured = json.loads(capsys.readouterr().out)

    assert structured["function"] == "execute"
    assert structured["params"]["inputs"][0]["command"] == "V3_SWAP_EXACT_IN"


def test_decode_calldata_rejects_bad_input(capsys):
    with pytest.raises(SystemExit) as excinfo:
        decode_main(["calldata", "0xdeadbeef"])

    assert excinfo.value.code == 2
    assert "selector" in capsys.readouterr().err


def test_decode_error(capsys):
    assert decode_main(["error", "0x5d1d0f9f"]) == 0
    decoded = json.loads(capsys.readouterr().out)
    assert decoded["error"] == "OnlyMintAllowed()"


def test_decode_v3_path(capsys):
    path = RouterCodec().encode.v3_path("V3_SWAP_EXACT_IN", [TOKEN_IN, 3000, TOKEN_OUT])
    assert decode_main(["v3-path", "V3_SWAP_EXACT_IN", "0x" + path.hex()]) == 0
    decoded = json.loads(capsys.readouterr().out)
    assert decoded == [TOKEN_IN, 3000, TOKEN_OUT]


def test_decode_tx_requires_rpc(monkeypatch):
    monkeypatch.delenv("RPC_URL", raising=False)
    monkeypatch.delenv("ETH_RPC_URL", raising=False)
    with pytest.raises(SystemExit):
        decode_main(["tx", "0x" + "00" * 32])


def test_decode_tx(monkeypatch, capsys):
    codec = RouterCodec()
    calldata = codec.encode().wrap_eth(FunctionRecipient.SENDER, 10 ** 18).build(deadline=1234)
    decoded_input = codec.decode.function_input(calldata)

    def fake_transaction(self: Decoder, trx_hash: str) -> dict[str, Any]:
        return {"hash": b"\x00\x01", "input": calldata, "decoded_input": decoded_input}

    monkeypatch.setattr(Decoder, "transaction", fake_transaction)

    assert decode_main(["tx", "0x" + "00" * 32, "--rpc", "http://localhost:8545"]) == 0
    result = json.loads(capsys.readouterr().out)

    assert result["hash"] == "0x0001"
    assert result["decoded_input"]["function"] == "execute"


def test_make_codec_without_rpc(monkeypatch):
    monkeypatch.delenv("RPC_URL", raising=False)
    monkeypatch.delenv("ETH_RPC_URL", raising=False)

    assert isinstance(_make_codec(), RouterCodec)
