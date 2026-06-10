"""
摄像头面部识别模块 — 让 Rick 能"看到"用户。
检测面部存在、表情，让 Rick 做出相应反应。
（仅在检测到摄像头且用户启用时运行）
"""
import threading
import time
from typing import Optional, Callable


class CameraUtils:
    """摄像头面部检测器。

    使用 OpenCV + MediaPipe（复用 magic 项目的方案）进行面部检测。
    检测到用户时，Rick 会打招呼或吐槽。
    检测不到用户时，Rick 会感到孤独。

    所有操作在后台线程中运行，不阻塞 UI。
    """

    def __init__(
        self,
        on_face_detected: Callable = None,
        on_face_lost: Callable = None,
        on_expression: Callable[[str], None] = None,
    ):
        self.on_face_detected = on_face_detected
        self.on_face_lost = on_face_lost
        self.on_expression = on_expression

        self._running = False
        self._thread = None
        self._cap = None
        self._face_detector = None
        self._available = False

        self._last_face_time = 0
        self._face_present = False
        self._check_interval = 3.0  # 每 3 秒检查一次

        self._init_camera()

    def _init_camera(self):
        """初始化摄像头和检测器"""
        try:
            import cv2
            self._cv2 = cv2
            self._cap = cv2.VideoCapture(0)
            if not self._cap.isOpened():
                self._available = False
                return

            # 尝试加载 MediaPipe 面部检测
            try:
                import mediapipe as mp
                self._mp = mp
                self._mp_face_detection = mp.solutions.face_detection
                self._face_detector = self._mp_face_detection.FaceDetection(
                    model_selection=0,  # 0=近距离, 1=远距离
                    min_detection_confidence=0.5
                )
                self._available = True
            except ImportError:
                # Fallback: 使用 OpenCV 的 Haar Cascade
                cascade_path = self._cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
                self._face_cascade = self._cv2.CascadeClassifier(cascade_path)
                self._available = True
        except ImportError:
            self._available = False
        except Exception:
            self._available = False

    @property
    def is_available(self) -> bool:
        return self._available

    def start(self):
        """开始后台检测"""
        if not self._available or self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._detection_loop, daemon=True)
        self._thread.start()

    def stop(self):
        """停止检测"""
        self._running = False
        if self._cap:
            self._cap.release()
        if self._face_detector:
            self._face_detector.close()

    def _detection_loop(self):
        """后台检测循环"""
        while self._running:
            try:
                ret, frame = self._cap.read()
                if not ret:
                    time.sleep(0.5)
                    continue

                faces = self._detect_faces(frame)
                now = time.time()

                if faces:
                    if not self._face_present:
                        self._face_present = True
                        if self.on_face_detected:
                            self.on_face_detected()
                    self._last_face_time = now

                    # 简化表情检测（基于面部数量）
                    if len(faces) > 1 and self.on_expression:
                        self.on_expression("multiple_faces")
                else:
                    if self._face_present and now - self._last_face_time > 5:
                        self._face_present = False
                        if self.on_face_lost:
                            self.on_face_lost()

                time.sleep(self._check_interval)

            except Exception:
                time.sleep(1)

    def _detect_faces(self, frame) -> list:
        """检测画面中的面部"""
        try:
            if hasattr(self, '_face_detector') and self._face_detector:
                # MediaPipe 方案
                rgb = self._cv2.cvtColor(frame, self._cv2.COLOR_BGR2RGB)
                results = self._face_detector.process(rgb)
                if results.detections:
                    return results.detections
            elif hasattr(self, '_face_cascade'):
                # OpenCV Haar Cascade 方案
                gray = self._cv2.cvtColor(frame, self._cv2.COLOR_BGR2GRAY)
                faces = self._face_cascade.detectMultiScale(
                    gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30)
                )
                return [f for f in faces]
        except Exception:
            pass
        return []

    def capture_snapshot(self) -> Optional[str]:
        """拍摄快照并保存为临时文件"""
        if not self._cap or not self._cap.isOpened():
            return None
        try:
            ret, frame = self._cap.read()
            if ret:
                import tempfile
                import os
                tmp = tempfile.NamedTemporaryFile(
                    suffix=".jpg", delete=False, prefix="rick_cam_"
                )
                self._cv2.imwrite(tmp.name, frame)
                return tmp.name
        except Exception:
            pass
        return None
