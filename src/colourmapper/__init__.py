"""colourmapper - bidirectional colour name <-> hex lookup.

Typical usage::

    from colourmapper import ColourMapper, ColourResult

    mapper = ColourMapper()
    result = mapper.get_colour_name("burnt orange")
    print(result.hex_value)   # "#c04e01"
"""

from colourmapper.ColourMapper import ColourMapper, ColourResult

__all__ = ["ColourMapper", "ColourResult"]
