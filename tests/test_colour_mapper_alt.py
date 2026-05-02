"""Integration tests against the real bundled colour map."""

import pytest

from colourmapper.ColourMapper import ColourMapper


@pytest.fixture(scope="module")
def mapper() -> ColourMapper:
    """Single shared mapper backed by the real bundled colour map."""
    return ColourMapper()


class TestInitColourMap:
    def test_red_in_map(self, mapper: ColourMapper) -> None:
        assert mapper.name_to_hex["Red"].lower() == "#ff0000"

    def test_dark_red_in_map(self, mapper: ColourMapper) -> None:
        assert mapper.name_to_hex["DarkRed"].lower() == "#840000"

    def test_hex_to_name_red(self, mapper: ColourMapper) -> None:
        assert mapper.hex_to_name["#ff0000"].lower() == "red"


class TestHexify:
    def test_valid_inputs(self) -> None:
        assert ColourMapper.hexify("FF0000") == "#ff0000"
        assert ColourMapper.hexify("#FF0000") == "#ff0000"
        assert ColourMapper.hexify("f00") == "#ff0000"
        assert ColourMapper.hexify("#f00") == "#ff0000"

    def test_invalid_inputs(self) -> None:
        assert ColourMapper.hexify("XYZ") is None
        assert ColourMapper.hexify("#ZZZZZZ") is None
        assert ColourMapper.hexify("12345") is None
        assert ColourMapper.hexify("") is None

    def test_hex_to_rgb(self) -> None:
        assert ColourMapper.hex_to_rgb("FF0000") == (255, 0, 0)
        assert ColourMapper.hex_to_rgb("#00FF00") == (0, 255, 0)
        assert ColourMapper.hex_to_rgb("0000ff") == (0, 0, 255)


class TestClosestColour:
    def test_exact_red(self, mapper: ColourMapper) -> None:
        closest_hex, closest_name = mapper.get_closest_colour("#FF0000")
        assert closest_hex.lower() == "#ff0000"
        assert closest_name.lower() == "red"

    def test_near_red(self, mapper: ColourMapper) -> None:
        _, closest_name = mapper.get_closest_colour("#FF0003")
        assert closest_name.lower() == "fire engine red"

    def test_purple_returns_something(self, mapper: ColourMapper) -> None:
        _, closest_name = mapper.get_closest_colour("#7F007F")
        assert closest_name is not None


class TestColourNameByName:
    def test_redcurrant(self, mapper: ColourMapper) -> None:
        result = mapper.get_colour_name("Redcurrant")
        assert result.found is True
        assert result.hex_value == "#88455e"
        assert result.name == "redcurrant"

    def test_case_insensitive(self, mapper: ColourMapper) -> None:
        result = mapper.get_colour_name("RedCUrRant")
        assert result.found is True
        assert result.hex_value == "#88455e"

    def test_dark_red_no_space(self, mapper: ColourMapper) -> None:
        result = mapper.get_colour_name("DarkRed")
        assert result.found is True
        assert result.hex_value == "#8b0000"


class TestColourNameByHex:
    def test_uppercase_hex(self, mapper: ColourMapper) -> None:
        result = mapper.get_colour_name("#FF0000")
        assert result.found is True
        assert result.name.lower() == "red"

    def test_lowercase_hex(self, mapper: ColourMapper) -> None:
        result = mapper.get_colour_name("#ff0000")
        assert result.found is True
        assert result.name.lower() == "red"

    def test_no_hash(self, mapper: ColourMapper) -> None:
        result = mapper.get_colour_name("FF0000")
        assert result.found is True
        assert result.name.lower() == "red"

    def test_shorthand(self, mapper: ColourMapper) -> None:
        result = mapper.get_colour_name("#F00")
        assert result.found is True
        assert result.name.lower() == "red"


class TestColourNameClosestMatch:
    def test_near_red(self, mapper: ColourMapper) -> None:
        result = mapper.get_colour_name("#FE0000")
        assert result.found is True
        assert result.name.lower() == "red"

    def test_unknown_name_not_found(self, mapper: ColourMapper) -> None:
        result = mapper.get_colour_name("Dingdong")
        assert result.found is False
        assert result.name == "dingdong"


class TestMissingMappingFile:
    def test_missing_file_raises(self, tmp_path) -> None:  # type: ignore[no-untyped-def]
        with pytest.raises(ColourMapper.MissingMappingFile):
            ColourMapper(mapping_file=tmp_path / "does_not_exist.json")
