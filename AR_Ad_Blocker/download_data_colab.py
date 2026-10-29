"""
This script is designed to be run in a Google Colab environment.
It handles mounting Google Drive and copying a dataset (expected as a .zip file)
to the local Colab filesystem for use in training.
"""

from google.colab import drive
import os

def download_and_unzip_from_drive():
    """
    Mounts Google Drive, copies a specified zip file to the /content/ directory,
    and unzips it.
    """
    # 1. Mount Google Drive
    print("---"" Mounting Google Drive ---")
    try:
        drive.mount('/content/drive')
    except Exception as e:
        print(f"An error occurred while mounting Google Drive: {e}")
        return

    # 2. Define file paths
    # IMPORTANT: The user MUST change this path to the correct location of the zip file.
    drive_zip_path = '/content/drive/MyDrive/path/to/your/billboard-dataset.zip'  # <-- CHANGE THIS
    content_zip_path = '/content/billboard-dataset.zip'
    
    # 3. Copy the file from Drive to Colab's local storage
    print(f"---"" Copying Dataset from Google Drive ---")
    print(f"Source: {drive_zip_path}")
    print(f"Destination: {content_zip_path}")

    if not os.path.exists(drive_zip_path):
        print(f"\nError: File not found at '{drive_zip_path}'.")
        print("Please update the 'drive_zip_path' variable in this script with the correct file location.")
        return

    # Use the 'cp' shell command for a clear progress indicator
    !cp "{drive_zip_path}" "{content_zip_path}"
    print("Copy complete.")

    # 4. Unzip the dataset
    if os.path.exists(content_zip_path):
        print(f"---"" Unzipping Dataset ---")
        # The -q flag means 'quiet' to reduce verbose output
        !unzip -q "{content_zip_path}" -d /content/
        print("Unzipping complete.")
        
        # Optional: Clean up the zip file after extraction to save space
        # os.remove(content_zip_path)
        # print("Cleaned up zip file.")
    else:
        print(f"\nError: Zip file not found at '{content_zip_path}'. Cannot unzip.")

if __name__ == '__main__':
    print("Starting dataset download process for Google Colab...")
    download_and_unzip_from_drive()
    print("---"" Script Finished ---")
    print("Your dataset should now be available in the /content/ directory.")
