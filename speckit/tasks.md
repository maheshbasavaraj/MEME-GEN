
# Tasks

This document breaks down the implementation of the billboard detection model into small, actionable tasks.

### Phase 1: Environment Setup & Data Configuration

*   [ ] **Task 1.1:** Create a new Kaggle notebook and enable the GPU accelerator (T4 x2 preferred).
*   [ ] **Task 1.2:** In the first cell, install the `ultralytics` library using `pip`.
*   [ ] **Task 1.3:** Import all necessary libraries (`YOLO`, `os`, etc.).
*   [ ] **Task 1.4:** Verify the location of the billboard dataset and create the `data.yaml` file.
    *   [ ] Confirm paths to `train/images` and `val/images`.
    *   [ ] Define the class names: `names: ['billboard']`.

### Phase 2: Model Training

*   [ ] **Task 2.1:** Define training hyperparameters in a dedicated cell.
    *   `model`: `yolov8s.pt`
    *   `epochs`: 100 (with `early_stopping`)
    *   `patience`: 10 (for early stopping)
    *   `batch`: 16 (or max possible on the GPU)
    *   `imgsz`: 640
*   [ ] **Task 2.2:** Instantiate the YOLO model: `model = YOLO('yolov8s.pt')`.
*   [ ] **Task 2.3:** Launch the training process using `model.train(...)` with the defined hyperparameters.
*   [ ] **Task 2.4:** Monitor the training output to ensure the validation mAP is improving.

### Phase 3: Evaluation and Export

*   [ ] **Task 3.1:** Once training is complete, identify the path to the best model checkpoint (`runs/detect/train/weights/best.pt`).
*   [ ] **Task 3.2:** Load the best model: `model = YOLO('path/to/best.pt')`.
*   [ ] **Task 3.3:** Run the validation command `model.val()` to confirm the final mAP score.
*   [ ] **Task 3.4:** Export the model to ONNX format with INT8 quantization.
    *   Use `model.export(format='onnx', int8=True, data='data.yaml')`.
*   [ ] **Task 3.5:** Verify that the `.onnx` file has been created and note its file size.

### Phase 4: Verification (Optional)

*   [ ] **Task 4.1:** Install `onnxruntime-gpu`.
*   [ ] **Task 4.2:** Write a short script to load the exported `.onnx` model and run inference on a sample image from the validation set.
*   [ ] **Task 4.3:** Confirm that the model produces valid bounding box predictions.
