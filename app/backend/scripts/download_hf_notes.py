import os
import subprocess
import sys


def install(package):
    subprocess.check_call([sys.executable, "-m", "pip", "install", package])


try:
    import pandas as pd
    from datasets import load_dataset
except ImportError:
    print("Installing required packages...")
    install("datasets")
    install("pandas")
    from datasets import load_dataset

print("Downloading clinical notes from HuggingFace (tstadel/maccrobat)...")
dataset = load_dataset("tstadel/maccrobat", split="train")

out_dir = "d:/projects/chatbot-hospital-system/app/backend/data/mimic"
os.makedirs(out_dir, exist_ok=True)
out_file = os.path.join(out_dir, "NOTEEVENTS.csv")

df = dataset.to_pandas()
# Map to MIMIC-like schema
df["subject_id"] = df.index.astype(str)
df["category"] = "Discharge summary"
df["description"] = "Clinical Note"
# Ensure 'text' column exists
if "text" not in df.columns:
    print("Warning: 'text' column not found in dataset. Checking columns:", df.columns)

df.to_csv(out_file, index=False)
print(f"Successfully downloaded {len(df)} clinical notes and saved to {out_file}")
