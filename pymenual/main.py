import argparse
import typing as ty
from collections import defaultdict
from pathlib import Path

import rich
import rich.pretty
import textual
import textual.screen
from textual import containers as tc
from textual import events as te
from textual import widgets as tw
from textual.app import App, ComposeResult
from textual.widgets.selection_list import Selection

SelectedOptions = dict[str, ty.Any]


def split_actions(
    heter_list: list[argparse.Action],
) -> defaultdict[type[argparse.Action], list[argparse.Action]]:
    action_mapping = defaultdict(list)
    actions = (
        argparse._StoreAction,
        argparse._StoreConstAction,
        argparse._AppendAction,
        argparse._AppendConstAction,
        argparse._CountAction,
    )
    while heter_list:
        item = heter_list.pop(0)
        for action in actions:
            if isinstance(item, action):
                action_mapping[action].append(item)

    if heter_list:
        raise Exception("Uncategorized action")

    return action_mapping


def build_parser() -> argparse.ArgumentParser:
    """
    # help
    parser.add_argument('--help', action='help', help='Show this help message and exit')
    """
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


class PreviewModal(textual.screen.ModalScreen):
    BINDINGS = [("ctrl+p", "app.pop_screen", "Close")]

    def __init__(
        self,
        name: ty.Optional[str] = None,
        id: ty.Optional[str] = None,
        classes: ty.Optional[str] = None,
        options: dict[str, ty.Any] = {},
    ):
        super().__init__(name=name, id=id, classes=classes)
        self._options = options

    def compose(self) -> ComposeResult:
        yield tc.Container(
            tw.Static("Preview", id="preview-title"),
            tw.Static(id="preview-content"),
            id="preview-container",
        )
        yield tw.Footer()

    def on_mount(self) -> None:
        self.styles.align = ("center", "middle")
        self.update_content(self._options)

    def update_content(self, content: dict) -> None:
        preview: tw.Static = self.query_one("#preview-content")
        preview.update(rich.pretty.Pretty(content))


class Menual(App[SelectedOptions]):
    BINDINGS = [
        ("d", "toggle_dark", "Toggle dark mode"),
        ("q", "quit", "Quit"),
        ("ctrl+o", "confirm", "Confirm Options"),
        ("tab", "next_widget", "Next widget"),
        ("shift+tab", "previous_widget", "Previous widget"),
        ("ctrl+p", "toggle_preview", "Toggle Preview"),
    ]

    CSS_PATH = Path("menual.tcss")

    def __init__(
        self,
        driver_class: None = None,
        css_path: None = None,
        watch_css: bool = False,
        parser: ty.Optional[argparse.ArgumentParser] = None,
    ):
        super().__init__(
            driver_class=driver_class,
            css_path=css_path,
            watch_css=watch_css,
        )
        self.__action_groups = split_actions(parser._actions)

    def action_next_widget(self) -> None:
        current = self.screen.focused
        widgets = tuple(self.query("SelectionList, Input").results())
        if current in widgets:
            index = widgets.index(current)
            next_widget = widgets[(index + 1) % len(widgets)]
            self.set_focus(next_widget)

    def action_previous_widget(self) -> None:
        current = self.screen.focused
        widgets = tuple(self.query("SelectionList, Input").results())
        if current in widgets:
            index = widgets.index(current)
            previous_widget = widgets[(index - 1) % len(widgets)]
            self.set_focus(previous_widget)

    def _build_widgets(self):
        # StoreConstAction
        selections = self.__action_groups[argparse._StoreConstAction]
        selection_list = [
            Selection(prompt=action.dest, value=action.dest, initial_state=action.const)
            for action in selections
        ]
        with tc.Horizontal():
            yield tw.SelectionList(*selection_list)

        def type_cvt(param_type: ty.Any):
            if param_type is str or param_type is None:
                return "text"
            elif param_type is int:
                return "integer"
            elif param_type is float:
                return "number"
            else:
                raise Exception(f"Unknown type {param_type}")

        # StoreAction
        store_actions = self.__action_groups[argparse._StoreAction]
        with tc.VerticalScroll():
            for val in store_actions:
                yield tw.Label(val.help or "")
                yield tw.Input(
                    placeholder=val.dest,
                    value=str(val.default),
                    type=type_cvt(val.type),
                )

        # AppendAction
        append_actions = self.__action_groups.get(argparse._AppendAction, [])
        for action in append_actions:
            yield tw.Label(action.help or "")
            yield tw.Input(
                placeholder=f"{action.dest} (comma-separated)",
                # value="test",
                value=str(action.default),
                type=type_cvt(action.type),
            )

        # AppendConstAction
        append_const_actions = self.__action_groups.get(argparse._AppendConstAction, [])
        for action in append_const_actions:
            yield tw.Label(action.help or "")
            yield tw.Checkbox(action.dest)

        # CountAction
        count_actions = self.__action_groups.get(argparse._CountAction, [])
        for action in count_actions:
            yield tw.Label(action.help or "")
            yield tw.Input(placeholder=action.dest, value=str(action.default or 0))

    def compose(self) -> ComposeResult:
        yield tw.Header(name="pymenual", show_clock=True)
        for widget in self._build_widgets():
            yield widget
        yield tw.Footer()

    def on_mount(self) -> None:
        self.query_one(tw.SelectionList).border_title = "Choose options"
        self.set_focus(self.query_one(tw.SelectionList))

    def _get_widgets_options(self) -> SelectedOptions:
        options: SelectedOptions = {}

        # Get SelectionList options
        selection_list = self.query_one(tw.SelectionList)
        for selection in selection_list.selected:
            options[selection] = True

        # Get Input widget values
        for input_widget in self.query(tw.Input):
            if input_widget.value:  # Only add non-empty inputs
                options[input_widget.placeholder] = input_widget.value

        for checkbox_widget in self.query(tw.Checkbox):
            if checkbox_widget.value:
                options[str(checkbox_widget.label)] = checkbox_widget.value
        return options

    def action_toggle_preview(self) -> None:
        self._preview_model = PreviewModal(options=self._get_widgets_options())
        self.push_screen(self._preview_model)

    def action_confirm(self):
        options = self._get_widgets_options()
        self.exit(result=options, return_code=0)


def create_menual(parser: argparse.ArgumentParser):
    app = Menual(parser=parser)
    return app


def main():
    parser = build_parser()
    menual = create_menual(parser)
    inline = True
    options = menual.run(inline=inline)
    print(f"collected options: {options}")


if __name__ == "__main__":
    main()