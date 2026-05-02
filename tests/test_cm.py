"""Tests for cm.py CLI entry point."""

import argparse
import asyncio
import dataclasses
import json
import subprocess
import sys
from io import StringIO
from pathlib import Path
from unittest.mock import patch

import pytest

from colourmapper.cm import emit, emit_error, map_colour, setup_argument_parser
from colourmapper.ColourMapper import ColourMapper, ColourResult

CM_SCRIPT = Path(__file__).parent.parent / "src" / "colourmapper" / "cm.py"

_SRC = str(Path(__file__).parent.parent / "src")


def run_cm(*args: str) -> tuple[dict | None, int]:
    import os

    env = {**os.environ, "PYTHONPATH": _SRC}
    result = subprocess.run(
        [sys.executable, str(CM_SCRIPT), *args],
        capture_output=True,
        text=True,
        env=env,
        check=False,
    )
    try:
        return json.loads(result.stdout), result.returncode
    except json.JSONDecodeError:
        return None, result.returncode


def _fake_flags(**kwargs) -> argparse.Namespace:
    defaults = dict(colour=None, url=False, map_file=False, dump_map_file=False, debug=False)
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


@pytest.fixture()
def parser():
    return setup_argument_parser()


class TestEmit:
    def test_emit_outputs_json(self, capsys) -> None:
        emit({"key": "value"})
        out = capsys.readouterr().out
        parsed = json.loads(out)
        assert parsed == {"key": "value"}

    def test_emit_uses_indent(self, capsys) -> None:
        emit({"a": 1})
        out = capsys.readouterr().out
        assert "\n" in out


class TestEmitError:
    def test_emit_error_basic(self, capsys) -> None:
        emit_error("something went wrong")
        out = capsys.readouterr().out
        parsed = json.loads(out)
        assert parsed == {"error": "something went wrong"}

    def test_emit_error_with_detail(self, capsys) -> None:
        emit_error("bad input", "traceback here")
        out = capsys.readouterr().out
        parsed = json.loads(out)
        assert parsed["error"] == "bad input"
        assert parsed["detail"] == "traceback here"

    def test_emit_error_without_detail_omits_key(self, capsys) -> None:
        emit_error("oops")
        out = capsys.readouterr().out
        parsed = json.loads(out)
        assert "detail" not in parsed


class TestArgumentParser:
    def test_defaults(self, parser) -> None:
        args = parser.parse_args([])
        assert args.colour is None
        assert args.url is False
        assert args.map_file is False
        assert args.dump_map_file is False
        assert args.debug is False

    def test_colour_positional(self, parser) -> None:
        args = parser.parse_args(["burnt orange"])
        assert args.colour == "burnt orange"

    def test_url_flag(self, parser) -> None:
        args = parser.parse_args(["--url", "red"])
        assert args.url is True

    def test_map_file_flag(self, parser) -> None:
        args = parser.parse_args(["--map-file"])
        assert args.map_file is True

    def test_dump_map_file_flag(self, parser) -> None:
        args = parser.parse_args(["--dump-map-file"])
        assert args.dump_map_file is True

    def test_debug_flag(self, parser) -> None:
        args = parser.parse_args(["--debug"])
        assert args.debug is True


class TestMapColour:
    def test_map_file_returns_path(self) -> None:
        flags = _fake_flags(map_file=True)
        result = asyncio.run(map_colour(flags))
        assert isinstance(result, dict)
        assert "path" in result
        assert Path(result["path"]).exists()

    def test_dump_map_file_returns_dict(self) -> None:
        flags = _fake_flags(dump_map_file=True)
        result = asyncio.run(map_colour(flags))
        assert isinstance(result, dict)
        assert len(result) > 0

    def test_no_colour_returns_none(self) -> None:
        flags = _fake_flags(colour=None)
        result = asyncio.run(map_colour(flags))
        assert result is None

    def test_colour_lookup_returns_colour_result(self) -> None:
        flags = _fake_flags(colour="red")
        result = asyncio.run(map_colour(flags))
        assert isinstance(result, ColourResult)
        assert result.found is True

    def test_colour_lookup_with_url(self) -> None:
        flags = _fake_flags(colour="red", url=True)
        result = asyncio.run(map_colour(flags))
        assert isinstance(result, dict)
        assert "url" in result
        assert result["url"].startswith("https://")

    def test_url_contains_hex(self) -> None:
        flags = _fake_flags(colour="#ff0000", url=True)
        result = asyncio.run(map_colour(flags))
        assert isinstance(result, dict)
        assert "ff0000" in result["url"]

    def test_hex_lookup(self) -> None:
        flags = _fake_flags(colour="#ff0000")
        result = asyncio.run(map_colour(flags))
        assert isinstance(result, ColourResult)
        assert result.found is True


