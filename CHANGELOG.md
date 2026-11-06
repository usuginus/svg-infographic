# Changelog

All notable changes to this project are recorded here. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and versions follow the policy in [CONTRIBUTING.md](CONTRIBUTING.md#compatibility).

## [Unreleased]

### Added
- `svgparts.__all__` and `CHECK_KINDS`, which define the public API and the kinds of problems `check()` reports.
- Tests that record the public API signatures and keep the plugin and marketplace versions in step.
- This changelog and a compatibility policy in CONTRIBUTING.md.
- Named items for the parts' arguments (`Stat`, `FlowStep`, `ChainNode`, `Event`, `Step`, `Actor`, `Message`, `Action`, `Lane`, `LaneStep`, `TreeNode`, `Bar`, `RoadmapRow`). Plain tuples still work, and optional fields can be left out.
- `swimlane` steps take an icon as an optional fifth field.
- Type hints on the public functions and methods, and a lint step (ruff) in CI.
- README.ja.md, a Japanese intro image, and a note in the issue forms that Japanese is welcome.

### Changed
- `wrap()` keeps katakana words whole, avoids starting a line with hiragana (a particle or the rest of a word), prefers a break after punctuation when the line is at least 70% full, and keeps a particle on the same line as the closing bracket before it.

## [1.4.0] - 2026-11-06

### Added
- Icons in boxes (`box(..., icon=)`), table rows (`row_icons`), sequence actors, tree nodes, `rule_row`, and `before_after`.
- Per-row highlight colors in `table(highlight={row: color})`.
- `tint()`: elements drawn with an accent color also get its light background.

### Changed
- Table headers have a shaded row.
- The README images explain the skill and are drawn with it.

## [1.3.0] - 2026-11-06

### Added
- `swimlane`, `before_after`, `tree`, and `roadmap`.
- Color themes: `Slide(..., theme={"PRIMARY": "#7C3AED"})`.
- `box()` wraps a long title to two lines.

### Fixed
- `check()` measures the vertical extent of text from the baseline, so fonts with a large line height (Noto Sans CJK) no longer report overlapping text.

## [1.2.0] - 2026-11-06

### Added
- `sequence`, `rule_row`, and `action_list`.

## [1.1.0] - 2026-11-06

### Added
- `check()`: measures the SVG in a headless browser and reports layout problems. `render()` runs it.
- `wrap()` and `paragraph()`; descriptions in `flow`, `chain` / `node`, and `timeline` can be a string.
- `SVGPARTS_CHROME_ARGS`, and Noto Sans CJK JP in the font stack.
- Unit tests and a GitHub Actions workflow.

### Changed
- ASCII text widths come from a measured per-character table.

### Fixed
- `Slide.render()` always saves the SVG, so a stale file is never rendered.

## [1.0.0] - 2026-11-05

### Added
- The svg-infographic skill and the svgparts parts library.

[Unreleased]: https://github.com/usuginus/svg-infographic/compare/v1.4.0...HEAD
[1.4.0]: https://github.com/usuginus/svg-infographic/releases/tag/v1.4.0
