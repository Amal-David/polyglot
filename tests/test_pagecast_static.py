"""Dependency-free guardrails for the Pagecast-safe static launch bundle."""

from __future__ import annotations

import hashlib
import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BUNDLE = ROOT / "site" / "pagecast"
HTML = BUNDLE / "index.html"


class PagecastStaticBundleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.html = HTML.read_text(encoding="utf-8")
        cls.manifest = json.loads((BUNDLE / "manifest.json").read_text(encoding="utf-8"))

    def test_title_story_and_semantic_markers(self) -> None:
        self.assertIn("<title>Polyglot — Learn a language between Codex and Claude Code turns</title>", self.html)
        self.assertEqual(len(re.findall(r"<h1(?:\\s|>)", self.html)), 1)
        for marker in (
            'href="#main"',
            'id="main" tabindex="-1"',
            "Read the demo transcript and summary",
            "polyglot review --pair en-de --direction reverse",
            "Prompt: sehen",
            "Answer: to see",
            "Grade [again/hard/good/easy]: good",
            "Next review: tomorrow",
        ):
            self.assertIn(marker, self.html)

    def test_exact_catalog_and_boundary_claims(self) -> None:
        for claim in (
            "74",
            "19,281",
            "520",
            "119",
            "79",
            "PL→EN 264",
            "UK→EN 265",
            "SV→EN 261",
            "EL→EN 256",
            "85 characters, about 43 tokens",
            "not native-speaker reviewed",
            "does not claim an official Duolingo top 20",
            "one labelled starter exposure",
            "Instead of staring at terminal churn",
            "Codex Desktop + CLI",
            "Claude Code",
            "Pi and Hermes support",
        ):
            self.assertIn(claim, self.html)

    def test_assets_are_local_and_expected_paths_are_declared(self) -> None:
        expected_present = {
            "assets/favicon.svg",
            "assets/fonts/dm-mono-latin-400-normal.woff2",
            "assets/fonts/hanken-grotesk-latin-400-normal.woff2",
            "assets/fonts/hanken-grotesk-latin-600-normal.woff2",
            "assets/fonts/newsreader-latin-400-normal.woff2",
            "assets/fonts/licenses/dm-mono-OFL.txt",
            "assets/fonts/licenses/hanken-grotesk-OFL.txt",
            "assets/fonts/licenses/newsreader-OFL.txt",
        }
        declared = {asset["path"] for asset in self.manifest["assets"]}
        self.assertTrue(expected_present.issubset(declared))
        for asset in self.manifest["assets"]:
            path = BUNDLE / asset["path"]
            self.assertEqual(asset["status"], "present", asset["path"])
            self.assertTrue(path.is_file(), asset["path"])
            payload = path.read_bytes()
            self.assertEqual(len(payload), asset["bytes"], asset["path"])
            self.assertEqual(hashlib.sha256(payload).hexdigest(), asset["sha256"], asset["path"])
        self.assertIn('src="./assets/polyglot-demo.mp4"', self.html)
        self.assertIn('poster="./assets/polyglot-poster.png"', self.html)
        self.assertNotRegex(self.html, r'(?:src|poster)="/(?!/)')
        self.assertNotRegex(self.html, r'(?:src|poster)="https?://')
        self.assertNotIn('url("/assets/', self.html)

    def test_no_runtime_or_host_auth_markers(self) -> None:
        forbidden = (
            "chatgpt.site",
            ".openai",
            "OpenAI Sites",
            "oai-authenticated",
            "signin-with-chatgpt",
            "signout-with-chatgpt",
            "fetch(",
            "<script",
        )
        for marker in forbidden:
            self.assertNotIn(marker.lower(), self.html.lower())

    def test_pagecast_has_final_canonical_and_social_metadata(self) -> None:
        page_url = (
            "https://pagecast-6cv.pages.dev/p/"
            "gentle-bumbling-panther-7373321451de0e735781830f87c14813/"
        )
        self.assertIn(f'<link rel="canonical" href="{page_url}">', self.html)
        self.assertIn(f'<meta property="og:url" content="{page_url}">', self.html)
        self.assertIn('<meta property="og:type" content="website">', self.html)
        self.assertIn('<meta name="twitter:card" content="summary_large_image">', self.html)
        self.assertIn(
            f'<meta property="og:image" content="{page_url}assets/polyglot-poster.png">',
            self.html,
        )

    def test_responsive_and_reduced_motion_markers(self) -> None:
        self.assertIn("@media (max-width:620px)", self.html)
        self.assertIn("overflow-x:hidden", self.html)
        self.assertIn("prefers-reduced-motion:reduce", self.html)
        self.assertIn("min-height:44px", self.html)


if __name__ == "__main__":
    unittest.main()
