#!/usr/bin/env python3
"""
Recombine CSV chunks into single file
"""

import pandas as pd
import glob
import os

CHUNKS_DIR = "cleaned_data_chunks"
OUTPUT_FILE = "cleaned_enriched.csv"

print(f"Recombining CSV chunks from {CHUNKS_DIR}/...")

# Find all chunk files
chunk_files = sorted(glob.glob(f"{CHUNKS_DIR}/cleaned_enriched_part_*.csv"))

if not chunk_files:
    print(f"Error: No chunk files found in {CHUNKS_DIR}/")
    exit(1)

print(f"Found {len(chunk_files)} chunk files:")
for f in chunk_files:
    size_mb = os.path.getsize(f) / (1024 * 1024)
    print(f"  {os.path.basename(f)}: {size_mb:.2f} MB")

# Read and combine
print(f"\nCombining chunks...")
chunks = []
for chunk_file in chunk_files:
    df = pd.read_csv(chunk_file)
    chunks.append(df)
    print(f"  Loaded {len(df)} rows from {os.path.basename(chunk_file)}")

# Concatenate
df_combined = pd.concat(chunks, ignore_index=True)

# Write
df_combined.to_csv(OUTPUT_FILE, index=False)

output_size_mb = os.path.getsize(OUTPUT_FILE) / (1024 * 1024)
print(f"\n✓ Combined {len(df_combined)} rows into {OUTPUT_FILE} ({output_size_mb:.2f} MB)")
