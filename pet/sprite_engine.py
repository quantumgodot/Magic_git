"""
精灵图引擎 — 加载 Shimeji 兼容格式的精灵图，驱动角色动画。

支持两种模式：
1. 精灵条模式：单张 PNG 水平排列所有帧
2. 独立帧模式：Shimeji-ee 标准（每帧一个 PNG 文件）

动画状态：idle / walk / fall / grabbed / surprised / sleep
"""

import json
import os
from pathlib import Path
from typing import Optional, Dict, List, Tuple
from dataclasses import dataclass, field
from enum import Enum

from PyQt6.QtCore import Qt, QRectF, QPointF
from PyQt6.QtGui import QPixmap, QImage, QPainter, QTransform


class AnimationState(Enum):
    IDLE = "idle"
    WALK_LEFT = "walk_left"
    WALK_RIGHT = "walk_right"
    FALL = "fall"
    GRABBED = "grabbed"
    SURPRISED = "surprised"
    SLEEP = "sleep"


@dataclass
class AnimationClip:
    """单个动画片段"""
    name: str
    frames: List[QPixmap] = field(default_factory=list)
    fps: float = 8.0
    loop: bool = True
    total_frames: int = 0

    @property
    def frame_duration(self) -> float:
        return 1.0 / self.fps if self.fps > 0 else 0.125

    def get_frame(self, index: int) -> QPixmap:
        if not self.frames:
            return QPixmap()
        return self.frames[index % len(self.frames)]


