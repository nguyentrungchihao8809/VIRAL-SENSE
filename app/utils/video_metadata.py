# app/agents/utils/video_metadata.py
import cv2

def get_video_info(video_path):

    cap = cv2.VideoCapture(video_path) # mở video bằng OpenCV
    
    fps = cap.get(cv2.CAP_PROP_FPS) # FPS: số frame mỗi giây

    total_frames = cap.get(cv2.CAP_PROP_FRAME_COUNT) # Tổng số frame trong video

    # Tránh chia cho 0
    if fps > 0:
        duration = total_frames / fps
    else:
        duration = 0

    cap.release()

    return {
        "fps": round(fps, 2),
        "duration": round(duration, 2)
    }