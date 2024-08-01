import argparse

import pytest

from pymenual.command import Command


def parser_to_command(parser) -> Command:
    cmd = Command.from_parser(parser)
    return cmd


def command_to_parser(command: Command) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog=command.name,
        description=command.description,
        usage=command.usage,
        epilog=command.epilog,
    )

    get_action = lambda x: parser._registry_get("action", x)

    for param in command.params:
        kwargs = {
            "dest": param.name,
            "help": param.help,
            "default": param.default,
            "required": param.required,
            "choices": param.choices,
            "action": get_action(param.action) if param.action != "store" else None,
            "nargs": param.nargs if param.nargs != 1 else None,
            "metavar": param.metavar or None,
            "type": param.input_type if param.input_type != str else None,
        }

        if param.is_option:
            parser.add_argument(
                *param.option_strings,
                **{k: v for k, v in kwargs.items() if v is not None}
            )
        else:
            parser.add_argument(
                param.name, **{k: v for k, v in kwargs.items() if v is not None}
            )

    return parser


@pytest.fixture
def original_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-D",
        "--download",
        dest="download",
        help="Downloading articles from learcpp.com",
        action="store_true",
    )

    parser.add_argument(
        "-A",
        "--all",
        const=False,
        help="Download, convert and merge",
        action="store_const",
        default=False,
    )
    parser.add_argument("-R", "--rmcache", help="Remove cache", action="store_true")
    parser.add_argument("-S", "--showerrors", help="Show errors", action="store_true")

    parser.add_argument(
        "--max_threads",
        action="store",
        type=int,
        default=22,
        help="Store an integer value",
    )
    parser.add_argument("--count", type=int, default=33, help="Count a int")

    # append
    parser.add_argument(
        "--file", action="append", default="config.env", help="Append Action"
    )

    # append_const
    parser.add_argument(
        "--mode", action="append_const", const="read", help="Append Const Action"
    )

    # count
    parser.add_argument(
        "--verbose-level", action="count", default=15, help="Count Action"
    )

    return parser


def test_parser_to_command_to_parser(original_parser: argparse.ArgumentParser):
    # Convert parser to Command
    command = parser_to_command(original_parser)

    # Convert Command back to parser
    reconstructed_parser = command_to_parser(command)

    # Compare the two parsers
    assert original_parser.prog == reconstructed_parser.prog
    assert original_parser.description == reconstructed_parser.description
    assert original_parser.usage == reconstructed_parser.usage
    assert original_parser.epilog == reconstructed_parser.epilog

    # Compare arguments
    original_actions = {
        action.dest: action
        for action in original_parser._actions
        if not isinstance(action, argparse._HelpAction)
    }
    reconstructed_actions = {
        action.dest: action
        for action in reconstructed_parser._actions
        if not isinstance(action, argparse._HelpAction)
    }

    assert set(original_actions.keys()) == set(reconstructed_actions.keys())

    for dest, original_action in original_actions.items():
        reconstructed_action = reconstructed_actions[dest]

        assert original_action.dest == reconstructed_action.dest
        assert original_action.help == reconstructed_action.help
        assert original_action.default == reconstructed_action.default
        assert original_action.required == reconstructed_action.required
        assert original_action.type == reconstructed_action.type
        assert original_action.choices == reconstructed_action.choices
        assert original_action.option_strings == reconstructed_action.option_strings
        # Compare nargs
        assert original_action.nargs == reconstructed_action.nargs

        # Compare action
        assert type(reconstructed_action) is type(original_action)

    # Test parsing
    test_args = [
        "--download",
        "--all",
        "--rmcache",
        "--showerrors",
        "--max_threads",
        "10",
        "--count",
        "5",
        "--file",
        "file1.txt",
        "--file",
        "file2.txt",
        "--mode",
        "--verbose-level",
        "--verbose-level",
    ]

    original_parsed = original_parser.parse_args(test_args)
    reconstructed_parsed = reconstructed_parser.parse_args(test_args)

    # Compare parsed results
    for attr in vars(original_parsed):
        assert getattr(original_parsed, attr) == getattr(reconstructed_parsed, attr)

    print("All tests passed successfully!")
