import re
import string
from collections import Counter

from skills_db import ALL_SKILLS, MAX_SKILL_PHRASE_LEN, STOPWORDS
from stemmer import stem_tokens

_WORD_RE = re.compile(r"[a-zA-Z][a-zA-Z0-9+#.\-]*")


def clean_text(text):
    """Lower-case and normalize whitespace/punctuation noise."""
    text = text.replace("\r", " ").replace("\n", " ")
    text = re.sub(r"\s+", " ", text)
    return text.strip().lower()


def tokenize(text):
    """Extract word-like tokens, keeping useful symbols such as
    'c++', 'c#', 'node.js' intact."""
    text = clean_text(text)
    tokens = _WORD_RE.findall(text)
    # Strip stray leading/trailing punctuation (commas, stray periods,
    # dashes) but keep '+' and '#' since they are meaningful in tech
    # terms like "c++" and "c#".
    strip_chars = "".join(ch for ch in string.punctuation if ch not in "+#")
    cleaned = []
    for t in tokens:
        t = t.strip(strip_chars)
        if t:
            cleaned.append(t)
    return cleaned


def remove_stopwords(tokens):
    return [t for t in tokens if t not in STOPWORDS]


def build_ngrams(tokens, n):
    return [" ".join(tokens[i:i + n]) for i in range(len(tokens) - n + 1)]


def extract_skills(raw_text):
    """Scan text for any phrase (1..MAX_SKILL_PHRASE_LEN words) that
    matches a known skill in SKILLS_DB. Returns a set of matched skills.
    """
    tokens = tokenize(raw_text)
    found = set()

    # check n-grams from longest to shortest so multi-word skills like
    # "machine learning" are captured, not just "machine" and "learning".
    for n in range(MAX_SKILL_PHRASE_LEN, 0, -1):
        for gram in build_ngrams(tokens, n):
            if gram in ALL_SKILLS:
                found.add(gram)

    return found


def get_processed_tokens(raw_text):
    """Full pipeline: tokenize -> remove stopwords -> stem.
    Returns list of stemmed tokens used for TF-IDF style vectors."""
    tokens = tokenize(raw_text)
    tokens = remove_stopwords(tokens)
    tokens = [t for t in tokens if not t.isdigit()]
    tokens = stem_tokens(tokens)
    return tokens


def term_frequencies(tokens):
    """Return a Counter of term -> raw frequency."""
    return Counter(tokens)


def extract_experience_years(raw_text):
    """Look for patterns like '4 years of experience', '3+ years',
    '2 yrs' etc. and return the maximum number found (int), or 0."""
    text = clean_text(raw_text)
    patterns = [
        r"(\d{1,2})\s*\+?\s*(?:years|year|yrs|yr)\s*(?:of)?\s*experience",
        r"experience\s*(?:of)?\s*(\d{1,2})\s*\+?\s*(?:years|year|yrs|yr)",
        r"(\d{1,2})\s*\+?\s*(?:years|yrs)\b",
    ]
    found = []
    for pat in patterns:
        for m in re.finditer(pat, text):
            try:
                found.append(int(m.group(1)))
            except (ValueError, IndexError):
                continue
    return max(found) if found else 0


def extract_education_level(raw_text):
    """Return the highest education level score found (see
    skills_db.EDUCATION_KEYWORDS), and the matched keyword."""
    from skills_db import EDUCATION_KEYWORDS

    text = clean_text(raw_text)
    best_score = 0
    best_keyword = None
    for keyword, score in EDUCATION_KEYWORDS.items():
        # word-boundary search so "be" doesn't match inside "believe" etc.
        pattern = r"(?<![a-z])" + re.escape(keyword) + r"(?![a-z])"
        if re.search(pattern, text):
            if score > best_score:
                best_score = score
                best_keyword = keyword
    return best_score, best_keyword
