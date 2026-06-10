"""
PetApp — 桌面宠物主控制器。
整合 Rick Widget、LLM 对话、摄像头识别、联网搜索。
管理系统托盘、设置窗口、全局状态。
"""
import sys
import os
import json
import random
from pathlib import Path

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QIcon, QAction, QFont
from PyQt6.QtWidgets import (
    QApplication, QSystemTrayIcon, QMenu, QWidget,
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QTextEdit, QCheckBox, QGroupBox, QFormLayout
)

from rick_widget import RickWidget
from behavior import Behavior
from sound_manager import SoundManager
from llm_chat import LLMChat
from camera_utils import CameraUtils
from web_search_utils import WebSearchUtils


class ChatDialog(QDialog):
    """与 Rick 聊天的小窗口"""

    def __init__(self, llm: LLMChat, rick: RickWidget, parent=None):
        super().__init__(parent)
        self.llm = llm
        self.rick = rick

        self.setWindowTitle("💬 和 Rick 聊天")
        self.setMinimumSize(350, 450)
        self._setup_ui()
        self.setStyleSheet(self._style())

    def _style(self):
        return """
            QDialog {
                background-color: #1a1a20;
                color: #e0e0e0;
                border: 1px solid #64FF64;
                border-radius: 8px;
            }
            QTextEdit {
                background-color: #24242e;
                color: #e0e0e0;
                border: 1px solid #444;
                border-radius: 6px;
                padding: 8px;
                font-size: 13px;
            }
            QLineEdit {
                background-color: #24242e;
                color: #e0e0e0;
                border: 1px solid #64FF64;
                border-radius: 6px;
                padding: 8px;
                font-size: 13px;
            }
            QPushButton {
                background-color: #3a7a3a;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 20px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #4a9a4a;
            }
            QLabel {
                color: #a0a0b0;
                font-size: 11px;
            }
        """

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(16, 16, 16, 16)

        # 标题
        title = QLabel("🧪 Rick Sanchez — 桌面宠物聊天")
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #64FF64;")
        layout.addWidget(title)

        # 对话历史
        self.chat_history = QTextEdit()
        self.chat_history.setReadOnly(True)
        self.chat_history.setMinimumHeight(250)
        layout.addWidget(self.chat_history)

        # 输入区域
        input_layout = QHBoxLayout()
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("输入消息... (回车发送)")
        self.input_field.returnPressed.connect(self._send_message)
        input_layout.addWidget(self.input_field)

        send_btn = QPushButton("发送")
        send_btn.clicked.connect(self._send_message)
        input_layout.addWidget(send_btn)
        layout.addLayout(input_layout)

        # 状态标签
        self.status_label = QLabel("")
        layout.addWidget(self.status_label)

        # 添加初始问候
        greeting = self.llm.get_greeting()
        self._append_message("Rick", greeting)

    def _send_message(self):
        text = self.input_field.text().strip()
        if not text:
            return

        self._append_message("你", text)
        self.input_field.clear()
        self.input_field.setEnabled(False)
        self.status_label.setText("🤔 Rick 思考中...")

        # 异步调用 LLM
        def on_reply(reply: str):
            self._append_message("Rick", reply)
            self.input_field.setEnabled(True)
            self.input_field.setFocus()
            self.status_label.setText("")
            # 同时让桌面 Rick 说
            if self.rick:
                self.rick.say(reply)

        self.llm.chat_async(text, on_reply)

    def _append_message(self, sender: str, text: str):
        self.chat_history.append(f"<b>{sender}:</b> {text}")
        # 滚动到底部
        scrollbar = self.chat_history.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())


