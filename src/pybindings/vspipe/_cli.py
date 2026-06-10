import argparse
import sys
import time
from contextlib import nullcontext
from typing import Any

import vapoursynth as vs

from ._utils import load_script, open_output_file, print_info_node, setup_callbacks
from ._vsenv import CustomPolicy


class VSPipeHelpFormatter(argparse.RawDescriptionHelpFormatter):
    """
    Custom help formatter to align long-only options with short+long options.
    """

    def __init__(
        self,
        prog: str,
        indent_increment: int = 2,
        max_help_position: int = 24,
        width: int | None = None,
        **kwargs: Any,
    ) -> None:
        # Increase max_help_position to accommodate padding for long-only options
        # while keeping help text on the same line where possible.
        super().__init__(prog, indent_increment, max_help_position + 10, width, **kwargs)

    def _format_action_invocation(self, action: argparse.Action) -> str:
        res = super()._format_action_invocation(action)
        # For options that only have a long name, prepend 4 spaces
        # to align them with those that have both a short and long name (e.g., -a, --arg).
        return (
            "    " + res
            if action.option_strings and len(action.option_strings) == 1 and action.option_strings[0].startswith("--")
            else res
        )


def build_parser() -> argparse.ArgumentParser:
    epilog = (
        "Examples:\n"
        "  Show script info:\n"
        "    vspipe --info script.vpy\n"
        "  Write to stdout:\n"
        "    vspipe [options] script.vpy -\n"
    )

    if sys.platform == "win32":
        epilog += '  Write to a named pipe (Windows only):\n    vspipe [options] script.vpy "\\\\.\\pipe\\<pipename>"\n'

    epilog += (
        "  Request all frames but don't output them:\n"
        "    vspipe [options] script.vpy --\n"
        "  Write frames 5-100 to file:\n"
        "    vspipe --start 5 --end 100 script.vpy output.raw\n"
        "  Pass values to a script:\n"
        '    vspipe --arg deinterlace=yes --arg "message=fluffy kittens" script.vpy output.raw\n'
        "  Pipe to x264 and write timecodes file:\n"
        "    vspipe script.vpy - -c y4m --timecodes timecodes.txt | x264 --demuxer y4m -o script.mkv -"
    )

    parser = argparse.ArgumentParser(
        prog="vspipe",
        description="VapourSynth script piping utility.",
        epilog=epilog,
        formatter_class=VSPipeHelpFormatter,
        add_help=False,
    )

    options = parser.add_argument_group("Available options")
    options.add_argument(
        "-a",
        "--arg",
        action="append",
        metavar="key=value",
        help="Argument to pass to the script environment",
    )
    options.add_argument(
        "-s",
        "--start",
        type=int,
        metavar="N",
        help="Set output frame/sample range start",
    )
    options.add_argument(
        "-e",
        "--end",
        type=int,
        metavar="N",
        help="Set output frame/sample range end (inclusive)",
    )
    options.add_argument(
        "-o",
        "--outputindex",
        type=int,
        metavar="N",
        help="Select output index",
    )
    options.add_argument(
        "-r",
        "--requests",
        type=int,
        metavar="N",
        help="Set number of concurrent frame requests",
    )
    options.add_argument(
        "-c",
        "--container",
        choices=["y4m", "wav", "w64"],
        metavar="<y4m/wav/w64>",
        help="Add headers for the specified format to the output",
    )
    options.add_argument(
        "-t",
        "--timecodes",
        metavar="FILE",
        help="Write timecodes v2 file",
    )
    options.add_argument(
        "-j",
        "--json",
        metavar="FILE",
        help="Write properties of output frames in json format to file",
    )
    options.add_argument(
        "-p",
        "--progress",
        action="store_true",
        help="Print progress to stderr",
    )
    options.add_argument(
        "--filter-time",
        action="store_true",
        help="Print time spent in individual filters to stderr after processing",
    )
    options.add_argument(
        "--filter-time-graph",
        metavar="FILE",
        help="Write output node's filter graph in dot format with time information after processing",
    )
    options.add_argument(
        "-i",
        "--info",
        action="store_true",
        help="Print all set output node info to <outfile> and exit",
    )
    options.add_argument(
        "-g",
        "--graph",
        choices=["simple", "full"],
        metavar="<simple/full>",
        help="Print output node's filter graph in dot format to <outfile> and exit",
    )
    options.add_argument(
        "--frame-ref-debug",
        action="store_true",
        help="Print frame allocation debug information",
    )
    options.add_argument(
        "-v",
        "--version",
        action="version",
        version=f"VSPipe {vs.__version__}",
        help="Show version info and exit",
    )
    options.add_argument(
        "-h",
        "--help",
        action="help",
        help="Show this help message and exit",
    )

    parser.add_argument("script", nargs="?", help="VapourSynth script file")
    parser.add_argument("outfile", nargs="?", help="Output file ('-' for stdout, '--' for no output)")

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()

    raw_argv = list(argv) if argv is not None else sys.argv[1:]

    args = parser.parse_args(raw_argv)

    # If outfile is missing but the last argument was "--",
    # it means argparse consumed it as an end-of-options marker.
    if args.outfile is None and raw_argv and raw_argv[-1] == "--":
        args.outfile = "--"

    if not args.script:
        parser.print_help()
        return 1

    # Initialize VapourSynth Environment & core
    flags = 0
    if args.frame_ref_debug:
        flags |= vs.CoreCreationFlags.ENABLE_FRAME_REF_DEBUG
    if args.graph or args.filter_time or args.filter_time_graph:
        flags |= vs.CoreCreationFlags.ENABLE_GRAPH_INSPECTION

    vs.register_policy(CustomPolicy(flags))

    if args.filter_time or args.filter_time_graph:
        vs.core.timings.enabled = True

    # Load the script
    return_code = load_script(args.script, args.arg)
    if return_code:
        return return_code

    # Retrieve outputs
    outputs = vs.get_outputs()
    if not outputs:
        sys.stderr.write("No output nodes set in script.\n")
        return 1

    # Retrieve primary output node
    output_index = args.outputindex if args.outputindex is not None else 0
    try:
        output = outputs[output_index]
    except KeyError:
        sys.stderr.write(f"Invalid output index: {output_index}\n")
        return 1

    node = output.clip if isinstance(output, vs.VideoOutputTuple) else output

    # Handle info and graph early-exit options
    if args.info:
        return print_info_node(args.outfile, outputs)

    if args.graph:
        try:
            graph = node.get_graph(mode=args.graph)
            ctx = (
                open(args.outfile, "w", encoding="utf-8")
                if args.outfile and args.outfile != "-"
                else nullcontext(sys.stdout)
            )
            with ctx as out:
                out.write(graph)
        except Exception as e:
            sys.stderr.write(f"Failed to write graph: {e}\n")
            return 1
        return 0

    # Check for output file
    if not args.outfile:
        sys.stderr.write("No output file specified.\n")
        return 1

    # Apply trim if requested
    if args.start is not None or args.end is not None:
        start = args.start if args.start is not None else 0
        end = args.end
        if isinstance(node, vs.VideoNode):
            node = node.std.Trim(first=start, last=end)
        else:
            node = node.std.AudioTrim(first=start, last=end)

    # Open output file/pipe for frames
    try:
        ctx_out = open_output_file(args.outfile)
    except Exception as e:
        sys.stderr.write(f"Failed to open output file: {e}\n")
        return 1

    with (
        setup_callbacks(args.progress, args.timecodes, args.json, node) as (progress_cb, frame_cb),
        ctx_out as outfile,
    ):
        # Start output
        output_args = dict[str, Any]()

        if isinstance(node, vs.VideoNode):
            output_args["y4m"] = args.container == "y4m"

        if isinstance(node, vs.AudioNode):
            output_args["wav"] = args.container == "wav"
            output_args["w64"] = args.container == "w64"

        start_time = time.monotonic()
        try:
            node.output(
                outfile,
                progress_update=progress_cb,
                frame_cb=frame_cb,
                prefetch=args.requests if args.requests is not None else 0,
                **output_args,
            )
        except Exception as e:
            sys.stderr.write(f"\nProcessing error: {e}\n")
            return 1

    elapsed = time.monotonic() - start_time
    if isinstance(node, vs.VideoNode):
        sys.stderr.write(
            f"Output {node.num_frames} frames in {elapsed:.2f} seconds "
            f"({node.num_frames / elapsed if elapsed > 0 else 0:.2f} fps)\n"
        )
    else:
        sys.stderr.write(f"Output {node.num_samples} samples in {elapsed:.2f} seconds\n")

    if args.filter_time:
        sys.stderr.write(node.get_filter_time(elapsed))

    if args.filter_time_graph:
        try:
            graph = node.get_graph(mode="times", processing_time=elapsed)
            with open(args.filter_time_graph, "w", encoding="utf-8") as f:
                f.write(graph)
        except Exception as e:
            sys.stderr.write(f"Failed to write filter time graph: {e}\n")

    return 0
