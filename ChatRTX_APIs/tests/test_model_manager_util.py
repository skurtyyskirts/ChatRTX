import hashlib
import os
import subprocess
import pytest
from unittest.mock import patch, MagicMock

from ChatRTX.model_manager.model_manager_util import (
    execute_command,
    parse_download_status,
    move_files,
    remove_directory,
    calculate_md5_checksum,
    OutputCapturePrint,
)


class TestExecuteCommand:
    def test_runs_successful_command(self):
        # Should not raise
        execute_command(["echo", "hello"])

    def test_handles_failed_command_without_raising(self):
        # CalledProcessError is caught internally and printed
        execute_command(["false"])

    @patch("subprocess.run")
    def test_calls_subprocess_with_shell_true(self, mock_run):
        mock_run.return_value = MagicMock(stdout=b"ok", stderr=b"")
        execute_command(["some", "command"])
        mock_run.assert_called_once()
        _, kwargs = mock_run.call_args
        assert kwargs.get("shell") is False

    @patch("subprocess.run")
    def test_captures_stdout_and_stderr(self, mock_run):
        mock_run.return_value = MagicMock(stdout=b"output", stderr=b"err")
        execute_command("cmd")
        _, kwargs = mock_run.call_args
        assert kwargs.get("stdout") == subprocess.PIPE
        assert kwargs.get("stderr") == subprocess.PIPE


class TestParseDownloadStatus:
    def test_completed_status_from_model_line(self):
        output = "Download status: COMPLETED\nDownloaded local path model: /tmp/model"
        status, path = parse_download_status(output)
        assert status == "COMPLETED"
        assert path == "/tmp/model"

    def test_completed_status_from_resource_line(self):
        output = "Download status: COMPLETED\nDownloaded local path resource: /tmp/resource"
        status, path = parse_download_status(output)
        assert status == "COMPLETED"
        assert path == "/tmp/resource"

    def test_returns_failed_with_no_status_line(self):
        status, path = parse_download_status("some unrelated output")
        assert status == "FAILED"
        assert path is None

    def test_returns_failed_on_empty_output(self):
        status, path = parse_download_status("")
        assert status == "FAILED"
        assert path is None

    def test_returns_failed_when_status_line_not_completed(self):
        output = "Download status: Download Status: Failed\nSome other line"
        status, path = parse_download_status(output)
        assert status == "FAILED"
        assert path is None

    def test_path_extracted_even_on_failed_status(self):
        # model path may be present even if status indicates failure
        output = "Downloaded local path model: /tmp/partial"
        status, path = parse_download_status(output)
        assert status == "FAILED"
        assert path == "/tmp/partial"


class TestMoveFiles:
    def test_moves_files_successfully(self, tmp_path):
        src = tmp_path / "src"
        dst = tmp_path / "dst"
        src.mkdir()
        (src / "file.txt").write_text("content")

        result = move_files(str(src), str(dst), ["file.txt"])

        assert result is True
        assert (dst / "file.txt").exists()
        assert not (src / "file.txt").exists()

    def test_returns_false_for_missing_source_file(self, tmp_path):
        src = tmp_path / "src"
        dst = tmp_path / "dst"
        src.mkdir()

        result = move_files(str(src), str(dst), ["nonexistent.txt"])
        assert result is False

    def test_creates_destination_directory(self, tmp_path):
        src = tmp_path / "src"
        dst = tmp_path / "new_dst"
        src.mkdir()
        (src / "data.bin").write_bytes(b"\x00\x01")

        move_files(str(src), str(dst), ["data.bin"])
        assert dst.exists()

    def test_moves_multiple_files(self, tmp_path):
        src = tmp_path / "src"
        dst = tmp_path / "dst"
        src.mkdir()
        for name in ["a.txt", "b.txt", "c.txt"]:
            (src / name).write_text(name)

        result = move_files(str(src), str(dst), ["a.txt", "b.txt", "c.txt"])
        assert result is True
        for name in ["a.txt", "b.txt", "c.txt"]:
            assert (dst / name).exists()


class TestRemoveDirectory:
    def test_removes_existing_directory(self, tmp_path):
        target = tmp_path / "to_delete"
        target.mkdir()
        (target / "file.txt").write_text("data")

        result = remove_directory(str(target))
        assert result is True
        assert not target.exists()

    def test_returns_false_for_nonexistent_directory(self, tmp_path):
        result = remove_directory(str(tmp_path / "ghost"))
        assert result is False

    def test_removes_nested_directory(self, tmp_path):
        target = tmp_path / "outer" / "inner"
        target.mkdir(parents=True)
        outer = tmp_path / "outer"

        result = remove_directory(str(outer))
        assert result is True
        assert not outer.exists()


class TestCalculateMd5Checksum:
    def test_returns_hex_string(self, tmp_path):
        f = tmp_path / "file.bin"
        f.write_bytes(b"hello world")
        result = calculate_md5_checksum(str(f))
        assert isinstance(result, str)
        assert len(result) == 32

    def test_matches_known_hash(self, tmp_path):
        f = tmp_path / "file.bin"
        data = b"hello world"
        f.write_bytes(data)
        expected = hashlib.md5(data).hexdigest()
        assert calculate_md5_checksum(str(f)) == expected

    def test_different_files_produce_different_checksums(self, tmp_path):
        f1 = tmp_path / "a.bin"
        f2 = tmp_path / "b.bin"
        f1.write_bytes(b"content A")
        f2.write_bytes(b"content B")
        assert calculate_md5_checksum(str(f1)) != calculate_md5_checksum(str(f2))

    def test_same_content_produces_same_checksum(self, tmp_path):
        f1 = tmp_path / "x.bin"
        f2 = tmp_path / "y.bin"
        f1.write_bytes(b"identical")
        f2.write_bytes(b"identical")
        assert calculate_md5_checksum(str(f1)) == calculate_md5_checksum(str(f2))

    def test_empty_file(self, tmp_path):
        f = tmp_path / "empty.bin"
        f.write_bytes(b"")
        expected = hashlib.md5(b"").hexdigest()
        assert calculate_md5_checksum(str(f)) == expected


class TestOutputCapturePrint:
    def test_captures_printed_output(self, capsys):
        cap = OutputCapturePrint()
        cap.custom_print("hello", "world")
        assert "hello world" in cap.get_captured_output()

    def test_captured_output_accumulates(self):
        cap = OutputCapturePrint()
        cap.custom_print("line one")
        cap.custom_print("line two")
        result = cap.get_captured_output()
        assert "line one" in result
        assert "line two" in result

    def test_get_captured_output_returns_string(self):
        cap = OutputCapturePrint()
        assert isinstance(cap.get_captured_output(), str)

    def test_empty_capture_returns_empty_string(self):
        cap = OutputCapturePrint()
        assert cap.get_captured_output() == ""
