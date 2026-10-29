
# Constitution

## Core Directives

1.  **Primary Goal:** Develop a billboard detection model that is both highly accurate and lightweight.
2.  **Target Platform:** The model should be optimized for deployment on edge devices or in environments with limited computational resources.
3.  **User:** The end-user is a developer who will integrate this model into a larger application for ad analysis or urban environment monitoring.

## UX Requirements

1.  **Simplicity:** The final output should be a single, quantized model file (`.onnx` or `.tflite`) that is easy to use.
2.  **Performance:** Inference speed is a critical metric. The model must be fast.
3.  **Clarity:** The training process, from starting with a base model to exporting the final quantized version, must be clearly documented and reproducible in a Kaggle notebook.

## Development Guidelines

1.  **Framework:** We will use the `ultralytics` Python library and the YOLOv8 architecture.
2.  **Model Selection:** We will start with a small, pre-trained model (`yolov8s.pt`) to balance performance and size.
3.  **Optimization:** The primary optimization techniques will be data augmentation during training and post-training INT8 quantization.
4.  **Workflow:** We will follow the `speckit` methodology (Specify, Plan, Tasks, Implement) for a structured development process.
5.  **Environment:** All development and training will be done within a Kaggle notebook to ensure reproducibility.
