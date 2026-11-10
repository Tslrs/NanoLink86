import cv2, time, sys
out = sys.argv[1]
cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1920); cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)
ret=False; frame=None
for _ in range(20):
    ret, frame = cap.read(); time.sleep(0.05)
cap.release()
if ret and frame is not None:
    cv2.imwrite(out, frame); print("ok", frame.shape, frame.mean())
else: print("capture failed")
