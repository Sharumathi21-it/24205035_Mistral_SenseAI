import os
import re
import zipfile
import zlib
import xml.etree.ElementTree as ET


class ExtractionError(Exception):
    pass


def _extract_txt(path):
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        return f.read()

_DOCX_NS = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}


def _extract_docx(path):
    try:
        with zipfile.ZipFile(path) as z:
            with z.open("word/document.xml") as doc_xml:
                tree = ET.parse(doc_xml)
    except (KeyError, zipfile.BadZipFile) as exc:
        raise ExtractionError(f"Could not read docx file: {exc}")

    root = tree.getroot()
    texts = []
    for node in root.iter("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}t"):
        if node.text:
            texts.append(node.text)
    for p in root.iter("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}p"):
        pass  # paragraphs already walked via 't' nodes above

    return " ".join(texts)


# ---------------------------------------------------------------- PDF --
_STREAM_RE = re.compile(rb"stream\r?\n(.*?)endstream", re.DOTALL)
_FLATE_RE = re.compile(rb"/Filter\s*/FlateDecode")
_TEXT_SHOW_RE = re.compile(rb"\((?:\\.|[^\\()])*\)|\[(?:\\.|[^\\\[\]])*\]")
_ESCAPES = {b"\\n": b"\n", b"\\r": b"\r", b"\\t": b"\t",
            b"\\(": b"(", b"\\)": b")", b"\\\\": b"\\"}


def _unescape_pdf_string(raw):
    for esc, rep in _ESCAPES.items():
        raw = raw.replace(esc, rep)
    return raw


def _extract_pdf(path):
    with open(path, "rb") as f:
        data = f.read()

    text_chunks = []

    for match in _STREAM_RE.finditer(data):
        # Peek a little before the stream keyword to see if it was
        # Flate-compressed (look back up to 200 bytes for the dict).
        start = match.start()
        header = data[max(0, start - 200):start]
        content = match.group(1)

        if _FLATE_RE.search(header):
            try:
                content = zlib.decompress(content)
            except zlib.error:
                try:
                    d = zlib.decompressobj()
                    content = d.decompress(content)
                except zlib.error:
                    continue

        # Only content streams contain text-drawing operators (Tj/TJ).
        if b"Tj" not in content and b"TJ" not in content:
            continue

        for piece in _TEXT_SHOW_RE.finditer(content):
            token = piece.group(0)
            if token.startswith(b"("):
                text_chunks.append(_unescape_pdf_string(token[1:-1]))
            elif token.startswith(b"["):
                for sub in re.finditer(rb"\((?:\\.|[^\\()])*\)", token):
                    text_chunks.append(_unescape_pdf_string(sub.group(0)[1:-1]))

    raw_text = b" ".join(text_chunks).decode("latin-1", errors="ignore")
    raw_text = re.sub(r"\s+", " ", raw_text).strip()

    if not raw_text:
        raise ExtractionError(
            "No extractable text found. This PDF may be a scanned image "
            "(no OCR is bundled, per the no-external-library constraint)."
        )
    return raw_text

_DISPATCH = {
    ".txt": _extract_txt,
    ".docx": _extract_docx,
    ".pdf": _extract_pdf,
}


def extract_text(path):
    """Extract raw text from a resume file. Raises ExtractionError on
    unsupported/broken files."""
    ext = os.path.splitext(path)[1].lower()
    handler = _DISPATCH.get(ext)
    if handler is None:
        raise ExtractionError(
            f"Unsupported file type '{ext}'. Supported: .txt, .docx, .pdf"
        )
    text = handler(path)
    if not text or not text.strip():
        raise ExtractionError(f"No text could be extracted from {path}")
    return text
