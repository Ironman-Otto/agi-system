import sys
from pathlib import Path


CANONICAL_SELECTION_RULES = {
    "cmb_core": ["specification_v3", "v3"],
    "behavior_model": ["Section 5", "Behavior Matrix"],
    "intent_model": ["Intent Object", "Directive"],
    "objective_governance": ["Objective Taxonomy", "Termination"],
    "questioning_subsystem": ["Question Generation"],
    "reflection_subsystem": ["Reflection"],
    "persistence_replay": ["Persistence"],
    "execution_model": ["Section 6"],
    "event_model": ["Section 4"],
    "identity_traceability": ["Section 7"],
    "system_overview": ["Skeleton", "Overview"]
}


def choose_authoritative(docs, rules):
    for keyword in rules:
        for d in docs:
            if keyword.lower() in d.lower():
                return d
    return docs[0] if docs else None


def main(normalized_folder):

    folder = Path(normalized_folder)
    clustering_file = folder / "architecture_module_clustering.md"

    text = clustering_file.read_text(encoding="utf-8")

    lines = text.splitlines()

    module_map = {}
    current_module = None

    for line in lines:
        if line.startswith("## ") and not line.startswith("## v"):
            current_module = line.replace("## ", "").strip()
            module_map[current_module] = []
        elif line.startswith("- ") and current_module:
            module_map[current_module].append(line.replace("- ", "").strip())

    output_lines = []
    output_lines.append("# Architecture Module Authority Map\n")

    for module, docs in module_map.items():
        rules = CANONICAL_SELECTION_RULES.get(module, [])
        authoritative = choose_authoritative(docs, rules)

        output_lines.append(f"## {module}\n")
        output_lines.append(f"Authoritative Base: {authoritative}")
        output_lines.append("Supporting Documents:")
        for d in docs:
            if d != authoritative:
                output_lines.append(f"- {d}")
        output_lines.append("")

    output_path = folder / "architecture_module_authority_map.md"
    output_path.write_text("\n".join(output_lines), encoding="utf-8")

    print("Module authority map generated.")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python generate_module_authority_map.py <normalized_folder>")
        sys.exit(1)

    main(sys.argv[1])
