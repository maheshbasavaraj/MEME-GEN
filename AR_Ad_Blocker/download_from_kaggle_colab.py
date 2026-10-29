"""
This script is designed for a Google Colab environment.
It handles downloading a dataset from Kaggle using the kagglehub library,
and then copies the data from the cache to the /content/ directory
so it can be used by other scripts.
"""

import kagglehub
import os
import shutil

def download_and_prepare_kaggle_dataset():
    """
    Downloads a dataset from Kaggle, then moves it to the expected /content/ location.
    """
    print("--- Starting Kaggle dataset download and preparation ---")

    # 1. Download dataset from Kaggle Hub
    # This will download the dataset to a local cache and return the path.
    # Note: You must accept the dataset license on Kaggle first.
    # You may also need to authenticate to Kaggle in your Colab environment.
    try:
        dataset_path = kagglehub.dataset_download('maheshbasavaraj/billboard-dataset')
        print(f"Dataset downloaded to cache at: {dataset_path}")
    except Exception as e:
        print(f"An error occurred during download: {e}")
        print("Please ensure you have accepted the license on the Kaggle dataset page and are authenticated.")
        return

    # 2. Define source and destination paths
    # The destination is where our training scripts expect to find the data.
    content_destination = '/content/billboard.v1i.yolov8'

    # The source path is the path returned by the kagglehub library itself.
    cached_source_path = dataset_path

    # 3. Copy data from the cache to the /content/ directory
    print(f"\n--- Preparing to copy data from cache to {content_destination} ---")
    if os.path.exists(cached_source_path):
        # Remove the destination directory if it already exists to prevent copy errors.
        if os.path.exists(content_destination):
            print(f"Removing existing directory: {content_destination}")
            shutil.rmtree(content_destination)
        
        # Copy the entire directory tree.
        print(f"Copying '{cached_source_path}' to '{content_destination}'...")
        shutil.copytree(cached_source_path, content_destination)
        print("Copy complete.")
    else:
        print(f"\nError: Could not find the expected folder at '{cached_source_path}'.")
        print("Please use the Colab file browser to inspect the contents of the cache directory and adjust the path if needed.")

if __name__ == '__main__':
    download_and_prepare_kaggle_dataset()
    print("\n--- Script Finished ---")
    print("If successful, the dataset is now ready in the /content/ directory.")
