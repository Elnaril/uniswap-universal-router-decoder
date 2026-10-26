import asyncio
import runpy
import sys
from typing import (
    Any,
    Callable,
)

import pytest

from uniswap_universal_router_decoder import (
    FunctionRecipient,
    RouterCodec,
)
from uniswap_universal_router_decoder.decoder import Decoder
import uniswap_universal_router_decoder.mcp_server as mcp_server


TOKEN_IN = "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2"
TOKEN_OUT = "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48"

EXPECTED_TOOLS = {
    "decode_calldata",
    "decode_error",
    "decode_transaction",
    "decode_v3_path",
    "describe_command",
    "encode_calldata",
    "encode_v3_path",
    "list_commands",
}


def _calldata() -> str:
    return (
        RouterCodec()
        .encode()
        .v3_swap_exact_in(FunctionRecipient.SENDER, 1000, 0, [TOKEN_IN, 3000, TOKEN_OUT])
        .build(deadline=1234)
    )


def _fake_transaction(calldata: str) -> Callable[[Decoder, str], dict[str, Any]]:
    decoded_input = RouterCodec().decode.function_input(calldata)

    def fake_transaction(self: Decoder, trx_hash: str) -> dict[str, Any]:
        return {"hash": b"\x00\x01", "input": calldata, "decoded_input": decoded_input}

    return fake_transaction


def test_build_server_requires_mcp_extra(monkeypatch):
    # Simulate the optional 'mcp' extra not being installed.
    monkeypatch.setitem(sys.modules, "mcp.server.mcpserver", None)

    with pytest.raises(SystemExit) as excinfo:
        mcp_server.build_server()

    assert "mcp" in str(excinfo.value)


def test_decode_calldata():
    result = mcp_server.decode_calldata(_calldata())

    assert result["function"] == "execute"
    assert result["params"]["deadline"] == 1234
    assert result["params"]["inputs"][0]["command"] == "V3_SWAP_EXACT_IN"


def test_decode_calldata_reports_error():
    result = mcp_server.decode_calldata("0xdeadbeef")

    assert set(result) == {"error"}
    assert result["error"]["message"]


def test_encode_calldata():
    plan = mcp_server.decode_calldata(_calldata())

    result = mcp_server.encode_calldata(plan)

    assert result["calldata"] == _calldata()
    assert result["deadline"] == 1234
    assert result["commands"] == ["V3_SWAP_EXACT_IN"]


def test_encode_calldata_mirrors_decode_calldata():
    plan = mcp_server.decode_calldata(_calldata())

    rebuilt = mcp_server.encode_calldata(plan)

    assert mcp_server.decode_calldata(rebuilt["calldata"]) == plan


def test_encode_calldata_reports_error():
    # V4_SWAP is a structured command: its decoded form cannot be rebuilt
    plan = {"function": "execute", "params": {"inputs": [{"command": "V4_SWAP", "params": {}}]}}

    result = mcp_server.encode_calldata(plan)

    assert result["error"]["type"] == "ValueError"


def test_encode_calldata_reports_malformed_plan():
    result = mcp_server.encode_calldata({"function": "execute", "params": {"inputs": ["not-a-command"]}})

    assert set(result) == {"error"}


def test_decode_error():
    assert mcp_server.decode_error("0x5d1d0f9f") == {"name": "OnlyMintAllowed()", "args": {}}


def test_decode_error_reports_unexpected_failure(monkeypatch):
    # contract_error() swallows decoding errors, so the defensive branch is reached
    # when the codec itself fails, not when the error data cannot be decoded.
    def boom(*args: Any, **kwargs: Any) -> None:
        raise RuntimeError("boom")

    monkeypatch.setattr(mcp_server, "RouterCodec", boom)

    assert mcp_server.decode_error("0x5d1d0f9f") == {"error": {"type": "RuntimeError", "message": "boom"}}


def test_decode_v3_path():
    path = RouterCodec().encode.v3_path("V3_SWAP_EXACT_IN", [TOKEN_IN, 3000, TOKEN_OUT])

    result = mcp_server.decode_v3_path("V3_SWAP_EXACT_IN", "0x" + path.hex())

    assert result == {"fn_name": "V3_SWAP_EXACT_IN", "path": [TOKEN_IN, 3000, TOKEN_OUT]}


def test_decode_v3_path_reports_error():
    result = mcp_server.decode_v3_path("NOT_A_FN", "0x" + "00" * 20)

    assert result["error"]["type"] == "ValueError"


def test_encode_v3_path():
    result = mcp_server.encode_v3_path("V3_SWAP_EXACT_IN", [TOKEN_IN, 3000, TOKEN_OUT])

    expected = RouterCodec().encode.v3_path("V3_SWAP_EXACT_IN", [TOKEN_IN, 3000, TOKEN_OUT])
    assert result == {"fn_name": "V3_SWAP_EXACT_IN", "path": "0x" + expected.hex()}


def test_encode_v3_path_accepts_string_fees():
    result = mcp_server.encode_v3_path("V3_SWAP_EXACT_IN", [TOKEN_IN, "3000", TOKEN_OUT])

    expected = RouterCodec().encode.v3_path("V3_SWAP_EXACT_IN", [TOKEN_IN, 3000, TOKEN_OUT])
    assert result["path"] == "0x" + expected.hex()


