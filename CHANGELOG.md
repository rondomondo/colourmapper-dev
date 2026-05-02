# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0] - 2024-01-01

### Added
- Bidirectional colour name <-> hex lookup backed by ~30K curated colour names
- Nearest-colour fallback using CIE Lab delta-E distance
- `cm` CLI entry point for colour lookup
- `mapping-file-create` CLI entry point for building custom mapping files
- Bundled mapping sources: named colours, Crayola, xkcd RGB
- Pure stdlib core with no runtime dependencies
