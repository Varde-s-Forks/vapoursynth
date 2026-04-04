import ctypes
import os
import runpy
import sys
import time
from collections.abc import Callable, Iterator, Mapping
from contextlib import AbstractContextManager, contextmanager, nullcontext
from pathlib import Path
from typing import BinaryIO, Literal, TextIO

import vapoursynth as vs


def load_script(script: str, arg: list[str]) -> int:
    env_dict = {"__name__": "__vapoursynth__"}
    if arg:
        for script_arg in arg:
            key, _, value = script_arg.partition("=")
            env_dict[key] = value

    try:
        script_path = Path(script).absolute()
        old_cwd = Path.cwd()
        os.chdir(script_path.parent)
        try:
            runpy.run_path(str(script_path), init_globals=env_dict, run_name="__vapoursynth__")
        finally:
            os.chdir(old_cwd)
    except Exception as e:
        sys.stderr.write(f"Script evaluation failed:\n{e}\n")
        return 1

    return 0


def get_timecodes_cb(tc_file: TextIO) -> Callable[[int, vs.VideoFrame | vs.AudioFrame], None]:
    current_time = 0.0
    tc_file.write("# timecode format v2\n")

    def cb(n: int, f: vs.VideoFrame | vs.AudioFrame) -> None:
        nonlocal current_time
        tc_file.write(f"{current_time * 1000:.6f}\n")
        props = f.props
        dur_num = props.get("_DurationNum", 0)
        dur_den = props.get("_DurationDen", 0)

        try:
            current_time += dur_num / dur_den
        except ZeroDivisionError:
            pass

    return cb


def get_json_cb(json_file: TextIO, total_items: int) -> Callable[[int, vs.VideoFrame | vs.AudioFrame], None]:
    def cb(n: int, f: vs.VideoFrame | vs.AudioFrame) -> None:
        comma = "," if n < total_items - 1 else ""
        json_file.write(f"  {f.props.to_json()}{comma}\n")

    return cb


def get_progress_cb(node: vs.VideoNode | vs.AudioNode) -> Callable[[int, int], None]:
    start_time = time.monotonic()
    last_report = 0.0

    is_audio = isinstance(node, vs.AudioNode)
    prefix = "Sample" if is_audio else "Frame"
    fps = "sps" if is_audio else "fps"

    def cb(current: int, total: int) -> None:
        nonlocal last_report
        now = time.monotonic()
        if current == 0:
            sys.stderr.write(f"{prefix}: 0/{total}\r")
            return

        if now - last_report < 0.5 and current != total:
            return

        last_report = now
        elapsed = now - start_time
        fps_str = ""
        if elapsed > 8:
            rate = current / elapsed
            fps_str = f" ({rate:.2f} {fps})"

        sys.stderr.write(f"{prefix}: {current}/{total}{fps_str}\r")
        if current == total:
            sys.stderr.write("\n")

    return cb


@contextmanager
def setup_callbacks(
    progress: bool,
    tc: str | None,
    json: str | None,
    node: vs.VideoNode | vs.AudioNode,
) -> Iterator[
    tuple[
        Callable[[int, int], None] | None,
        Callable[[int, vs.VideoFrame | vs.AudioFrame], None] | None,
    ],
]:
    cbs = list[Callable[[int, vs.VideoFrame | vs.AudioFrame], None]]()
    files = list[TextIO]()

    if tc:
        tc_f = open(tc, "w")
        cb = get_timecodes_cb(tc_f)
        files.append(tc_f)
        cbs.append(cb)

    json_finale = None
    if json:
        js_f = open(json, "w")
        js_f.write("[\n")
        cb = get_json_cb(js_f, node.num_frames if isinstance(node, vs.VideoNode) else node.num_samples)
        files.append(js_f)
        cbs.append(cb)

        def _close_json() -> None:
            js_f.write("]\n")

        json_finale = _close_json

    frame_cb = None
    if cbs:

        def execute_cbs(n: int, f: vs.VideoFrame | vs.AudioFrame) -> None:
            for c in cbs:
                c(n, f)

        frame_cb = execute_cbs

    progress_cb = get_progress_cb(node) if progress else None

    try:
        yield progress_cb, frame_cb
    finally:
        if json_finale:
            json_finale()
        for f in files:
            f.close()


