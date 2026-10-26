"""
MCP (Model Context Protocol) server exposing the codec to AI agents.

The server has no on-chain side effect: its tools only inspect or derive Universal
Router data, they never sign or broadcast a transaction. It is a thin wrapper around
the codec and the JSON renderings already used by the command line tools, so both
surfaces stay in sync.

It targets `mcp` >= 2 (where `FastMCP` was renamed to `MCPServer`) and is exposed
through the optional `mcp` extra::

    pip install 'uniswap-universal-router-decoder[mcp]'
    ur-mcp          # speaks MCP over stdio

`mcp` is imported lazily (inside build_server) so neither this module nor the core
library ever require the extra.
"""
from __future__ import annotations

from importlib import (
    import_module,
    metadata,
)
import os
from typing import (
    Any,
    Optional,
    TYPE_CHECKING,
    Union,
)

from web3.types import HexStr

from uniswap_universal_router_decoder._command_spec import describe_command as _describe_command
from uniswap_universal_router_decoder._command_spec import (
    encode_commands,
    list_command_specs,
)
from uniswap_universal_router_decoder._serialization import (
    decoded_input_to_dict,
    to_json_primitives,
    transaction_to_dict,
)
from uniswap_universal_router_decoder.router_codec import RouterCodec


if TYPE_CHECKING:
    from mcp.server.mcpserver import MCPServer


_RPC_ENV_VARS = ("RPC_URL", "ETH_RPC_URL")

_PACKAGE_NAME = "uniswap-universal-router-decoder"

_MISSING_SDK_MESSAGE = (
    "The MCP server requires the optional 'mcp' extra (mcp >= 2). Install it with:\n"
    f"    pip install '{_PACKAGE_NAME}[mcp]'"
)

_INSTRUCTIONS = (
    "Tools to inspect, derive and discover Uniswap Universal Router data. These tools never sign or send a "
    "transaction.\n"
    "Use list_commands / describe_command to discover the decoded call format and the commands, decode_transaction "
    "(needs an RPC endpoint) or decode_calldata to see what a route does, encode_calldata to rebuild the calldata "
    "from a decoded call, and decode_error / decode_v3_path / encode_v3_path for the lower level pieces."
)


def _error(exc: Exception) -> dict[str, Any]:
    return {"error": {"type": type(exc).__name__, "message": str(exc)}}


def _resolve_rpc(rpc_url: Optional[str]) -> Optional[str]:
    if rpc_url:
        return rpc_url
    for variable in _RPC_ENV_VARS:
        value = os.environ.get(variable)
        if value:
            return value
    return None


def _package_version() -> str:
    try:
        return metadata.version(_PACKAGE_NAME)
    except metadata.PackageNotFoundError:
        return "unknown"


def decode_transaction(tx_hash: str, rpc_url: Optional[str] = None) -> dict[str, Any]:
    """
    Fetch a transaction from an RPC endpoint and decode the Universal Router call it contains.

    :param tx_hash: the hash of the transaction sent to the Universal Router
    :param rpc_url: the RPC endpoint to use, overriding $RPC_URL / $ETH_RPC_URL
    :return: the transaction fields plus a structured "decoded_input", or an "error"
    """
    endpoint = _resolve_rpc(rpc_url)
    if endpoint is None:
        return _error(ValueError("No RPC endpoint: pass rpc_url or set RPC_URL / ETH_RPC_URL."))
    try:
        trx = RouterCodec(rpc_endpoint=endpoint).decode.transaction(HexStr(tx_hash))
    except Exception as exc:
        return _error(exc)
    return transaction_to_dict(trx)


def decode_calldata(calldata: str) -> dict[str, Any]:
    """
    Decode raw Universal Router calldata (no RPC endpoint needed).

    :param calldata: the "0x"-prefixed calldata of a transaction sent to the Universal Router
    :return: {"function": <name>, "params": ...} or an "error"
    """
    try:
        decoded = RouterCodec().decode.function_input(HexStr(calldata))
    except Exception as exc:
        return _error(exc)
    return decoded_input_to_dict(decoded)


