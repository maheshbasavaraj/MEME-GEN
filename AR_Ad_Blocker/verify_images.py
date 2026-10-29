
import os
from PIL import Image
import glob

def verify_and_clean_dataset():
    """
    Verifies image integrity in a hardcoded dataset path, removing corrupted
    images and their corresponding labels.
    """
    # Hardcoded path to the dataset within the Kaggle working directory
    dataset_base_path = '/kaggle/working/billboard-dataset'
    
    # Check if the base path exists
    if not os.path.isdir(dataset_base_path):
        print(f"❌ ERROR: The specified dataset path does not exist: {dataset_base_path}")
        print("Please ensure you have copied the dataset correctly to the /kaggle/working/ directory.")
        return

    image_dirs = ['train/images', 'valid/images', 'test/images']
    corrupted_files = []
    total_checked = 0

    print(f"Starting image integrity check for: {dataset_base_path}")

    for img_dir in image_dirs:
        full_dir_path = os.path.join(dataset_base_path, img_dir)
        if not os.path.isdir(full_dir_path):
            print(f"Info: Directory not found, skipping: {full_dir_path}")
            continue

        print(f"\nChecking directory: {full_dir_path}")
        
        # Use glob to find all image files, case-insensitively
        image_patterns = ['*.jpg', '*.jpeg', '*.png', '*.bmp', '*.gif']
        image_files = []
        for pattern in image_patterns:
            image_files.extend(glob.glob(os.path.join(full_dir_path, pattern), recursive=False))

        if not image_files:
            print("Info: No images found in this directory.")
            continue

        for file_path in image_files:
            total_checked += 1
            try:
                with Image.open(file_path) as img:
                    img.load()  # Attempt to load image data to trigger errors
            except Exception as e:
                print(f"  - Found corrupted file: {os.path.basename(file_path)} (Error: {e})")
                corrupted_files.append(file_path)

    print("\n--- Check Complete ---")
    print(f"Total images checked: {total_checked}")

    if not corrupted_files:
        print("✅ No corrupted images found.")
    else:
        print(f"❌ Found {len(corrupted_files)} corrupted files. Removing them now...")
        for file_path in corrupted_files:
            # Determine the corresponding label path
            label_path = file_path.replace('/images/', '/labels/')
            base, _ = os.path.splitext(label_path)
            label_path = base + '.txt'

            try:
                os.remove(file_path)
                print(f"  - Removed image: {os.path.basename(file_path)}")
                if os.path.exists(label_path):
                    os.remove(label_path)
                    print(f"  - Removed label: {os.path.basename(label_path)}")
            except OSError as e:
                print(f"Error removing file {file_path}: {e}")
        print("✅ All corrupted files have been removed.")

# --- Execute the function when the script is run ---
if __name__ == '__main__':
    verify_and_clean_dataset()
