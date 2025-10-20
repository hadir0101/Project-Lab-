
import os, csv
from pathlib import Path

roots = [
    Path(r"C:\Users\hadir\Downloads\speech_bci_project\data\raw\general"),
    Path(r"C:\Users\hadir\Downloads\speech_bci_project\data\raw\Semantic"),
    Path(r"C:\Users\hadir\Downloads\speech_bci_project\data\raw\acoustic"),
    Path(r"C:\Users\hadir\Downloads\speech_bci_project\data\raw\articulatory")
]
rows = []
for r in roots:
    if not r.exists(): 
        continue
    for f in r.rglob("*"):
        if f.is_file():
            rows.append({"modality": r.name, "rel_path": str(f), "size_bytes": f.stat().st_size})

Path("manifests").mkdir(exist_ok=True, parents=True)
with open("manifests/step0_filelist.csv", "w", newline="", encoding="utf-8") as fp:
    w = csv.DictWriter(fp, fieldnames=["modality","rel_path","size_bytes"])
    w.writeheader(); w.writerows(rows)

print("Total files:", len(rows))
print("By modality:")
from collections import Counter
print(Counter([r["modality"] for r in rows]))
