import time
from ultralytics import YOLO

# -----------------------------------
# Load PyTorch YOLOv8n model
# -----------------------------------
model = YOLO(r"D:\CS_Projects\Yolo8n\yolov8n.pt")

# -----------------------------------
# Image path
# -----------------------------------
image_path = r"D:\CS_Projects\Yolo8n\Compare-models\test.jpg"

# -----------------------------------
# Warm-up runs (not timed)
# -----------------------------------
for _ in range(5):
    model.predict(
        image_path,
        verbose=False
    )

# -----------------------------------
# Measure average execution time
# -----------------------------------
N = 20
start = time.perf_counter()

for _ in range(N):
    results = model.predict(
        image_path,
        verbose=False
    )

end = time.perf_counter()

avg_ms = (end - start) * 1000 / N

# -----------------------------------
# Print results
# -----------------------------------
print("-" * 50)
print(f"Average total time over {N} runs: {avg_ms:.2f} ms")
print("-" * 50)

print("Ultralytics timing breakdown:")
print(f"Preprocess : {results[0].speed['preprocess']:.2f} ms")
print(f"Inference : {results[0].speed['inference']:.2f} ms")
print(f"Postprocess: {results[0].speed['postprocess']:.2f} ms")