def test_encode_v3_path_mirrors_decode_v3_path():
    encoded = mcp_server.encode_v3_path("V3_SWAP_EXACT_OUT", [TOKEN_IN, 3000, TOKEN_OUT])

    assert mcp_server.decode_v3_path("V3_SWAP_EXACT_OUT", encoded["path"]) == {
        "fn_name": "V3_SWAP_EXACT_OUT",
        "path": [TOKEN_IN, 3000, TOKEN_OUT],
    }


def test_encode_v3_path_reports_error():
    result = mcp_server.encode_v3_path("V3_SWAP_EXACT_IN", [TOKEN_IN])

    assert result["error"]["type"] == "ValueError"


def test_list_commands():
    result = mcp_server.list_commands()

    assert result["format"]["function"]["default"] == "execute"
    assert {spec["command"] for spec in result["commands"]} >= {"V3_SWAP_EXACT_IN", "WRAP_ETH"}


def test_describe_command():
    result = mcp_server.describe_command("WRAP_ETH")

    assert result["command"] == "WRAP_ETH"
    assert {param["name"] for param in result["params"]} == {"recipient", "amountMin"}


def test_describe_command_unknown():
    result = mcp_server.describe_command("nope")

    assert result["error"]["type"] == "ValueError"
    assert "Unknown command 'nope'" in result["error"]["message"]


def test_decode_transaction_with_rpc_url(monkeypatch):
    calldata = _calldata()
    monkeypatch.setattr(Decoder, "transaction", _fake_transaction(calldata))

    result = mcp_server.decode_transaction("0x" + "00" * 32, rpc_url="http://localhost:8545")

    assert result["hash"] == "0x0001"
    assert result["decoded_input"]["function"] == "execute"


def test_decode_transaction_with_env_rpc(monkeypatch):
    monkeypatch.setenv("RPC_URL", "http://localhost:8545")
    monkeypatch.delenv("ETH_RPC_URL", raising=False)
    monkeypatch.setattr(Decoder, "transaction", _fake_transaction(_calldata()))

    result = mcp_server.decode_transaction("0x" + "00" * 32)

    assert result["decoded_input"]["function"] == "execute"


def test_decode_transaction_without_rpc(monkeypatch):
    monkeypatch.delenv("RPC_URL", raising=False)
    monkeypatch.delenv("ETH_RPC_URL", raising=False)

    result = mcp_server.decode_transaction("0x" + "00" * 32)

    assert result["error"]["type"] == "ValueError"


def test_decode_transaction_reports_rpc_error(monkeypatch):
    def boom(self: Decoder, trx_hash: str) -> dict[str, Any]:
        raise RuntimeError("rpc down")

    monkeypatch.setattr(Decoder, "transaction", boom)

    result = mcp_server.decode_transaction("0x" + "00" * 32, rpc_url="http://localhost:8545")

    assert result["error"] == {"type": "RuntimeError", "message": "rpc down"}


def test_every_tool_has_a_title():
    assert {tool_function.__name__ for tool_function in mcp_server._TOOL_FUNCTIONS} == set(mcp_server._TOOL_TITLES)


def test_registered_tools_with_mcp_sdk():
    pytest.importorskip("mcp.server.mcpserver")

    server = mcp_server.build_server()
    tools = asyncio.run(server.list_tools())

    assert {tool.name for tool in tools} == EXPECTED_TOOLS

    # every tool is read-only; only decode_transaction reaches an external entity
    annotations = {tool.name: tool.annotations for tool in tools}
    assert all(annotation is not None and annotation.read_only_hint is True for annotation in annotations.values())
    assert annotations["decode_transaction"] is not None
    assert annotations["decode_transaction"].open_world_hint is True
    assert annotations["decode_calldata"] is not None
    assert annotations["decode_calldata"].open_world_hint is False

    # every tool carries a human-readable title for the host UI
    assert all(tool.title for tool in tools)
    assert {tool.name: tool.title for tool in tools}["encode_calldata"] == "Build calldata"

    result = asyncio.run(server.call_tool("describe_command", {"command": "WRAP_ETH"}))
    assert "WRAP_ETH" in result.content[0].text

    result = asyncio.run(
        server.call_tool("encode_v3_path", {"fn_name": "V3_SWAP_EXACT_IN", "path": [TOKEN_IN, 3000, TOKEN_OUT]})
    )
    assert "0x" in result.content[0].text

    result = asyncio.run(server.call_tool("encode_calldata", {"plan": mcp_server.decode_calldata(_calldata())}))
    assert "0x" in result.content[0].text


def test_package_version_fallback(monkeypatch):
    def raise_not_found(name: str) -> str:
        raise mcp_server.metadata.PackageNotFoundError(name)

    monkeypatch.setattr(mcp_server.metadata, "version", raise_not_found)

    assert mcp_server._package_version() == "unknown"


def test_main_runs_server(monkeypatch):
    transports: list[str] = []

    class FakeServer:
        def run(self, transport: str = "stdio") -> None:
            transports.append(transport)

    monkeypatch.setattr(mcp_server, "build_server", lambda: FakeServer())

    mcp_server.main()

    assert transports == ["stdio"]


def test_python_m_entry_point(monkeypatch):
    mcp_module = pytest.importorskip("mcp.server.mcpserver")
    transports: list[str] = []

    def fake_run(self: Any, transport: str = "stdio", **kwargs: Any) -> None:
        transports.append(transport)

    monkeypatch.setattr(mcp_module.MCPServer, "run", fake_run)

    runpy.run_path(str(mcp_server.__file__), run_name="__main__")

    assert transports == ["stdio"]
