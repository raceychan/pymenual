"""
a class that translates commands from argparse or cli or typer into our own commands
"""

"""
def introspect_click_app(app: BaseCommand) -> dict[CommandName, CommandSchema]:
    '''
    Introspect a Click application and build a data structure containing
    information about all commands, options, arguments, and subcommands,
    including the docstrings and command function references.

    This function recursively processes each command and its subcommands
    (if any), creating a nested dictionary that includes details about
    options, arguments, and subcommands, as well as the docstrings and
    command function references.

    Args:
        app (click.BaseCommand): The Click application's top-level group or command instance.

    Returns:
        Dict[str, CommandData]: A nested dictionary containing the Click application's
        structure. The structure is defined by the CommandData TypedDict and its related
        TypedDicts (OptionData and ArgumentData).
    '''

    def process_command(
        cmd_name: CommandName, cmd_obj: click.Command, parent=None
    ) -> CommandSchema:
        cmd_data = CommandSchema(
            name=cmd_name,
            docstring=cmd_obj.help,
            function=cmd_obj.callback,
            options=[],
            arguments=[],
            subcommands={},
            parent=parent,
            is_group=isinstance(cmd_obj, click.Group),
        )

        for param in cmd_obj.params:
            default = MultiValueParamData.process_cli_option(param.default)
            if isinstance(param, (click.Option, click.core.Group)):
                option_data = OptionSchema(
                    name=param.opts,
                    type=param.type,
                    is_flag=param.is_flag,
                    is_boolean_flag=param.is_bool_flag,
                    flag_value=param.flag_value,
                    counting=param.count,
                    opts=param.opts,
                    secondary_opts=param.secondary_opts,
                    required=param.required,
                    default=default,
                    help=param.help,
                    multiple=param.multiple,
                    nargs=param.nargs,
                )
                if isinstance(param.type, click.Choice):
                    option_data.choices = param.type.choices
                cmd_data.options.append(option_data)
            elif isinstance(param, click.Argument):
                argument_data = ArgumentSchema(
                    name=param.name,
                    type=param.type,
                    required=param.required,
                    multiple=param.multiple,
                    default=default,
                    nargs=param.nargs,
                )
                if isinstance(param.type, click.Choice):
                    argument_data.choices = param.type.choices
                cmd_data.arguments.append(argument_data)

        if isinstance(cmd_obj, click.core.Group):
            for subcmd_name, subcmd_obj in cmd_obj.commands.items():
                cmd_data.subcommands[CommandName(subcmd_name)] = process_command(
                    CommandName(subcmd_name), subcmd_obj, parent=cmd_data
                )

        return cmd_data

    data: dict[CommandName, CommandSchema] = {}

    # Special case for the root group
    if isinstance(app, click.Group):
        root_cmd_name = CommandName("root")
        data[root_cmd_name] = process_command(root_cmd_name, app)
        app = data[root_cmd_name]

    if isinstance(app, click.Group):
        for cmd_name, cmd_obj in app.commands.items():
            data[CommandName(cmd_name)] = process_command(
                CommandName(cmd_name), cmd_obj
            )
    elif isinstance(app, click.Command):
        cmd_name = CommandName(app.name)
        data[cmd_name] = process_command(cmd_name, app)

    return data

"""
import argparse
from functools import singledispatch


class CLI:
    options: ...
    arguments: ...


    @classmethod
    @singledispatch
    def from_inspect(cls, cli: object):
        ...

    


def cvt_argparser(parser: argparse.ArgumentParser): ...


