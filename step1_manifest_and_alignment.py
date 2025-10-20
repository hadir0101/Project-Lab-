# step1_manifest_and_alignment.py
import csv, re
from pathlib import Path
from collections import Counter, defaultdict

# Accept both lower- and upper-case folder names just in case
CAND_ROOTS = [
    ("general",       Path(r"C:\Users\hadir\Downloads\speech_bci_project\data\raw\general")),
    ("semantics",     Path(r"C:\Users\hadir\Downloads\speech_bci_project\data\raw\Semantic")),  # or \semantics if that's your folder
    ("acoustic",      Path(r"C:\Users\hadir\Downloads\speech_bci_project\data\raw\acoustic")),
    ("articulatory",  Path(r"C:\Users\hadir\Downloads\speech_bci_project\data\raw\articulatory")),
]
ROOTS = []
for canonical, p in CAND_ROOTS:
    if p.exists():
        ROOTS.append((canonical, p))

if not ROOTS:
    raise SystemExit("No data/raw/* modality folders found.")

def guess_subject(path_str: str):
    # Patterns: sub-01, sub_01, sub01, s01
    for pat in [r"(sub[-_ ]?\d{2,3})", r"(s\d{2,3})"]:
        m = re.search(pat, path_str, flags=re.IGNORECASE)
        if m:
            return m.group(1).lower().replace(" ", "").replace("_", "-")
    return None

def guess_trial(path_str: str):
    # Patterns: word-23, trial_045, utt12, item7, w23, t45
    pats = [
        r"(word|trial|utt|item)[-_ ]?(\d+)",
        r"(w|t)[-_ ]?(\d+)",
    ]
    for pat in pats:
        m = re.search(pat, path_str, flags=re.IGNORECASE)
        if m:
            label = m.group(1).lower()
            num = int(m.group(2))
            return f"{label}-{num}"
    return None

manifest_rows = []
for modality, root in ROOTS:
    for f in root.rglob("*"):
        if f.is_file():
            rel = f.as_posix()
            row = {
                "modality": modality,
                "rel_path": rel,
                "filename": f.name,
                "ext": f.suffix.lower(),
                "size_bytes": f.stat().st_size,
                "subject_guess": guess_subject(rel),
                "trial_guess": guess_trial(rel),
            }
            manifest_rows.append(row)

# Write manifest
Path("manifests").mkdir(parents=True, exist_ok=True)
man_path = Path("manifests/manifest.csv")
with man_path.open("w", newline="", encoding="utf-8") as fp:
    w = csv.DictWriter(fp, fieldnames=list(manifest_rows[0].keys()))
    w.writeheader()
    w.writerows(manifest_rows)


by_key = defaultdict(lambda: {"general":0,"semantics":0,"acoustic":0,"articulatory":0, "files":[]})
for r in manifest_rows:
    key = (r["subject_guess"], r["trial_guess"])
    by_key[key][r["modality"]] += 1
    by_key[key]["files"].append(r["rel_path"])

def _safe(x):  
    return "" if x is None else x

align_rows = []
complete_quads = 0

for (subj, trial), data in sorted(by_key.items(), key=lambda kv: (_safe(kv[0][0]), _safe(kv[0][1]))):
    row = {
        "subject": subj,
        "trial": trial,
        "has_general": int(data["general"] > 0),
        "has_semantics": int(data["semantics"] > 0),
        "has_acoustic": int(data["acoustic"] > 0),
        "has_articulatory": int(data["articulatory"] > 0),
        "total_files_for_key": data["general"] + data["semantics"] + data["acoustic"] + data["articulatory"],
    }
    if row["has_general"] and row["has_semantics"] and row["has_acoustic"] and row["has_articulatory"]:
        complete_quads += 1
    align_rows.append(row)


align_path = Path("manifests/alignment_report.csv")
with align_path.open("w", newline="", encoding="utf-8") as fp:
    w = csv.DictWriter(fp, fieldnames=list(align_rows[0].keys()))
    w.writeheader()
    w.writerows(align_rows)


missing_rows = [r for r in manifest_rows if (not r["subject_guess"] or not r["trial_guess"])]
miss_path = Path("manifests/missing_keys.csv")
with miss_path.open("w", newline="", encoding="utf-8") as fp:
    w = csv.DictWriter(fp, fieldnames=list(manifest_rows[0].keys()))
    w.writeheader()
    w.writerows(missing_rows)



print(f"Wrote manifest -> {man_path}")
print(f"Wrote alignment -> {align_path}")
print("By modality:", Counter(r["modality"] for r in manifest_rows))
print("Missing subject guesses:", sum(1 for r in manifest_rows if not r["subject_guess"]))
print("Missing trial guesses:", sum(1 for r in manifest_rows if not r["trial_guess"]))
print("Complete (subject,trial) with ALL 4 modalities:", complete_quads)
missing_any = sum(1 for r in align_rows if (r["has_general"] + r["has_semantics"] + r["has_acoustic"] + r["has_articulatory"]) < 4)
print("Keys missing at least one modality:", missing_any)