class SettingsDialog(QDialog):
    """设置窗口"""

    def __init__(self, pet_app, parent=None):
        super().__init__(parent)
        self.pet_app = pet_app
        self.setWindowTitle("⚙️ Rick 桌面宠物 - 设置")
        self.setMinimumSize(400, 300)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(20, 20, 20, 20)

        # LLM 设置
        llm_group = QGroupBox("🤖 LLM 设置")
        llm_form = QFormLayout()

        self.llm_enabled = QCheckBox("启用 LLM")
        self.llm_enabled.setChecked(self.pet_app.llm.is_available)
        self.llm_enabled.toggled.connect(self._on_llm_toggle)
        llm_form.addRow(self.llm_enabled)

        self.api_key_input = QLineEdit()
        self.api_key_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.api_key_input.setText(os.environ.get("OPENAI_API_KEY", ""))
        llm_form.addRow("API Key:", self.api_key_input)

        self.base_url_input = QLineEdit()
        self.base_url_input.setText(
            os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1")
        )
        llm_form.addRow("Base URL:", self.base_url_input)

        self.model_input = QLineEdit()
        self.model_input.setText("gpt-3.5-turbo")
        llm_form.addRow("Model:", self.model_input)

        llm_group.setLayout(llm_form)
        layout.addWidget(llm_group)

        # 音效设置
        sound_group = QGroupBox("🔊 音效设置")
        sound_layout = QFormLayout()

        self.sound_enabled = QCheckBox("启用音效")
        self.sound_enabled.setChecked(not self.pet_app.sound.mute)
        self.sound_enabled.toggled.connect(
            lambda v: setattr(self.pet_app.sound, 'mute', not v)
        )
        sound_layout.addRow(self.sound_enabled)

        sound_group.setLayout(sound_layout)
        layout.addWidget(sound_group)

        # 摄像头设置
        cam_group = QGroupBox("📷 摄像头设置")
        cam_layout = QFormLayout()

        self.cam_enabled = QCheckBox("启用摄像头面部检测")
        self.cam_enabled.setChecked(
            self.pet_app.behavior.is_camera_enabled
        )
        self.cam_enabled.toggled.connect(self._on_cam_toggle)
        cam_layout.addRow(self.cam_enabled)

        cam_status = "可用 ✅" if self.pet_app.camera and self.pet_app.camera.is_available else "不可用 ❌"
        cam_layout.addRow("状态:", QLabel(cam_status))

        cam_group.setLayout(cam_layout)
        layout.addWidget(cam_group)

        # 保存按钮
        save_btn = QPushButton("💾 保存设置")
        save_btn.clicked.connect(self._save_settings)
        layout.addWidget(save_btn)

        self.setStyleSheet("""
            QDialog { background-color: #1a1a20; color: #e0e0e0; }
            QGroupBox { border: 1px solid #444; border-radius: 6px; margin-top: 10px; padding-top: 16px; font-weight: bold; color: #64FF64; }
            QGroupBox::title { subcontrol-origin: margin; left: 12px; }
            QLineEdit { background: #24242e; color: #e0e0e0; border: 1px solid #444; border-radius: 4px; padding: 6px; }
            QPushButton { background: #3a7a3a; color: white; border: none; border-radius: 6px; padding: 10px; font-weight: bold; }
            QPushButton:hover { background: #4a9a4a; }
            QCheckBox { color: #e0e0e0; }
        """)

    def _on_llm_toggle(self, enabled):
        self.pet_app.behavior.is_llm_enabled = enabled
        if enabled and not self.pet_app.llm.is_available:
            self.api_key_input.setFocus()

    def _on_cam_toggle(self, enabled):
        self.pet_app.behavior.is_camera_enabled = enabled
        if enabled:
            if self.pet_app.camera and self.pet_app.camera.is_available:
                self.pet_app.camera.start()
            else:
                self.pet_app.behavior.is_camera_enabled = False
                self.cam_enabled.setChecked(False)
        else:
            if self.pet_app.camera:
                self.pet_app.camera.stop()

    def _save_settings(self):
        """保存设置"""
        api_key = self.api_key_input.text().strip()
        if api_key:
            os.environ["OPENAI_API_KEY"] = api_key
            self.pet_app.llm = LLMChat(
                api_key=api_key,
                base_url=self.base_url_input.text().strip(),
                model=self.model_input.text().strip(),
            )
            self.pet_app.behavior.is_llm_enabled = self.pet_app.llm.is_available

        self.accept()


