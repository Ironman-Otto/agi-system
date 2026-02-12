import json
import sys
from pathlib import Path

def load_manifest(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))

def load_architecture_texts(files):
    texts = []
    for f in files:
        try:
            texts.append(Path(f).read_text(encoding="utf-8"))
        except:
            pass
    return "\n".join(texts)

def main(code_manifest_path, arch_manifest_path):

    code_manifest = load_manifest(code_manifest_path)
    arch_manifest = load_manifest(arch_manifest_path)

    code_files = [f["path"] for f in code_manifest["files"]]
    arch_files = [f["path"] for f in arch_manifest["files"]]

    # Load architecture text content
    arch_texts = load_architecture_texts(arch_files)

    missing_coverage = []
    for code_file in code_files:
        name = Path(code_file).stem
        if name not in arch_texts:
            missing_coverage.append(code_file)

    orphaned_references = []
    for word in arch_texts.split():
        if word.endswith(".py") and word not in code_files:
            orphaned_references.append(word)

    print("\nDRIFT REPORT")
    print("============")

    print("\nMissing Architecture Coverage:")
    for f in missing_coverage:
        print(" -", f)

    print("\nOrphaned Architecture References:")
    for r in set(orphaned_references):
        print(" -", r)

if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
