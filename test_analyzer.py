import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from analyzer import ResumeAnalyzer, cosine_similarity


class TestAnalyzer(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.jd_path = os.path.join(self.tmpdir, "jd.txt")
        with open(self.jd_path, "w") as f:
            f.write("Looking for a Python developer with 3 years of experience in "
                    "Django, PostgreSQL and Docker. Bachelor's degree required.")

        self.strong_resume = os.path.join(self.tmpdir, "strong.txt")
        with open(self.strong_resume, "w") as f:
            f.write("Software engineer with 5 years of experience in Python, Django, "
                    "PostgreSQL and Docker. B.Tech in Computer Science.")

        self.weak_resume = os.path.join(self.tmpdir, "weak.txt")
        with open(self.weak_resume, "w") as f:
            f.write("Graphic designer skilled in Photoshop and Illustrator with 2 "
                    "years of experience. Diploma in Visual Arts.")

    def test_cosine_similarity_identical_vectors(self):
        v = {"python": 1.0, "django": 0.5}
        self.assertAlmostEqual(cosine_similarity(v, v), 1.0, places=6)

    def test_cosine_similarity_orthogonal_vectors(self):
        v1 = {"python": 1.0}
        v2 = {"photoshop": 1.0}
        self.assertEqual(cosine_similarity(v1, v2), 0.0)

    def test_strong_candidate_outranks_weak(self):
        analyzer = ResumeAnalyzer()
        results, jd_meta = analyzer.analyze(self.jd_path, [self.weak_resume, self.strong_resume])
        # results should be sorted best-first regardless of input order
        self.assertEqual(os.path.basename(results[0].filename), "strong.txt")
        self.assertGreater(results[0].final_score, results[1].final_score)

    def test_skill_extraction_in_jd(self):
        analyzer = ResumeAnalyzer()
        _, jd_meta = analyzer.analyze(self.jd_path, [self.strong_resume])
        self.assertIn("python", jd_meta["jd_skills"])
        self.assertIn("django", jd_meta["jd_skills"])
        self.assertIn("postgresql", jd_meta["jd_skills"])

    def test_missing_skills_detected(self):
        analyzer = ResumeAnalyzer()
        results, _ = analyzer.analyze(self.jd_path, [self.weak_resume])
        self.assertIn("python", results[0].missing_skills)


if __name__ == "__main__":
    unittest.main()
