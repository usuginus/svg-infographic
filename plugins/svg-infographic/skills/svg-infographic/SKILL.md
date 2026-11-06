---
name: svg-infographic
description: Draws business infographics (process flows, comparison tables, hierarchies, roadmaps, incident reviews, pull request walkthroughs) as a single slide-ready SVG, then converts it to PNG and checks how it looks before handing it over. Use it whenever the user asks to "make an infographic", "diagram this", "draw a flow chart", "turn this into a figure for a slide", "make it an image", or pastes a prompt that specifies SVG code, even if the skill is not named. Not for charts of numeric data (bar, line, etc.).
---

# SVG infographics

Organize text or business requirements into a single SVG that can be pasted straight into PowerPoint or a browser.
Renderers draw SVG differently, so **a figure is not done until it has been converted to PNG and checked by eye**.

## Steps

1. **Decide the message**: Write, in one sentence, the conclusion the viewer should take away. Use it as the slide heading.
2. **Pick the elements**: Choose the facts, steps, or comparison axes that support the conclusion. Put at most 3–5 items in one row. If there are more, ask the user whether to group them or split the figure.
3. **Decide the layout**: Choose the arrangement that fits the content. Do not force it into a fixed template. "Figure types and sizes" below is only a guide.
4. **Write the SVG**: Write a generator script in a temporary working directory using the parts library `scripts/svgparts.py` (see "Parts library"). Draw directly only what the library cannot, following the same color and weight rules.
5. **Convert to PNG and check**: `Slide.render()` (or `python3 scripts/svgparts.py render in.svg out.png`) uses a Chrome-family browser in headless mode to produce a PNG at 2× resolution. Open the PNG as an image, check the following, and fix and re-render if anything is wrong.
   - `save()` printed no "possible overflow" warnings. The warnings are based on estimated text width, so when one appears, confirm it in the PNG
   - Text does not touch the edges of cards or frames, and nothing overlaps
   - Arrows, lines, and shadows are drawn, and nothing is clipped at the edges
   - The browser is searched for in this order: Google Chrome, Chromium, Microsoft Edge. If none is found, ask the user to set the environment variable `SVGPARTS_CHROME` to the browser's executable
   - Do not use macOS `sips` or `qlmanage` for conversion. `sips` renders only two weights (≤500 as regular, ≥600 as heavy) and shifts `text-anchor="middle"` text to the right. `qlmanage` crops to a square. Use `sips` only when no browser is available at all, and tell the user that weights and centering will be wrong
6. **Hand it over**: Make the PNG visible to the user (display it if the environment can show images) and give the absolute paths of the SVG and PNG. Say what was included and what was left out. If the user asks for the code, also output the full SVG in an ```xml block.

## Parts library (scripts/svgparts.py)

Colors, font sizes, weights, and spacing are fixed inside the parts. Draw cards, arrows, badges, and so on with these parts so that every figure looks the same. To change the look, change the library.

Replace `<skill directory>` with the directory shown when the skill is loaded ("Base directory for this skill").

```python
import sys
sys.path.insert(0, "<skill directory>/scripts")
from svgparts import Slide, C

