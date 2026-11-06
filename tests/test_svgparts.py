"""Tests for the parts library. Run from the repository root:

    python3 -m unittest discover -s tests -v

Tests that need a browser are skipped when Chrome, Chromium, or Edge is not found.
"""
import glob
import os
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "plugins", "svg-infographic", "skills", "svg-infographic", "scripts"))
import svgparts  # noqa: E402
from svgparts import C, Slide, check, text_width, wrap  # noqa: E402

try:
    svgparts.find_browser()
    HAS_BROWSER = True
except FileNotFoundError:
    HAS_BROWSER = False
needs_browser = unittest.skipUnless(HAS_BROWSER, "Chrome, Chromium, or Edge not found")


def gallery():
    """Three slides that use every part with its default spacing. They must produce no warnings and no issues."""
    a = Slide("Parts gallery A", "Basic parts")
    a.header("Parts gallery A: cards, flows, tables, and text", "svgparts")
    a.stats(64, [("Downtime", "About 15 min", C.ORANGE, "clock"), ("Requests", "1,200", C.TEXT, "document"),
                 ("Actions", "3 (2 done)", C.TEXT, "check")])
    a.section(150, "flow")
    a.flow(166, [("Receive", ["Take the application"], None),
                 ("Review", "Check the details and ask for missing documents", C.PRIMARY),
                 ("Decide", ["Approve or reject"], None), ("Notify", ["Email the result"], C.GREEN)])
    a.section(280, "table and steps")
    a.table(a.M, 296, 440, ["Channel", "Speed", "Cost"], [16, 150, 290], [
        ("Email", "Minutes", "Free"), ("Push", ("Seconds", C.GREEN, 500), "Free"),
        ("SMS", "Seconds", ("Paid", C.ORANGE, 500))], highlight=(1,),
        row_icons=["document", ("bell", C.PRIMARY), None])
    a.steps(500, 310, [("Join the queue", "Queued by request time"), ("Assign on return", "First in line gets it"),
                       ("Pass it on", "After 7 days, the next patron")])
    a.bullets(a.M, 450, 440, ["A bullet item", "Another bullet item"])
    a.paragraph(500, 462, 436, "A paragraph is wrapped to its width automatically, so long sentences need no "
                "manual line breaks.", 13, C.SUB, max_lines=3)
    a.pill(a.M, 494, "Category")
    a.numbered(150, 505, 3)
    a.status(190, 510, "In progress", C.ORANGE)

    b = Slide("Parts gallery B", "Diagram parts")
    b.header("Parts gallery B: nodes, zones, and decisions", "svgparts")
    b.section(84, "chain")
    b.chain(100, [("user", "Patron", ["Reserves a book"], None),
                  ("server", "System", "Checks availability and sets the queue", C.PRIMARY),
                  ("bell", "Notification", ["Emails the patron"], None),
                  ("building", "Desk", ["Hands over the book"], C.GREEN)])
    b.zone(b.M, 236, 440, 150, "zone")
    b.node(44, 266, 180, 104, "database", "Database", ["Stores bookings"])
    b.node(264, 266, 180, 104, "queue", "Queue", ["Holds requests"])
    b.connector(230, 318, 258, 318)
    b.span(44, 444, 418, "span")
    b.decision(500, 246, 180, 44, "Has a plan?")
    b.elbow([(590, 290), (590, 340)])
    b.edge_label(614, 315, "Yes")
    b.terminal(500, 340, 180, 40, "Done", C.GREEN)
    b.elbow([(680, 268), (780, 268), (780, 340)])
    b.edge_label(730, 268, "No")
    b.terminal(720, 340, 120, 40, "Skip")
    b.box(500, 420, 180, 48, "Process", sub="with a subtitle")
    b.titled(720, 452, "flag", "Titled heading")

    c = Slide("Parts gallery C", "Time and range parts")
    c.header("Parts gallery C: timelines, schematics, and ranges", "svgparts")
    c.section(84, "timeline (equal spacing, not proportional to time)")
    c.timeline(140, [("9:00", "Spike", ["Responses slow down"], None),
                     ("9:05", "Stop", "CPU hits its limit and requests time out", C.ORANGE),
                     ("9:12", "Scale up", ["From 2 to 4 servers"], C.PRIMARY),
                     ("9:20", "Recovered", ["Normal speed again"], C.GREEN)])
    c.section(250, "sketch")
    sk = c.sketch(44, 290, 400, 150, xlabels=("9:00", "10:00", "11:00"), ylabel="load")
    sk.area([(0, 0), (0.3, 0.6), (0.6, 0.9), (1, 0.4), (1, 0)], C.ORANGE)
    sk.line([(0, 0.8), (1, 0.8)], C.SUB, 1.5, dash=True)
    sk.label(0.72, 0.86, "limit")
    f = c.scale(520, 300, 0, 10)
    c.band(f(1), f(4), 290, 18, C.ORANGE, "busy")
    c.band(f(6), f(8), 320, 18, C.GREEN, "quiet")
    c.range_bar(500, 376, 436, "Response time", 120, 300, 500, "120–300 ms")
    c.ratio(500, 400, 436, "Total", "1,200", C.TEXT, "of which done", 0.6)
    d = Slide("Parts gallery D", "Sequences, rules, and action lists")
    d.header("Parts gallery D: sequences, rules, and action lists", "svgparts")
    _, bottom = d.sequence(70, [("u", "Patron", None, None, "user"), ("w", "Web app", "browser", C.PRIMARY, "laptop"),
                                ("a", "Reservation API", None, None), ("d", "Database", None, None)], [
        ("u", "w", "Choose a book", None), ("w", "a", "Request a reservation", C.PRIMARY),
        ("a", "d", "Save it", None), ("a", "w", "Queue position", None),
        ("u", "d", "A message that passes over a lifeline", C.ORANGE)])
    y = d.rule_row(d.M, bottom + 20, d.W - 2 * d.M, "Must it be read today?", "Send a push notification",
                   "A deadline is close", "Also email patrons without the app", cond_icon="clock", result_icon="bell")
    d.action_list(y + 20, [("Scale up before opening", "Run 4 servers from 8:30", "Done", C.GREEN),
                           ("Cache search results", "Return cached results for repeated searches", "In progress",
                            C.ORANGE)])
    e = Slide("Parts gallery E", "Swimlanes and before/after")
    e.header("Parts gallery E: swimlanes and before/after", "svgparts")
    y = e.swimlane(70, [("p", "Patron"), ("s", "System"), ("d", "Library desk")], [
        ("p", 0, "Reserve a book", None), ("s", 1, "Assign a copy", C.PRIMARY), ("s", 2, "Send an email", None),
        ("d", 2, "Set the book aside", None), ("p", 3, "Pick it up", C.GREEN)])
    e.before_after(y + 28, ["Patrons phone the desk", ("Staff search by hand", True)],
                   ["Patrons reserve on the web", ("The system assigns a copy", True)], icons=("warning", "check"))

    f = Slide("Parts gallery F", "Trees, roadmaps, and themes", theme={"PRIMARY": "#7C3AED"})
    f.header("Parts gallery F: trees, roadmaps, and themes", "svgparts")
    y = f.tree(70, ("Library", None, [
        ("Lending", "3 teams", [("Desk", None, [], None), ("Reservations", None, [], C.PRIMARY)], None),
        ("Collections", None, [("Buying", None, [], None), ("Repair", None, [], None)], None),
        ("Systems", None, [("Web app", None, [], None, "laptop")], C.GREEN, "server")], None, "building"))
    f.roadmap(y + 30, ["Q1", "Q2", "Q3", "Q4"], [
        ("Web app", [(0, 1.5, "Reservations", C.PRIMARY), (2, 4, "Mobile layout", C.GREEN)]),
        ("Desk", [(1, 1.4, "Self checkout", C.ORANGE)]),
        ("Systems", [(0.5, 3.5, "Move search to the new server", C.SUB)])])
    return {"gallery-a": a, "gallery-b": b, "gallery-c": c, "gallery-d": d, "gallery-e": e, "gallery-f": f}


