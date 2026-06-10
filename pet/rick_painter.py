"""
Rick Sanchez 角色绘制器 — 使用 QPainter 手绘 Rick 形象。
无需外部素材，纯代码绘制。支持多种表情和姿态。
"""

from PyQt6.QtCore import Qt, QPointF, QRectF, QTimer
from PyQt6.QtGui import (
    QPainter, QColor, QPen, QBrush, QLinearGradient, QRadialGradient,
    QPainterPath, QPolygonF
)
import math
import random


class RickPose:
    """Rick 的姿态定义"""
    IDLE = "idle"
    WALK_LEFT = "walk_left"
    WALK_RIGHT = "walk_right"
    SURPRISED = "surprised"
    ANGRY = "angry"
    BURP = "burp"
    DRINK = "drink"


class RickPainter:
    """用 QPainter 绘制 Rick Sanchez 的桌面宠物形象。

    特征：灰色皮肤、蓝色尖发、浓眉、白大褂、传送枪。
    所有绘制用纯代码，无需任何图片素材。
    """

    # 颜色定义
    SKIN = QColor(180, 180, 185)        # 灰皮肤
    SKIN_DARK = QColor(150, 150, 155)   # 阴影
    HAIR = QColor(120, 180, 240)        # 蓝头发
    HAIR_DARK = QColor(80, 140, 210)    # 深蓝头发
    LAB_COAT = QColor(240, 245, 250)    # 白大褂
    LAB_COAT_SHADOW = QColor(210, 215, 225)
    SHIRT = QColor(120, 180, 200)       # 蓝衬衫
    PANTS = QColor(80, 70, 60)          # 棕色裤子
    BELT = QColor(60, 50, 40)           # 深棕皮带
    EYEBROW = QColor(80, 85, 90)        # 浓眉
    EYE_WHITE = QColor(255, 255, 255)
    PUPIL = QColor(30, 30, 35)
    MOUTH = QColor(100, 60, 60)
    PORTAL_GUN = QColor(160, 160, 170)  # 传送枪主体
    PORTAL_GREEN = QColor(100, 255, 100)
    DROOL = QColor(160, 220, 180)       # 口水绿

    def __init__(self, size: int = 120):
        self.size = size
        self.scale = size / 120.0  # 基于 120px 基准的缩放
        self.breath_offset = 0.0
        self.walk_phase = 0.0
        self.blink_timer = 0
        self.is_blinking = False
        self.current_pose = RickPose.IDLE
        self._mouth_open = 0.0  # 0=闭, 1=开
        self._eyebrow_angle = 0.0

    def update_animation(self, dt: float):
        """更新动画参数"""
        self.breath_offset = math.sin(self.walk_phase * 2.0) * 0.02
        self.blink_timer += 1
        # 随机眨眼（每 3-5 秒眨一次）
        if self.blink_timer > random.randint(180, 300):
            self.is_blinking = True
            self.blink_timer = 0
        elif self.blink_timer > 8:
            self.is_blinking = False

    def set_pose(self, pose: str):
        self.current_pose = pose
        if pose == RickPose.SURPRISED:
            self._mouth_open = 1.0
            self._eyebrow_angle = 0.3
        elif pose == RickPose.ANGRY:
            self._mouth_open = 0.3
            self._eyebrow_angle = -0.2
        elif pose == RickPose.BURP:
            self._mouth_open = 0.8
        else:
            self._mouth_open = max(0, self._mouth_open - 0.05)
            self._eyebrow_angle *= 0.9

    def paint(self, painter: QPainter, rect: QRectF):
        """在给定矩形内绘制 Rick"""
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        cx = rect.center().x()
        cy = rect.center().y()
        s = self.scale * 120.0

        # 应用呼吸效果
        breath = self.breath_offset * s

        # --- 身体（白大褂） ---
        self._draw_body(painter, cx, cy, s, breath)
        # --- 腿 ---
        self._draw_legs(painter, cx, cy, s, breath)
        # --- 手臂 ---
        self._draw_arms(painter, cx, cy, s, breath)
        # --- 头部 ---
        self._draw_head(painter, cx, cy - s * 0.42, s, breath)
        # --- 头发 ---
        self._draw_hair(painter, cx, cy - s * 0.42, s, breath)
        # --- 传送枪 ---
        self._draw_portal_gun(painter, cx, cy, s, breath)

        painter.restore()

    def _draw_body(self, p: QPainter, cx, cy, s, breath):
        """白大褂 + 衬衫"""
        body_rect = QRectF(cx - s * 0.22, cy - s * 0.15, s * 0.44, s * 0.48)
        p.setPen(QPen(self.LAB_COAT_SHADOW, 1.5))
        p.setBrush(QBrush(self.LAB_COAT))
        p.drawRoundedRect(body_rect, s * 0.08, s * 0.08)

        # 衬衫领口
        shirt_path = QPainterPath()
        shirt_path.moveTo(cx - s * 0.12, cy - s * 0.15)
        shirt_path.lineTo(cx, cy - s * 0.02)
        shirt_path.lineTo(cx + s * 0.12, cy - s * 0.15)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(self.SHIRT))
        p.drawPath(shirt_path)

        # 腰带
        belt_rect = QRectF(cx - s * 0.20, cy + s * 0.22, s * 0.40, s * 0.05)
        p.setBrush(QBrush(self.BELT))
        p.drawRect(belt_rect)

    def _draw_legs(self, p: QPainter, cx, cy, s, breath):
        """棕色裤子 + 腿"""
        p.setPen(QPen(self.PANTS.darker(120), 1.0))
        p.setBrush(QBrush(self.PANTS))

        walk_offset = math.sin(self.walk_phase) * s * 0.04
        # 左腿
        p.drawRoundedRect(
            QRectF(cx - s * 0.15, cy + s * 0.27, s * 0.12, s * 0.22),
            s * 0.03, s * 0.03
        )
        # 右腿
        p.drawRoundedRect(
            QRectF(cx + s * 0.03, cy + s * 0.27, s * 0.12, s * 0.22),
            s * 0.03, s * 0.03
        )
        # 鞋子
        p.setBrush(QColor(50, 50, 55))
        p.drawRoundedRect(
            QRectF(cx - s * 0.18, cy + s * 0.46, s * 0.16, s * 0.06),
            s * 0.02, s * 0.02
        )
        p.drawRoundedRect(
            QRectF(cx + s * 0.02, cy + s * 0.46, s * 0.16, s * 0.06),
            s * 0.02, s * 0.02
        )

    def _draw_arms(self, p: QPainter, cx, cy, s, breath):
        """手臂（两侧自然下垂或举起）"""
        arm_color = self.LAB_COAT
        p.setPen(QPen(arm_color.darker(110), 1.0))
        p.setBrush(QBrush(arm_color))

        # 左臂
        left_arm = QPainterPath()
        left_arm.moveTo(cx - s * 0.20, cy - s * 0.10)
        left_arm.cubicTo(
            cx - s * 0.35, cy + s * 0.05,
            cx - s * 0.38, cy + s * 0.20,
            cx - s * 0.30, cy + s * 0.30
        )
        p.drawPath(left_arm)

        # 右臂（举着传送枪）
        right_arm = QPainterPath()
        right_arm.moveTo(cx + s * 0.20, cy - s * 0.10)
        right_arm.cubicTo(
            cx + s * 0.35, cy - s * 0.05,
            cx + s * 0.32, cy + s * 0.05,
            cx + s * 0.28, cy + s * 0.20
        )
        p.drawPath(right_arm)

        # 手
        p.setBrush(QBrush(self.SKIN))
        p.drawEllipse(QPointF(cx - s * 0.30, cy + s * 0.30), s * 0.05, s * 0.05)
        p.drawEllipse(QPointF(cx + s * 0.28, cy + s * 0.20), s * 0.05, s * 0.05)

    def _draw_head(self, p: QPainter, cx, cy, s, breath):
        """头部：灰色椭圆脸 + 五官"""
        # 脸部椭圆
        head_rect = QRectF(cx - s * 0.18, cy - s * 0.22, s * 0.36, s * 0.38)
        p.setPen(QPen(self.SKIN_DARK, 1.0))
        p.setBrush(QBrush(self.SKIN))
        p.drawEllipse(head_rect)

        # 皱纹线
        p.setPen(QPen(self.SKIN_DARK, 0.8))
        wrinkle_y = cy - s * 0.12
        p.drawLine(QPointF(cx - s * 0.08, wrinkle_y), QPointF(cx + s * 0.02, wrinkle_y))
        p.drawLine(QPointF(cx - s * 0.06, wrinkle_y + s * 0.03), QPointF(cx + s * 0.04, wrinkle_y + s * 0.03))

        # --- 浓眉 ---
        p.setPen(QPen(self.EYEBROW, 2.5, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        brow_y = cy - s * 0.06
        # 左眉
        p.drawLine(
            QPointF(cx - s * 0.14, brow_y + s * 0.02),
            QPointF(cx - s * 0.03, brow_y - s * 0.04)
        )
        # 右眉
        p.drawLine(
            QPointF(cx + s * 0.03, brow_y - s * 0.04),
            QPointF(cx + s * 0.14, brow_y + s * 0.02)
        )

        # --- 眼睛 ---
        eye_y = cy
        if self.is_blinking:
            # 闭眼
            p.setPen(QPen(self.EYEBROW, 2.0))
            p.drawLine(
                QPointF(cx - s * 0.10, eye_y),
                QPointF(cx - s * 0.02, eye_y)
            )
            p.drawLine(
                QPointF(cx + s * 0.02, eye_y),
                QPointF(cx + s * 0.10, eye_y)
            )
        else:
            # 睁眼
            p.setPen(QPen(self.EYEBROW, 1.0))
            p.setBrush(QBrush(self.EYE_WHITE))
            p.drawEllipse(QPointF(cx - s * 0.06, eye_y), s * 0.05, s * 0.06)
            p.drawEllipse(QPointF(cx + s * 0.06, eye_y), s * 0.05, s * 0.06)
            # 瞳孔
            p.setBrush(QBrush(self.PUPIL))
            p.drawEllipse(QPointF(cx - s * 0.06, eye_y), s * 0.022, s * 0.025)
            p.drawEllipse(QPointF(cx + s * 0.06, eye_y), s * 0.022, s * 0.025)
            # 高光
            p.setBrush(QBrush(QColor(255, 255, 255)))
            p.drawEllipse(QPointF(cx - s * 0.07, eye_y - s * 0.015), s * 0.01, s * 0.01)
            p.drawEllipse(QPointF(cx + s * 0.05, eye_y - s * 0.015), s * 0.01, s * 0.01)

        # --- 嘴巴 ---
        mouth_y = cy + s * 0.08
        p.setPen(QPen(self.MOUTH, 1.2))
        if self._mouth_open > 0.5:
            # 张嘴
            mouth_rect = QRectF(
                cx - s * 0.06, mouth_y - s * 0.01,
                s * 0.12, s * 0.06 * self._mouth_open
            )
            p.setBrush(QBrush(QColor(80, 40, 40)))
            p.drawRoundedRect(mouth_rect, s * 0.02, s * 0.02)
        else:
            # 闭嘴 / 微笑
            p.drawArc(
                QRectF(cx - s * 0.06, mouth_y - s * 0.03, s * 0.12, s * 0.06),
                0, -180 * 16
            )

        # 口水（标志性特征）
        if self._mouth_open > 0.3:
            p.setPen(QPen(self.DROOL, 1.0))
            p.setBrush(QBrush(self.DROOL))
            drool_start = QPointF(cx + s * 0.02, mouth_y + s * 0.05)
            p.drawLine(drool_start, QPointF(cx + s * 0.05, mouth_y + s * 0.12))
            p.drawEllipse(QPointF(cx + s * 0.05, mouth_y + s * 0.13), s * 0.015, s * 0.02)

    def _draw_hair(self, p: QPainter, cx, cy, s, breath):
        """标志性的蓝色尖发"""
        hair_path = QPainterPath()

        # Rick 的头发是典型的尖刺实验室风格
        spikes = [
            (cx - s * 0.2, cy - s * 0.1),    # 左侧起
            (cx - s * 0.18, cy - s * 0.3),   # 左尖
            (cx - s * 0.10, cy - s * 0.18),
            (cx - s * 0.06, cy - s * 0.35),  # 中间高尖
            (cx + s * 0.02, cy - s * 0.22),
            (cx + s * 0.08, cy - s * 0.32),  # 右尖
            (cx + s * 0.16, cy - s * 0.20),
            (cx + s * 0.20, cy - s * 0.10),  # 右侧落
            (cx + s * 0.18, cy),
            (cx - s * 0.18, cy),
        ]

        hair_path.moveTo(spikes[0][0], spikes[0][1])
        for i in range(1, len(spikes)):
            hair_path.lineTo(spikes[i][0], spikes[i][1])
        hair_path.closeSubpath()

        # 渐变头发
        gradient = QLinearGradient(cx, cy - s * 0.3, cx, cy)
        gradient.setColorAt(0, self.HAIR)
        gradient.setColorAt(1, self.HAIR_DARK)
        p.setPen(QPen(self.HAIR_DARK, 1.0))
        p.setBrush(QBrush(gradient))
        p.drawPath(hair_path)

    def _draw_portal_gun(self, p: QPainter, cx, cy, s, breath):
        """传送枪（右手持）"""
        gun_cx = cx + s * 0.28
        gun_cy = cy + s * 0.15

        # 枪身
        p.setPen(QPen(self.PORTAL_GUN.darker(120), 1.0))
        p.setBrush(QBrush(self.PORTAL_GUN))
        gun_body = QPainterPath()
        gun_body.moveTo(gun_cx, gun_cy - s * 0.1)
        gun_body.lineTo(gun_cx + s * 0.08, gun_cy - s * 0.07)
        gun_body.lineTo(gun_cx + s * 0.10, gun_cy + s * 0.02)
        gun_body.lineTo(gun_cx + s * 0.02, gun_cy + s * 0.01)
        gun_body.closeSubpath()
        p.drawPath(gun_body)

        # 绿色能量光
        p.setPen(Qt.PenStyle.NoPen)
        glow = QRadialGradient(gun_cx + s * 0.09, gun_cy - s * 0.04, s * 0.04)
        glow.setColorAt(0, QColor(100, 255, 100, 200))
        glow.setColorAt(1, QColor(100, 255, 100, 0))
        p.setBrush(QBrush(glow))
        p.drawEllipse(QPointF(gun_cx + s * 0.09, gun_cy - s * 0.04), s * 0.04, s * 0.04)
