import os
import sys
import tempfile
import zipfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from extractor import extract_text, ExtractionError

_DOCX_DOCUMENT_XML = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:body>
    <w:p><w:r><w:t>Python Developer</w:t></w:r></w:p>
    <w:p><w:r><w:t>5 years of experience with Django</w:t></w:r></w:p>
  </w:body>
</w:document>"""


def _make_minimal_docx(path):
    """Build a minimal but valid .docx (a zip with word/document.xml)
    using only the standard library, to test our extractor end to end."""
    with zipfile.ZipFile(path, "w") as z:
        z.writestr("[Content_Types].xml",
                    '<?xml version="1.0"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"/>')
        z.writestr("word/document.xml", _DOCX_DOCUMENT_XML)


class TestExtractor(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def test_extract_txt(self):
        path = os.path.join(self.tmpdir, "resume.txt")
        with open(path, "w") as f:
            f.write("Simple text resume content.")
        text = extract_text(path)
        self.assertIn("Simple text resume", text)

    def test_extract_docx(self):
        path = os.path.join(self.tmpdir, "resume.docx")
        _make_minimal_docx(path)
        text = extract_text(path)
        self.assertIn("Python Developer", text)
        self.assertIn("Django", text)

    def test_unsupported_extension_raises(self):
        path = os.path.join(self.tmpdir, "resume.xyz")
        with open(path, "w") as f:
            f.write("data")
        with self.assertRaises(ExtractionError):
            extract_text(path)

    def test_empty_file_raises(self):
        path = os.path.join(self.tmpdir, "empty.txt")
        with open(path, "w") as f:
            f.write("   ")
        with self.assertRaises(ExtractionError):
            extract_text(path)


if __name__ == "__main__":
    unittest.main()
