from ultralytics import YOLO

# Load model
model = YOLO("yolov8n.pt")

# Run webcam inference as a stream
results = model.predict(
    source=0,
    classes=[0],
    show=True,
    stream=True
)

# Process frames continuously
for r in results:
    pass