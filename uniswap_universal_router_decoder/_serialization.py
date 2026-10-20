"""
JSON-friendly renderings of the Universal Router decoder output.

The decoder returns rich Python objects (web3 contract functions, raw bytes,
checksummed addresses, ...) that are not directly serialisable. The helpers in
this module flatten that output into plain dicts/lists/strings so it can be
printed as JSON or returned from a tool call (for example an MCP server).
"""
from __future__ import annotations

from typing import (
    Any,
    cast,
    Sequence,
)

from uniswap_universal_router_decoder.decoder import DecodedInput


def to_json_primitives(value: Any) -> Any:
    """
    Recursively convert decoder values into JSON-serialisable primitives.

    bytes/bytearray become "0x"-prefixed hex strings, dicts and sequences are
    walked, and everything else (int, str, bool, None, ...) is returned as is.

    :param value: any value coming out of the decoder
    :return: a JSON-serialisable equivalent
    """
    if isinstance(value, (bytes, bytearray)):
        return "0x" + bytes(value).hex()
    if isinstance(value, dict):
        mapping = cast("dict[str, Any]", value)
        return {str(key): to_json_primitives(item) for key, item in mapping.items()}
    if isinstance(value, (list, tuple)):
        sequence = cast("Sequence[Any]", value)
        return [to_json_primitives(item) for item in sequence]
    return value


def _function_name(value: Any) -> str:
    return getattr(value, "fn_name", str(value))


def _to_jsonable(value: Any) -> Any:
    """
    Recursively convert decoder values into JSON-serialisable structures.

    Same as to_json_primitives(), but also aware of decoded commands: a decoded command is a tuple
    whose first element is a web3 contract function, and it is rendered as
    {"command": <name>, "params": <structured params>, "revert_on_fail": <bool>}.

    :param value: any value coming out of the decoder
    :return: a JSON-serialisable equivalent
    """
    if isinstance(value, dict):
        mapping = cast("dict[str, Any]", value)
        return {str(key): _to_jsonable(item) for key, item in mapping.items()}
    if isinstance(value, (list, tuple)):
        sequence = cast("Sequence[Any]", value)
        if sequence and hasattr(sequence[0], "fn_name"):
            entry: dict[str, Any] = {
                "command": _function_name(sequence[0]),
                "params": _to_jsonable(sequence[1]),
            }
            if len(sequence) == 3 and isinstance(sequence[2], dict):
                metadata = cast("dict[str, Any]", sequence[2])
                entry["revert_on_fail"] = bool(metadata.get("revert_on_fail", True))
            return entry
        return [_to_jsonable(item) for item in sequence]
    return to_json_primitives(value)


def decoded_input_to_dict(decoded_input: DecodedInput) -> dict[str, Any]:
    """
    Render a `(function, params)` decoder result as a JSON-friendly dict.

    :param decoded_input: the tuple returned by Decoder.function_input()
    :return: {"function": <name>, "params": <structured params>}
    """
    function, params = decoded_input
    return {"function": _function_name(function), "params": _to_jsonable(params)}


def transaction_to_dict(trx: dict[str, Any]) -> dict[str, Any]:
    """
    Render the dict returned by Decoder.transaction() as a JSON-friendly dict.

    :param trx: the dict returned by Decoder.transaction()
    :return: the same dict, JSON-friendly, with a structured "decoded_input"
    """
    result = {str(key): to_json_primitives(value) for key, value in trx.items() if key != "decoded_input"}
    result["decoded_input"] = decoded_input_to_dict(trx["decoded_input"])
    return result
