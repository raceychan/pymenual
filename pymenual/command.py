from dataclasses import dataclass

"""
@dataclass
class OptionSchema:
    name: list[str]
    type: ParamType
    default: MultiValueParamData | None = None
    required: bool = False
    is_flag: bool = False
    is_boolean_flag: bool = False
    flag_value: Any = ""
    opts: list = field(default_factory=list)
    counting: bool = False
    secondary_opts: list = field(default_factory=list)
    key: str | tuple[str] = field(default_factory=generate_unique_id)
    help: str | None = None
    choices: Sequence[str] | None = None
    multiple: bool = False
    multi_value: bool = False
    nargs: int = 1

    def __post_init__(self):
        self.multi_value = isinstance(self.type, click.Tuple)


@dataclass
class ArgumentSchema:
    name: str
    type: str
    required: bool = False
    key: str = field(default_factory=generate_unique_id)
    default: MultiValueParamData | None = None
    choices: Sequence[str] | None = None
    multiple: bool = False
    nargs: int = 1


@dataclass
class CommandSchema:
    name: CommandName
    function: Callable[..., Any | None]
    key: str = field(default_factory=generate_unique_id)
    docstring: str | None = None
    options: list[OptionSchema] = field(default_factory=list)
    arguments: list[ArgumentSchema] = field(default_factory=list)
    subcommands: dict["CommandName", "CommandSchema"] = field(default_factory=dict)
    parent: "CommandSchema | None" = None
    is_group: bool = False

    @property
    def path_from_root(self) -> list["CommandSchema"]:
        node = self
        path = [self]
        while True:
            node = node.parent
            if node is None:
                break
            path.append(node)
        return list(reversed(path))
"""

import argparse
import typing as ty
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Union
from uuid import uuid4

import click


def uuid_factory() -> str:
    return str(uuid4())


@dataclass
class Parameter:
    name: str
    input_type: type = str
    help: str = ""
    default: Any = None
    required: bool = False
    choices: Optional[List[Any]] = None
    action: str = ""
    nargs: Union[int, str] = 1
    metavar: str = ""
    multiple: bool = False
    is_option: bool = False
    value: Union[Any, list[Any]] = None

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
            nargs=action.nargs or 1,
            metavar=action.metavar,
            multiple=multiple,
            is_option=bool(action.option_strings),
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
        )


@dataclass
class Command:
    """Represents a command or subcommand with its arguments and options."""

    name: str
    command_id: str = field(default_factory=uuid_factory)
    description: str = ""
    usage: str = ""
    epilog: str = ""
    params: List[Parameter] = field(default_factory=list)
    subcommands: Dict[str, "Command"] = field(default_factory=dict)
    parent: Optional["Command"] = None

    @classmethod
    def from_parser(cls, parser: argparse.ArgumentParser) -> "Command":
        cmd = cls(
            name=parser.prog,
            description=parser.description or "",
            usage=parser.usage or "",
            epilog=parser.epilog or "",
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
