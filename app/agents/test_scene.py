from pathlib import Path
from app.agents.scene_agent import SceneDetectAgent
import json

BASE_DIR = Path(__file__).resolve().parent.parent.parent

video_path = BASE_DIR / "dataset" / "test.mp4"

print(video_path)

agent = SceneDetectAgent()

result = agent.process(
    content_id=1,
    video_path=str(video_path)
)

print(json.dumps(result, indent=4))

print("\n=== Giải thích ===")
print(f"content_id  : {result['content_id']}")
print(f"agent       : {result['agent']}")
print(f"scene_count : {result['scene_count']}")
print(f"asl         : {result['asl']} giây")
print(f"fps         : {result['fps']}")
print(f"duration    : {result['duration']} giây")
print(f"status      : {result['status']}")