# Contributing

Thank you for helping. Bug reports, new parts, and fixes to the rules are all welcome.

## Before you start

- For a bug, open an issue with the bug report form. Attach the SVG and the `CHECK` / `WARN` lines if you have them.
- For a new part or a large change, open an issue first so we can agree on the shape before you write code.
- Small fixes (typos, a wrong default, a missing test) can go straight to a pull request.

## Set up

You need Python 3 and Google Chrome, Chromium, or Microsoft Edge. Nothing else is installed.

```
python3 -m unittest discover -s tests -v   # run the tests
python3 examples/gen_examples.py           # redraw the README images
```

If the browser is not found, set `SVGPARTS_CHROME` to its executable. Set `SVGPARTS_CHROME_ARGS=--no-sandbox` where the browser sandbox is unavailable.

## Changing the parts library

The parts library is `plugins/svg-infographic/skills/svg-infographic/scripts/svgparts.py`. When you add or change a part:

1. Keep colors, sizes, and weights inside the part, following the rules in `SKILL.md`.
2. Use the gallery in `tests/test_svgparts.py`: add the part to one of the gallery slides with its default spacing. The tests require no warnings and no `check()` problems.
3. Add the part to the parts table in `SKILL.md`, and to "When to use icons and diagrams" if it is for a new kind of figure.
4. Redraw the README images with `python3 examples/gen_examples.py` and look at the PNGs.
5. Add an entry under `[Unreleased]` in `CHANGELOG.md`. Do not change `version`; it is bumped when a release is made.
6. If a public signature changed, run `python3 tests/test_api.py --update` and say so in the changelog entry.

## Changing the rules in SKILL.md

`SKILL.md` is what Claude reads. Write rules as plain instructions, and give a literal example when a rule could be misread. The wording rules apply to the skill's own text as well: no metaphors, and no numbers that change over time.

## Compatibility

The public API is what `svgparts.__all__` lists, the public methods of `Slide` and `Sketch` with their arguments, the theme keys (the color role names in `C`), and the problem kinds in `CHECK_KINDS`. Names that start with `_`, the `data-part` attributes in the SVG, and the text after the kind in a `check()` message are internal.

Versions follow [Semantic Versioning](https://semver.org/):

| Change | Version |
|--------|---------|
| A bug fix | patch |
| A new part, a new optional argument, a new icon, or a new problem kind | minor |
| A change to default spacing, colors, or the look of a part | minor |
| Removing or renaming a part, an argument, or a problem kind; changing the order of positional arguments | major |

The look of a figure can change in a minor release; the code that draws it keeps working. Before removing or renaming something, keep the old name for at least one minor release and make it emit a `DeprecationWarning`.

`tests/test_api.py` records every public signature in `tests/public_api.txt`, so an unintended change fails the tests.

## Releases

1. Move the `[Unreleased]` entries in `CHANGELOG.md` under a new version heading with the date.
2. Set `version` in `.claude-plugin/marketplace.json` (both places) and `plugins/svg-infographic/.claude-plugin/plugin.json`. The tests check that they match and that the changelog has the version.
3. Merge, then create a GitHub release `vX.Y.Z` from `main` with the changelog entry as the notes.

## Pull requests

- Use a [Conventional Commits](https://www.conventionalcommits.org/) title, such as `feat: add a funnel part` or `fix: wrap long lane names`. Pull requests are squash-merged, so the title becomes the commit message on `main`.
- The `unittest` check must pass. It runs on Ubuntu with Noto Sans CJK, so text widths differ from macOS.
- Images in pull requests and examples must not contain real customer data or anything confidential.

By contributing, you agree that your contribution is licensed under the [MIT License](LICENSE).
