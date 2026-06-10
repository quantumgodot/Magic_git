import cv2
from modules.face_analysis import sort_student

# 先拍一张照片保存为 test_face.jpg（用你的摄像头或直接用手头的一张人脸图）
   # 手动准备一张含清晰正脸的照片
# 如果你还没拍照，可以先用 assets/characters/ 下任意一张角色图代替

house, desc = sort_student(r"D:\00.AI\magic\magic\an.jpg")
print(f"分院结果: {house}")
print(f"描述: {desc}")