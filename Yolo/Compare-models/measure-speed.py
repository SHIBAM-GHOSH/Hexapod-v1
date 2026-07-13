import time
from ultralytics import YOLO

# Load model once
model = YOLO(r"D:\CS_Projects\Yolo8n\yolov8n.pt")

# Warm-up run (ignore timing)
model.predict(r"D:\CS_Projects\Yolo8n\Compare-models\test.jpg", verbose=False)

# Actual timed run
start = time.perf_counter()
model.predict(r"D:\CS_Projects\Yolo8n\Compare-models\test.jpg", verbose=False)
end = time.perf_counter()

print(f"Inference time: {(end - start) * 1000:.2f} ms")