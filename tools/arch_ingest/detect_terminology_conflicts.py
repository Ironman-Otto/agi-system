import sys
from pathlib import Path
import re
from collections import defaultdict


TARGET_TERMS = [
    "Intent",
    "Directive",
    "Objective",
    "Behavior",
    "Message",
    "Event",
    "ACK",
    "Reflection",
    "Question",
    "Executive",
    "CMB",
    "Persistence"
]


DEFINITION_PATTERNS = [
    r"(\b{}\b\s+is\s+.+?\. )",
    r"(\b{}\b\s+refers\s+to\s+.+?\. )",
    r"(\b{}\b\s+represents\s+.+?\. )",
    r"(\b{}\b\s+defines\s+.+?\. )"
]


def extract_definitions(text, term):
    definitions = []
    for pattern in DEFINITION_PATTERNS:
        regex = pattern.format(term)
        matches = re.findall(regex, text, re.IGNORECASE | re.DOTALL)
        for m in matches:
            cleaned = m.strip().replace("\n", " ")
            definitions.append(cleaned)
    return definitions


def main(normalized_folder):

    folder = Path(normalized_folder)
    documents = list(folder.glob("*.txt"))

    term_map = defaultdict(list)

    for doc in documents:
        text = doc.read_text(encoding="utf-8", errors="ignore")

        for term in TARGET_TERMS:
            defs = extract_definitions(text, term)
            for d in defs:
                term_map[term].append({
                    "document": doc.name,
                    "definition": d
                })

    output_lines = []
    output_lines.append("# Terminology Conflict Report\n")

    for term in TARGET_TERMS:
        entries = term_map.get(term, [])
        if len(entries) > 1:
            output_lines.append(f"\n## {term}\n")
            for e in entries:
                output_lines.append(f"- ({e['document']}) {e['definition']}")
            output_lines.append("")

    output_path = folder / "terminology_conflicts_report.md"
    output_path.write_text("\n".join(output_lines), encoding="utf-8")

    print("Terminology conflict report generated.")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python detect_terminology_conflicts.py <normalized_folder>")
        sys.exit(1)

    main(sys.argv[1])