def encode_calldata(plan: dict[str, Any]) -> dict[str, Any]:
    """
    Build the Universal Router calldata of an "execute" call from its decoded form.

    The mirror of decode_calldata(): where the decoder turns calldata into commands, this turns the decoded
    commands back into calldata, so a route can be decoded, edited and rebuilt. The expected shape is the one
    returned by decode_calldata() / decode_transaction() (see list_commands for the format). A command whose
    decoded form cannot be encoded (the structured commands, or a parameter whose type does not match the command)
    returns an "error".

    :param plan: the decoded call to rebuild, as returned by decode_calldata() / decode_transaction()
    :return: {"calldata": ..., "deadline": ..., "commands": [...]} or an "error"
    """
    try:
        calldata = encode_commands(RouterCodec(), plan)
        params = plan["params"]
        commands = [entry["command"] for entry in params["inputs"]]
        deadline = params.get("deadline")
    except Exception as exc:
        return _error(exc)
    return {"calldata": calldata, "deadline": deadline, "commands": commands}


def decode_error(error_data: str) -> dict[str, Any]:
    """
    Decode a Uniswap Universal Router / Permit2 / V4 custom error.

    :param error_data: the "0x"-prefixed error data, ex: "0x5d1d0f9f"
    :return: {"name": <signature>, "args": ...} or an "error"
    """
    try:
        name, params = RouterCodec().decode.contract_error(error_data)
    except Exception as exc:
        return _error(exc)
    return {"name": name, "args": to_json_primitives(params)}


def decode_v3_path(fn_name: str, path: str) -> dict[str, Any]:
    """
    Decode a V3 router path into the ordered tokens and pool fees.

    :param fn_name: "V3_SWAP_EXACT_IN" or "V3_SWAP_EXACT_OUT"
    :param path: the "0x"-prefixed encoded V3 path
    :return: {"fn_name": ..., "path": [<token>, <fee>, <token>, ...]} or an "error"
    """
    try:
        decoded = RouterCodec().decode.v3_path(fn_name, path)
    except Exception as exc:
        return _error(exc)
    return {"fn_name": fn_name, "path": to_json_primitives(decoded)}


def encode_v3_path(fn_name: str, path: list[Union[int, str]]) -> dict[str, Any]:
    """
    Encode a V3 swap path from its ordered tokens and the pool fees between them.

    The mirror of decode_v3_path(): where the decoder turns a packed path into tokens and fees, this turns tokens
    and fees into the packed path to use as the "path" parameter of a V3 swap command.

    :param fn_name: "V3_SWAP_EXACT_IN" or "V3_SWAP_EXACT_OUT" (which reverses the path)
    :param path: the tokens with the pool fee between each pair, ex: ["0x...", 3000, "0x...", 500, "0x..."]
    :return: {"fn_name": ..., "path": <the "0x"-prefixed packed path>} or an "error"
    """
    try:
        encoded = RouterCodec().encode.v3_path(fn_name, path)
    except Exception as exc:
        return _error(exc)
    return {"fn_name": fn_name, "path": "0x" + encoded.hex()}


def list_commands() -> dict[str, Any]:
    """
    Describe the decoded call format and every Universal Router command.

    :return: {"format": <the envelope>, "commands": [<command description>, ...]}
    """
    return list_command_specs()


def describe_command(command: str) -> dict[str, Any]:
    """
    Describe one Universal Router command: its parameters, their types and, where the type is not enough, their
    meaning.

    :param command: the command name, as it appears in a decoded call (ex: V3_SWAP_EXACT_IN, decreaseLiquidity)
    :return: {"command": ..., "params": [...]} or an "error"
    """
    try:
        return _describe_command(command)
    except ValueError as exc:
        return _error(exc)


_TOOL_FUNCTIONS = (
    decode_transaction,
    decode_calldata,
    encode_calldata,
    decode_error,
    decode_v3_path,
    encode_v3_path,
    list_commands,
    describe_command,
)


def _mcp_server_class() -> type[MCPServer[Any]]:
    try:
        module = import_module("mcp.server.mcpserver")
    except ImportError as exc:
        raise SystemExit(_MISSING_SDK_MESSAGE) from exc
    return getattr(module, "MCPServer")


def build_server() -> MCPServer[Any]:
    """
    Build the MCP server with every tool registered.

    :return: a configured `mcp.server.mcpserver.MCPServer` instance
    """
    server_class = _mcp_server_class()
    server = server_class(
        name=_PACKAGE_NAME,
        instructions=_INSTRUCTIONS,
        version=_package_version(),
    )
    for tool_function in _TOOL_FUNCTIONS:
        server.add_tool(tool_function)
    return server


def main() -> None:
    """Run the MCP server over stdio (the `ur-mcp` entry point)."""
    server = build_server()
    server.run(transport="stdio")


if __name__ == "__main__":
    main()
