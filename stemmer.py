_STEP1_SUFFIXES = [
    ("sses", "ss"),
    ("ies", "i"),
    ("ss", "ss"),
    ("s", ""),
]

_STEP2_SUFFIXES = [
    "ational", "tional", "enci", "anci", "izer", "abli", "alli",
    "entli", "eli", "ousli", "ization", "ation", "ator", "alism",
    "iveness", "fulness", "ousness", "aliti", "iviti", "biliti",
]

_STEP3_SUFFIXES = ["ing", "edly", "ed", "ely", "er", "ers"]


def _is_vowel(ch):
    return ch in "aeiou"


def _has_vowel(stem):
    return any(_is_vowel(ch) for ch in stem)


def stem(word):
    """Reduce a single word to a normalized root form."""
    if not word:
        return word

    w = word.lower()

    if len(w) <= 2 or w.isdigit():
        return w

    for suffix, replacement in _STEP1_SUFFIXES:
        if w.endswith(suffix) and len(w) - len(suffix) >= 2:
            candidate = w[: -len(suffix)] + replacement
            if _has_vowel(candidate):
                w = candidate
                break

    for suffix in _STEP2_SUFFIXES:
        if w.endswith(suffix) and len(w) - len(suffix) >= 2:
            w = w[: -len(suffix)]
            break

    # Step 3: verb forms (ing/ed/er ...)
    for suffix in _STEP3_SUFFIXES:
        if w.endswith(suffix) and len(w) - len(suffix) >= 2:
            candidate = w[: -len(suffix)]
            if _has_vowel(candidate):
                # undo double consonant e.g. "programming" -> "programm" -> "program"
                if len(candidate) >= 2 and candidate[-1] == candidate[-2] and candidate[-1] not in "lsz":
                    candidate = candidate[:-1]
                w = candidate
                break

    return w


def stem_tokens(tokens):
    return [stem(t) for t in tokens]
