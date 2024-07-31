import argparse

from textual import widgets as tw

"""
Widget builder -- build widgets based on the commands provided
"""

# we need to build such mapping
# PymenualCommand : textual.Widget
# so that we can then build mapping
# from argparse.Action to  PymenualCommand
# as well as click.Command to PymenualCommand

mapping = {
    argparse._StoreConstAction: tw.Select,
    argparse._StoreAction: tw.Input,
    argparse._AppendAction: tw.Input,
    argparse._AppendConstAction: tw.Checkbox,
    argparse._CountAction: tw.Checkbox,
}
