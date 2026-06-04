import base64
import os
import shutil
import pandas as pd
from collections import defaultdict

csv_path = "ecg/multisession_PTB-XL.csv"
source_base_dir = "ecg/untouched_datasets/PTB-XL"
dest_base_dir = "ecg_structured/PTB"

df = pd.read_csv(csv_path)

if "patient_id" not in df.columns or "filename_hr" not in df.columns:
    raise ValueError("CSV must contain 'patient_id' and 'filename_hr' columns.")

patient_groups = defaultdict(list)
for _, row in df.iterrows():
    p_id = str(row["patient_id"])
    rel_path = row["filename_hr"]
    if not pd.isna(rel_path) and not pd.isna(p_id):
        patient_groups[p_id].append(rel_path)

strings_to_encode = [f"{p_id}#PTB" for p_id in patient_groups.keys()]
max_len = max(len(s) for s in strings_to_encode) if strings_to_encode else 0


def get_encoded_folder_name(original_name, max_length):
    combined_text = f"{original_name}#PTB"
    padded_text = combined_text.ljust(max_length)
    encoded_name = (
        base64.b32encode(padded_text.encode("utf-8"))
        .decode("utf-8")
        .replace("=", "")
    )
    return encoded_name


copied_count = 0

for patient_id, paths in patient_groups.items():
    paths.sort()

    encoded_folder_name = get_encoded_folder_name(patient_id, max_len)

    patient_dest_dir = os.path.join(dest_base_dir, encoded_folder_name)
    os.makedirs(patient_dest_dir, exist_ok=True)

    for index, rel_path in enumerate(paths, start=1):
        record_name = f"RECORD_{index}"
        old_base_name = os.path.basename(rel_path)

        src_hea = os.path.join(source_base_dir, rel_path + ".hea")
        src_dat = os.path.join(source_base_dir, rel_path + ".dat")

        dest_hea = os.path.join(patient_dest_dir, f"{record_name}.hea")
        dest_dat = os.path.join(patient_dest_dir, f"{record_name}.dat")

        if os.path.exists(src_hea) and os.path.exists(src_dat):
            with open(src_hea, "r", encoding="utf-8") as f:
                lines = f.readlines()

            if lines:
                first_line_parts = lines[0].split()
                if first_line_parts:
                    first_line_parts[0] = record_name
                    lines[0] = " ".join(first_line_parts) + "\n"

            for i in range(1, len(lines)):
                if old_base_name in lines[i]:
                    lines[i] = lines[i].replace(old_base_name, record_name)

            with open(dest_hea, "w", encoding="utf-8") as f:
                f.writelines(lines)

            shutil.copy2(src_dat, dest_dat)

            copied_count += 2
        else:
            print(f"Warning: Pair missing for {rel_path} at source.")

print(
    f"Process complete. Successfully copied and encoded data into {copied_count} files."
)