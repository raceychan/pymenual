import argparse

from pymenual.command import (
    Command,
    Const,
    ConstPayload,
    Option,
    Parameter,
    ParamTrait,
    Payload,
)


def test_build_from_argparse():
    # Create an argparse parser
    parser = argparse.ArgumentParser(prog="myapp", description="A sample app")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose output")
    parser.add_argument("input_file", help="Input file to process")

    # Build universal classes
    cmd = Command(name="myapp", description="A sample app")
    cmd.params = [
        Option(
            name="verbose",
            input_type=bool,
            trait=ConstPayload(True),
            help="Enable verbose output",
        ),
        Option(
            name="input_file",
            help="Input file to process",
            required=True,
            input_type=str,
            trait=ParamTrait(),
        ),
    ]

    # Assert the structure
    assert cmd.name == "myapp"
    assert cmd.description == "A sample app"
    assert len(cmd.params) == 2
    assert isinstance(cmd.params[0], Option)
    assert isinstance(cmd.params[1], Option)
    assert cmd.params[0].name == "verbose"
    assert cmd.params[1].name == "input_file"


def test_reconstruct_argparse():
    # Create universal classes
    cmd = Command(name="myapp", description="A sample app")
    cmd.params = [
        Option(
            name="verbose",
            input_type=bool,
            trait=ConstPayload(True),
            help="Enable verbose output",
        ),
        Option(
            name="input_file",
            input_type=str,
            trait=Payload(),
            help="Input file to process",
            required=True,
        ),
    ]

    # Reconstruct argparse parser
    parser = argparse.ArgumentParser(prog=cmd.name, description=cmd.description)
    for arg in cmd.params:
        arg.to_action()

    # Assert the reconstruction
    actions = parser._actions[1:]  # Exclude the default help action
    assert len(actions) == 2
    assert actions[0].dest == "verbose"
    assert actions[1].dest == "input_file"


def test_store_action():
    cmd = Command(
        name="test",
        params=[
            Option(
                input_type=int, help="A simple store action", option_strings=["--foo"]
            )
        ],
    )

    assert len(cmd.params) == 1
    assert isinstance(cmd.params[0], Option)
    assert cmd.params[0].option_strings == ["--foo"]
    assert cmd.params[0].input_type == int


def test_store_true_action():
    cmd = Command(
        name="test",
        params=[
            Option(
                input_type=bool,
                trait=ConstPayload(True),
                help="Enable verbose output",
                option_strings=["--verbose"],
            )
        ],
    )

    assert len(cmd.params) == 1
    assert isinstance(cmd.params[0], Option)
    assert cmd.params[0].option_strings == ["--verbose"]
    assert isinstance(cmd.params[0].trait, ConstPayload)


def test_store_const_action():
    cmd = Command(
        name="test",
        params=[
            Option(
                input_type=str,
                trait=ConstPayload("advanced"),
                help="Set mode",
                option_strings=["--mode"],
            )
        ],
    )

    assert len(cmd.params) == 1
    assert isinstance(cmd.params[0], Option)
    assert cmd.params[0].option_strings == ["--mode"]
    assert isinstance(cmd.params[0].trait, ConstPayload)
    assert cmd.params[0].trait.value == "advanced"


def test_append_action():
    parser = argparse.ArgumentParser()
    parser.add_argument("--item", action="append", help="Add items")

    cmd = Command(
        name="test",
        params=[
            Parameter(
                name="item",
                action="append",
                help="Add items",
                is_option=True,
                multiple=True,
            )
        ],
    )

    assert len(cmd.params) == 1
    assert cmd.params[0].name == "item"
    assert cmd.params[0].action == "append"
    assert cmd.params[0].multiple == True


def test_count_action():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-v", "--verbose", action="count", default=0, help="Increase verbosity"
    )

    cmd = Command(
        name="test",
        params=[
            Parameter(
                name="verbose",
                action="count",
                default=0,
                help="Increase verbosity",
                is_option=True,
            )
        ],
    )

    assert len(cmd.params) == 1
    assert cmd.params[0].name == "verbose"
    assert cmd.params[0].action == "count"
    assert cmd.params[0].default == 0


def test_reconstruct_store_action():
    cmd = Command(name="test")
    cmd.params = [
        Parameter(
            name="foo", input_type=int, help="A simple store action", is_option=True
        )
    ]

    parser = argparse.ArgumentParser()
    for param in cmd.params:
        if param.is_option:
            parser.add_argument(
                f"--{param.name}", type=param.input_type, help=param.help
            )
        else:
            parser.add_argument(param.name, type=param.input_type, help=param.help)

    actions = parser._actions[1:]  # Exclude the default help action
    assert len(actions) == 1
    store_action = actions[0]
    assert store_action.dest == "foo"
    assert store_action.type == int
    assert store_action.help == "A simple store action"
    assert type(store_action) is argparse._StoreAction


