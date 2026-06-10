# config.py
import os

# 项目根目录
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# 资源路径
ASSETS = os.path.join(BASE_DIR, "assets")
CHARACTERS = os.path.join(ASSETS, "characters")
SPELLS_FILE = os.path.join(ASSETS, "spells.json")
MUSIC_START = os.path.join(ASSETS, "music", "start.mp3")
MUSIC_BATTLE = os.path.join(ASSETS, "music", "battle.mp3")
MUSIC_VICTORY = os.path.join(ASSETS, "music", "victory.mp3")
PRANK_HORN = os.path.join(ASSETS, "effects", "prank_horn.png")
PRANK_BEARD = os.path.join(ASSETS, "effects", "prank_beard.png")
SCAR = os.path.join(ASSETS, "effects", "scar.png")
FONT_PATH = os.path.join(ASSETS, "fonts", "HarryP.ttf")

# 玩家数据
PLAYER_FACE = os.path.join(BASE_DIR, "data", "player_face.jpg")
PLAYER_CARD = os.path.join(BASE_DIR, "data", "player_card.png")
FEATURES_CACHE = os.path.join(BASE_DIR, "data", "character_features.npy")

# 学院角色配置
HOUSE_CHARACTERS = {
    "Gryffindor": os.path.join(CHARACTERS, "gryffindor.jpg"),
    "Slytherin": os.path.join(CHARACTERS, "slytherin.jpg"),
    "Ravenclaw": os.path.join(CHARACTERS, "ravenclaw.jpg"),
    "Hufflepuff": os.path.join(CHARACTERS, "hufflepuff.jpg")
}

# 人脸关键点索引（mediapipe FaceMesh）
EYE_LEFT_IDX = [33, 133, 155, 154, 153, 145, 144, 163, 7, 173, 157, 158, 159, 160, 161, 246]
EYE_RIGHT_IDX = [362, 263, 398, 384, 385, 386, 387, 388, 466, 390, 373, 374, 380, 381, 382, 463]
NOSE_IDX = [1, 2, 98, 327, 168, 6, 197, 195, 5, 4, 45, 275, 220, 44, 19, 240]
MOUTH_IDX = [61, 146, 91, 181, 84, 17, 314, 405, 321, 375, 78, 191, 80, 81, 82, 13,
             312, 311, 310, 415, 308, 324, 318, 402, 317, 14, 87, 178, 88, 95]

# 摄像头尺寸
CAM_WIDTH = 640
CAM_HEIGHT = 480

# 游戏窗口
WIN_WIDTH = 1024
WIN_HEIGHT = 600
FPS = 30