def open_output_file(path: str | os.PathLike[str]) -> AbstractContextManager[BinaryIO]:
    path = str(path)
    if path == "-":
        if sys.platform == "win32":
            import msvcrt

            msvcrt.setmode(sys.stdout.fileno(), os.O_BINARY)
        return nullcontext(sys.stdout.buffer)

    if path == "--" or path == ".":
        return open(os.devnull, "wb")

    if sys.platform != "win32" or not path.startswith("\\\\.\\pipe\\"):
        return open(path, "wb")

    import msvcrt

    PIPE_ACCESS_OUTBOUND = 0x00000002
    PIPE_TYPE_BYTE = 0x00000000
    PIPE_READMODE_BYTE = 0x00000000
    PIPE_WAIT = 0x00000000
    INVALID_HANDLE_VALUE = -1

    kernel32 = ctypes.windll.kernel32
    hPipe = kernel32.CreateNamedPipeW(
        path,
        PIPE_ACCESS_OUTBOUND,
        PIPE_TYPE_BYTE | PIPE_READMODE_BYTE | PIPE_WAIT,
        1,
        0,
        0,
        0,
        None,
    )

    if hPipe == INVALID_HANDLE_VALUE:
        raise OSError(f"Failed to create named pipe: {path}")

    if kernel32.ConnectNamedPipe(hPipe, None) == 0:
        error = kernel32.GetLastError()
        # ERROR_PIPE_CONNECTED = 535
        if error != 535:
            kernel32.CloseHandle(hPipe)
            raise OSError(f"Failed to connect named pipe: {path} (Error: {error})")

    fd = msvcrt.open_osfhandle(hPipe, os.O_WRONLY | os.O_BINARY)
    return os.fdopen(fd, "wb")


def print_info_node(
    outfile: str | Path | None,
    outputs: Mapping[int, vs.VideoOutputTuple | vs.VideoNode | vs.AudioNode],
) -> Literal[0]:
    ctx = Path(outfile).open("w", encoding="utf-8") if outfile and str(outfile) != "-" else nullcontext(sys.stdout)

    with ctx as out:
        for idx, output in sorted(outputs.items()):
            node = output.clip if isinstance(output, vs.VideoOutputTuple) else output
            alpha = "Yes" if isinstance(output, vs.VideoOutputTuple) and output.alpha else "No"
            lines = [f"Output Index: {idx}"]

            if isinstance(node, vs.VideoNode):
                lines.extend(
                    [
                        "Type: Video",
                        f"Width: {node.width}",
                        f"Height: {node.height}",
                        f"Frames: {node.num_frames}",
                        f"FPS: {node.fps.numerator}/{node.fps.denominator} "
                        f"({node.fps.numerator / node.fps.denominator:.3f} fps)",
                    ]
                )
                if fmt := node.format:
                    lines.extend(
                        [
                            f"Format Name: {fmt.name}",
                            f"Color Family: {fmt.color_family.name}",
                            f"Alpha: {alpha}",
                            f"Sample Type: {fmt.sample_type.name}",
                            f"Bits: {fmt.bits_per_sample}",
                            f"SubSampling W: {fmt.subsampling_w}",
                            f"SubSampling H: {fmt.subsampling_h}",
                        ]
                    )
                else:
                    lines.append("Format: Variable")
            elif isinstance(node, vs.AudioNode):
                fmt = node.format
                layout = ", ".join(c.name.title().replace("_", " ") for c in fmt.channel_layout)
                lines.extend(
                    [
                        "Type: Audio",
                        f"Samples: {node.num_samples}",
                        f"Sample Rate: {node.sample_rate} Hz",
                        f"Format Name: {fmt.name}",
                        f"Sample Type: {fmt.sample_type.name}",
                        f"Bits: {fmt.bits_per_sample}",
                        f"Channels: {fmt.num_channels}",
                        f"Layout: {layout}",
                    ]
                )

            out.write("\n".join(lines) + "\n")

    return 0
