"""
对话气泡 — 在 Rick 头顶弹出半透明气泡，显示台词。
支持渐入渐出动画，自动消失。
"""
from PyQt6.QtCore import (
    Qt, QTimer, QPointF, QRectF, QPropertyAnimation,
    QEasingCurve, pyqtProperty
)
from PyQt6.QtGui import (
    QPainter, QColor, QPen, QBrush, QFont, QPainterPath, QFontMetrics
)
from PyQt6.QtWidgets import QWidget


class SpeechBubble(QWidget):
    """半透明对话气泡 Widget。

    显示在 Rick 角色上方，包含指向角色的三角箭头。
    支持渐入渐出动画和自动消失定时器。
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )

        self._text = ""
        self._opacity = 0.0
        self._max_width = 220
        self._padding = 10
        self._arrow_height = 8

        self._fade_timer = QTimer(self)
        self._fade_timer.timeout.connect(self._fade_step)
        self._fade_direction = 0  # 1=淡入, -1=淡出

        self._auto_hide_timer = QTimer(self)
        self._auto_hide_timer.setSingleShot(True)
        self._auto_hide_timer.timeout.connect(self.hide_bubble)

        self.hide()

    def set_opacity(self, value: float):
        self._opacity = value
        self.update()

    def get_opacity(self) -> float:
        return self._opacity

    opacity = pyqtProperty(float, get_opacity, set_opacity)

    def show_text(self, text: str, duration_ms: int = 3000):
        """显示文本气泡"""
        self._text = text
        self._calc_size()
        self._fade_direction = 1
        self._opacity = 0.0
        self.show()
        self._fade_timer.start(16)  # ~60fps

        if duration_ms > 0:
            self._auto_hide_timer.start(duration_ms)

    def hide_bubble(self):
        """渐隐气泡"""
        self._fade_direction = -1
        self._fade_timer.start(16)

    def _fade_step(self):
        if self._fade_direction == 1:
            self._opacity = min(1.0, self._opacity + 0.08)
            if self._opacity >= 1.0:
                self._fade_timer.stop()
        elif self._fade_direction == -1:
            self._opacity = max(0.0, self._opacity - 0.06)
            if self._opacity <= 0.0:
                self._fade_timer.stop()
                self.hide()
        self.update()

    def _calc_size(self):
        """根据文本计算气泡大小"""
        font = QFont("Arial", 11)
        fm = QFontMetrics(font)
        # 简单换行
        words = self._text.split()
        lines = []
        current_line = ""
        for word in words:
            test_line = current_line + (" " if current_line else "") + word
            if fm.horizontalAdvance(test_line) <= self._max_width - self._padding * 2:
                current_line = test_line
            else:
                if current_line:
                    lines.append(current_line)
                current_line = word
        if current_line:
            lines.append(current_line)

        if not lines:
            lines = [self._text]

        self._lines = lines
        line_height = fm.height() + 2
        text_width = max(
            fm.horizontalAdvance(line) for line in lines
        ) + self._padding * 2
        text_height = line_height * len(lines) + self._padding * 2

        self._bubble_width = min(text_width, self._max_width)
        self._bubble_height = text_height + self._arrow_height
        self.resize(int(self._bubble_width), int(self._bubble_height))

    def paintEvent(self, event):
        if self._opacity <= 0.0:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setOpacity(self._opacity)

        # 气泡背景
        bubble_rect = QRectF(
            0, 0,
            self._bubble_width,
            self._bubble_height - self._arrow_height
        )

        # 三角箭头
        arrow_cx = self._bubble_width / 2
        arrow_y = bubble_rect.bottom()

        path = QPainterPath()
        path.addRoundedRect(bubble_rect, 10, 10)
        # 箭头
        path.moveTo(arrow_cx - 6, arrow_y)
        path.lineTo(arrow_cx, arrow_y + self._arrow_height)
        path.lineTo(arrow_cx + 6, arrow_y)
        path.closeSubpath()

        # 填充
        bg_color = QColor(30, 30, 35, 220)
        border_color = QColor(100, 255, 100, 200)  # 传送门绿边框

        painter.setPen(QPen(border_color, 1.5))
        painter.setBrush(QBrush(bg_color))
        painter.drawPath(path)

        # 文本
        font = QFont("Arial", 11, QFont.Weight.Bold)
        font.setStyleHint(QFont.StyleHint.SansSerif)
        painter.setFont(font)
        painter.setPen(QColor(240, 245, 250))
        painter.setBrush(Qt.BrushStyle.NoBrush)

        text_rect = QRectF(
            self._padding,
            self._padding,
            self._bubble_width - self._padding * 2,
            self._bubble_height - self._arrow_height - self._padding * 2
        )
        painter.drawText(text_rect, Qt.AlignmentFlag.AlignCenter, self._text)

        painter.end()

    def position_above(self, target_widget):
        """将气泡定位在目标 widget 上方"""
        if not target_widget:
            return
        target_pos = target_widget.pos()
        target_size = target_widget.size()

        bubble_x = target_pos.x() + target_size.width() // 2 - self.width() // 2
        bubble_y = target_pos.y() - self.height() + 5
        self.move(int(bubble_x), int(bubble_y))