class TextWidthTest(unittest.TestCase):
    def test_ascii_widths_differ_by_character(self):
        self.assertLess(text_width("i", 10), text_width("W", 10))

    def test_full_width_character_is_one_em(self):
        self.assertEqual(text_width("予約", 12), 24)


class WrapTest(unittest.TestCase):
    def test_english_breaks_at_spaces(self):
        s = "Returned books go straight to the next patron in line and the queue moves forward"
        lines = wrap(s, 220, 13)
        self.assertGreater(len(lines), 1)
        self.assertEqual(" ".join(lines), s)
        for ln in lines:
            self.assertLessEqual(text_width(ln, 13), 220)

    def test_japanese_keeps_line_start_rules(self):
        s = "返却された本は、予約の順番が最も早い利用者に自動で割り当てられ、メールで知らせる"
        lines = wrap(s, 200, 13)
        self.assertEqual("".join(lines), s)
        for ln in lines:
            self.assertNotIn(ln[0], svgparts._NO_LINE_START)
            self.assertNotIn(ln[-1], svgparts._NO_LINE_END)
            self.assertLessEqual(text_width(ln, 13), 200)

    def test_japanese_prefers_break_after_particle(self):
        self.assertEqual(wrap("同じ本を予約した人の中で、申し込んだ順に並ぶ", 180, 13),
                         ["同じ本を予約した人の中で、", "申し込んだ順に並ぶ"])

    def test_word_wider_than_line_is_kept_whole(self):
        self.assertEqual(wrap("Supercalifragilistic word", 60, 13), ["Supercalifragilistic", "word"])


