import importlib.util
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("dictation_tools", ROOT / "scripts" / "dictation_tools.py")
tools = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(tools)


class DictationToolsTest(unittest.TestCase):
    def test_align_detects_omission_replacement_and_spelling(self):
        source = "The team scaled up the system."
        dictation = "The team scale up the sistem."
        result = tools.align_texts(source, dictation)
        categories = [item["category"] for item in result["errors"]]
        self.assertIn("spelling", categories)
        self.assertTrue(set(categories) & {"omission", "misheard", "extra"})
        self.assertGreaterEqual(result["summary"]["error_count"], 2)

    def test_daily_html_contains_practice_elements(self):
        source = "They scaled up the model without extra cost."
        dictation = "They scaled the model without extra cost."
        alignment = tools.align_texts(source, dictation)
        metadata = {
            "title": "Scaling Models",
            "date": "2026-11-14",
            "domain": "AI",
            "segment": "00:00-01:00",
            "duration": "5:00",
            "source_url": "https://example.com/talk",
            "expressions": [{"expression": "scale up", "meaning": "扩大规模"}],
        }
        output = tools.build_daily_html(source, dictation, alignment, metadata)
        self.assertIn("每日听写跟读单", output)
        self.assertIn("跟读练习", output)
        self.assertIn("scale up", output)
        self.assertIn("查看你的听写稿", output)

    def test_save_session_and_report(self):
        source = "The team scaled up the system."
        dictation = "The team scaled the system."
        alignment = tools.align_texts(source, dictation)
        metadata = {
            "material_id": "scaling-models",
            "title": "Scaling Models",
            "date": "2026-11-14",
            "segment": "00:00-01:00",
            "source_url": "https://example.com/talk",
            "main_weakness": "弱读",
            "expressions": ["scale up"],
            "status": "in_progress",
        }
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            result = tools.save_session(root, metadata, alignment, dictation, "00:01:00", None)
            self.assertTrue(Path(result["daily_note"]).exists())
            self.assertTrue((root / "Materials" / "scaling-models" / "progress.json").exists())
            report = root / "Reports" / "weekly" / "current.md"
            tools.build_period_report(root, "weekly", report)
            self.assertTrue(report.exists())
            self.assertIn("Scaling Models", report.read_text(encoding="utf-8"))

    def test_merge_alignments(self):
        first = tools.align_texts("One two.", "One.")
        second = tools.align_texts("Three four.", "Three for.")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            one = root / "one.json"
            two = root / "two.json"
            tools.write_json(one, first)
            tools.write_json(two, second)
            merged = tools.merge_alignments([one, two])
            self.assertEqual(merged["summary"]["error_count"], first["summary"]["error_count"] + second["summary"]["error_count"])
            self.assertEqual(merged["errors"][0]["id"], 1)


if __name__ == "__main__":
    unittest.main()
