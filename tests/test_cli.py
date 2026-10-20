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


def _swap_params():
    return {
        "function_recipient": "SENDER",
        "amount_in": 1000,
        "amount_out_min": 0,
        "path": [TOKEN_IN, 3000, TOKEN_OUT],
    }


def test_encode_list(capsys):
    assert encode_main(["list"]) == 0
    specs = json.loads(capsys.readouterr().out)
    assert {spec["command"] for spec in specs} >= {"v3_swap_exact_in", "wrap_eth"}


def test_encode_describe(capsys):
    assert encode_main(["describe", "wrap_eth"]) == 0
    spec = json.loads(capsys.readouterr().out)
    assert spec["command"] == "wrap_eth"
    assert {param["name"] for param in spec["params"]} == {"function_recipient", "amount", "custom_recipient"}


def test_encode_build_single_command(capsys):
    assert encode_main(
        ["build", "--command", "v3_swap_exact_in", "--params", json.dumps(_swap_params()), "--deadline", "1234"]
    ) == 0
    result = json.loads(capsys.readouterr().out)

    assert result["deadline"] == 1234
    assert result["commands"] == ["v3_swap_exact_in"]
    structured = decoded_input_to_dict(RouterCodec().decode.function_input(result["calldata"]))
    assert structured["params"]["inputs"][0]["command"] == "V3_SWAP_EXACT_IN"


def test_encode_build_from_plan(tmp_path, capsys):
    plan = tmp_path / "plan.json"
    plan.write_text(
        json.dumps(
            {
                "deadline": 4321,
                "commands": [{"command": "v3_swap_exact_in", "params": _swap_params()}],
            }
        )
    )
    assert encode_main(["build", "--plan", str(plan)]) == 0
    result = json.loads(capsys.readouterr().out)

    assert result["deadline"] == 4321
    assert result["calldata"].startswith("0x")


def test_encode_build_from_plan_list(tmp_path, capsys):
    plan = tmp_path / "plan.json"
    plan.write_text(
        json.dumps([{"command": "wrap_eth", "params": {"function_recipient": "SENDER", "amount": 10 ** 18}}])
    )

    assert encode_main(["build", "--plan", str(plan), "--deadline", "1234"]) == 0
    result = json.loads(capsys.readouterr().out)

    assert result["commands"] == ["wrap_eth"]
    assert result["deadline"] == 1234


def test_encode_build_from_plan_stdin(monkeypatch, capsys):
    plan = json.dumps([{"command": "wrap_eth", "params": {"function_recipient": "SENDER", "amount": 10 ** 18}}])
    monkeypatch.setattr("sys.stdin", io.StringIO(plan))

    assert encode_main(["build", "--plan", "-", "--deadline", "1234"]) == 0
    result = json.loads(capsys.readouterr().out)

    assert result["commands"] == ["wrap_eth"]


def test_encode_build_requires_command_or_plan(capsys):
    with pytest.raises(SystemExit):
        encode_main(["build"])


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
