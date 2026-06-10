"""
行为状态机 — 控制 Rick 的 AI 行为：空闲、行走、说话、睡觉。
随机切换到不同状态，模拟自然行为。
"""
import random
import time
from enum import Enum, auto


class BehaviorState(Enum):
    IDLE = auto()          # 待机（呼吸、眨眼、偶尔转头）
    WALKING = auto()       # 行走中
    TALKING = auto()       # 正在说话（气泡显示中）
    SLEEPING = auto()      # 睡觉（眼睛闭着，偶尔打鼾）
    REACTING = auto()      # 反应中（被点击后的反馈）
    THINKING = auto()      # 思考中（LLM 查询中）


class Behavior:
    """桌面宠物的行为大脑。

    状态机在几个状态之间随机切换，模拟真实宠物的不可预测性。
    每个状态有持续时间范围和转换概率。
    """

    # 状态配置：(最小持续时间, 最大持续时间, 可转换到的状态列表+权重)
    STATE_CONFIG = {
        BehaviorState.IDLE: {
            "min_duration": 2.0,
            "max_duration": 8.0,
            "transitions": [
                (BehaviorState.WALKING, 0.35),
                (BehaviorState.IDLE, 0.50),
                (BehaviorState.SLEEPING, 0.15),
            ]
        },
        BehaviorState.WALKING: {
            "min_duration": 3.0,
            "max_duration": 10.0,
            "transitions": [
                (BehaviorState.IDLE, 0.65),
                (BehaviorState.WALKING, 0.20),
                (BehaviorState.SLEEPING, 0.10),
                (BehaviorState.TALKING, 0.05),
            ]
        },
        BehaviorState.TALKING: {
            "min_duration": 1.5,
            "max_duration": 4.0,
            "transitions": [
                (BehaviorState.IDLE, 1.0),
            ]
        },
        BehaviorState.SLEEPING: {
            "min_duration": 5.0,
            "max_duration": 20.0,
            "transitions": [
                (BehaviorState.IDLE, 0.8),
                (BehaviorState.WALKING, 0.2),
            ]
        },
        BehaviorState.REACTING: {
            "min_duration": 0.5,
            "max_duration": 2.0,
            "transitions": [
                (BehaviorState.IDLE, 0.9),
                (BehaviorState.TALKING, 0.1),
            ]
        },
        BehaviorState.THINKING: {
            "min_duration": 1.0,
            "max_duration": 5.0,
            "transitions": [
                (BehaviorState.TALKING, 0.85),
                (BehaviorState.IDLE, 0.15),
            ]
        },
    }

    def __init__(self):
        self.current_state = BehaviorState.IDLE
        self.state_start_time = time.time()
        self.state_duration = self._random_duration(BehaviorState.IDLE)
        self.walk_direction = 1  # 1=右, -1=左
        self.walk_speed = 1.0    # 像素/帧
        self.talk_text = ""
        self.reaction_triggered = False

        # 全局状态
        self.is_llm_enabled = False
        self.is_sound_enabled = True
        self.is_camera_enabled = False

    def _random_duration(self, state: BehaviorState) -> float:
        config = self.STATE_CONFIG[state]
        return random.uniform(config["min_duration"], config["max_duration"])

    def _choose_next_state(self, state: BehaviorState) -> BehaviorState:
        config = self.STATE_CONFIG[state]
        transitions = config["transitions"]
        r = random.random()
        cumulative = 0
        for target, weight in transitions:
            cumulative += weight
            if r <= cumulative:
                return target
        return transitions[-1][0]

    def update(self, dt: float):
        """每帧调用，检查是否需要切换状态"""
        elapsed = time.time() - self.state_start_time
        if elapsed >= self.state_duration and self.current_state not in (
            BehaviorState.REACTING, BehaviorState.TALKING, BehaviorState.THINKING
        ):
            self._transition()

        # 行走时随机改变方向
        if self.current_state == BehaviorState.WALKING:
            if random.random() < 0.01:
                self.walk_direction *= -1

    def _transition(self, target: BehaviorState = None):
        """状态转换"""
        if target is None:
            target = self._choose_next_state(self.current_state)
        self.current_state = target
        self.state_start_time = time.time()
        self.state_duration = self._random_duration(target)

        if target == BehaviorState.WALKING:
            self.walk_direction = random.choice([-1, 1])
            self.walk_speed = random.uniform(0.5, 1.5)

    def trigger_reaction(self, text: str = ""):
        """外部触发反应（如被点击）"""
        self.talk_text = text
        self._transition(BehaviorState.REACTING)

    def trigger_talk(self, text: str):
        """触发说话"""
        self.talk_text = text
        self._transition(BehaviorState.TALKING)

    def trigger_think(self):
        """触发思考状态（LLM 查询中）"""
        self._transition(BehaviorState.THINKING)

    def on_think_done(self, text: str):
        """LLM 思考完成"""
        self.talk_text = text
        self._transition(BehaviorState.TALKING)

    @property
    def is_moving(self) -> bool:
        return self.current_state == BehaviorState.WALKING

    @property
    def is_talking(self) -> bool:
        return self.current_state in (BehaviorState.TALKING, BehaviorState.THINKING)

    @property
    def is_sleeping(self) -> bool:
        return self.current_state == BehaviorState.SLEEPING