s = Slide("Figure title", "One sentence describing the figure (used as aria-label)")
s.header("A heading that states the conclusion", "Note at top right (ticket number, etc.)")
s.stats(60, [("Downtime", "About 15 min", C.ORANGE), ("Affected bookings", "120", C.TEXT)])
s.section(152, "Row heading")
s.flow(166, [("Heading", ["Description line 1", "Description line 2"], None), ("Result", ["…"], C.ORANGE)])
s.save("/path/out.svg")
s.render("/path/out.png")
```

| Part | Use |
|---|---|
| `header(title, meta)` | Slide heading and the note at top right |
| `section(y, title)` | Row heading |
| `stat` / `stats` | Label and value pair (`stats` lays them out in one row) |
| `flow(y, items)` | Boxes in a row joined by arrows. An accent color sets the border and heading color |
| `card` / `pill` / `status` / `bullets` | Card, number or category badge, status indicator, bullet list. Combine them to build custom cards |
| `table(x, y, w, headers, col_x, rows, highlight)` | Table. Rows in `highlight` get a light blue background |
| `steps(x, y, items)` | Numbered steps stacked vertically |
| `arrow` / `arrow_down` / `line` / `dot` / `numbered` | Lines and marks |
| `columns(n, gap)` | Width and x positions that split the area inside the side margins into n columns |
| `text(..., max_width=)` | Text. With `max_width`, warns about possible overflow |
| `icon(name, x, y, size, color)` | Line icon (see the list below) |
| `titled(x, y, icon, title)` | Card heading with an icon |
| `stat(..., icon=)` | Puts an icon on the right of a value card |
| `ratio(x, y, w, label, value, color, part_label, fraction)` | Card showing a total and the share of a part as one bar |
| `node(x, y, w, h, icon, title, sub, accent)` | Diagram element (person, system, data, etc.). Icon, name, and description, centered |
| `chain(y, items)` | Nodes in one row joined by arrows. Shows who or what something passes through |
| `connector(x1, y1, x2, y2, label=)` | Arrow in any direction. Use it to join nodes vertically or diagonally |
| `zone(x, y, w, h, label)` | Dashed frame marking an owner or environment. Put nodes inside (for example, the boundary between your own system and an external service) |
| `span(x1, x2, y, label, color)` | Bracket and label marking a range of elements in a row ("before the email is sent", "after it is sent", etc.) |
| `timeline(y, items)` | Events in time order at equal spacing. State in the row heading that spacing is not proportional to time |
| `decision` / `box` / `terminal` | Decision diagram parts: decision (light blue, rounded), process (rectangle), end (ACK, NACK, done, etc.; the color shows what the outcome means) |
| `elbow(pts)` / `edge_label(x, y, label)` | Arrow with right-angle bends, and a label such as "Yes" or "No" placed on an arrow (with a background fill so it does not sit on the line) |
| `sketch(x, y, w, h, xlabels, ylabel)` | Frame for a schematic. Draw with the returned `line` / `area` / `label` in 0–1 coordinates. Writes "Schematic (not actual values)" automatically |
| `scale(x, w, v0, v1)` / `band(x1, x2, y, h, color, label)` | A function that maps values to coordinates, and a band showing a time window or range. Use them to build a time-proportional axis |
| `range_bar(x, y, w, label, lo, hi, vmax, value)` | Horizontal bar from minimum to maximum |

There are 24 icons: `user` `users` `building` `server` `database` `laptop` `ai` `container` `wallet` `coin` `point` `warning` `check` `clock` `lock` `key` `document` `bell` `flag` `shield` `search` `funnel` `queue` `workflow`. Check their shapes with `python3 scripts/svgparts.py icons out.png`. To add a missing icon, add it to `ICONS` and check its shape in the catalog before using it (strokes only, inside 2–22 of a 24×24 grid).

## Basics of a readable slide

- **One message per slide.** The heading states the conclusion, not the topic ("Cause: bookings spiked on Monday morning and the search server hit its CPU limit", not "Cause").
- **Show the reading order with the layout.** Assume left to right, top to bottom. Place overview before detail, cause before effect.
- **Use three levels of size, weight, and color for importance.** Heading → row heading → card heading → description, each smaller and lighter. Elements at the same level look the same.
- **Align.** Align left edges, top edges, and spacing. Cards in the same row have the same width and height. Laying them out with `columns()` aligns them automatically.
- **Put related things close and unrelated things apart.** Spacing between cards (12px or more) and between rows (30px or more) is wider than line spacing inside a card (18–24px).
- **Give each color one meaning.** Orange is a problem, green is done or reached, blue is numbering and new items. Do not add other colors. Do not color things without a reason.
- **Use fewer words.** At most two lines of description per item. Write facts as short phrases, not sentences. Give numbers their units.
- **Do not add decoration.** No gradients or heavy shadows. Use icons and diagrams only when the rules in the next section call for them.
- **Use the source's terms.** Do not call the same thing by different names within a figure.

## When to use icons and diagrams

**Put one main diagram on each slide that shows the conclusion. Text cards support it.** If content you were about to write as bullets matches one of the following, draw it.

- **When to use a diagram**
  - Something passes between people, systems, or data, or goes through them in order → `chain` / `node` / `connector`; boundaries of owners or environments → `zone`
  - A procedure whose destination depends on a condition ("ACK if out of scope", "NACK on failure", etc.) → decision diagram (`decision` / `box` / `terminal` / `elbow` / `edge_label`). Do not write a procedure with several exits as bullets
  - Behavior changes by category (error categories, etc.) → arrows from category to behavior to result. Draw retries as a loop with `elbow`
  - The point is how a quantity changes over time, or the gap to a limit (backlog, capacity versus load, etc.) → schematic (`sketch`). State in the figure that it is not real data
  - The point is how times or time windows overlap → time-proportional axis (`scale` / `band`). Use the equally spaced `timeline` only to show the order of events
  - The point is the size of a range (response time 120–300 ms, etc.) → `range_bar`. Make charts that compare values precisely with a charting library or skill
  - The point is a share of a whole → `ratio`
  - Boundaries of a range ("before the email is sent" and "after it is sent", etc.) → `span`
  - Differences before and after a change → cards side by side, coloring only the parts that changed
  - Use rows of text boxes (`flow`) for procedures without branches and for chains of causes
- **How to draw arrows**
  - Arrows are at least 28px long (`elbow` and `connector` warn when they are shorter). Short arrows squash the head and hide the direction. When placing nodes side by side, leave at least 40px between them
  - When a label or icon sits above or below an arrow, make the gap at least the label width plus 20px. Use circled numbers only when they do not clash with another numbering in the same figure
  - Do not put labels such as "Yes" or "No" on top of the line. Put them to the right of a vertical arrow and above a horizontal arrow
  - In decision diagrams, decide the spacing between elements first, then place the elements. Make elements shorter if needed to keep arrows long enough
- **Do not include numbers that change over time**: customer counts, order counts, percentages, current settings (rps, etc.), and durations differ depending on when the figure is viewed. Specified values (expiry periods, retention periods, etc.) are fine. When showing a measured value as the basis for a decision, write in the figure when it was measured and that it will change
- **What to keep as text**: lists of conditions or notes ("what counts as an incident", etc.). A diagram adds no information
- **When to add icons**
  - Only on elements where telling the kind apart speeds up understanding (people, systems, money, status, time). Not on every card
  - At most one icon per element
  - In the same figure, use the same icon for the same thing, and never the same icon for different things
  - Use the secondary text color (`C.SUB`). Only elements you want to emphasize use their accent color (orange or green)
  - Size 22–24px. Icons must not stand out more than the text
- **What not to use**
  - Photos, illustrations, or images from image-generation AI. They do not match in style and their text cannot be edited
  - External icon sets. If you use one, check its license and get the user's permission before downloading any file

## Wording

- **Do not use metaphors.** Use literal wording, even if it takes more words.
  - "Respond to the outage", not "fight the fire". "Decide who does what and in which order", not "direct traffic". "Speed up the slowest step", not "crush the bottleneck". "Two main features", not "two flagship pillars".
  - Even if the source uses a metaphor such as "turbocharge", rewrite it in the figure as, for example, "halve the processing time".
- Do not personify ("the system protected us") or blur degree ("quite", "significantly"). If there is a number, write the number.
- Write the message you send with the figure by the same rules.
- Write the text in the figure in the user's language.

## Figure types and sizes

| Type | Examples | Size |
|---|---|---|
| Process flow | Horizontal steps, branches, swimlanes | 960×240–320 |
| Roadmap | Quarterly timeline, milestones by phase | 960×240–320 |
| Comparison table | Feature comparison, pricing plans, pros and cons | 960×540 |
| Hierarchy, pyramid | Org chart, strategy layers, DIKW | 960×540 |
| Explainer slide | Incident review, pull request changes, overview of an initiative | 960×540 |

- Use 960×540 (16:9) as the default for a figure that fills one slide. At 800 wide, the slide has empty space on both sides and the same font size looks cramped.
- Use about 24px outer margin and 20px card padding (16px for five boxes in a row).
- Always set a `viewBox` equal to `width` / `height` (the library does this automatically).

## Colors

| Role | Color | Library |
|---|---|---|
| Primary (number badges, new items) | `#2563EB` | `C.PRIMARY` |
| Accent: problems, points of attention | `#F97316` | `C.ORANGE` |
| Accent: done, reached | `#10B981` | `C.GREEN` |
| Background | `#F8FAFC` | `C.BG` |
| Card | `#FFFFFF`, border `#E2E8F0` | `C.CARD` / `C.LINE` |
| Primary text | `#1E293B` | `C.TEXT` |
| Secondary text | `#64748B` | `C.SUB` |
| Arrows, connectors | `#94A3B8` | `C.ARROW` |

