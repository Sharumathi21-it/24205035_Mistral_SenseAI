import math
from collections import Counter

from extractor import extract_text, ExtractionError
from preprocessor import (
    get_processed_tokens,
    extract_skills,
    extract_experience_years,
    extract_education_level,
    term_frequencies,
)

WEIGHTS = {
    "text_similarity": 0.35,
    "skill_match": 0.40,
    "experience": 0.15,
    "education": 0.10,
}


# ------------------------------------------------------------- TF-IDF --
def _term_frequency_vector(tokens):
    tf = term_frequencies(tokens)
    total = sum(tf.values()) or 1
    return {term: count / total for term, count in tf.items()}


def _idf_weights(list_of_token_lists):
    """Standard idf = log(N / (1 + df))"""
    n_docs = len(list_of_token_lists)
    df = Counter()
    for tokens in list_of_token_lists:
        for term in set(tokens):
            df[term] += 1
    return {term: math.log(n_docs / (1 + freq)) + 1 for term, freq in df.items()}


def _tfidf_vector(tf_vector, idf_weights):
    return {term: weight * idf_weights.get(term, 0.0) for term, weight in tf_vector.items()}


def cosine_similarity(vec_a, vec_b):
    """Cosine similarity between two sparse dict-vectors."""
    if not vec_a or not vec_b:
        return 0.0
    common_terms = set(vec_a) & set(vec_b)
    dot = sum(vec_a[t] * vec_b[t] for t in common_terms)
    norm_a = math.sqrt(sum(v * v for v in vec_a.values()))
    norm_b = math.sqrt(sum(v * v for v in vec_b.values()))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


# -------------------------------------------------------------- SCORING --
def _skill_match_score(jd_skills, resume_skills):
    if not jd_skills:
        return 1.0, set(), set()  # nothing explicit required -> full marks
    matched = jd_skills & resume_skills
    missing = jd_skills - resume_skills
    score = len(matched) / len(jd_skills)
    return score, matched, missing


def _experience_score(required_years, candidate_years):
    if required_years <= 0:
        return 1.0
    if candidate_years >= required_years:
        return 1.0
    return round(candidate_years / required_years, 4)


def _education_score(required_level, candidate_level):
    if required_level <= 0:
        return 1.0
    if candidate_level >= required_level:
        return 1.0
    return round(candidate_level / required_level, 4)


class CandidateResult:
    def __init__(self, filename):
        self.filename = filename
        self.error = None
        self.final_score = 0.0
        self.text_similarity = 0.0
        self.skill_score = 0.0
        self.experience_score = 0.0
        self.education_score = 0.0
        self.matched_skills = set()
        self.missing_skills = set()
        self.candidate_years = 0
        self.education_keyword = None

    def as_dict(self):
        return {
            "filename": self.filename,
            "error": self.error,
            "final_score_percent": round(self.final_score * 100, 2),
            "breakdown": {
                "text_similarity_percent": round(self.text_similarity * 100, 2),
                "skill_match_percent": round(self.skill_score * 100, 2),
                "experience_score_percent": round(self.experience_score * 100, 2),
                "education_score_percent": round(self.education_score * 100, 2),
            },
            "matched_skills": sorted(self.matched_skills),
            "missing_skills": sorted(self.missing_skills),
            "candidate_experience_years": self.candidate_years,
            "candidate_education_keyword": self.education_keyword,
        }


class ResumeAnalyzer:
    def __init__(self, weights=None):
        self.weights = weights or WEIGHTS

    def analyze(self, jd_path, resume_paths):
        """Analyze all resumes against a single JD. Returns a list of
        CandidateResult sorted best-first."""
        jd_text = extract_text(jd_path)
        jd_tokens = get_processed_tokens(jd_text)
        jd_skills = extract_skills(jd_text)
        jd_required_years = extract_experience_years(jd_text)
        jd_required_edu, _ = extract_education_level(jd_text)

        resume_token_lists = []
        raw_texts = {}
        results = []

        for path in resume_paths:
            result = CandidateResult(path)
            try:
                text = extract_text(path)
                raw_texts[path] = text
                tokens = get_processed_tokens(text)
                resume_token_lists.append(tokens)
            except ExtractionError as exc:
                result.error = str(exc)
                resume_token_lists.append([])
            results.append(result)

        corpus = [jd_tokens] + resume_token_lists
        idf = _idf_weights(corpus)
        jd_vector = _tfidf_vector(_term_frequency_vector(jd_tokens), idf)

        for result, tokens in zip(results, resume_token_lists):
            if result.error:
                continue
            text = raw_texts[result.filename]

            resume_vector = _tfidf_vector(_term_frequency_vector(tokens), idf)
            result.text_similarity = cosine_similarity(jd_vector, resume_vector)

            resume_skills = extract_skills(text)
            result.skill_score, result.matched_skills, result.missing_skills = (
                _skill_match_score(jd_skills, resume_skills)
            )

            result.candidate_years = extract_experience_years(text)
            result.experience_score = _experience_score(jd_required_years, result.candidate_years)

            cand_edu, cand_keyword = extract_education_level(text)
            result.education_keyword = cand_keyword
            result.education_score = _education_score(jd_required_edu, cand_edu)

            result.final_score = (
                self.weights["text_similarity"] * result.text_similarity
                + self.weights["skill_match"] * result.skill_score
                + self.weights["experience"] * result.experience_score
                + self.weights["education"] * result.education_score
            )

        results.sort(key=lambda r: (r.error is not None, -r.final_score))
        return results, {
            "jd_skills": sorted(jd_skills),
            "jd_required_years": jd_required_years,
            "jd_required_education_score": jd_required_edu,
        }
