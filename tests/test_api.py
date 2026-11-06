"""Guards for the public API and release metadata.

The public API is svgparts.__all__ plus the public methods of Slide and Sketch. Their signatures are recorded in
tests/public_api.txt. When a change to them is intended, update the record and describe the change in CHANGELOG.md:

    python3 tests/test_api.py --update
"""
import inspect
import json
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "plugins", "svg-infographic", "skills", "svg-infographic", "scripts"))
import svgparts  # noqa: E402

RECORD = os.path.join(ROOT, "tests", "public_api.txt")


def public_api():
    """One line per public function or method: its name and signature."""
    lines = []
    for name in svgparts.__all__:
        obj = getattr(svgparts, name)
        if inspect.isclass(obj) and name in ("Slide", "Sketch"):
            for attr, member in sorted(vars(obj).items()):
                if attr.startswith("_") and attr != "__init__":
                    continue
                if callable(member):
                    lines.append(f"{name}.{attr}{inspect.signature(member)}")
        elif callable(obj) and not inspect.isclass(obj):
            lines.append(f"{name}{inspect.signature(obj)}")
        else:
            lines.append(name)
    return "\n".join(lines) + "\n"


class PublicApiTest(unittest.TestCase):
    def test_public_api_matches_the_record(self):
        with open(RECORD, encoding="utf-8") as f:
            recorded = f.read()
        self.assertEqual(public_api(), recorded,
                         "The public API changed. If this is intended, run `python3 tests/test_api.py --update` "
                         "and describe the change in CHANGELOG.md.")

    def test_check_kinds_are_listed_in_the_browser_script(self):
        for kind in svgparts.CHECK_KINDS:
            word = kind.split()[0]
            self.assertIn(word, svgparts._CHECK_JS)


class MetadataTest(unittest.TestCase):
    def test_plugin_and_marketplace_versions_match(self):
        with open(os.path.join(ROOT, ".claude-plugin", "marketplace.json"), encoding="utf-8") as f:
            market = json.load(f)
        with open(os.path.join(ROOT, "plugins", "svg-infographic", ".claude-plugin", "plugin.json"),
                  encoding="utf-8") as f:
            plugin = json.load(f)
        self.assertEqual(market["metadata"]["version"], plugin["version"])
        self.assertEqual(market["plugins"][0]["version"], plugin["version"])

    def test_released_version_has_a_changelog_entry(self):
        with open(os.path.join(ROOT, "plugins", "svg-infographic", ".claude-plugin", "plugin.json"),
                  encoding="utf-8") as f:
            version = json.load(f)["version"]
        with open(os.path.join(ROOT, "CHANGELOG.md"), encoding="utf-8") as f:
            self.assertIn(f"## [{version}]", f.read())


if __name__ == "__main__":
    if "--update" in sys.argv:
        with open(RECORD, "w", encoding="utf-8") as f:
            f.write(public_api())
        print("updated", RECORD)
    else:
        unittest.main()
