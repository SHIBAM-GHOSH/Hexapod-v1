import time
from ultralytics import YOLO

# Load OpenVINO model
model = YOLO(
    r"D:\CS_Projects\Yolo8n\yolov8n_openvino_model",
    task="detect"
)

# Image path
image_path = r"D:\CS_Projects\Yolo8n\Compare-models\test.jpg"

# Warm-up on GPU
for _ in range(5):
    model.predict(
        image_path,
        device="GPU",
        verbose=False
    )

# Benchmark on GPU
N = 20
start = time.perf_counter()

for _ in range(N):
    results = model.predict(
        image_path,
        device="GPU",
        verbose=False
    )

end = time.perf_counter()

avg_ms = (end - start) * 1000 / N

print("-" * 50)
print(f"Average total time over {N} runs: {avg_ms:.2f} ms")
print("-" * 50)

print("Ultralytics timing breakdown:")
print(results[0].speed)