def test_reconstruct_store_true_action():
    cmd = Command(name="test")
    cmd.params = [
        Parameter(
            name="verbose",
            action="store_true",
            help="Enable verbose output",
            is_option=True,
        )
    ]

    parser = argparse.ArgumentParser()
    for param in cmd.params:
        if param.is_option:
            parser.add_argument(f"--{param.name}", action=param.action, help=param.help)
        else:
            parser.add_argument(param.name, action=param.action, help=param.help)

    actions = parser._actions[1:]  # Exclude the default help action
    assert len(actions) == 1
    assert actions[0].dest == "verbose"
    assert type(actions[0]) == argparse._StoreTrueAction
    assert actions[0].help == "Enable verbose output"


def test_reconstruct_store_const_action():
    cmd = Command(name="test")
    cmd.params = [
        Parameter(
            name="mode",
            action="store_const",
            default="simple",
            help="Set mode",
            is_option=True,
        )
    ]

    parser = argparse.ArgumentParser()
    for param in cmd.params:
        if param.is_option:
            parser.add_argument(
                f"--{param.name}",
                action=param.action,
                const="advanced",
                default=param.default,
                help=param.help,
            )
        else:
            parser.add_argument(
                param.name,
                action=param.action,
                const="advanced",
                default=param.default,
                help=param.help,
            )

    actions = parser._actions[1:]  # Exclude the default help action
    assert len(actions) == 1
    assert actions[0].dest == "mode"
    assert type(actions[0]) == argparse._StoreConstAction
    assert actions[0].const == "advanced"
    assert actions[0].default == "simple"


def test_reconstruct_append_action():
    cmd = Command(name="test")
    cmd.params = [
        Parameter(
            name="item",
            action="append",
            help="Add items",
            is_option=True,
            multiple=True,
        )
    ]

    parser = argparse.ArgumentParser()
    for param in cmd.params:
        if param.is_option:
            parser.add_argument(f"--{param.name}", action=param.action, help=param.help)
        else:
            parser.add_argument(param.name, action=param.action, help=param.help)

    actions = parser._actions[1:]  # Exclude the default help action
    assert len(actions) == 1
    assert actions[0].dest == "item"
    assert type(actions[0]) == argparse._AppendAction


def test_reconstruct_count_action():
    cmd = Command(name="test")
    cmd.params = [
        Parameter(
            name="verbose",
            action="count",
            default=0,
            help="Increase verbosity",
            is_option=True,
        )
    ]

    parser = argparse.ArgumentParser()
    for param in cmd.params:
        if param.is_option:
            parser.add_argument(
                f"-{param.name[0]}",
                f"--{param.name}",
                action=param.action,
                default=param.default,
                help=param.help,
            )
        else:
            parser.add_argument(
                param.name, action=param.action, default=param.default, help=param.help
            )

    actions = parser._actions[1:]  # Exclude the default help action
    assert len(actions) == 1
    assert actions[0].dest == "verbose"
    assert type(actions[0]) is argparse._CountAction
    assert actions[0].default == 0


# def test_click_equivalent_store():
#     @click.command()
#     @click.option('--foo', type=int, help='A simple store action')
#     def cli(foo):
#         pass

#     cmd = Command(name='cli')
#     cmd.arguments = [
#         Argument(name='foo', type=int, help='A simple store action', is_option=True)
#     ]

#     assert len(cmd.arguments) == 1
#     assert cmd.arguments[0].name == 'foo'
#     assert cmd.arguments[0].type == int

# def test_click_equivalent_store_true():
#     @click.command()
#     @click.option('--verbose', is_flag=True, help='Enable verbose output')
#     def cli(verbose):
#         pass

#     cmd = Command(name='cli')
#     cmd.arguments = [
#         Argument(name='verbose', action='store_true', help='Enable verbose output', is_option=True)
#     ]

#     assert len(cmd.arguments) == 1
#     assert cmd.arguments[0].name == 'verbose'
#     assert cmd.arguments[0].action == 'store_true'

# def test_click_equivalent_store_const():
#     @click.command()
#     @click.option('--mode', type=click.Choice(['simple', 'advanced']), default='simple', help='Set mode')
#     def cli(mode):
#         pass

#     cmd = Command(name='cli')
#     cmd.arguments = [
#         Argument(name='mode', type=str, choices=['simple', 'advanced'], default='simple', help='Set mode', is_option=True)
#     ]

#     assert len(cmd.arguments) == 1
#     assert cmd.arguments[0].name == 'mode'
#     assert cmd.arguments[0].choices == ['simple', 'advanced']
#     assert cmd.arguments[0].default == 'simple'

# def test_click_equivalent_append():
#     @click.command()
#     @click.option('--item', multiple=True, help='Add items')
#     def cli(item):
#         pass

#     cmd = Command(name='cli')
#     cmd.arguments = [
#         Argument(name='item', multiple=True, help='Add items', is_option=True)
#     ]

#     assert len(cmd.arguments) == 1
#     assert cmd.arguments[0].name == 'item'
#     assert cmd.arguments[0].multiple == True

# def test_click_equivalent_count():
#     @click.command()
#     @click.option('-v', '--verbose', count=True, help='Increase verbosity')
#     def cli(verbose):
#         pass

#     cmd = Command(name='cli')
#     cmd.arguments = [
#         Argument(name='verbose', action='count', help='Increase verbosity', is_option=True)
#     ]

#     assert len(cmd.arguments) == 1
#     assert cmd.arguments[0].name == 'verbose'
#     assert cmd.arguments[0].action == 'count'
