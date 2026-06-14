from scenedetect import detect, ContentDetector
from app.utils.video_metadata import get_video_info


class SceneDetectAgent:

    def process(self, content_id, video_path):

        # lấy thông tin video
        video_info = get_video_info(video_path)

        # phát hiện cảnh trong video
        scenes = detect(video_path, ContentDetector())

        scene_count = len(scenes)

        # tính thời lượng từng cảnh
        durations = []

        for start, end in scenes:
            durations.append(
                end.get_seconds() - start.get_seconds()
            )

        # Average Scene Length
        if scene_count > 0:
            asl = sum(durations) / scene_count
        else:
            asl = 0

        return {
            "content_id": content_id,
            "agent": "scene_detect",
            "scene_count": scene_count,
            "asl": round(asl, 2),
            "fps": video_info["fps"],
            "duration": video_info["duration"],
            "status": "SUCCESS"
        }