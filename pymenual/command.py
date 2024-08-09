import argparse
import typing as ty
from dataclasses import dataclass, field
from functools import singledispatch
from uuid import uuid4

import click

# command -> function
# argument -> positional arguments
# option -> keyword arguments


def uuid_factory() -> str:
    return str(uuid4())


class _Missing: ...


MISSING = _Missing()
ValueType = ty.TypeVar("ValueType")
SizeMark = ty.Literal["AT_MOST_ONE", "AT_LEAST_ONE", "ANY"]


# ====
@dataclass
class Const(ty.Generic[ValueType]):
    value: ValueType


@dataclass
class ParamTrait(ty.Generic[ValueType]): ...


@dataclass
class Payload(ParamTrait[ValueType]):
    value: ty.Union[ValueType, _Missing] = MISSING


@dataclass
class ConstPayload(Payload[ValueType], Const): ...


@dataclass
class MultiPayload(ParamTrait[ValueType]):
    size: ty.Union[SizeMark, int]
    value: list[ValueType] = field(default_factory=list)

    @classmethod
    def size_cvt(cls, narg: ty.Union[str, int]) -> ty.Union[SizeMark, int]:
        narg_map: dict[str, SizeMark] = {
            "?": "AT_MOST_ONE",
            "+": "AT_LEAST_ONE",
            "*": "ANY",
        }
        if isinstance(narg, str):
            return narg_map[narg]

        if narg == -1:
            return "ANY"

        return narg


@dataclass
class MultiConst(MultiPayload[ValueType], Const): ...


@dataclass
class Count(ParamTrait[ValueType]):
    value: int


@dataclass
class Parameter(ty.Generic[ValueType]):
    input_type: object
    trait: ParamTrait[ty.Any] = field(default_factory=Payload)
    help: str = ""
    alias: ty.Union[str, ty.Sequence[str], None] = ""
    nargs: ty.Union[int, str, None] = None
    choices: ty.Union[ty.Iterable[ValueType], _Missing] = MISSING
    required: bool = False
    hidden: bool = False

    def __post_init__(self): ...

    @classmethod
    @singledispatch
    def from_param(cls, param: click.core.Parameter) -> "Parameter":
        if param.multiple:
            trait = MultiPayload(size=MultiPayload.size_cvt(param.nargs))
        else:
            trait = ParamTrait()
        if isinstance(param.type, click.Choice):
            input_type = str
            choices = list(param.type.choices)
        else:
            type_map: dict[click.types.ParamType, type] = {
                click.types.INT: int,
                click.types.FLOAT: float,
                click.types.BOOL: bool,
            }
            input_type = type_map.get(param.type, param.type)
            choices = MISSING

        return cls(
            input_type=input_type,
            trait=trait,
            alias=param.opts,
            nargs=param.nargs,
            choices=choices,
            required=param.required,
        )

    @classmethod
    def from_action(cls, action: argparse.Action) -> "Parameter":
        if isinstance(action, argparse._StoreConstAction):
            trait = ConstPayload(action.const)
        elif isinstance(action, argparse._CountAction):
            trait = Count(0)
        elif action.nargs in ("+", "*", "?"):
            trait = MultiPayload(size=MultiPayload.size_cvt(action.nargs))
        else:
            trait = Payload(None)

        return cls(
            input_type=action.type or str,
            trait=trait,
            help=action.help or "",
            alias=action.option_strings,
            nargs=action.nargs,
            choices=action.choices or MISSING,
            required=action.required,
            hidden=(action.help == argparse.SUPPRESS),
        )

    def to_param(self) -> "click.core.Parameter": ...

    def to_action(self) -> argparse.Action: ...
@dataclass
class Option(Parameter[ValueType]):
    name: str = ""
    option_strings: ty.Sequence[str] = field(default_factory=lambda: [""])

    @classmethod
    # @Parameter.from_param.register
    def from_param(cls, param: click.core.Option) -> "Option":
        if param.multiple:
            trait = MultiPayload(size=MultiPayload.size_cvt(param.nargs))
        else:
            trait = ParamTrait()
        if isinstance(param.type, click.Choice):
            input_type = str
            choices = list(param.type.choices)
        else:
            type_map: dict[click.types.ParamType, type] = {
                click.types.INT: int,
                click.types.FLOAT: float,
                click.types.BOOL: bool,
            }
            input_type = type_map.get(param.type, param.type)
            choices = MISSING

        return cls(
            name=param.name or "",
            input_type=input_type,
            trait=trait,
            alias=param.opts,
            nargs=param.nargs,
            choices=choices,
            required=param.required,
        )


# ===============


@dataclass
class Command:
    """Represents a command or subcommand with its arguments and options."""

    name: str
    command_id: str = field(default_factory=uuid_factory)
    description: ty.Optional[str] = None
    usage: ty.Optional[str] = None
    epilog: ty.Optional[str] = None
    params: list[Parameter[ty.Any]] = field(default_factory=list)
    subcommands: dict[str, "Command"] = field(default_factory=dict)
    parent: ty.Optional["Command"] = None

    @classmethod
    def from_parser(cls, parser: argparse.ArgumentParser) -> "Command":
        cmd = cls(
            name=parser.prog,
            description=parser.description,
            usage=parser.usage,
            epilog=parser.epilog,
        )

        for action in parser._actions:
            if isinstance(action, argparse._SubParsersAction):
                for subparser_name, subparser in action.choices.items():
                    subcmd = cls.from_parser(subparser)
                    subcmd.parent = cmd
                    cmd.subcommands[subparser_name] = subcmd
            elif not isinstance(action, argparse._HelpAction):
                cmd.params.append(Parameter.from_action(action))

        return cmd