class DefaultsTest(unittest.TestCase):
    def test_gallery_has_no_estimate_warnings(self):
        for name, s in gallery().items():
            with self.subTest(name):
                self.assertEqual(s.warnings, [])

    def test_sequence_rejects_message_to_itself(self):
        s = Slide("t", "t")
        with self.assertRaises(ValueError):
            s.sequence(70, [("a", "A", None, None), ("b", "B", None, None)], [("a", "a", "loop", None)])

    def test_theme_swaps_colors_and_derives_backgrounds(self):
        s = Slide("t", "t", theme={"PRIMARY": "#7c3aed"})
        s.decision(10, 10, 120, 40, "Has a plan?")
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "t.svg")
            s.save(path, quiet=True)
            with open(path, encoding="utf-8") as fh:
                svg = fh.read()
        self.assertIn("#7C3AED", svg)
        self.assertNotIn(C.PRIMARY, svg)
        self.assertNotIn(C.PRIMARY_BG, svg)

    def test_theme_rejects_unknown_roles(self):
        with self.assertRaises(ValueError):
            Slide("t", "t", theme={"PURPLE": "#7C3AED"})

    def test_table_highlight_takes_a_color_per_row(self):
        s = Slide("t", "t")
        s.table(10, 10, 400, ["A", "B"], [16, 200], [("x", "y"), ("z", "w")], highlight={0: C.ORANGE, 1: C.GREEN})
        svg = "".join(s.out)
        self.assertIn(C.ORANGE_BG, svg)
        self.assertIn(C.GREEN_BG, svg)

    def test_box_icon_keeps_text_inside(self):
        s = Slide("t", "t")
        s.box(10, 10, 180, 48, "Reservation API", sub="internal", icon="server")
        self.assertEqual(s.warnings, [])
        self.assertTrue(any(o.startswith("<g transform") for o in s.out))

    def test_long_box_title_wraps_to_two_lines(self):
        s = Slide("t", "t")
        s.box(10, 10, 120, 48, "Set the book aside")
        self.assertEqual(sum(1 for o in s.out if o.startswith("<text")), 2)

    def test_short_arrow_is_reported(self):
        s = Slide("t", "t")
        s.connector(0, 0, 20, 0)
        self.assertTrue(any(w.startswith("Arrow too short") for w in s.warnings))


@needs_browser
class CheckTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)

    def path(self, name):
        return os.path.join(self.tmp.name, name)

    def test_gallery_has_no_issues(self):
        for name, s in gallery().items():
            with self.subTest(name):
                s.render(self.path(name + ".png"))
                self.assertEqual(s.issues, [])

    def test_examples_have_no_issues(self):
        for svg in sorted(glob.glob(os.path.join(ROOT, "examples", "*.svg"))):
            with self.subTest(os.path.basename(svg)):
                self.assertEqual(check(svg), [])

    def test_broken_layout_is_reported(self):
        s = Slide("broken", "deliberately broken layout")
        s.card(24, 80, 200, 60)
        s.text(44, 110, "This text is far too long for the card it sits in", 14, C.TEXT, 600, max_width=160)
        s.text(100, 200, "Overlap A", 14)
        s.text(110, 204, "Overlap B", 14)
        s.connector(300, 300, 500, 300)
        s.text(380, 305, "on the arrow", 12)
        s.card(600, 280, 120, 60)
        s.connector(560, 310, 680, 310)
        s.text(950, 520, "outside", 14)
        sk = s.sketch(300, 380, 200, 100)
        sk.area([(0, 0), (0.5, 1), (1, 0)], C.ORANGE)
        sk.label(0.45, 0.5, "covered")
        s.save(self.path("broken.svg"), quiet=True)
        kinds = {i.split(":")[0] for i in check(self.path("broken.svg"))}
        self.assertLessEqual(kinds, set(svgparts.CHECK_KINDS))
        self.assertEqual(kinds, {"Overflow", "Crosses the edge of a box", "Overlapping text",
                                 "Arrow crosses text", "Arrow enters a box", "Outside the canvas",
                                 "Filled area covers text"})


if __name__ == "__main__":
    unittest.main()
