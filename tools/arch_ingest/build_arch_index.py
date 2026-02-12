import json
import sys
from pathlib import Path
from collections import Counter
import re


MODULE_KEYWORDS = [
    "CMB",
    "AEM",
    "Behavior",
    "Intent",
    "Transport",
    "ACK",
    "Message",
    "Concept",
    "Planner",
    "Router",
    "Matrix",
]


def analyze_text(text: str):
    words = re.findall(r"\b[A-Za-z_]+\b", text)
    counter = Counter(words)

    module_hits = {}
    for keyword in MODULE_KEYWORDS:
        module_hits[keyword] = counter.get(keyword, 0)

    return {
        "total_words": len(words),
        "module_mentions": module_hits
    }


def main(normalized_folder: str):

    folder = Path(normalized_folder)
    report = {}

    for file in folder.glob("*.txt"):

        text = file.read_text(encoding="utf-8", errors="ignore")
        analysis = analyze_text(text)

        report[file.name] = analysis

    output_path = folder / "architecture_analysis.json"
    output_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print("Analysis complete.")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python build_arch_index.py <normalized_folder>")
        sys.exit(1)

    main(sys.argv[1])
