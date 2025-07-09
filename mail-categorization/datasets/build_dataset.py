from pathlib import Path
import json
import pandas as pd
from datasets import Dataset

#  paths
ROOT = Path(__file__).resolve().parents[1]          # gmail-editor/
RAW  = ROOT / "data" 
PROC = ROOT / "data" / "processed-Dataset"
PROC.mkdir(parents=True, exist_ok=True)

LABELS_F = RAW / "labeled_emails.json"   
META_F   = RAW / "raw_emails.json"   
OUT_DIR  = PROC   

#  helpers
def load_labels(fp):
    """Flatten every object into one list."""
    data = json.load(open(fp))
    rows = []
    for block in data:
        rows.extend(block.get("results", block.get("result", [])))
    return pd.DataFrame(rows)          # id, category


def load_meta(fp):
    return pd.read_json(fp)            # id, sender, subject


#  build
if __name__ == "__main__":
    labels_df = load_labels(LABELS_F)
    meta_df   = load_meta(META_F)

    df = meta_df.merge(labels_df, on="id", how="inner").drop(['id'], axis=1)  

    # drop NA, rename if you want (“text”, “label”, …)
    ds = Dataset.from_pandas(df, preserve_index=False)
    ds.save_to_disk(OUT_DIR)

    print(f"Saved {len(ds):,} rows to {OUT_DIR}")
