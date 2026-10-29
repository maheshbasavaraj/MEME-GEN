import os
import glob
import shutil
from ultralytics import YOLO

def consolidate_labels(dataset_path):
    """Consolidates all class IDs in YOLO label files to 0."""
    print("\n--- Consolidating labels to a single class (0) ---")
    label_dirs = ['train/labels', 'valid/labels', 'test/labels']
    total_labels_changed = 0
    for dir_name in label_dirs:
        full_path = os.path.join(dataset_path, dir_name)
        if not os.path.isdir(full_path):
            continue
        for file_path in glob.glob(os.path.join(full_path, '*.txt')):
            lines_to_write = []
            changed_in_this_file = False
            with open(file_path, 'r') as f:
                for line in f:
                    parts = line.strip().split()
                    if parts and int(parts[0]) != 0:
                        parts[0] = '0'
                        total_labels_changed += 1
                        changed_in_this_file = True
                    lines_to_write.append(' '.join(parts) + '\n')
            if changed_in_this_file:
                with open(file_path, 'w') as f:
                    f.writelines(lines_to_write)
    print(f"Label consolidation complete. Total labels changed: {total_labels_changed}")

def create_yaml_config(dataset_path):
    """Creates the final_data.yaml file pointing to the corrected dataset."""
    print("\n--- Creating final data.yaml for training ---")
    yaml_content = f"""
train: {dataset_path}/train/images
val: {dataset_path}/valid/images
nc: 1
names: ['billboard']
"""
    yaml_path = "/content/final_data.yaml"
    with open(yaml_path, "w") as f:
        f.write(yaml_content)
    print(f"Successfully created {yaml_path}")
    return yaml_path

def train_model(data_yaml_path):
    """Trains the YOLOv8 model."""
    print("\n--- Starting model training ---")
    # Initialize the model with a pre-trained model (e.g., yolov8s.pt)
    model = YOLO('yolov8s.pt')
    
    # Train the model
    model.train(
        data=data_yaml_path,
        epochs=100,
        patience=10,
        batch=16,
        imgsz=640,
        project='/content/runs/detect',
        name='train_final'
    )
    print("\n--- Training pipeline complete! ---")

if __name__ == '__main__':
    # This script is designed to be run in a Google Colab environment.
    # 1. Place your dataset (e.g., 'billboard.v1i.yolov8') in the '/content/' directory.
    # 2. Make sure you have installed the required libraries:
    #    !pip install ultralytics

    # Define the path to your dataset in the Colab environment.
    dataset_path = "/content/billboard.v1i.yolov8"

    print("--- Starting YOLOv8 Training Pipeline for Google Colab ---")
    
    # Verify that the dataset exists
    if not os.path.isdir(dataset_path):
        print(f"Error: Dataset not found at '{dataset_path}'.")
        print("Please upload your dataset to the /content/ directory before running.")
    else:
        # 1. Consolidate labels in the dataset
        consolidate_labels(dataset_path)

        # 2. Create the YAML config file for the dataset
        final_yaml_path = create_yaml_config(dataset_path)

        # 3. Run the training
        train_model(final_yaml_path)