class SpriteEngine:
    """精灵图动画引擎。

    管理角色的所有动画片段，按时间推进帧，输出当前帧的 QPixmap。

    兼容 Shimeji-ee 精灵图格式：
    - 精灵条（sheet）：idle.png / walk.png / ...（水平排列帧）
    - 独立帧（frames）：idle/0.png, idle/1.png, ... / walk/0.png, ...

    配置文件 config.json：
    {
        "animations": {
            "idle": {"frames": 4, "fps": 4},
            "walk": {"frames": 8, "fps": 10},
            ...
        }
    }
    """

    def __init__(self, sprite_dir: Optional[str] = None, size: int = 128):
        self.size = size
        self.sprite_dir = Path(sprite_dir) if sprite_dir else None
        self.clips: Dict[str, AnimationClip] = {}
        self._current_state = AnimationState.IDLE
        self._current_frame = 0
        self._frame_time = 0.0
        self._loaded = False

        # 动画状态映射（支持镜像翻转到 walk_left）
        self._flip_x = False

        if self.sprite_dir and self.sprite_dir.exists():
            self._load_sprites()

    @property
    def is_loaded(self) -> bool:
        return self._loaded and len(self.clips) > 0

    def _load_sprites(self):
        """从精灵图目录加载所有动画"""
        config_path = self.sprite_dir / "config.json"
        if not config_path.exists():
            return

        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
        except Exception:
            return

        animations = config.get("animations", {})
        for name, anim_cfg in animations.items():
            clip = self._load_clip(name, anim_cfg)
            if clip and clip.frames:
                self.clips[name] = clip

        if self.clips:
            self._loaded = True

    def _load_clip(self, name: str, cfg: dict) -> Optional[AnimationClip]:
        """加载单个动画片段"""
        frames = []
        total_frames = cfg.get("frames", 1)
        fps = cfg.get("fps", 8.0)

        # 方式 1：精灵条（sheet）
        sheet_name = cfg.get("sheet", f"{name}.png")
        sheet_path = self.sprite_dir / sheet_name

        if sheet_path.exists():
            pixmap = QPixmap(str(sheet_path))
            if not pixmap.isNull():
                frame_w = pixmap.width() // total_frames
                frame_h = pixmap.height()
                for i in range(total_frames):
                    frame = pixmap.copy(i * frame_w, 0, frame_w, frame_h)
                    scaled = frame.scaled(
                        self.size, self.size,
                        Qt.AspectRatioMode.KeepAspectRatio,
                        Qt.TransformationMode.SmoothTransformation
                    )
                    frames.append(scaled)

        # 方式 2：独立帧文件（Shimeji-ee 格式）
        if not frames:
            frame_dir = self.sprite_dir / name
            if frame_dir.exists() and frame_dir.is_dir():
                pngs = sorted(frame_dir.glob("*.png"))
                for png_path in pngs[:total_frames]:
                    pixmap = QPixmap(str(png_path))
                    if not pixmap.isNull():
                        scaled = pixmap.scaled(
                            self.size, self.size,
                            Qt.AspectRatioMode.KeepAspectRatio,
                            Qt.TransformationMode.SmoothTransformation
                        )
                        frames.append(scaled)

        if frames:
            return AnimationClip(
                name=name,
                frames=frames,
                fps=fps,
                total_frames=len(frames),
            )
        return None

    # ========== 运行控制 ==========

    def set_state(self, state: AnimationState):
        """切换动画状态"""
        self._current_state = state

        # walk_left 需要翻转
        if state == AnimationState.WALK_LEFT:
            self._flip_x = True
            # 使用 walk 动画但水平翻转
            state_key = "walk"
        elif state == AnimationState.WALK_RIGHT:
            self._flip_x = False
            state_key = "walk"
        else:
            self._flip_x = False
            state_key = state.value

        # 如果当前状态没有对应动画，fallback 到 idle
        if state_key not in self.clips:
            state_key = "idle"

        # 重置帧计数
        if hasattr(self, '_state_key') and self._state_key != state_key:
            self._current_frame = 0
            self._frame_time = 0.0
        self._state_key = state_key

    def update(self, dt: float):
        """推进动画时间"""
        clip = self._get_current_clip()
        if not clip:
            return

        self._frame_time += dt
        frame_dur = clip.frame_duration
        if self._frame_time >= frame_dur:
            self._frame_time -= frame_dur
            self._current_frame = (self._current_frame + 1) % clip.total_frames

    def get_current_frame(self) -> QPixmap:
        """获取当前帧"""
        clip = self._get_current_clip()
        if not clip:
            return QPixmap()
        frame = clip.get_frame(self._current_frame)
        if self._flip_x and not frame.isNull():
            return frame.transformed(QTransform().scale(-1, 1))
        return frame

    def _get_current_clip(self) -> Optional[AnimationClip]:
        state_key = getattr(self, '_state_key', 'idle')
        return self.clips.get(state_key)

    # ========== 工具方法 ==========

    @staticmethod
    def create_default_config(output_dir: str):
        """生成默认的精灵图配置文件模板"""
        config = {
            "name": "Rick Sanchez",
            "description": "Rick and Morty desktop pet sprite configuration",
            "frame_size": {"width": 128, "height": 128},
            "animations": {
                "idle": {
                    "frames": 4,
                    "fps": 4,
                    "sheet": "idle.png",
                    "description": "待机呼吸动画"
                },
                "walk": {
                    "frames": 8,
                    "fps": 10,
                    "sheet": "walk.png",
                    "description": "行走动画（右向，引擎自动翻转左向）"
                },
                "fall": {
                    "frames": 4,
                    "fps": 8,
                    "sheet": "fall.png",
                    "description": "下落动画"
                },
                "grabbed": {
                    "frames": 2,
                    "fps": 4,
                    "sheet": "grabbed.png",
                    "description": "被拖拽时的动画"
                },
                "surprised": {
                    "frames": 2,
                    "fps": 4,
                    "sheet": "surprised.png",
                    "description": "惊讶反应动画"
                },
                "sleep": {
                    "frames": 2,
                    "fps": 2,
                    "sheet": "sleep.png",
                    "description": "睡觉动画"
                }
            }
        }

        os.makedirs(output_dir, exist_ok=True)
        config_path = os.path.join(output_dir, "config.json")
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)

        print(f"[SpriteEngine] 已创建配置模板: {config_path}")
        print(f"[SpriteEngine] 请将对应动画的 PNG 精灵条放入: {output_dir}")
        print(f"[SpriteEngine] 精灵条格式：水平排列帧，帧宽=128px，帧高=128px")

        return config_path
