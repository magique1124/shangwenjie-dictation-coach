import datetime as dt
import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("rank_candidates", ROOT / "scripts" / "rank_candidates.py")
rank = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(rank)


class RankCandidatesTest(unittest.TestCase):
    def test_article_audio_and_recent_material_win(self):
        candidates = [
            {
                "title": "Old auto video",
                "source_type": "auto_caption_video",
                "transcript_type": "auto_generated",
                "access": "public",
                "published_at": "2024-01-01",
                "duration": "10:00",
            },
            {
                "title": "Recent article audio",
                "source_type": "official_article_audio",
                "transcript_type": "official_article_text",
                "access": "public",
                "published_at": "2026-10-01",
                "audio_duration": "6:26",
                "listen_to_article": True,
            },
        ]
        ranked = rank.rank_candidates(candidates, dt.date(2026, 11, 15))
        self.assertEqual(ranked[0]["title"], "Recent article audio")
        self.assertGreater(ranked[0]["score"], ranked[1]["score"])
        self.assertTrue(ranked[0]["eligible"])

    def test_text_only_is_not_eligible(self):
        candidate = {
            "title": "Text only",
            "source_type": "text_only",
            "transcript_type": "official",
            "access": "public",
            "published_at": "2026-11-01",
            "duration": "8:00",
        }
        ranked = rank.rank_candidates([candidate], dt.date(2026, 11, 15))
        self.assertFalse(ranked[0]["eligible"])


if __name__ == "__main__":
    unittest.main()
