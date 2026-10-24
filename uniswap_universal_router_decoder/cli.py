"""
Command line interface to encode/decode Uniswap Universal Router data.

Two entry points are installed:
* ur-decode: decode a transaction, raw calldata, a custom error or a V3 path.
* ur-encode: describe the decoded call format and the commands, build calldata from them, or encode a V3 path.

Every subcommand prints JSON to stdout, which makes the CLI easy to consume from
a shell or by an agent (and it is the same code a future MCP server would wrap).
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from typing import (
    Any,
    cast,
    Optional,
    Sequence,
)

from uniswap_universal_router_decoder._command_spec import (
    describe_command,
    encode_commands,
    list_command_specs,
)
from uniswap_universal_router_decoder._serialization import (
    decoded_input_to_dict,
    to_json_primitives,
    transaction_to_dict,
)
from uniswap_universal_router_decoder.router_codec import RouterCodec


def _dump(data: Any) -> None:
    print(json.dumps(data, indent=2))


def _error_message(exc: Exception) -> str:
    # KeyError renders its argument with quotes, and a bare key name is cryptic on its own
    if isinstance(exc, KeyError) and exc.args:
        return f"missing or invalid key: {exc.args[0]!r}"
    return str(exc)


def _make_codec(rpc: Optional[str] = None, require_rpc: bool = False) -> RouterCodec:
    rpc_url = rpc or os.environ.get("RPC_URL") or os.environ.get("ETH_RPC_URL")
    if rpc_url:
        return RouterCodec(rpc_endpoint=rpc_url)
    if require_rpc:
        raise SystemExit("An RPC endpoint is required: pass --rpc or set RPC_URL.")
    return RouterCodec()


def _build_decode_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="ur-decode", description="Decode Uniswap Universal Router data as JSON.")
    subparsers = parser.add_subparsers(dest="subcommand", required=True)

    tx_parser = subparsers.add_parser(
        "tx",
        help="Decode a transaction sent to the UR.",
        description="Fetch a transaction from an RPC endpoint and decode the Universal Router call it contains.",
    )
    tx_parser.add_argument("tx_hash", help="the hash of the transaction sent to the UR.")
    tx_parser.add_argument("--rpc", default=None, help="RPC endpoint (defaults to $RPC_URL).")

    calldata_parser = subparsers.add_parser(
        "calldata",
        help="Decode raw UR calldata.",
        description="Decode raw Universal Router calldata. No RPC endpoint is needed.",
    )
    calldata_parser.add_argument("calldata", help="the '0x'-prefixed calldata of a transaction sent to the UR.")

    error_parser = subparsers.add_parser(
        "error",
        help="Decode a UR/Permit2/V4 custom error.",
        description="Decode a Universal Router, Permit2 or V4 custom error into its name and arguments.",
    )
    error_parser.add_argument("error_data", help="the '0x'-prefixed error data, ex: 0x5d1d0f9f.")

    path_parser = subparsers.add_parser(
        "v3-path",
        help="Decode a V3 path.",
        description="Decode a V3 swap path into the ordered tokens and pool fees. No RPC endpoint is needed.",
    )
    path_parser.add_argument(
        "fn_name",
        choices=("V3_SWAP_EXACT_IN", "V3_SWAP_EXACT_OUT"),
        help="the swap function the path belongs to.",
    )
    path_parser.add_argument("path", help="the '0x'-prefixed encoded V3 path.")
    return parser


def decode_main(argv: Optional[Sequence[str]] = None) -> int:
    """
    Entry point of the ur-decode command.

    :param argv: the command line arguments (defaults to sys.argv[1:])
    :return: the process exit code
    """
    parser = _build_decode_parser()
    args = parser.parse_args(argv)
    try:
        _decode(args)
    except (KeyError, ValueError) as exc:
        parser.error(_error_message(exc))
    return 0


def _decode(args: argparse.Namespace) -> None:
    if args.subcommand == "tx":
        trx = _make_codec(args.rpc, require_rpc=True).decode.transaction(args.tx_hash)
        _dump(transaction_to_dict(trx))
    elif args.subcommand == "calldata":
        decoded = _make_codec().decode.function_input(args.calldata)
        _dump(decoded_input_to_dict(decoded))
    elif args.subcommand == "error":
        name, params = _make_codec().decode.contract_error(args.error_data)
        _dump({"error": name, "args": to_json_primitives(params)})
    elif args.subcommand == "v3-path":
        _dump(to_json_primitives(_make_codec().decode.v3_path(args.fn_name, args.path)))


def _build_encode_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="ur-encode", description="Encode Uniswap Universal Router commands.")
    subparsers = parser.add_subparsers(dest="subcommand", required=True)

    subparsers.add_parser(
        "list",
        help="Describe the decoded call format and the commands.",
        description=(
            "Print the JSON format a decoded call must follow to be rebuilt, and every Universal Router command "
            "the encoder can rebuild from it, with the parameters each one takes."
        ),
        epilog="Use 'ur-encode describe <command>' for the parameters of one command.",
    )

    describe_parser = subparsers.add_parser(
        "describe",
        help="Describe one command.",
        description=(
            "Print the parameters of a single Universal Router command: their names, their types and, where the "
            "type alone is not enough, their meaning."
        ),
        epilog="Use 'ur-encode list' for the decoded call format and the command names.",
    )
    describe_parser.add_argument(
        "command",
        help="the command name, as it appears in a decoded call (ex: V3_SWAP_EXACT_IN, WRAP_ETH, decreaseLiquidity).",
    )

    build_parser = subparsers.add_parser(
        "build",
        help="Build UR calldata from a decoded call.",
        description="Build the Universal Router calldata of an 'execute' call from its decoded form.",
        epilog="Use 'ur-encode list' for the format, and 'ur-decode calldata' to get an example of it.",
    )
    build_parser.add_argument(
        "--command",
        default=None,
        help="A single command name as decoded (ex: V3_SWAP_EXACT_IN, see 'ur-decode').",
    )
    build_parser.add_argument("--params", default=None, help="JSON object with the parameters of --command.")
    build_parser.add_argument(
        "--plan",
        default=None,
        help="JSON file (or '-' for stdin) with the decoded call to rebuild (the ur-decode output).",
    )
    build_parser.add_argument("--deadline", type=int, default=None, help="Unix timestamp deadline for the tx.")
    build_parser.add_argument("--rpc", default=None, help="RPC endpoint (defaults to $RPC_URL).")

    path_parser = subparsers.add_parser(
        "v3-path",
        help="Encode a V3 path.",
        description=(
            "Encode a V3 swap path: the tokens to swap through, with the pool fee between each pair. The result is "
            "the packed bytes to use as the 'path' parameter of a V3 swap command."
        ),
        epilog="Use 'ur-decode v3-path' for the reverse operation.",
    )
    path_parser.add_argument(
        "fn_name",
        choices=("V3_SWAP_EXACT_IN", "V3_SWAP_EXACT_OUT"),
        help="the swap function the path belongs to (V3_SWAP_EXACT_OUT reverses the path).",
    )
    path_parser.add_argument(
        "path",
        nargs="+",
        help=(
            "the tokens and the pool fees between them, either as a JSON list, or as separate arguments: "
            "<token> <fee> <token> [<fee> <token> ...]."
        ),
    )
    return parser


def _load_plan(source: str) -> Any:
    if source == "-":
        return json.load(sys.stdin)
    with open(source, "r", encoding="utf-8") as plan_file:
        return json.load(plan_file)


def _plan_from_args(args: argparse.Namespace, parser: argparse.ArgumentParser) -> dict[str, Any]:
    if args.plan:
        plan: Any = _load_plan(args.plan)
        if not isinstance(plan, dict):
            parser.error("the plan must be a JSON object holding a decoded 'execute' call")
        plan_dict = cast("dict[str, Any]", plan)
        if args.deadline is not None:
            plan_dict.setdefault("params", {})["deadline"] = args.deadline
        return plan_dict
    if args.command:
        params: dict[str, Any] = json.loads(args.params) if args.params else {}
        plan_params: dict[str, Any] = {"inputs": [{"command": args.command, "params": params}]}
        if args.deadline is not None:
            plan_params["deadline"] = args.deadline
        return {"function": "execute", "params": plan_params}
    parser.error("provide --plan or --command")


def _v3_path_sequence(values: Sequence[str]) -> list[Any]:
    """
    Read a V3 path given either as a JSON list, or as separate <token> <fee> <token> [<fee> <token> ...] arguments.

    :param values: the path elements, as given on the command line
    :return: the tokens with the pool fee between each pair
    """
    if len(values) == 1:
        loaded: Any = json.loads(values[0])
        if not isinstance(loaded, list):
            raise ValueError("the V3 path must be a JSON list of tokens and pool fees")
        return list(cast(list[Any], loaded))
    return list(values)


def encode_main(argv: Optional[Sequence[str]] = None) -> int:
    """
    Entry point of the ur-encode command.

    :param argv: the command line arguments (defaults to sys.argv[1:])
    :return: the process exit code
    """
    parser = _build_encode_parser()
    args = parser.parse_args(argv)
    try:
        _encode(args, parser)
    except (KeyError, ValueError) as exc:
        parser.error(_error_message(exc))
    return 0


def _encode(args: argparse.Namespace, parser: argparse.ArgumentParser) -> None:
    if args.subcommand == "list":
        _dump(list_command_specs())
    elif args.subcommand == "describe":
        _dump(describe_command(args.command))
    elif args.subcommand == "build":
        plan = _plan_from_args(args, parser)
        calldata = encode_commands(_make_codec(args.rpc), plan)
        inputs = cast("list[dict[str, Any]]", plan["params"]["inputs"])
        _dump({
            "calldata": calldata,
            "deadline": plan["params"].get("deadline"),
            "commands": [entry["command"] for entry in inputs],
        })
    elif args.subcommand == "v3-path":
        encoded = _make_codec().encode.v3_path(args.fn_name, _v3_path_sequence(args.path))
        _dump({"fn_name": args.fn_name, "path": "0x" + encoded.hex()})
