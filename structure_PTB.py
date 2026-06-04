import base64
import os
import shutil

src_dir = "ecg/untouched_datasets/PTB"
dst_dir = "ecg_structured/PTB"

patient_folders = []
if os.path.exists(src_dir):
    for item in os.listdir(src_dir):
        if os.path.isdir(os.path.join(src_dir, item)):
            patient_folders.append(item)

strings_to_encode = [f"{folder}#PTB" for folder in patient_folders]
max_len = max(len(s) for s in strings_to_encode) if strings_to_encode else 0


def get_encoded_folder_name(original_name, max_length):
    combined_text = f"{original_name}#PTB"
    padded_text = combined_text.ljust(max_length)
    encoded_name = (
        base64.b32encode(padded_text.encode("utf-8")).decode("utf-8").replace("=", "")
    )
    return encoded_name


if not os.path.exists(src_dir):
    exit()

os.makedirs(dst_dir, exist_ok=True)

for folder_name in os.listdir(src_dir):
    src_patient_path = os.path.join(src_dir, folder_name)

    if os.path.isdir(src_patient_path):
        encoded_folder_name = get_encoded_folder_name(folder_name, max_len)
        dst_patient_path = os.path.join(dst_dir, encoded_folder_name)

        valid_files = [
            f for f in os.listdir(src_patient_path) if not f.endswith(".xyz")
        ]

        if len(valid_files) < 4:
            continue

        os.makedirs(dst_patient_path, exist_ok=True)

        base_records = sorted(
            list(
                set(
                    [
                        os.path.splitext(f)[0]
                        for f in valid_files
                        if f.endswith((".dat", ".hea"))
                    ]
                )
            )
        )

        for index, old_base in enumerate(base_records, start=1):
            new_base = f"RECORD_{index}"
            old_hea_name = f"{old_base}.hea"
            old_dat_name = f"{old_base}.dat"

            if old_hea_name in valid_files:
                src_hea_path = os.path.join(src_patient_path, old_hea_name)
                dst_hea_path = os.path.join(dst_patient_path, f"{new_base}.hea")

                with open(src_hea_path, "r", encoding="utf-8") as f:
                    lines = f.readlines()

                if lines:
                    first_line_parts = lines[0].split()
                    if first_line_parts:
                        first_line_parts[0] = new_base
                        lines[0] = " ".join(first_line_parts) + "\n"

                for i in range(1, len(lines)):
                    if old_base in lines[i]:
                        lines[i] = lines[i].replace(old_base, new_base)

                with open(dst_hea_path, "w", encoding="utf-8") as f:
                    f.writelines(lines)

            if old_dat_name in valid_files:
                src_dat_path = os.path.join(src_patient_path, old_dat_name)
                dst_dat_path = os.path.join(dst_patient_path, f"{new_base}.dat")
                shutil.copy2(src_dat_path, dst_dat_path)