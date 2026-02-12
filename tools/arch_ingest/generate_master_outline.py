import sys
from pathlib import Path
import re
from collections import defaultdict, Counter


# Broad architecture domain categories
DOMAIN_KEYWORDS = {
    "CMB": ["CMB", "Router", "Message", "Transport", "ACK", "Communication"],
    "AEM": ["AEM", "Executive", "Cognitive Executive", "Agent Loop"],
    "Behavior": ["Behavior", "Behavior Matrix", "Execution Model"],
    "Intent": ["Intent", "Directive", "Objective", "Taxonomy"],
    "Questioning": ["Question", "Curiosity", "Inquiry"],
    "Reflection": ["Reflection", "Self-assessment", "Meta"],
    "Persistence": ["Persistence", "Replay", "Storage"],
    "Concept Space": ["Concept", "Conceptual Model"],
    "Error Handling": ["Error", "Recovery", "Fault"],
    "Learning": ["Learning", "Adaptation"],
    "Hardware": ["FPGA", "ASIC", "CLM", "Hardware"]
}


def detect_headings(text):
    lines = text.splitlines()
    headings = []
    for line in lines:
        if len(line.strip()) > 0 and len(line.strip()) < 120:
            if line.strip().istitle() or line.strip().startswith("Architecture"):
                headings.append(line.strip())
    return headings[:20]  # limit noise


def detect_domains(text):
    found = []
    for domain, keywords in DOMAIN_KEYWORDS.items():
        for kw in keywords:
            if kw.lower() in text.lower():
                found.append(domain)
                break
    return found


def main(normalized_folder):

    folder = Path(normalized_folder)
    documents = list(folder.glob("*.txt"))

    domain_map = defaultdict(list)
    heading_map = {}

    for doc in documents:
        text = doc.read_text(encoding="utf-8", errors="ignore")

        domains = detect_domains(text)
        for d in domains:
            domain_map[d].append(doc.name)

        headings = detect_headings(text)
        heading_map[doc.name] = headings

    # Build outline
    outline = []
    outline.append("# Master Architecture Outline\n")

    for domain in sorted(domain_map.keys()):
        outline.append(f"## {domain}\n")
        for doc in sorted(domain_map[domain]):
            outline.append(f"- {doc}")
        outline.append("")

    outline.append("\n---\n")
    outline.append("# Document Headings Snapshot\n")

    for doc, headings in heading_map.items():
        outline.append(f"\n## {doc}\n")
        for h in headings[:10]:
            outline.append(f"- {h}")

    output_path = folder / "architecture_master_outline.md"
    output_path.write_text("\n".join(outline), encoding="utf-8")

    print("Master outline generated.")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python generate_master_outline.py <normalized_folder>")
        sys.exit(1)

    main(sys.argv[1])
