import base64
import csv
import os
import shutil

csv_path = "ecg/multisession_ECG-ID.csv"
source_dir = "ecg/untouched_datasets/ECG-ID"
target_dir = "ecg_structured/ECG-ID"

os.makedirs(target_dir, exist_ok=True)

valid_folders = set()
if os.path.exists(csv_path):
    with open(csv_path, mode="r", encoding="utf-8") as f:
        reader = csv.reader(f)
        for row in reader:
            if row:
                valid_folders.add(row[0].strip())

# Added '#' delimiter here for max length calculation
strings_to_encode = [f"{folder}#ECG-ID" for folder in valid_folders]
if strings_to_encode:
    max_len = max(len(s) for s in strings_to_encode)
else:
    max_len = 0

for folder_name in os.listdir(source_dir):
    source_folder_path = os.path.join(source_dir, folder_name)

    if os.path.isdir(source_folder_path) and folder_name in valid_folders:
        # Added '#' delimiter here between the folder name and dataset string
        combined_text = f"{folder_name}#ECG-ID"
        padded_text = combined_text.ljust(max_len)

        # Swapped b64encode for b32encode and removed the trailing "=" symbols cleanly
        encoded_name = (
            base64.b32encode(padded_text.encode("utf-8"))
            .decode("utf-8")
            .replace("=", "")
        )

        target_folder_path = os.path.join(target_dir, encoded_name)
        os.makedirs(target_folder_path, exist_ok=True)

        for file_name in os.listdir(source_folder_path):
            src_file_path = os.path.join(source_folder_path, file_name)

            if os.path.isfile(src_file_path):
                name_part, ext = os.path.splitext(file_name)
                ext = ext.lower()

                if ext == ".atr":
                    continue

                new_name_part = name_part.replace("rec_", "RECORD_")
                dest_file_path = os.path.join(
                    target_folder_path, f"{new_name_part}{ext}"
                )

                if ext == ".hea":
                    with open(src_file_path, "r", encoding="utf-8") as f:
                        content = f.read()

                    updated_content = content.replace("rec_", "RECORD_")

                    with open(dest_file_path, "w", encoding="utf-8") as f:
                        f.write(updated_content)

                elif ext == ".dat":
                    shutil.copy2(src_file_path, dest_file_path)

        print(f"Processed & Moved: {folder_name} -> {encoded_name}")

print("\nProcessing complete! Only .dat and updated .hea files kept.")