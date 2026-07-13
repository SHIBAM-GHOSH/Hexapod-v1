from ultralytics import YOLO

# Load the OpenVINO exported model
model = YOLO("yolov8n_openvino_model")

# Run person detection on webcam
model.predict(
    source=0,          # Use default webcam
    classes=[0],       # Detect only humans
    conf=0.5,          # Confidence threshold
    show=True,         # Display output window
    device="cpu"       # OpenVINO uses Intel-optimized inference
)

#With OpenVINO, device="cpu" uses the OpenVINO runtime, not standard PyTorch CPU inference.