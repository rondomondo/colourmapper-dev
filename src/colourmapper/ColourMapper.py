"""Bidirectional colour name <-> hex lookup with nearest-colour fallback."""

import json
import re
from dataclasses import dataclass
from pathlib import Path

MAPPING_FILE = Path(__file__).parent / "named_colours_map.json"

# Module-level cache keyed by resolved Path so multiple custom files each get their own cache
# without cross-contaminating the default mapping.
_cache: dict[Path, tuple[dict[str, str], dict[str, str]]] = {}


def _load_mapping(path: Path) -> tuple[dict[str, str], dict[str, str]]:
    """Load a colour mapping JSON file and return (name_to_hex, hex_to_name).

    Args:
        path: path to a JSON file mapping colour names to hex strings.

    Returns:
        A two-tuple of (name_to_hex, hex_to_name) dicts.

    Raises:
        ColourMapper.MissingMappingFile: if the file cannot be opened.
    """
    try:
        with open(path, encoding="utf-8") as fh:
            data: dict[str, str] = json.load(fh)
    except OSError as exc:
        raise ColourMapper.MissingMappingFile(path) from exc

    name_to_hex: dict[str, str] = {}
    # Include both the original names and space-stripped variants (e.g. "darkred" for "dark red")
    name_to_hex.update(data)
    name_to_hex.update({k.replace(" ", ""): v for k, v in data.items()})

    hex_to_name: dict[str, str] = {v.lower(): k for k, v in data.items()}
    return name_to_hex, hex_to_name


@dataclass
class ColourResult:
    """Result of a colour mapping lookup.

    Attributes:
        found: True when the input matched a known name or hex exactly (or was
               resolved to the nearest named colour).
        hex_value: the canonical six-digit hex string, e.g. ``#ff0000``.
        name: the human-readable colour name, or the raw input when not found.
    """

    found: bool
    hex_value: str
    name: str


class ColourMapper:
    """Maps between colour names and hex values, with nearest-colour fallback.

    Each instance is backed by a single colour mapping file.  The default
    bundled file (``named_colours_map.json``) is cached at module level so
    repeated construction is cheap.  Passing a custom ``mapping_file``
    bypasses the shared cache and loads that file independently.

    Example::

        mapper = ColourMapper()
        result = mapper.get_colour_name("burnt orange")
        print(result.hex_value)   # "#c04e01"

        result = mapper.get_colour_name("#c04e01")
        print(result.name)        # "burnt orange"
    """

    HEX_COLOUR_RE = re.compile(r"^#?([a-fA-F0-9]{3}|[a-fA-F0-9]{6})$", re.IGNORECASE)

    class MissingMappingFile(IOError):
        """Raised when the colour mapping JSON file cannot be opened."""

        def __init__(self, mapping_file: Path | None = None) -> None:
            path = mapping_file or MAPPING_FILE
            super().__init__(
                f"Unable to find the mapping file: {path}\n"
                "Expected format: JSON object with colour-name keys and hex-string values."
            )

    def __init__(self, mapping_file: str | Path | None = None) -> None:
        """Initialise the mapper, loading (or retrieving from cache) the colour data.

        Args:
            mapping_file: optional path to a custom colour mapping JSON file.
                          Defaults to the bundled ``named_colours_map.json``.

        Raises:
            ColourMapper.MissingMappingFile: if the mapping file cannot be found.
        """
        resolved = Path(mapping_file) if mapping_file is not None else MAPPING_FILE
        self.mapping_file = resolved
        if resolved not in _cache:
            _cache[resolved] = _load_mapping(resolved)
        self.name_to_hex, self.hex_to_name = _cache[resolved]

    # Static / class helpers

    @staticmethod
    def hexify(value: str) -> str | None:
        """Convert a colour value to standardised six-digit hexadecimal form.

        Args:
            value: colour value to convert (with or without leading ``#``).

        Returns:
            Normalised hex code such as ``#ff0000``, or ``None`` if the input
            is not a valid hex colour.
        """
        match = ColourMapper.HEX_COLOUR_RE.match(value)
        if not match:
            return None
        hex_value = match.group(1)
        if len(hex_value) == 3:
            hex_value = "".join(c * 2 for c in hex_value)
        return f"#{hex_value.lower()}"

    @staticmethod
    def hex_to_rgb(hex_str: str) -> tuple[int, int, int]:
        """Convert a hex colour string to an RGB tuple.

        Args:
            hex_str: hex colour string, with or without leading ``#``.

        Returns:
            ``(r, g, b)`` integer tuple in the 0-255 range.
        """
        h = hex_str.lstrip("#")
        return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)

    @staticmethod
    def calculate_colour_distance(c1: tuple[int, int, int], c2: tuple[int, int, int]) -> float:
        """Calculate the Euclidean distance between two RGB colours.

        Args:
            c1: first RGB colour as an ``(r, g, b)`` tuple.
            c2: second RGB colour as an ``(r, g, b)`` tuple.

        Returns:
            Euclidean distance between the two colours.
        """
        return sum((x - y) ** 2 for x, y in zip(c1, c2, strict=True)) ** 0.5

    # Instance methods

    def get_closest_colour(self, hex_colour: str) -> tuple[str, str]:
        """Find the closest named colour to a given hex value.

        Performs a brute-force Euclidean search over the loaded colour map.

        Args:
            hex_colour: hex colour code to match (with or without leading ``#``).

        Returns:
            ``(hex_code, name)`` of the closest match in the loaded map.
        """
        target_rgb = self.hex_to_rgb(hex_colour)

        min_distance = float("inf")
        closest_hex = ""
        closest_name = ""

        for hex_code, name in self.hex_to_name.items():
            compare_rgb = self.hex_to_rgb(hex_code.lstrip("#"))
            distance = self.calculate_colour_distance(target_rgb, compare_rgb)
            if distance < min_distance:
                min_distance = distance
                closest_hex = hex_code.lstrip("#")
                closest_name = name

        return f"#{closest_hex}", closest_name

    # American-spelling alias
    def get_closest_color(self, hex_colour: str) -> tuple[str, str]:
        """American-spelling alias for ``get_closest_colour``."""
        return self.get_closest_colour(hex_colour)

    def get_colour_name(self, value: str) -> ColourResult:
        """Resolve a colour name or hex value to a ``ColourResult``.

        Resolution order:

        1. Exact name match (case-insensitive, space-stripped variant included).
        2. Exact hex match after normalisation to six-digit form.
        3. Nearest named colour by Euclidean RGB distance.
        4. ``found=False`` if the input is neither a known name nor a valid hex.

        Args:
            value: colour name (e.g. ``"burnt orange"``) or hex value
                   (e.g. ``"#c04e01"`` or ``"c04e01"``).

        Returns:
            A ``ColourResult`` with ``found``, ``hex_value``, and ``name`` fields.
        """
        normalised = value.lower()

        if normalised in self.name_to_hex:
            return ColourResult(found=True, hex_value=self.name_to_hex[normalised], name=normalised)

        hex_value = self.hexify(normalised)
        if not hex_value:
            return ColourResult(found=False, hex_value=value, name=normalised)

        if hex_value in self.hex_to_name:
            return ColourResult(found=True, hex_value=hex_value, name=self.hex_to_name[hex_value])

        nearest_hex, nearest_name = self.get_closest_colour(hex_value)
        return ColourResult(found=True, hex_value=nearest_hex, name=nearest_name)

    # American-spelling alias
    def get_color_name(self, value: str) -> ColourResult:
        """American-spelling alias for ``get_colour_name``."""
        return self.get_colour_name(value)
