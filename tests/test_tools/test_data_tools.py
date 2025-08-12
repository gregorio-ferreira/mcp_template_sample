"""Tests for data tools."""

from mcp_server.tools.data_tools import format_json, parse_json


class TestParseJson:
    def test_parses_json_string(self) -> None:
        data = parse_json('{"a": 1, "b": 2}')
        assert data == {"a": 1, "b": 2}


class TestFormatJson:
    def test_formats_mapping(self) -> None:
        text = format_json({"b": 2, "a": 1}, indent=2)
        assert text == '{\n  "a": 1,\n  "b": 2\n}'

    def test_round_trip(self) -> None:
        original = {"x": "y"}
        assert parse_json(format_json(original)) == original
