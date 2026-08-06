import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from preprocessor import (
    tokenize, remove_stopwords, extract_skills,
    extract_experience_years, extract_education_level, get_processed_tokens,
)


class TestPreprocessor(unittest.TestCase):
    def test_tokenize_basic(self):
        tokens = tokenize("Python, Django and REST APIs!")
        self.assertIn("python", tokens)
        self.assertIn("django", tokens)

    def test_tokenize_keeps_special_tokens(self):
        tokens = tokenize("Experienced in C++ and C# development")
        self.assertIn("c++", tokens)
        self.assertIn("c#", tokens)

    def test_remove_stopwords(self):
        tokens = ["this", "is", "a", "python", "developer"]
        filtered = remove_stopwords(tokens)
        self.assertEqual(filtered, ["python", "developer"])

    def test_extract_skills_multiword(self):
        skills = extract_skills("Strong background in machine learning and data analysis")
        self.assertIn("machine learning", skills)
        self.assertIn("data analysis", skills)

    def test_extract_skills_single_word(self):
        skills = extract_skills("Proficient in Python and Docker")
        self.assertIn("python", skills)
        self.assertIn("docker", skills)

    def test_extract_experience_years(self):
        self.assertEqual(extract_experience_years("I have 4 years of experience"), 4)
        self.assertEqual(extract_experience_years("3+ years experience in backend"), 3)
        self.assertEqual(extract_experience_years("No experience mentioned here"), 0)

    def test_extract_education_level(self):
        score, keyword = extract_education_level("I hold a Master's degree in CS")
        self.assertGreater(score, 0)
        self.assertEqual(keyword, "master")

    def test_get_processed_tokens_stems(self):
        tokens = get_processed_tokens("developing developer developed development")
        # all forms should stem toward a common root
        self.assertTrue(len(set(tokens)) <= 2)


if __name__ == "__main__":
    unittest.main()
