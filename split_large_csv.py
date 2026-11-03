#!/usr/bin/env python3
"""
Split large CSV into manageable chunks for git
"""

import pandas as pd
import os

INPUT_FILE = "cleaned_enriched.csv"
OUTPUT_DIR = "cleaned_data_chunks"
CHUNK_SIZE = 1000  # rows per file

# Create output directory
os.makedirs(OUTPUT_DIR, exist_ok=True)

print(f"Splitting {INPUT_FILE} into chunks of {CHUNK_SIZE} rows...")

# Read and split
chunk_num = 1
total_rows = 0

for chunk in pd.read_csv(INPUT_FILE, chunksize=CHUNK_SIZE):
    output_file = f"{OUTPUT_DIR}/cleaned_enriched_part_{chunk_num:03d}.csv"

    # For first chunk, include header
    chunk.to_csv(output_file, index=False)

    rows_in_chunk = len(chunk)
    total_rows += rows_in_chunk
    file_size_mb = os.path.getsize(output_file) / (1024 * 1024)

    print(f"  Part {chunk_num}: {rows_in_chunk} rows, {file_size_mb:.2f} MB -> {output_file}")
    chunk_num += 1

print(f"\nTotal: {total_rows} rows split into {chunk_num - 1} files")
print(f"Output directory: {OUTPUT_DIR}/")
