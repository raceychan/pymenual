import argparse
import typing as ty
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Union
from uuid import uuid4

import click


def uuid_factory() -> str:
    return str(uuid4())


ACTION_TYPE = ty.Literal["store", "append", "count"]


@dataclass
class Parameter:
    name: str
    input_type: type = str
    help: str = ""
    default: Any = None
    required: bool = False
    choices: Optional[ty.Sequence[Any]] = None
    action: str = ""  # TODO: ACTION_TYPE
    nargs: Union[int, str, None] = None
    metavar: str = ""
    multiple: bool = False
    is_option: bool = False
    value: Union[Any, ty.Sequence[Any]] = None
    option_strings: ty.Sequence[str] = field(default_factory=lambda: [""])

    @classmethod
    def from_action(cls, action: argparse.Action) -> "Parameter":
        multiple = (
            action.nargs in ("*", "+")
            or isinstance(action.nargs, int)
            and action.nargs > 1
        )
        return cls(
            name=action.dest,
            input_type=action.type or str,
            help=action.help or "",
            default=action.default,
            required=action.required,
            choices=action.choices,
            action=action.__class__.__name__,
            nargs=action.nargs,
            metavar=action.metavar,
            multiple=multiple,
            is_option=bool(action.option_strings),
            option_strings=action.option_strings,
        )

    @classmethod
    def from_param(cls, param: click.core.Parameter) -> "Parameter":
        multiple = (
            param.multiple or isinstance(param, click.Option) and param.nargs != 1
        )
        input_type = param.type or str
        if isinstance(param.type, click.Choice):
            input_type = str
            choices = list(param.type.choices)
        else:
            choices = None

        return cls(
            name=param.name or "",
            input_type=input_type,
            help=param.help or "",
            default=param.default,
            required=param.required,
            choices=choices,
            action=(
                "store"
                if not isinstance(param, click.Option)
                else "store_true" if param.is_flag else "store"
            ),
            nargs=param.nargs if isinstance(param, click.Option) else 1,
            metavar=param.metavar,
            multiple=multiple,
            is_option=isinstance(param, click.Option),
            option_strings=param.opts,
        )


@dataclass
class Command:
    """Represents a command or subcommand with its arguments and options."""

    name: str
    command_id: str = field(default_factory=uuid_factory)
    description: ty.Optional[str] = None
    usage: ty.Optional[str] = None
    epilog: ty.Optional[str] = None
    params: List[Parameter] = field(default_factory=list)
    subcommands: Dict[str, "Command"] = field(default_factory=dict)
    parent: Optional["Command"] = None

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