If the user specifies colors, use theirs.

## Text

- Font: `'Hiragino Sans', 'Yu Gothic UI', 'Noto Sans JP', system-ui, sans-serif`. With `system-ui` alone, Japanese text falls back to inconsistent fonts on Windows.
- Sizes: heading 20px, row heading 15px, card heading 14–15px, values 16px, descriptions 12–13px. **Never go below 12px** (it becomes unreadable when the slide is scaled down or projected).
- Weights: **never use 700**. At 700, CJK text is heavy and the whole figure looks dark.
  - 600: headings, row headings, card headings, and badges only
  - 500: values and secondary labels
  - 400: descriptions
  - Emphasize with color rather than weight. When many elements are bold, it is no longer clear what matters.
- **SVG does not wrap text.** Decide line breaks yourself and call `text()` once per line.
  - Estimate width as font-size px per full-width (CJK) character and 0.62 × font-size px per half-width character (`text_width()`).
  - Do not break in the middle of a word. In Japanese, break after a particle or after "・".

## Rendering compatibility (things that differ between renderers)

- **Do not use `<marker>`.** sips did not draw the arrowheads. Draw the line and head of an arrow as one `<path>` (`arrow()`).
- Write colors and sizes directly as element attributes. CSS classes in `<style>` do not work in some renderers, such as PowerPoint.
- Shadows (`feDropShadow`) render in Chrome and sips but are ignored by some renderers. Cards also get a border so they stay distinct without the shadow (`card()`).
- Do not use external images (`<image href>`), external fonts, or `<foreignObject>`. Draw icons with `<rect>`, `<circle>`, `<path>`, and `<polygon>`.
- Put a one-sentence description of the figure in `<title>` and `aria-label` (the arguments of `Slide()`).
