"""
Rick Widget v4 — 多图轮播原版 Rick。

从 assets/rick_frames/ 加载多张 Rick PNG，隔几秒淡入淡出切换。
透明无边框置顶窗口，单击台词，双击聊天，右键菜单。
"""

from PyQt6.QtCore import Qt, QTimer, QPoint, QRectF, pyqtSignal
from PyQt6.QtGui import QPainter, QPixmap, QMouseEvent, QFont, QColor, QPen, QBrush
from PyQt6.QtWidgets import QWidget, QMenu, QApplication

import random
import sys
import os
from pathlib import Path

from behavior import Behavior, BehaviorState
from speech_bubble import SpeechBubble
from sound_manager import SoundManager


class RickWidget(QWidget):
    """桌面 Rick — 多图轮播"""

    speak_requested = pyqtSignal(str)
    chat_requested = pyqtSignal(str)

    SIZE = 150
    SWITCH_INTERVAL = 4000   # 每 4 秒换图
    FADE_DURATION = 400      # 淡入淡出 400ms

    def __init__(self, behavior: Behavior, sound_manager: SoundManager, parent=None):
        super().__init__(parent)

        self.behavior = behavior
        self.sound = sound_manager

        # --- 加载多张 Rick 图片 ---
        self._frames: list[QPixmap] = []
        self._current_idx = 0
        self._next_idx = 0
        self._fade_progress = 1.0  # 0=显示旧图, 1=显示新图
        self._is_switching = False
        self._load_all_images()

        # --- 窗口属性 ---
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool |
            Qt.WindowType.NoDropShadowWindowHint
        )
        self.setFixedSize(self.SIZE, self.SIZE)

        if sys.platform == "darwin":
            self.setAttribute(Qt.WidgetAttribute.WA_MacAlwaysShowToolWindow)

        # --- 对话气泡 ---
        self.bubble = SpeechBubble()
        self.speak_requested.connect(self._on_speak)

        # --- 拖拽 ---
        self._dragging = False
        self._drag_offset = QPoint()

        # --- 双击检测 ---
        self._click_timer = QTimer(self)
        self._click_timer.setSingleShot(True)
        self._click_timer.timeout.connect(self._on_single_click)
        self._pending_double = False

        # --- 鼠标微移 ---
        self._offset_x = 0
        self._offset_y = 0

        # --- 30fps 渲染 ---
        self._anim_timer = QTimer(self)
        self._anim_timer.setInterval(33)
        self._anim_timer.timeout.connect(self._tick)
        self._anim_timer.start()

        # --- 图片轮播定时器 ---
        self._switch_timer = QTimer(self)
        self._switch_timer.setInterval(self.SWITCH_INTERVAL)
        self._switch_timer.timeout.connect(self._start_switch)
        if len(self._frames) > 1:
            self._switch_timer.start()

        # --- 闲时说话 ---
        self._auto_speak_timer = QTimer(self)
        self._auto_speak_timer.setSingleShot(True)
        self._auto_speak_timer.timeout.connect(self._maybe_speak)
        self._schedule_auto_speak()

        self._init_position()
        self._setup_menu()
        self.show()

    # ========== 图片加载 ==========

    def _load_all_images(self):
        """从 assets/rick_frames/ 加载所有 PNG"""
        frame_dir = Path(__file__).parent / "assets" / "rick_frames"
        fallback = Path(__file__).parent / "assets" / "rick.png"

        # 优先从 rick_frames 目录加载
        if frame_dir.exists():
            pngs = sorted(frame_dir.glob("*.png"))
            for p in pngs:
                pix = QPixmap(str(p))
                if not pix.isNull():
                    scaled = pix.scaled(
                        self.SIZE, self.SIZE,
                        Qt.AspectRatioMode.KeepAspectRatio,
                        Qt.TransformationMode.SmoothTransformation
                    )
                    self._frames.append(scaled)

        # Fallback: 单张 rick.png
        if not self._frames and fallback.exists():
            pix = QPixmap(str(fallback))
            if not pix.isNull():
                self._frames.append(pix.scaled(
                    self.SIZE, self.SIZE,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                ))

        if self._frames:
            print(f"[RickWidget] ✅ 加载 {len(self._frames)} 张 Rick 图片")
        else:
            print("[RickWidget] ⚠️ 未找到图片，运行 python download_rick.py")

    # ========== 轮播 ==========

    def _start_switch(self):
        """开始切换到下一张"""
        if len(self._frames) < 2:
            return
        self._next_idx = (self._current_idx + 1) % len(self._frames)
        self._fade_progress = 0.0
        self._is_switching = True

    def _tick(self):
        """每帧更新"""
        # 鼠标偏移衰减
        self._offset_x *= 0.85
        self._offset_y *= 0.85
        if abs(self._offset_x) < 0.1: self._offset_x = 0
        if abs(self._offset_y) < 0.1: self._offset_y = 0

        # 淡入淡出进度
        if self._is_switching:
            self._fade_progress += 33 / self.FADE_DURATION
            if self._fade_progress >= 1.0:
                self._fade_progress = 1.0
                self._current_idx = self._next_idx
                self._is_switching = False

        if self.bubble.isVisible():
            self.bubble.position_above(self)
        self.update()

    # ========== 绘制 ==========

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Source)

        padding = 6
        rect = QRectF(padding + self._offset_x, padding + self._offset_y,
                      self.SIZE - padding * 2, self.SIZE - padding * 2)

        if not self._frames:
            # 无图片提示
            painter.setPen(QPen(QColor(100, 255, 100, 180), 2))
            painter.setBrush(QBrush(QColor(20, 20, 28, 220)))
            painter.drawRoundedRect(rect, 12, 12)
            font = QFont("Arial", 11, QFont.Weight.Bold)
            painter.setFont(font)
            painter.setPen(QColor(120, 180, 240))
            painter.drawText(rect, Qt.AlignmentFlag.AlignCenter,
                           "🧪\npython\ndownload_rick.py")
            painter.end()
            return

        # 淡入淡出：当前图淡出 + 下一张淡入
        if self._is_switching and len(self._frames) > 1:
            # 当前图（逐渐透明）
            painter.setOpacity(1.0 - self._fade_progress)
            current_pix = self._frames[self._current_idx]
            painter.drawPixmap(rect, current_pix, QRectF(current_pix.rect()))

            # 下一张（逐渐显现）
            painter.setOpacity(self._fade_progress)
            next_pix = self._frames[self._next_idx]
            painter.drawPixmap(rect, next_pix, QRectF(next_pix.rect()))

            painter.setOpacity(1.0)
        else:
            pix = self._frames[self._current_idx]
            painter.drawPixmap(rect, pix, QRectF(pix.rect()))

        # 图片计数标记（左下角小点）
        if len(self._frames) > 1:
            painter.setOpacity(0.7)
            dot_y = self.SIZE - 12
            total_dots = len(self._frames)
            dot_spacing = 8
            start_x = self.SIZE // 2 - (total_dots * dot_spacing) // 2
            for i in range(total_dots):
                dx = start_x + i * dot_spacing
                if i == self._current_idx and not self._is_switching:
                    color = QColor(100, 255, 100, 220)
                    r = 3
                else:
                    color = QColor(150, 150, 160, 120)
                    r = 2
                painter.setPen(Qt.PenStyle.NoPen)
                painter.setBrush(QBrush(color))
                painter.drawEllipse(int(dx), int(dot_y), r, r)
            painter.setOpacity(1.0)

        painter.end()

    # ========== 鼠标交互 ==========

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self._dragging = True
            self._drag_offset = event.pos()
            if self._pending_double:
                self._pending_double = False
                self._click_timer.stop()
                self._on_double_click()
            else:
                self._pending_double = True
                self._click_timer.start(250)
            event.accept()

    def mouseMoveEvent(self, event: QMouseEvent):
        if self._dragging:
            delta = event.pos() - self._drag_offset
            if abs(delta.x()) > 2 or abs(delta.y()) > 2:
                self._pending_double = False
                self._click_timer.stop()
                self.move(self.pos() + delta)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._dragging = False

    def enterEvent(self, event):
        self._offset_x = 2
        self._offset_y = -1

    def leaveEvent(self, event):
        self._offset_x = 0
        self._offset_y = 0

    # ========== 交互逻辑 ==========

    def _on_single_click(self):
        self._pending_double = False
        quotes = [
            "Wubba lubba dub dub!",
            "*burp* What do you want, Morty?",
            "Don't touch me!",
            "I'm Desktop Rick!",
            "And that's the way the news goes.",
            "*burp* You got any Szechuan sauce?",
        ]
        quote = random.choice(quotes)
        self.behavior.trigger_reaction(quote)
        self.sound.play_random()
        self.speak_requested.emit(quote)

    def _on_double_click(self):
        self.chat_requested.emit("")

    def _schedule_auto_speak(self):
        if not self._auto_speak_timer.isActive():
            self._auto_speak_timer.start(random.randint(20000, 50000))

    def _maybe_speak(self):
        if self.behavior.current_state == BehaviorState.IDLE:
            if random.random() < 0.2:
                q = random.choice(["*burp*", "Hmm...", "Morty...", "*sigh*"])
                self.behavior.trigger_talk(q)
                self.speak_requested.emit(q)
        self._schedule_auto_speak()

    def _on_speak(self, text):
        self.bubble.show_text(text, duration_ms=3500)

    # ========== 菜单 ==========

    def _init_position(self):
        screen = QApplication.primaryScreen()
        if screen:
            geo = screen.availableGeometry()
            self.move(geo.right() - self.SIZE - 50, geo.bottom() - self.SIZE - 40)

    def _setup_menu(self):
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_menu)

    def _show_menu(self, pos):
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu { background-color: #1e1e23; color: #f0f0f0;
                    border: 1px solid #64FF64; border-radius: 6px; padding: 4px; }
            QMenu::item { padding: 6px 24px; border-radius: 4px; }
            QMenu::item:selected { background-color: #333340; }
        """)
        menu.addAction(f"🖼️ {len(self._frames)} 张图轮播中").setEnabled(False)
        menu.addSeparator()
        menu.addAction("💬 和 Rick 聊天").triggered.connect(self._on_chat_clicked)
        sound_text = "🔊 音效：" + ("关" if self.sound.mute else "开")
        menu.addAction(sound_text).triggered.connect(self._toggle_sound)
        llm_text = "🤖 LLM：" + ("开" if self.behavior.is_llm_enabled else "关")
        menu.addAction(llm_text).triggered.connect(self._toggle_llm)
        menu.addSeparator()
        menu.addAction("❌ 退出").triggered.connect(QApplication.quit)
        menu.exec(self.mapToGlobal(pos))

    def _on_chat_clicked(self):
        self.chat_requested.emit("")

    def _toggle_sound(self):
        self.sound.mute = not self.sound.mute

    def _toggle_llm(self):
        self.behavior.is_llm_enabled = not self.behavior.is_llm_enabled

    def say(self, text):
        self.behavior.trigger_talk(text)
        self.speak_requested.emit(text)

    def closeEvent(self, event):
        self._anim_timer.stop()
        self._switch_timer.stop()
        self._auto_speak_timer.stop()
        self._click_timer.stop()
        self.bubble.close()
        super().closeEvent(event)
