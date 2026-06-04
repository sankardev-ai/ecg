import base64
import csv
import os
import shutil
from collections import defaultdict

csv_file_path = "ecg/multisession_MIMIC-IV-ECG_Demo.csv"
output_base_dir = "ecg_structured"

SUFFIX_STR = "MIMIC-IV-ECG_Demo"
extensions = [".hea", ".dat"]

person_session_mapping = defaultdict(dict)
unique_people = set()

with open(csv_file_path, mode="r", encoding="utf-8") as infile:
    reader = csv.reader(infile)
    for row in reader:
        if not row:
            continue
        base_source_path = row[0].strip()

        parts = base_source_path.split("/")
        if len(parts) >= 3:
            person_id = parts[-3]
            session_id = parts[-2]
            unique_people.add(person_id)

            if session_id not in person_session_mapping[person_id]:
                next_index = len(person_session_mapping[person_id]) + 1
                person_session_mapping[person_id][
                    session_id
                ] = f"RECORD_{next_index}"

max_len = max(len(pid + "#" + SUFFIX_STR) for pid in unique_people)


def get_base32_folder_name(person_id, total_width):
    combined = person_id + "#" + SUFFIX_STR
    padded = combined.ljust(total_width)

    encoded_str = base64.b32encode(padded.encode("utf-8")).decode("utf-8")

    return encoded_str.replace("=", "")


encoded_folder_map = {
    pid: get_base32_folder_name(pid, max_len) for pid in unique_people
}

copied_files_count = 0
missing_records_count = 0

with open(csv_file_path, mode="r", encoding="utf-8") as infile:
    reader = csv.reader(infile)

    for row in reader:
        if not row:
            continue

        base_source_path = row[0].strip()
        record_found = False

        parts = base_source_path.split("/")
        person_id = parts[-3]
        session_id = parts[-2]
        file_base_name = parts[-1]

        encoded_folder = encoded_folder_map[person_id]
        record_alias = person_session_mapping[person_id][session_id]

        for ext in extensions:
            source_file = base_source_path + ext

            if os.path.exists(source_file):
                record_found = True

                relative_path = os.path.join(
                    output_base_dir,
                    "MIMIC-IV-ECG_Demo",
                    encoded_folder,
                    record_alias + ext,
                )
                destination_file = os.path.abspath(relative_path)

                destination_dir = os.path.dirname(destination_file)
                os.makedirs(destination_dir, exist_ok=True)

                shutil.copy2(source_file, destination_file)
                copied_files_count += 1

                if ext == ".hea":
                    with open(destination_file, "r", encoding="utf-8") as f:
                        hea_content = f.read()

                    updated_hea_content = hea_content.replace(
                        file_base_name, record_alias
                    )

                    with open(destination_file, "w", encoding="utf-8") as f:
                        f.write(updated_hea_content)
            else:
                print(f"Warning: File missing: {source_file}")

        if not record_found:
            missing_records_count += 1

print("\n--- Task Completed ---")
print(
    f"Successfully processed {copied_files_count} files using delimited Base32 directory names."
)