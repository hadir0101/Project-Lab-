import csv, re
from pathlib import Path
from collections import defaultdict

MANIFEST = Path("manifests/manifest.csv")
OUT_CLEAN = Path("manifests/clean_index.csv")
OUT_DROPPED = Path("manifests/dropped_incomplete.csv")

def safe_read_manifest(p: Path):
    rows = []
    with p.open("r", encoding="utf-8") as fp:
        r = csv.DictReader(fp)
        for row in r:
            rows.append(row)
    return rows

def ensure_subject(row):
    subj = row.get("subject_guess") or ""
    if not subj:
        
        path = row["rel_path"].replace("\\", "/").lower()
        m = re.search(r"(sub[-_ ]?\d{1,3})", path)
        if m:
            subj = m.group(1).replace(" ", "").replace("_", "-")
    return subj or None

def assign_trial_indices(rows):
    """
    For each (subject, modality), sort files by filename then assign trial_idx = 1..N
    """
    grouped = defaultdict(list)
    for row in rows:
        subj = ensure_subject(row)
        if not subj:  
            continue
        grouped[(subj, row["modality"])].append(row)


    trial_map = {}
    for (subj, mod), lst in grouped.items():
        lst_sorted = sorted(lst, key=lambda r: (r["filename"].lower(), r["rel_path"].lower()))
        for i, r in enumerate(lst_sorted, start=1):
            key = (subj, mod, i)
            trial_map[key] = r

    return trial_map

def main():
    rows = safe_read_manifest(MANIFEST)

    trial_map = assign_trial_indices(rows)

    per_subj_counts = defaultdict(lambda: defaultdict(set))  
    per_subj_paths = defaultdict(lambda: defaultdict(dict))  # subj -> trial_idx -> {mod: rel_path}
    modalities = set()

    for (subj, mod, idx), r in trial_map.items():
        modalities.add(mod)
        per_subj_counts[subj][mod].add(idx)
        per_subj_paths[subj][idx][mod] = r["rel_path"]

    clean_rows = []
    dropped_rows = []

    for subj, mod2idxs in per_subj_counts.items():
        if not modalities.issubset(mod2idxs.keys()):
          
            for idx, mod_paths in per_subj_paths[subj].items():
                dropped_rows.append({"subject": subj, "trial_idx": idx, "reason": "subject_missing_modality"})
            continue

        
        common = None
        for mod in modalities:
            idxs = mod2idxs[mod]
            common = idxs if common is None else (common & idxs)

        if not common:
            
            for idx, mod_paths in per_subj_paths[subj].items():
                dropped_rows.append({"subject": subj, "trial_idx": idx, "reason": "no_common_trial_idx"})
            continue

        for idx in sorted(common):
            mod_paths = per_subj_paths[subj][idx]
            if all(m in mod_paths for m in modalities):
                clean_rows.append({
                    "subject": subj,
                    "trial_idx": idx,
                    **{f"{m}_path": mod_paths[m] for m in sorted(modalities)}
                })
            else:
                dropped_rows.append({"subject": subj, "trial_idx": idx, "reason": "missing_one_or_more_modalities"})

   
    OUT_CLEAN.parent.mkdir(parents=True, exist_ok=True)
    if clean_rows:
        fieldnames = ["subject", "trial_idx"] + [f"{m}_path" for m in sorted(modalities)]
        with OUT_CLEAN.open("w", newline="", encoding="utf-8") as fp:
            w = csv.DictWriter(fp, fieldnames=fieldnames)
            w.writeheader(); w.writerows(clean_rows)

    if dropped_rows:
        with OUT_DROPPED.open("w", newline="", encoding="utf-8") as fp:
            w = csv.DictWriter(fp, fieldnames=["subject","trial_idx","reason"])
            w.writeheader(); w.writerows(dropped_rows)

   
    subs = sorted(set(r["subject"] for r in clean_rows))
    print(f"Wrote clean index -> {OUT_CLEAN}  (rows: {len(clean_rows)})")
    print(f"Wrote dropped list -> {OUT_DROPPED}  (rows: {len(dropped_rows)})")
    print(f"Subjects in clean set: {subs}")
   
    from collections import Counter
    c = Counter([r["subject"] for r in clean_rows])
    print("Trials per subject (clean):", dict(c))

if __name__ == "__main__":
    main()
