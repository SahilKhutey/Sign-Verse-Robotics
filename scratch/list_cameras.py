import cv2

def list_cameras(max_to_test=10):
    available_indices = []
    print("[Discovery] Probing hardware indices 0-10...")
    for i in range(max_to_test):
        cap = cv2.VideoCapture(i)
        if cap.isOpened():
            ret, _ = cap.read()
            if ret:
                available_indices.append(i)
            cap.release()
    print(f"[Discovery] Found {len(available_indices)} active camera(s): {available_indices}")
    return available_indices

if __name__ == "__main__":
    list_cameras()
