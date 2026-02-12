import sys
from pathlib import Path
from collections import defaultdict, Counter
import re


CANONICAL_MODULES = {
    "cmb_core": ["CMB", "Channel", "Router", "Communication", "Socket"],
    "cmb_ack_protocol": ["ACK", "Acknowledgement", "State Machine"],
    "message_schema_contracts": ["Message Contract", "Envelope", "Schema", "Payload"],
    "event_model": ["Event Model", "Event", "Event Type"],
    "execution_model": ["Execution Model", "Task Lifecycle"],
    "behavior_model": ["Behavior", "Behavior Matrix"],
    "intent_model": ["Intent", "Directive"],
    "objective_governance": ["Objective", "Taxonomy", "Priority"],
    "questioning_subsystem": ["Question", "Curiosity", "Inquiry"],
    "reflection_subsystem": ["Reflection", "Self-assessment"],
    "learning_subsystem": ["Learning", "Behavior Extraction"],
    "persistence_replay": ["Persistence", "Replay"],
    "identity_traceability": ["Identity", "Traceability", "Correlation"],
    "hardware_architecture": ["FPGA", "ASIC", "Hardware", "CLM", "L Series"],
    "system_overview": ["Overview", "Skeleton", "Architecture Summary"]
}


def score_document(text):
    scores = Counter()
    for module, keywords in CANONICAL_MODULES.items():
        for kw in keywords:
            matches = len(re.findall(re.escape(kw), text, re.IGNORECASE))
            scores[module] += matches
    return scores


def detect_version_family(filename):
    match = re.search(r'v(\d+)', filename.lower())
    return match.group(0) if match else None


def main(normalized_folder):

    folder = Path(normalized_folder)
    documents = list(folder.glob("*.txt"))

    module_map = defaultdict(list)
    version_map = defaultdict(list)

    for doc in documents:
        text = doc.read_text(encoding="utf-8", errors="ignore")
        scores = score_document(text)

        if scores:
            primary_module = scores.most_common(1)[0][0]
        else:
            primary_module = "unclassified"

        module_map[primary_module].append(doc.name)

        version = detect_version_family(doc.name)
        if version:
            version_map[version].append(doc.name)

    # Write output
    output_lines = []
    output_lines.append("# Canonical Module Clustering\n")

    for module in sorted(module_map.keys()):
        output_lines.append(f"## {module}\n")
        for doc in sorted(module_map[module]):
            output_lines.append(f"- {doc}")
        output_lines.append("")

    output_lines.append("\n---\n# Version Families\n")

    for version in sorted(version_map.keys()):
        output_lines.append(f"\n## {version}\n")
        for doc in version_map[version]:
            output_lines.append(f"- {doc}")

    output_path = folder / "architecture_module_clustering.md"
    output_path.write_text("\n".join(output_lines), encoding="utf-8")

    print("Clustering complete.")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python cluster_architecture_modules.py <normalized_folder>")
        sys.exit(1)

    main(sys.argv[1])
