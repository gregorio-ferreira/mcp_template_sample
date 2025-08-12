"""Tests for file tools."""

from pathlib import Path

import pytest

from mcp_server.tools.file_tools import list_directory, read_file


class TestReadFile:
    def test_reads_existing_file(self, tmp_path: Path) -> None:
        p = tmp_path / "example.txt"
        p.write_text("hello")
        assert read_file(str(p)) == "hello"

    def test_missing_file(self, tmp_path: Path) -> None:
        with pytest.raises(FileNotFoundError):
            read_file(str(tmp_path / "missing.txt"))


class TestListDirectory:
    def test_lists_only_files(self, tmp_path: Path) -> None:
        file1 = tmp_path / "a.txt"
        file1.write_text("a")
        sub = tmp_path / "subdir"
        sub.mkdir()
        (sub / "b.txt").write_text("b")
        result = list_directory(str(tmp_path))
        assert str(file1) in result
        assert str(sub / "b.txt") not in result

    def test_path_not_directory(self, tmp_path: Path) -> None:
        file1 = tmp_path / "a.txt"
        file1.write_text("a")
        with pytest.raises(NotADirectoryError):
            list_directory(str(file1))
