# Project

This CLAUDE.md applies to all projects and directories (including subdirectories) that contain this file,
unless a path is excluded by `.claudeignore`.

## Context exclusions

A `.claudeignore` file in the project root lists glob patterns for paths Claude should not read or index
(dependencies, build output, secrets, large data files, etc.). Treat `.claudeignore` as authoritative:
if a path matches, do not read or summarise its contents.

## Memory

Project-level memories are stored under `~/.claude/projects/` and loaded automatically. Global preferences
and cross-project rules live in `~/.claude/`. When a task references prior decisions or past context,
check those memory files before asking the user to re-explain.

## Writing style

- Never use em dashes (--); use commas, parentheses, hyphens, or separate sentences instead
- British spelling: `realise` not `realize`, `colour` not `color`, etc.
- Stay within the ASCII character set
- No comments explaining what code does -- only why (hidden constraints, non-obvious invariants)
- No unnecessary `**kwargs` silently ignored without a docstring note

## Code style

- `ruff` for linting/formatting (`line-length = 119`)
- `mypy` with `strict = false` and `ignore_missing_imports = true`
- Line length: 119 characters max
- Python 3.12+ with full type annotations
- Import order: standard lib, third-party, local
- Naming: `snake_case` for functions/variables, `PascalCase` for classes
- Use Pydantic v2 for data validation and schemas
- Use FastAPI for HTTP endpoints

## Section comments

Use plain section headings without decorator lines:

```python
# Section title
```

Not:

```python
# ---------------------------------------------------------------------------
# Section title
# ---------------------------------------------------------------------------
```

The dashes cause rendering problems in some editors and CI log viewers.

## Docstrings: Google style

All public functions must have Google-style docstrings.

```python
def fn(url: str, overwrite: bool = False) -> dict:
    """One-line summary

    Optional longer description when intent is non-obvious.

    Args:
        url: The redirect destination URL.
        overwrite: When True, silently replace an existing key.

    Returns:
        A dict suitable for passing to put_object as extra kwargs.

    Raises:
        ValueError: If url uses an unsupported scheme.
    """
```

Rules:

- First line is a short imperative summary with no trailing period
- `Args:`, `Returns:`, `Raises:` sections only when present
- Parameter descriptions start lowercase
- Omit obvious sections (no `Returns:` on a `None`-returning function)

## Type hints

- All public function signatures must have full type hints
- Buffer parameters should be typed `Optional[BytesIO]` or `Union[BytesIO, bytes, str, Path]` as
  appropriate -- not `Optional[bytes]`
- `from __future__ import annotations` is not currently used; explicit imports from `typing` are required
  for Python <3.10 compat syntax

## Running tests

```bash
python -m pytest
```

Test location and `pythonpath` settings are configured in `pyproject.toml`. Check that file for the
canonical pytest root and any path configuration before adjusting test commands.

## Mermaid diagrams

For flowchart and related diagram types:

- Use `<br>` instead of `\n` for line breaks inside node labels:

    ```
    flowchart LR
        CM["ConfigManager<br>config.yaml"]
    ```

- Wrap connecting label text with `<br>` and `&nbsp;` for padding:

    ```
    CM -->|"<b>&nbsp;merged opts&nbsp;</b>"| QCM
    ```
