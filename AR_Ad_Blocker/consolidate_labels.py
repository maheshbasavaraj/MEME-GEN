import os
import glob

def consolidate_labels(dataset_path):
    """
    Consolidates all class IDs in YOLO label files to 0.
    """
    label_dirs = ['train/labels', 'valid/labels', 'test/labels']
    total_files_processed = 0
    total_labels_changed = 0

    print(f"Starting label consolidation for dataset at: {dataset_path}")

    for dir_name in label_dirs:
        full_path = os.path.join(dataset_path, dir_name)
        if not os.path.isdir(full_path):
            print(f"Warning: Directory not found, skipping: {full_path}")
            continue

        print(f"\nProcessing directory: {full_path}")
        label_files = glob.glob(os.path.join(full_path, '*.txt'))

        if not label_files:
            print("Info: No label files found in this directory.")
            continue

        for file_path in label_files:
            total_files_processed += 1
            lines_to_write = []
            changed_in_this_file = False

            with open(file_path, 'r') as f:
                lines = f.readlines()

            for line in lines:
                parts = line.strip().split()
                if not parts:
                    continue

                class_id = int(parts[0])
                if class_id != 0:
                    parts[0] = '0'
                    total_labels_changed += 1
                    changed_in_this_file = True

                lines_to_write.append(' '.join(parts) + '\n')

            if changed_in_this_file:
                with open(file_path, 'w') as f:
                    f.writelines(lines_to_write)

    print("\n--- Consolidation Complete ---")
    print(f"Total files processed: {total_files_processed}")
    print(f"Total labels remapped to class 0: {total_labels_changed}")

if __name__ == '__main__':

    # This script is designed to be run in a Google Colab environment.

    # Before running, ensure your dataset folder (e.g., 'billboard.v1i.yolov8')

    # is located in the '/content/' directory.

    

    # Define the path to the dataset in Colab.

    path_to_fix = '/content/billboard.v1i.yolov8'

    

    print("--- Preparing to consolidate labels for Google Colab ---")

    if not os.path.isdir(path_to_fix):

        print(f"Error: Dataset not found at '{path_to_fix}'.")

        print("Please make sure your dataset is uploaded or unzipped in the /content/ directory.")

    else:

        consolidate_labels(path_to_fix)
