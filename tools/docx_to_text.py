# tools/docx_to_text.py

import sys
from docx import Document
from pathlib import Path

def extract_docx_text(path: Path) -> str:
    doc = Document(path)
    return "\n".join(p.text for p in doc.paragraphs)

if __name__ == "__main__":
    input_path = Path(sys.argv[1])
    output_path = input_path.with_suffix(".extracted.txt")

    text = extract_docx_text(input_path)
    output_path.write_text(text, encoding="utf-8")

    print(f"Extracted: {output_path}")
