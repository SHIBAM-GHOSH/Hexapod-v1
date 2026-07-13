from ultralytics import YOLO

# Load YOLOv8 Nano model
model = YOLO("yolov8n.pt")

# Start webcam and detect only humans (class 0)
model.predict(
    source=0,
    show=True,
    classes=[0],
    conf=0.5
)