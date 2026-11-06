# svg-infographic

A [Claude Code](https://docs.claude.com/en/docs/claude-code) skill that draws business infographics (process flows, comparison tables, timelines, incident reviews, and more) as a single slide-ready SVG. Claude converts each figure to PNG and checks it for overflowing text and overlaps before handing it over.

![Process flow example](examples/example-1-flow.png)

| Comparison table | Incident review |
|---|---|
| ![Comparison table example](examples/example-2-compare.png) | ![Incident review example](examples/example-3-incident.png) |

All examples are fictional. The script that draws them is [examples/gen_examples.py](examples/gen_examples.py).

## Features

- **The heading states the conclusion**: "Cause: a Monday spike maxed out the search server's CPU", not "Cause". Each slide carries one message.
- **Drawn with a parts library**: cards, arrows, tables, timelines, steps, zones, icons, and more live in a Python parts library ([svgparts.py](plugins/svg-infographic/skills/svg-infographic/scripts/svgparts.py)). Colors, font sizes, and weights are fixed inside the library, so every figure looks consistent.
- **Checked with real fonts**: after rendering, the library opens the SVG in the browser and measures it. It reports text that overflows or crosses the edge of a card, overlapping text, arrows or lines that cross text, and arrows that enter a box. Claude then looks at the PNG for spacing and balance.
- **Wraps text**: descriptions can be given as a single string and are wrapped to fit. English breaks at spaces; Japanese breaks after punctuation or particles and follows Japanese line-breaking rules.
- **No metaphors**: wording such as "fight the fire" or "turbocharge" is rewritten literally, as "respond to the outage" or "halve the processing time".
- **Works for CJK text**: full-width and half-width characters are measured separately, and the font stack and weights are chosen so that Japanese text stays legible.

## Requirements

- Claude Code
- Python 3 (standard library only)
- A browser for PNG conversion: Google Chrome, Chromium, or Microsoft Edge
  - If none is found automatically, set the environment variable `SVGPARTS_CHROME` to the browser's executable
- For Japanese text, one of Hiragino Sans, Yu Gothic UI, or Noto Sans JP

## Install

Run these two commands in Claude Code:

```
/plugin marketplace add usuginus/svg-infographic
/plugin install svg-infographic@svg-infographic
```

## Usage

Give Claude the content and ask for a figure. The skill is used even if you do not name it, for requests such as:

- "Diagram the processing flow in this design doc"
- "Turn the comparison of these three options into a figure for a slide"
- "Summarize the incident timeline and follow-up actions in one infographic"

Claude decides the message, chooses a layout, writes the SVG with the parts library, and converts it to PNG to check it. It then gives you the paths of the SVG and PNG.

You can also use the parts library directly, without the skill:

```python
import sys
sys.path.insert(0, "plugins/svg-infographic/skills/svg-infographic/scripts")
from svgparts import Slide, C

s = Slide("Figure title", "One sentence describing the figure")
s.header("A heading that states the conclusion", "Note")
s.flow(120, [
    ("Receive", ["Take the application"], None),
    ("Review", ["Check the details"], C.PRIMARY),
    ("Notify", ["Email the result"], C.GREEN),
])
s.render("out.png")   # also writes out.svg and prints any layout problems
```

To check an SVG made some other way, run `python3 svgparts.py check in.svg`. To see all icons, run `python3 svgparts.py icons icons.png`.

## Tests

```
python3 -m unittest discover -s tests -v
```

The tests draw every part with its default spacing and require no warnings and no layout problems. Tests that need a browser are skipped when none is found. GitHub Actions runs them on Ubuntu with Noto Sans CJK.

## Layout

```
.claude-plugin/marketplace.json          # marketplace definition
plugins/svg-infographic/
  .claude-plugin/plugin.json             # plugin definition
  skills/svg-infographic/
    SKILL.md                             # steps and rules
    scripts/svgparts.py                  # parts library
examples/                                # examples and the script that draws them
tests/                                   # unit tests
```

## License

[MIT](LICENSE)
