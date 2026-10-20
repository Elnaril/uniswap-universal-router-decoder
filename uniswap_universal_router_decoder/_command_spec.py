"""
Discoverable description of the UR commands the encoder can build from data.

The spec is derived by introspection from the fluent encoder methods of
`BaseChainedFunctionBuilder`, so it stays in sync with the actual API instead of
duplicating it by hand. It powers `list_command_specs()`/`describe_command()` (so
an agent or a human can discover the surface) and the `encode_commands()` helper
used by the CLI, which delegates the actual encoding to `Encoder.function_input()`.
"""
from __future__ import annotations

from dataclasses import (
    asdict,
    dataclass,
)
import inspect
from typing import (
    Any,
    Optional,
    Union,
)

from uniswap_universal_router_decoder.encoder import (
    BaseChainedFunctionBuilder,
    ENCODABLE_METHODS,
    resolve_command,
)
from uniswap_universal_router_decoder.router_codec import (
    AsyncRouterCodec,
    RouterCodec,
)


@dataclass(frozen=True)
class CommandParam:
    name: str
    type: str
    required: bool
    default: Any


@dataclass(frozen=True)
class CommandSpec:
    command: str
    params: tuple[CommandParam, ...]


def _type_name(annotation: Any) -> str:
    return getattr(annotation, "__name__", str(annotation))


def _parameters(command: str) -> dict[str, inspect.Parameter]:
    signature = inspect.signature(getattr(BaseChainedFunctionBuilder, command))
    return {name: param for name, param in signature.parameters.items() if name != "self"}


def _build_spec(command: str) -> CommandSpec:
    params = tuple(
        CommandParam(
            name=name,
            type=_type_name(param.annotation),
            required=param.default is inspect.Parameter.empty,
            default=None if param.default is inspect.Parameter.empty else param.default,
        )
        for name, param in _parameters(command).items()
    )
    return CommandSpec(command=command, params=params)


COMMAND_SPECS: dict[str, CommandSpec] = {command: _build_spec(command) for command in ENCODABLE_METHODS}


def list_command_specs() -> list[dict[str, Any]]:
    """Return the description of every encodable command."""
    return [asdict(COMMAND_SPECS[name]) for name in sorted(COMMAND_SPECS)]


def describe_command(name: str) -> dict[str, Any]:
    """
    Return the description of a single encodable command.

    :param name: the command name (builder method name or RouterFunction name)
    :return: the command description
    """
    return asdict(COMMAND_SPECS[resolve_command(name)])


def encode_commands(
        codec: Union[RouterCodec, AsyncRouterCodec],
        commands: list[dict[str, Any]],
        deadline: Optional[int] = None) -> str:
    """
    Build UR calldata from a list of declarative commands.

    Thin wrapper around Encoder.function_input()/AsyncEncoder.function_input().

    :param codec: a RouterCodec or AsyncRouterCodec instance
    :param commands: a list of {"command": <name>, "params": {<param name>: <value>}}
    :param deadline: optional unix timestamp after which the transaction is invalid
    :return: the encoded calldata, as a "0x"-prefixed hex string
    """
    return codec.encode.function_input(commands, deadline)
