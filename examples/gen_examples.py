"""Draw the examples shown in the README. All content is fictional.

    python3 examples/gen_examples.py
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "plugins", "svg-infographic", "skills", "svg-infographic", "scripts"))
from svgparts import Slide, C  # noqa: E402


def done(s, name):
    print(s.render(os.path.join(HERE, f"{name}.png")))


# ---- 1. Process flow ----
s = Slide("Library book reservation flow", "How a patron reserves a book and picks it up, and where the system is involved")
s.header("Returned books go straight to the next patron in line", "Process flow")
s.section(96, "From reservation to pickup")
s.chain(116, [
    ("user", "Patron", ["Searches the catalog", "and reserves a book"], None),
    ("server", "Reservation system", ["Checks availability", "and sets the queue"], C.PRIMARY),
    ("bell", "Notification", ["Emails the patron", "when the book is ready"], None),
    ("building", "Library desk", ["Patron picks it up", "within 7 days"], C.GREEN),
], h=112)
s.section(282, "When the book is on loan")
s.steps(s.M, 318, [
    ("Join the queue", "Patrons who reserved the same book are queued by request time"),
    ("Assign on return", "When the book is returned, it goes to the first patron in the queue"),
    ("Pass it on if not picked up", "The pickup period is 7 days. After that, the next patron gets it"),
], step=56)
s.zone(560, 300, 376, 150, "What the patron sees")
s.bullets(580, 348, 336, [
    "Two states: \"In queue\" and \"Ready\"",
    "While in queue, their position is shown",
    "\"Ready\" is sent by email and on the web",
], step=34)
done(s, "example-1-flow")


# ---- 2. Comparison table ----
s = Slide("Comparing notification channels", "Email, push notifications, and SMS compared by speed, cost, and best use")
s.header("Send urgent notices by push, and notices to keep by email", "Comparison")
s.section(96, "How the three channels differ")
s.table(s.M, 112, s.W - 2 * s.M, ["Channel", "Delivery", "Cost", "Kept as a record", "Best for"],
        [16, 140, 310, 470, 620], [
    ("Email", "Seconds to minutes", "Nearly free", ("Yes", C.GREEN, 500), "Receipts, confirmations"),
    ("Push", ("Seconds", C.GREEN, 500), "Nearly free", "Rarely", "Notices with a close deadline"),
    ("SMS", ("Seconds", C.GREEN, 500), ("Charged per message", C.ORANGE, 500), "On the device", "Verification codes"),
], highlight=(1,), row_h=44)
s.section(330, "How to choose")
for i, (q, qsub, a, asub, color) in enumerate([
    ("Must it be read today?", "A deadline or pickup period is close", "Send a push notification", "Also email patrons who do not have the app", C.PRIMARY),
    ("Will they need to look it up later?", "Receipts, confirmations, changes to terms", "Send an email", "Put the topic and date in the subject", C.GREEN),
]):
    y = 350 + i * 82
    s.card(s.M, y, 380, 64)
    s.text(s.M + 20, y + 27, q, 14, C.TEXT, 600, max_width=340)
    s.text(s.M + 20, y + 48, qsub, 12, C.SUB, max_width=340)
    s.connector(s.M + 392, y + 32, 516, y + 32, label="Yes")
    s.card(524, y, s.W - s.M - 524, 64, color)
    s.text(544, y + 27, a, 14, color, 600, max_width=372)
    s.text(544, y + 48, asub, 12, C.SUB, max_width=372)
done(s, "example-2-compare")


# ---- 3. Incident review ----
s = Slide("Reservation system incident review", "Timeline and follow-up actions for a search outage on a Monday morning")
s.header("Cause: a Monday spike maxed out the search server's CPU", "Incident review")
s.stats(64, [("Downtime", "About 15 min", C.ORANGE, "clock"),
             ("Affected reservations", "120", C.TEXT, "document"),
             ("Follow-up actions", "3 (2 done)", C.TEXT, "check")])
s.section(164, "Timeline")
s.timeline(222, [
    ("9:00", "Spike at opening", ["Search responses", "start to slow down"], None),
    ("9:05", "Search stops", ["CPU hits its limit and", "requests time out"], C.ORANGE),
    ("9:12", "Servers added", ["Search servers go", "from 2 to 4"], C.PRIMARY),
    ("9:20", "Recovered", ["Search responds at", "normal speed again"], C.GREEN),
])
s.section(340, "Follow-up actions")
y = 358
for label, desc, st, color in [
    ("Scale up before opening", "Run 4 servers from 8:30 on Mondays and after holidays", "Done", C.GREEN),
    ("Alert on CPU usage", "Notify the on-call person when CPU stays above 80% for 5 min", "Done", C.GREEN),
    ("Cache search results", "Return cached results for repeated searches to reduce load", "In progress", C.ORANGE),
]:
    s.card(s.M, y, s.W - 2 * s.M, 46)
    s.text(s.M + 20, y + 28, label, 14, C.TEXT, 600, max_width=250)
    s.text(s.M + 290, y + 28, desc, 12.5, C.SUB, max_width=500)
    s.status(s.W - s.M - 110, y + 28, st, color)
    y += 52
done(s, "example-3-incident")