class PetApp:
    """桌面宠物 Rick 主控制器"""

    CONFIG_FILE = Path(__file__).parent / "config.json"

    def __init__(self):
        self.app = QApplication(sys.argv)
        self.app.setApplicationName("Desktop Rick")
        self.app.setQuitOnLastWindowClosed(False)

        # 加载配置
        self.config = self._load_config()

        # 初始化模块
        self.behavior = Behavior()
        self.sound = SoundManager(mute=False)
        self.llm = LLMChat(
            api_key=self.config.get("api_key"),
            base_url=self.config.get("base_url"),
            model=self.config.get("model", "gpt-3.5-turbo"),
        )
        self.web_search = WebSearchUtils()
        self.camera = CameraUtils(
            on_face_detected=self._on_face_detected,
            on_face_lost=self._on_face_lost,
        )

        # 恢复配置状态
        self.behavior.is_llm_enabled = self.llm.is_available
        self.behavior.is_camera_enabled = self.config.get("camera_enabled", False)
        self.sound.mute = self.config.get("mute", False)

        # 创建 Rick Widget
        self.rick = RickWidget(self.behavior, self.sound)
        self.rick.chat_requested.connect(self._on_chat_requested)

        # 创建系统托盘
        self._setup_tray()

        # 初始问候
        QTimer.singleShot(1500, self._initial_greeting)

        # 如果摄像头启用，启动检测
        if self.behavior.is_camera_enabled and self.camera.is_available:
            QTimer.singleShot(2000, self.camera.start)

    def _load_config(self) -> dict:
        """加载配置文件"""
        default = {
            "api_key": os.environ.get("OPENAI_API_KEY", ""),
            "base_url": os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1"),
            "model": "gpt-3.5-turbo",
            "mute": False,
            "camera_enabled": False,
        }
        if self.CONFIG_FILE.exists():
            try:
                with open(self.CONFIG_FILE) as f:
                    data = json.load(f)
                    default.update(data)
            except Exception:
                pass
        return default

    def _save_config(self):
        """保存配置"""
        config = {
            "api_key": self.config.get("api_key", ""),
            "base_url": self.config.get("base_url", ""),
            "model": self.config.get("model", "gpt-3.5-turbo"),
            "mute": self.sound.mute,
            "camera_enabled": self.behavior.is_camera_enabled,
        }
        try:
            with open(self.CONFIG_FILE, 'w') as f:
                json.dump(config, f, indent=2)
        except Exception:
            pass

    def _setup_tray(self):
        """系统托盘"""
        self.tray = QSystemTrayIcon(self.app)
        # 尝试设置图标（如果无图标文件则降级到文字）
        icon_path = Path(__file__).parent / "assets" / "rick_icon.png"
        if icon_path.exists():
            self.tray.setIcon(QIcon(str(icon_path)))
        else:
            # 无图标文件，使用系统默认
            self.tray.setIcon(self.app.style().standardIcon(
                self.app.style().StandardPixmap.SP_ComputerIcon
            ))

        self.tray.setToolTip("Desktop Rick - Wubba lubba dub dub!")

        tray_menu = QMenu()
        tray_menu.setStyleSheet("""
            QMenu {
                background-color: #1e1e23;
                color: #f0f0f0;
                border: 1px solid #64FF64;
                border-radius: 6px;
            }
            QMenu::item:selected { background-color: #333340; }
        """)

        # 显示/隐藏
        show_action = tray_menu.addAction("👁️ 显示 Rick")
        show_action.triggered.connect(self.rick.show)

        hide_action = tray_menu.addAction("🙈 隐藏 Rick")
        hide_action.triggered.connect(self.rick.hide)

        tray_menu.addSeparator()

        # 聊天
        chat_action = tray_menu.addAction("💬 聊天")
        chat_action.triggered.connect(lambda: self._on_chat_requested(""))

        # 设置
        settings_action = tray_menu.addAction("⚙️ 设置")
        settings_action.triggered.connect(self._open_settings)

        tray_menu.addSeparator()

        # 退出
        quit_action = tray_menu.addAction("❌ 退出")
        quit_action.triggered.connect(self._quit)

        self.tray.setContextMenu(tray_menu)
        self.tray.show()

    def _initial_greeting(self):
        """初始问候"""
        greeting = self.llm.get_greeting()
        self.rick.say(greeting)

    def _on_chat_requested(self, _):
        """打开聊天窗口"""
        dialog = ChatDialog(self.llm, self.rick)
        dialog.exec()

    def _open_settings(self):
        """打开设置窗口"""
        dialog = SettingsDialog(self)
        dialog.exec()
        self._save_config()

    def _on_face_detected(self):
        """摄像头检测到面部"""
        quotes = [
            "*burp* Finally, someone to talk to.",
            "Oh great, you're back. Thrilled.",
            "Morty! I was just working on something.",
        ]
        self.rick.say(random.choice(quotes))

    def _on_face_lost(self):
        """摄像头丢失面部"""
        quotes = [
            "Where'd you go? Whatever, I'll just keep working.",
            "Morty? ... Whatever.",
            "*burp* Alone again. Perfect.",
        ]
        self.rick.say(random.choice(quotes))

    def _quit(self):
        """退出应用"""
        if self.camera:
            self.camera.stop()
        self._save_config()
        self.rick.close()
        self.app.quit()

    def run(self):
        """启动应用"""
        return self.app.exec()


def create_app() -> PetApp:
    return PetApp()