class TestMainCLI:
    def test_no_args_exits_nonzero(self) -> None:
        _, code = run_cm()
        assert code != 0

    def test_colour_lookup_exit_zero(self) -> None:
        _, code = run_cm("red")
        assert code == 0

    def test_colour_lookup_returns_found(self) -> None:
        result, _ = run_cm("red")
        assert result is not None
        assert result["found"] is True

    def test_map_file_exit_zero(self) -> None:
        _, code = run_cm("--map-file")
        assert code == 0

    def test_dump_map_file_exit_zero(self) -> None:
        _, code = run_cm("--dump-map-file")
        assert code == 0

    def test_url_flag_includes_url(self) -> None:
        result, _ = run_cm("--url", "red")
        assert result is not None
        assert "url" in result

    def test_debug_flag_includes_detail_on_error(self) -> None:
        result, code = run_cm("--debug", "--format")
        assert code != 0


class TestMain:
    def test_main_with_colour_emits_result(self, monkeypatch, capsys) -> None:
        import colourmapper.cm as cm_mod

        monkeypatch.setattr("sys.argv", ["cm", "red"])
        asyncio.run(cm_mod.main())
        out = capsys.readouterr().out
        parsed = json.loads(out)
        assert parsed["found"] is True

    def test_main_no_args_exits_nonzero(self, monkeypatch) -> None:
        import colourmapper.cm as cm_mod

        monkeypatch.setattr("sys.argv", ["cm"])
        with pytest.raises(SystemExit) as exc_info:
            asyncio.run(cm_mod.main())
        assert exc_info.value.code == 1

    def test_main_map_file_exits_zero(self, monkeypatch, capsys) -> None:
        import colourmapper.cm as cm_mod

        monkeypatch.setattr("sys.argv", ["cm", "--map-file"])
        asyncio.run(cm_mod.main())
        out = capsys.readouterr().out
        parsed = json.loads(out)
        assert "path" in parsed

    def test_main_exception_emits_error(self, monkeypatch, capsys) -> None:
        import colourmapper.cm as cm_mod

        monkeypatch.setattr("sys.argv", ["cm", "red"])
        monkeypatch.setattr(cm_mod, "map_colour", lambda _: (_ for _ in ()).throw(RuntimeError("fail")))

        async def bad_map(flags):
            raise RuntimeError("fail")

        monkeypatch.setattr(cm_mod, "map_colour", bad_map)
        with pytest.raises(SystemExit) as exc_info:
            asyncio.run(cm_mod.main())
        assert exc_info.value.code == 1
        out = capsys.readouterr().out
        parsed = json.loads(out)
        assert parsed["error"] == "fail"

    def test_main_debug_includes_detail_on_error(self, monkeypatch, capsys) -> None:
        import colourmapper.cm as cm_mod

        monkeypatch.setattr("sys.argv", ["cm", "--debug", "red"])

        async def bad_map(flags):
            raise RuntimeError("debug fail")

        monkeypatch.setattr(cm_mod, "map_colour", bad_map)
        with pytest.raises(SystemExit) as exc_info:
            asyncio.run(cm_mod.main())
        assert exc_info.value.code == 1
        out = capsys.readouterr().out
        parsed = json.loads(out)
        assert "detail" in parsed


class TestEntryPointKeyboardInterrupt:
    def test_entry_keyboard_interrupt(self, capsys) -> None:
        from colourmapper.cm import _entry

        with patch("colourmapper.cm.asyncio.run", side_effect=KeyboardInterrupt):
            with pytest.raises(SystemExit) as exc_info:
                _entry()
            assert exc_info.value.code == 0
        out = capsys.readouterr().out
        parsed = json.loads(out)
        assert parsed["error"] == "interrupted"

    def test_entry_unexpected_exception(self, capsys) -> None:
        from colourmapper.cm import _entry

        def _raise_and_close(coro):
            coro.close()
            raise RuntimeError("boom")

        with patch("colourmapper.cm.asyncio.run", side_effect=_raise_and_close):
            with pytest.raises(SystemExit) as exc_info:
                _entry()
            assert exc_info.value.code == 1
        out = capsys.readouterr().out
        parsed = json.loads(out)
        assert "boom" in parsed["error"]
