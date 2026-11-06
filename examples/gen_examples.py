"""Draw the images shown in the README. Each one explains the skill and is itself drawn with the skill.

    python3 examples/gen_examples.py
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "plugins", "svg-infographic", "skills", "svg-infographic", "scripts"))
from svgparts import Slide, C  # noqa: E402


def done(s, name):
    print(s.render(os.path.join(HERE, f"{name}.png")))


# ---- Intro: how the skill works ----
s = Slide("How svg-infographic works", "Claude decides the message, draws with a parts library, measures the result "
          "in a browser, and hands over the SVG and PNG")
s.header("Claude draws the slide, then measures it before you see it", "svg-infographic")
s.section(84, "From your request to a checked figure")
w, xs = s.chain(104, [
    ("document", "Decide", "One conclusion as the heading", None),
    ("workflow", "Lay out", "Pick the figure type that fits", None),
    ("container", "Draw", "Parts fix colors, sizes, and weights", None),
    ("search", "Measure", "Real fonts in a headless browser", C.PRIMARY),
    ("check", "Deliver", "SVG and PNG, ready for slides", C.GREEN),
], h=112)
draw_x, measure_x = xs[2] + w / 2, xs[3] + w / 2
s.elbow([(measure_x, 222), (measure_x, 250), (draw_x, 250), (draw_x, 222)], C.PRIMARY)
s.text((draw_x + measure_x) / 2, 272, "Problems found: fix and render again", 12, C.PRIMARY, 500, "middle",
       max_width=s.W - 2 * s.M)
s.section(312, "What every figure gets")
cw, cxs = s.columns(3, 12)
for x, (icon, title, desc) in zip(cxs, [
    ("flag", "Conclusion first", "The heading states what the viewer should take away, not the topic."),
    ("search", "Measured, not guessed", "Overflow, overlaps, and arrows over text are found with the real fonts."),
    ("document", "Literal wording", "No metaphors. One meaning per color. Numbers that change over time stay out."),
]):
    s.card(x, 328, cw, 130)
    s.titled(x + s.PAD, 362, icon, title)
    s.paragraph(x + s.PAD, 392, cw - 2 * s.PAD, desc, 13, C.SUB, max_lines=3)
s.text(s.M, 496, "Ask for a figure in plain words. The skill is used even if you do not name it.", 13, C.SUB,
       max_width=s.W - 2 * s.M)
done(s, "intro")


# ---- Gallery 1: the check loop as a sequence diagram ----
s = Slide("The check loop", "Order of messages between you, Claude, the parts library, and the browser")
s.header("Claude fixes the layout until the browser reports nothing", "Sequence diagram")
_, bottom = s.sequence(70, [
    ("you", "You", None, None),
    ("claude", "Claude", None, C.PRIMARY),
    ("parts", "svgparts", "parts library", None),
    ("browser", "Browser", "headless", None),
], [
    ("you", "claude", "Diagram this design doc", None),
    ("claude", "parts", "Write the figure with parts", None),
    ("parts", "browser", "Render the PNG and run check()", None),
    ("browser", "claude", "Overflow in one card", C.ORANGE),
    ("claude", "parts", "Shorten the text and render again", None),
    ("browser", "claude", "No problems found", C.GREEN),
    ("claude", "you", "SVG, PNG, and what was left out", C.GREEN),
], step=36)
s.bullets(s.M, bottom + 36, s.W - 2 * s.M, [
    "render() runs check() automatically, so every figure is measured before it is shown",
    "Spacing and balance are still judged by eye in the PNG",
], step=26)
done(s, "gallery-1-sequence")


# ---- Gallery 2: before and after the skill ----
s = Slide("Before and after the skill", "The same figure rules, with and without the skill")
s.header("Every figure follows the same rules", "Before and after")
y = s.before_after(70, [
    "Heading names the topic",
    ("Metaphors such as \"fight the fire\"", True),
    ("Text runs past the edge of a card", True),
    ("Colors picked anew for each figure", True),
], [
    "Heading states the conclusion",
    ("Literal words: \"respond to the outage\"", True),
    ("Overflow is measured and fixed", True),
    ("Orange is a problem, green is done", True),
], titles=("Without the skill", "With the skill"))
s.section(y + 40, "The same text, written both ways")
hw = (s.W - 2 * s.M - 64) / 2
for row, (before_label, before_text, after_label, after_text) in enumerate([
    ("Topic", "Cause", "Conclusion", "Cause: bookings pushed CPU to 100%"),
    ("Metaphor", "We fought the fire all morning", "Literal", "We restored search by 9:20"),
]):
    ry = y + 56 + row * 90
    for x, label, text, color in [(s.M, before_label, before_text, None),
                                  (s.M + hw + 64, after_label, after_text, C.GREEN)]:
        s.card(x, ry, hw, 76, color or C.LINE)
        s.text(x + s.PAD, ry + 26, label, 12, C.SUB, 500)
        s.text(x + s.PAD, ry + 56, text, 16, C.TEXT, 600, max_width=hw - 2 * s.PAD)
    s.connector(s.M + hw + 14, ry + 38, s.M + hw + 50, ry + 38)
done(s, "gallery-2-before-after")


# ---- Gallery 3: what check() finds ----
s = Slide("What check() finds", "Problems check() reports with the real fonts, and what is still checked by eye")
s.header("check() finds what an estimate of text width cannot", "Comparison")
s.table(s.M, 70, s.W - 2 * s.M, ["Problem", "What it means", "Typical fix"], [16, 230, 600], [
    ("Overflow", "Text is wider than the space given to it", "Shorten it or let it wrap"),
    ("Crosses a box edge", "Text starts inside a card and ends outside", "Move it or widen the card"),
    ("Overlapping text", "Two pieces of text share the same space", "Add spacing between rows"),
    ("Line or arrow on text", "A line crosses or touches a label", "Move the label beside the line"),
    ("Arrow enters a box", "An arrow runs into a card it does not point to", "Route it around the card"),
    ("Filled area over text", "A shaded area in a schematic covers a label", "Move the label off the area"),
    ("Outside the canvas", "Text is cut off at the edge of the slide", "Move it inside the margins"),
], row_h=34)
s.section(400, "What is still checked by eye")
s.rule_row(s.M, 418, s.W - 2 * s.M, "check() reports nothing", "Open the PNG and look at it",
           "No overflow, overlap, or arrow problems", "Spacing, balance, and whether the message is clear", C.GREEN)
done(s, "gallery-3-check")


# ---- Gallery 4: the parts, as a tree ----
s = Slide("The parts library", "Parts of svgparts grouped by what they draw")
s.header("Every part belongs to one of four groups", "Hierarchy")
y = s.tree(64, ("svgparts", "Python standard library only", [
    ("Text and cards", None, [], None),
    ("Flows and diagrams", None, [], C.PRIMARY),
    ("Time and ranges", None, [], None),
    ("Rules and changes", None, [], None),
], None), box_w=200)
gw, gxs = s.columns(4, 16)
for x, parts in zip(gxs, [
    ["header, section", "text, paragraph", "card, pill, status", "stat, stats", "table", "action_list"],
    ["flow, chain, node", "zone, connector", "decision, box, terminal", "swimlane", "sequence", "tree"],
    ["timeline", "roadmap", "sketch, scale, band", "range_bar", "ratio"],
    ["rule_row", "before_after", "steps", "bullets", "icon"],
]):
    s.card(x, y + 20, gw, 200)
    s.bullets(x + s.PAD, y + 52, gw - 2 * s.PAD, parts, 13, step=28)
s.text(s.M, y + 256, "Each part fixes its colors, sizes, and spacing, and warns when its text may not fit.", 13, C.SUB,
       max_width=s.W - 2 * s.M)
done(s, "gallery-4-parts")
