
import csv
from pathlib import Path

CLEAN = Path("manifests/clean_index.csv")
SPLIT_DIR = Path("splits")
SPLIT_DIR.mkdir(parents=True, exist_ok=True)

train_subjs = [f"sub-{i:02d}" for i in range(1, 12)]   # 01..11
val_subjs   = [f"sub-{i:02d}" for i in range(12, 14)]  # 12..13
test_subjs  = [f"sub-{i:02d}" for i in range(14, 16)]  # 14..15

rows = list(csv.DictReader(open(CLEAN, newline="", encoding="utf-8")))
def write_subset(name, subjects):
    out = SPLIT_DIR / f"{name}.csv"
    sel = [r for r in rows if r["subject"] in subjects]
    if sel:
        with open(out, "w", newline="", encoding="utf-8") as fp:
            w = csv.DictWriter(fp, fieldnames=rows[0].keys())
            w.writeheader(); w.writerows(sel)
    print(f"{name}: {len(sel)} rows -> {out}")

write_subset("train", train_subjs)
write_subset("val",   val_subjs)
write_subset("test",  test_subjs)
