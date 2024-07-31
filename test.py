from pymenual.menual import Menual


def build_parser():
    import argparse

    parser = argparse.ArgumentParser(__name__)

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


parser = build_parser()


def test(commands: ...):
    menual = Menual.from_argparse(commands)
    inline = False
    options = menual.run(inline=inline)
    print(f"collected options: {options}")


test(parser)
