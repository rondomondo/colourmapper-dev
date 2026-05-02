#!/usr/bin/env python3
"""CLI entry point for colourmapper - look up colours by name or hex value."""

import argparse
import asyncio
import dataclasses
import json
import os
import re
import sys
import traceback

from colourmapper.ColourMapper import ColourMapper, ColourResult

PROGRAM_NAME = os.path.basename(re.sub(r"\.py$", "", sys.argv[0]))


def emit(data: object) -> None:
    """Serialise data to formatted JSON and write to stdout.

    Args:
        data: any JSON-serialisable value.
    """
    print(json.dumps(data, indent=2))


def emit_error(message: str, detail: str | None = None) -> None:
    """Write a JSON error payload to stdout and return.

    Args:
        message: short human-readable error description.
        detail: optional traceback or extended detail string.
    """
    payload: dict = {"error": message}
    if detail:
        payload["detail"] = detail
    emit(payload)


def setup_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog=PROGRAM_NAME,
        description=(
            "Look up a colour by name or hex value.\n\n"
            "Accepts a colour name (e.g. 'burnt orange', 'Sapphire') or a hex\n"
            "value with or without a leading '#' (e.g. '#ededed', 'ededed').\n\n"
            "When a name is given, returns the nearest matching hex value.\n"
            "When a hex value is given, returns the nearest named colour.\n\n"
            "All output is valid JSON and can be piped to jq."
        ),
        epilog=(
            "Examples:\n"
            f"  {PROGRAM_NAME} 'burnt orange'\n"
            f"  {PROGRAM_NAME} Sapphire\n"
            f"  {PROGRAM_NAME} '#ededed'\n"
            f"  {PROGRAM_NAME} ededed\n"
            f"  {PROGRAM_NAME} --url 'burnt orange'\n"
            f"  {PROGRAM_NAME} --map-file\n"
            f"  {PROGRAM_NAME} --dump-map-file\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "colour",
        metavar="COLOUR",
        help=(
            "Colour to look up. Can be a name ('burnt orange', 'Sapphire') or a "
            "hex value with or without a leading '#' ('#ededed', 'ededed')."
        ),
        nargs="?",
        default=None,
    )

    options = parser.add_argument_group("Options")
    options.add_argument(
        "--url",
        action="store_true",
        default=False,
        help=(
            "Include a browser-preview URL in the output. "
            "Opens https://www.colorhexa.com/<hex> to show a colour swatch, "
            "complementary colours, and RGB/HSL/HSV conversion values."
        ),
    )
    options.add_argument(
        "--map-file",
        action="store_true",
        default=False,
        help="Print the path to the colour mapping file as JSON and exit.",
    )
    options.add_argument(
        "--dump-map-file",
        action="store_true",
        default=False,
        help="Print the full contents of the colour mapping file as formatted JSON and exit.",
    )
    options.add_argument(
        "--debug",
        action="store_true",
        help="Enable detailed debug logging.",
    )

    return parser


async def map_colour(flags: argparse.Namespace) -> object:
    """Execute the colour lookup described by the parsed CLI flags.

    Args:
        flags: parsed argument namespace from ``setup_argument_parser``.

    Returns:
        A JSON-serialisable result dict, a ``ColourResult``, or ``None``
        when no colour argument was supplied.
    """
    mapper = ColourMapper()

    if flags.map_file:
        return {"path": str(mapper.mapping_file)}

    if flags.dump_map_file:
        with open(mapper.mapping_file, encoding="utf-8") as f:
            return json.load(f)

    if not flags.colour:
        return None

    result = mapper.get_colour_name(flags.colour)
    if not flags.url:
        return result

    d = dataclasses.asdict(result)
    hex_bare = result.hex_value.lstrip("#")
    d["url"] = f"https://www.color-hex.com/color/{hex_bare}"
    return d


async def main() -> None:
    flags = None
    try:
        parser = setup_argument_parser()
        flags = parser.parse_args()

        if not flags.map_file and not flags.dump_map_file and flags.colour is None:
            parser.print_help()
            sys.exit(1)

        result = await map_colour(flags)
        if result is not None:
            if isinstance(result, ColourResult):
                emit(dataclasses.asdict(result))
            elif isinstance(result, dict):
                emit(result)
            else:
                emit(result)

    except Exception as ex:
        detail = traceback.format_exc() if flags and flags.debug else None
        emit_error(str(ex), detail)
        sys.exit(1)


def _entry() -> None:
    """Sync entry point for the cm console script (pip install)."""
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        emit_error("interrupted")
        sys.exit(0)
    except Exception as ex:
        emit_error(f"Unexpected error: {ex}")
        sys.exit(1)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        emit_error("interrupted")
        sys.exit(0)
    except Exception as ex:
        emit_error(f"Unexpected error: {ex}")
        sys.exit(1)
