import cv2
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
import numpy as np
import os
from config import (EYE_LEFT_IDX, EYE_RIGHT_IDX, NOSE_IDX, MOUTH_IDX,
                    HOUSE_CHARACTERS, FEATURES_CACHE)

# ---------- 模型路径 (请确保模型文件存在) ----------
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(CURRENT_DIR, "..", "models", "face_landmarker.task")

# ---------- 全局 FaceLandmarker 单例 ----------
_face_landmarker = None

def _get_landmarker():
    global _face_landmarker
    if _face_landmarker is None:
        if not os.path.exists(MODEL_PATH):
            raise FileNotFoundError(
                f"FaceLandmarker model not found. Expected file at: {MODEL_PATH}\n"
                "请将 face_landmarker.task 放入 magic/models/ 目录，或检查 MODEL_PATH 是否正确。"
            )
        base_options = python.BaseOptions(model_asset_path=MODEL_PATH)
        options = vision.FaceLandmarkerOptions(
            base_options=base_options,
            running_mode=vision.RunningMode.IMAGE,
            num_faces=1,
            min_face_detection_confidence=0.5
        )
        _face_landmarker = vision.FaceLandmarker.create_from_options(options)
    return _face_landmarker

# ---------- 核心函数 (接口与原来完全一致) ----------
def extract_landmarks(image_path):
    """提取468个关键点，返回 NormalizedLandmark 列表 (无 .landmark 属性)"""
    img = cv2.imread(image_path)
    if img is None:
        return None
    rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

    # 转换为 MediaPipe Image 对象
    mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
    detector = _get_landmarker()
    results = detector.detect(mp_image)

    if not results.face_landmarks:
        return None
    # 新版返回的 face_landmarks[0] 就是包含 468 个 NormalizedLandmark 的列表
    return results.face_landmarks[0]

def get_region_points(landmarks, indices):
    """获取指定索引的归一化坐标数组 (landmarks 是 NormalizedLandmark 列表)"""
    pts = []
    for idx in indices:
        lm = landmarks[idx]          # 直接索引，不再用 .landmark
        pts.append([lm.x, lm.y])
    return np.array(pts)

def extract_face_features(image_path):
    """提取图像的脸部区域特征点集（用于比较）"""
    landmarks = extract_landmarks(image_path)
    if landmarks is None:
        return None
    left_eye = get_region_points(landmarks, EYE_LEFT_IDX)
    right_eye = get_region_points(landmarks, EYE_RIGHT_IDX)
    nose = get_region_points(landmarks, NOSE_IDX)
    mouth = get_region_points(landmarks, MOUTH_IDX)
    # 合并眼睛区域
    eyes = np.vstack([left_eye, right_eye])
    return {"eyes": eyes, "nose": nose, "mouth": mouth}

# ---------- 相似度计算（完全相同）----------
def similarity(set1, set2):
    """计算两组点集的相似度（普氏分析对齐后欧氏距离）"""
    pts1 = set1.copy()
    pts2 = set2.copy()
    # 减均值
    mu1 = np.mean(pts1, axis=0)
    mu2 = np.mean(pts2, axis=0)
    pts1 -= mu1
    pts2 -= mu2
    # 归一化尺度
    scale1 = np.sqrt(np.mean(np.sum(pts1**2, axis=1)))
    scale2 = np.sqrt(np.mean(np.sum(pts2**2, axis=1)))
    if scale1 < 1e-6 or scale2 < 1e-6:
        return 0.0
    pts1 /= scale1
    pts2 /= scale2
    # SVD旋转对齐
    M = np.dot(pts1.T, pts2)
    U, _, Vt = np.linalg.svd(M)
    R = np.dot(U, Vt)
    if np.linalg.det(R) < 0:
        Vt[-1, :] *= -1
        R = np.dot(U, Vt)
    pts1_rot = np.dot(pts1, R)
    # 平均距离
    dist = np.mean(np.sqrt(np.sum((pts1_rot - pts2)**2, axis=1)))
    # 转为相似度 (0~1)
    return 1.0 / (1.0 + dist)

# ---------- 角色特征缓存 (完全相同) ----------
def build_character_features():
    """预计算四个角色的特征并缓存"""
    features = {}
    for house, path in HOUSE_CHARACTERS.items():
        feat = extract_face_features(path)
        if feat:
            features[house] = feat
    np.save(FEATURES_CACHE, features, allow_pickle=True)
    print("Character features cached.")
    return features

def load_character_features():
    if os.path.exists(FEATURES_CACHE):
        try:
            feats = np.load(FEATURES_CACHE, allow_pickle=True).item()
        except Exception as e:
            print("Failed to load cached character features:", e)
            return build_character_features()
        if not isinstance(feats, dict) or not feats:
            print("Cached character features empty or invalid, rebuilding...")
            return build_character_features()
        return feats
    else:
        print("No cache found, building character features...")
        return build_character_features()

# ---------- 分院主函数 (完全相同) ----------
def sort_student(player_img_path):
    """比较玩家与四个角色，返回分院结果和描述"""
    player_feat = extract_face_features(player_img_path)
    if player_feat is None:
        return None, "Face not detected"
    char_feats = load_character_features()
    if not char_feats:
        return None, "Character features missing"

    # 分别比较眼睛、鼻子、嘴巴
    region_names = ["eyes", "nose", "mouth"]
    priority = ["eyes", "nose", "mouth"]
    matches = {}
    best_matches = {}
    for region in region_names:
        best_sim = -1
        best_house = None
        for house, cfeat in char_feats.items():
            sim = similarity(player_feat[region], cfeat[region])
            if sim > best_sim:
                best_sim = sim
                best_house = house
        matches[region] = best_house
        best_matches[region] = (best_house, best_sim)

    # 统计学院票数
    vote_count = {}
    for house in char_feats.keys():
        vote_count[house] = 0
    for region in region_names:
        vote_count[matches[region]] += 1

    # 按优先级决定平局
    final_house = max(vote_count, key=lambda h: (vote_count[h],
                                                  priority.index('eyes') if matches['eyes']==h else -1,
                                                  priority.index('nose') if matches['nose']==h else -1,
                                                  priority.index('mouth') if matches['mouth']==h else -1))
    # 生成描述
    parts = []
    for region in region_names:
        parts.append(f"{best_matches[region][0]}的{region}")
    description = f"你拥有" + "、".join(parts) + "的特征"
    return final_house, description