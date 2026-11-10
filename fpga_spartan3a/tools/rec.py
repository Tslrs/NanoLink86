"""Record the VGA capture card to an mp4: python3 rec.py out.mp4 seconds  (run from the Terminal panel: macOS camera permission)"""
import sys, time, cv2

out, secs = sys.argv[1], float(sys.argv[2])
cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)
for _ in range(10):
    cap.read()
W, H, FPS = 1280, 720, 30
vw = cv2.VideoWriter(out, cv2.VideoWriter_fourcc(*"mp4v"), FPS, (W, H))
t0 = time.time()
n = 0
print("recording...", flush=True)
while time.time() - t0 < secs:
    ok, f = cap.read()
    if not ok:
        continue
    # keep real-time speed: write as many frames as elapsed time requires
    want = int((time.time() - t0) * FPS)
    f = cv2.resize(f, (W, H))
    while n < want:
        vw.write(f)
        n += 1
vw.release()
cap.release()
print("done", n, "frames", flush=True)
