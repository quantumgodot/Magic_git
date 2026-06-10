# modules/prank.py
import cv2
import numpy as np
from PIL import Image
from config import PRANK_HORN, PRANK_BEARD, SCAR, PLAYER_FACE

def add_overlay(face_img, overlay_path, position):
    """在脸部图像上叠加贴纸"""
    overlay = Image.open(overlay_path).convert("RGBA")
    face_pil = Image.fromarray(cv2.cvtColor(face_img, cv2.COLOR_BGR2RGB)).convert("RGBA")
    face_pil.paste(overlay, position, overlay)
    return cv2.cvtColor(np.array(face_pil), cv2.COLOR_RGBA2BGR)

def prank_player():
    """对玩家照片涂鸦整蛊"""
    img = cv2.imread(PLAYER_FACE)
    if img is None:
        return None
    # 检测人脸位置以放置贴纸
    mp_face_detection = __import__('mediapipe').solutions.face_detection
    with mp_face_detection.FaceDetection(min_detection_confidence=0.5) as fd:
        rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        results = fd.process(rgb)
        if results.detections:
            det = results.detections[0]
            bbox = det.location_data.relative_bounding_box
            h, w = img.shape[:2]
            x = int(bbox.xmin * w)
            y = int(bbox.ymin * h)
            bw = int(bbox.width * w)
            bh = int(bbox.height * h)

            # 加恶魔角、胡子、伤疤
            img = add_overlay(img, PRANK_HORN, (x-20, y-40))
            img = add_overlay(img, PRANK_BEARD, (x, y+int(bh*0.7)))
            img = add_overlay(img, SCAR, (x+int(bw*0.4), y+int(bh*0.3)))
    # 保存整蛊图
    prank_path = PLAYER_FACE.replace('.jpg', '_pranked.jpg')
    cv2.imwrite(prank_path, img)
    return prank_path