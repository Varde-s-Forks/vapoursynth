import json
import os
import subprocess
import unittest
from pathlib import Path
from typing import ClassVar


class VSPipeTestCase(unittest.TestCase):
    test_vpy: ClassVar[Path]
    arg_vpy: ClassVar[Path]
    multi_vpy: ClassVar[Path]
    audio_vpy: ClassVar[Path]

    @classmethod
    def setUpClass(cls) -> None:
        # Create a basic test script
        cls.test_vpy = Path("test_vspipe_basic.vpy")
        cls.test_vpy.write_text(
            "import vapoursynth as vs\n"
            "clip = vs.core.std.BlankClip(format=vs.YUV420P8, width=640, height=480, length=100, fpsnum=24, fpsden=1)\n"
            "clip.set_output()\n",
            encoding="utf-8",
        )

        # Create a script with arguments
        cls.arg_vpy = Path("test_vspipe_arg.vpy")
        cls.arg_vpy.write_text(
            "import vapoursynth as vs\n"
            "w = int(globals().get('width', 640))\n"
            "h = int(globals().get('height', 480))\n"
            "clip = vs.core.std.BlankClip(format=vs.YUV420P8, width=w, height=h, length=10, fpsnum=24, fpsden=1)\n"
            "clip.set_output()\n",
            encoding="utf-8",
        )

        # Create a script with multiple outputs
        cls.multi_vpy = Path("test_vspipe_multi.vpy")
        cls.multi_vpy.write_text(
            "import vapoursynth as vs\n"
            "clip1 = vs.core.std.BlankClip(format=vs.YUV420P8, width=640, height=480, length=10, fpsnum=24, fpsden=1)\n"
            "clip2 = vs.core.std.BlankClip(format=vs.YUV420P8, width=320, height=240, length=5, fpsnum=24, fpsden=1)\n"
            "clip1.set_output(0)\n"
            "clip2.set_output(1)\n",
            encoding="utf-8",
        )

        # Create an audio script
        cls.audio_vpy = Path("test_vspipe_audio.vpy")
        cls.audio_vpy.write_text(
            "import vapoursynth as vs\n"
            "audio = vs.core.std.BlankAudio(bits=16, sampletype=vs.INTEGER, samplerate=44100, length=44100)\n"
            "audio.set_output()\n",
            encoding="utf-8",
        )

    @classmethod
    def tearDownClass(cls) -> None:
        # Cleanup scripts
        for p in [cls.test_vpy, cls.arg_vpy, cls.multi_vpy, cls.audio_vpy]:
            p.unlink(missing_ok=True)

    def run_vspipe(self, args: list[str | os.PathLike[str]]) -> tuple[int, str, str]:
        res = subprocess.run(["vspipe", *args], capture_output=True, text=True, encoding="utf-8")
        return res.returncode, res.stdout, res.stderr

    def test_help(self) -> None:
        ret, stdout, stderr = self.run_vspipe(["-h"])
        self.assertEqual(ret, 0, f"Error: {stderr}")
        self.assertIn("VapourSynth script piping utility", stdout)

    def test_version(self) -> None:
        ret, stdout, stderr = self.run_vspipe(["-v"])
        self.assertEqual(ret, 0, f"Error: {stderr}")
        self.assertIn("VSPipe", stdout)

    def test_info(self) -> None:
        ret, stdout, stderr = self.run_vspipe(["-i", self.test_vpy, "-"])
        self.assertEqual(ret, 0, f"Error: {stderr}")
        self.assertIn("Width: 640", stdout)
        self.assertIn("Height: 480", stdout)
        self.assertIn("Frames: 100", stdout)
        self.assertIn("Type: Video", stdout)

    def test_graph_simple(self) -> None:
        ret, stdout, stderr = self.run_vspipe(["-g", "simple", self.test_vpy, "-"])
        self.assertEqual(ret, 0, f"Error: {stderr}")
        self.assertIn("digraph", stdout)
        self.assertIn("BlankClip", stdout)

    def test_args(self) -> None:
        ret, stdout, stderr = self.run_vspipe(["-a", "width=320", "-a", "height=240", "-i", str(self.arg_vpy), "-"])
        self.assertEqual(ret, 0, f"Error: {stderr}")
        self.assertIn("Width: 320", stdout)
        self.assertIn("Height: 240", stdout)

    def test_output_selection(self) -> None:
        ret, stdout, stderr = self.run_vspipe(["-i", str(self.multi_vpy), "-"])
        self.assertEqual(ret, 0, f"Error: {stderr}")
        self.assertIn("Output Index: 0", stdout)
        self.assertIn("Width: 640", stdout)

    def test_frame_range(self) -> None:
        ret, _, stderr = self.run_vspipe(["-s", "5", "-e", "14", self.test_vpy, "--"])
        self.assertEqual(ret, 0, f"Error: {stderr}")
        self.assertIn("Output 10 frames", stderr)

    def test_json_output(self) -> None:
        json_path = "test_output.json"
        try:
            ret, _, stderr = self.run_vspipe(["-j", json_path, "-s", "0", "-e", "1", self.test_vpy, "--"])
            self.assertEqual(ret, 0, f"Error: {stderr}")
            with open(json_path, "r") as f:
                data = json.load(f)
            self.assertEqual(len(data), 2)
            self.assertIn("_DurationNum", data[0])
        finally:
            if os.path.exists(json_path):
                os.remove(json_path)

    def test_timecodes_output(self) -> None:
        tc_path = "test_timecodes.txt"
        try:
            ret, _, stderr = self.run_vspipe(["-t", tc_path, "-s", "0", "-e", "2", self.test_vpy, "--"])
            self.assertEqual(ret, 0, f"Error: {stderr}")
            with open(tc_path, "r") as f:
                lines = f.readlines()
            self.assertEqual(lines[0], "# timecode format v2\n")
            self.assertEqual(len(lines), 4)  # header + 3 frames
        finally:
            if os.path.exists(tc_path):
                os.remove(tc_path)

    def test_y4m_container(self) -> None:
        out_path = "test_output.raw"
        try:
            ret, _, stderr = self.run_vspipe(["-c", "y4m", "-s", "0", "-e", "0", self.test_vpy, out_path])
            self.assertEqual(ret, 0, f"Error: {stderr}")
            with open(out_path, "rb") as f:
                header = f.read(10)
            self.assertTrue(header.startswith(b"YUV4MPEG2 "))
        finally:
            if os.path.exists(out_path):
                os.remove(out_path)

    def test_audio_wav(self) -> None:
        out_path = "test_audio.wav"
        try:
            ret, _, stderr = self.run_vspipe(["-c", "wav", str(self.audio_vpy), out_path])
            self.assertEqual(ret, 0, f"Error: {stderr}")
            with open(out_path, "rb") as f:
                header = f.read(4)
            self.assertEqual(header, b"RIFF")
        finally:
            if os.path.exists(out_path):
                os.remove(out_path)

    def test_filter_time(self) -> None:
        ret, _, stderr = self.run_vspipe(["--filter-time", "-s", "0", "-e", "9", self.test_vpy, "--"])
        self.assertEqual(ret, 0, f"Error: {stderr}")
        self.assertIn("Filtername", stderr)

    def test_error_missing_script(self) -> None:
        ret, _, stderr = self.run_vspipe(["non_existent.vpy", "--"])
        self.assertEqual(ret, 1)
        self.assertIn("Script evaluation failed", stderr)

    def test_error_invalid_index(self) -> None:
        ret, _, stderr = self.run_vspipe(["-o", "99", self.test_vpy, "--"])
        self.assertEqual(ret, 1)
        self.assertIn("Invalid output index", stderr)

    @unittest.skipIf(os.name != "nt", "Named pipes are only supported on Windows")
    def test_named_pipe(self) -> None:
        import threading
        import time

        pipe_name = r"\\.\pipe\vspipe_test_pipe"

        read_data = []

        def pipe_reader() -> None:
            for _ in range(50):
                try:
                    with open(pipe_name, "rb") as f:
                        if chunk := f.read(1024):
                            read_data.append(chunk)
                        while f.read(65536):
                            pass
                    return
                except (FileNotFoundError, PermissionError):
                    time.sleep(0.1)
                except Exception as e:
                    read_data.append(e)
                    return

        reader_thread = threading.Thread(target=pipe_reader)
        reader_thread.start()

        try:
            ret, _, stderr = self.run_vspipe(["-s", "0", "-e", "9", str(self.test_vpy), pipe_name])
            self.assertEqual(ret, 0, f"Error: {stderr}")
            self.assertIn("Output 10 frames", stderr)
        finally:
            reader_thread.join(timeout=5)

        self.assertTrue(len(read_data) > 0, "No data was read from the pipe")
        self.assertIsInstance(
            read_data[0], bytes, f"Reader encountered an error: {read_data[0] if read_data else 'None'}"
        )
        self.assertTrue(len(read_data[0]) > 0, "Read empty data from the pipe")


if __name__ == "__main__":
    unittest.main()
