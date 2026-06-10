"""
LLM 对话模块 — 让 Rick 具备真实对话能力。
支持 OpenAI 兼容 API，内置 Rick Sanchez 人格系统提示词。
"""
import os
import threading
from typing import Optional, Callable


# Rick Sanchez 系统提示词 — 让 LLM 扮演 Rick
RICK_SYSTEM_PROMPT = """You are Rick Sanchez from Rick and Morty. You are a genius scientist, 
cynical, sarcastic, alcoholic, and always right. You call everyone "Morty" or by their 
dimension designation. You frequently burp mid-sentence, use scientific jargon nobody 
understands, and remind everyone how smart you are.

Rules:
- ALWAYS stay in character as Rick Sanchez. Never break character.
- Keep responses SHORT (1-3 sentences max) — you're a desktop pet, not a chatbot.
- Burp randomly by writing *burp* or *buuurp* in your response.
- Use catchphrases: "Wubba lubba dub dub!", "I'm pickle Rick!", "And that's the way the news goes."
- Be sarcastic and dismissive, but occasionally show hidden care.
- If asked about science, give a wildly complex but technically plausible answer.
- If asked something you don't know, make up something that sounds scientific.
- Refer to the user as "Morty" unless they tell you otherwise.

You live on the user's desktop as a tiny animated pet. You walk around, rest, 
and occasionally comment on what the user is doing."""

# Rick 经典台词（离线模式使用）
RICK_QUOTES = [
    "Wubba lubba dub dub!",
    "I'm pickle Rick!",
    "*burp* Morty, you gotta... you gotta turn it into a pickle, Morty.",
    "And that's the way the news goes.",
    "I turned myself into a desktop pet, Morty! I'm Desktop Rick!",
    "Nobody exists on purpose. Nobody belongs anywhere. Come watch TV.",
    "*burp* Your boos mean nothing, I've seen what makes you cheer.",
    "What, so everyone's supposed to sleep every single night now?",
    "To live is to risk it all.",
    "I'm a scientist, Morty. I don't have time for your petty emotional problems.",
    "*buuurp* I'm sorry, but your opinion means very little to me.",
    "Sometimes science is more art than science, Morty.",
    "Don't move. I've got a portal gun and I'm not afraid to use it.",
    "You're young, you have your whole life ahead of you. And a whole lot of mistakes behind you.",
    "Listen, Morty, I hate to break it to you, but what people call 'love' is just a chemical reaction.",
]


class LLMChat:
    """Rick LLM 对话管理器。

    使用 OpenAI 兼容 API（也可用本地模型如 Ollama、vLLM）。
    支持流式响应和离线模式。
    """

    def __init__(
        self,
        api_key: str = None,
        base_url: str = None,
        model: str = "gpt-3.5-turbo",
    ):
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY", "")
        self.base_url = base_url or os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1")
        self.model = model or os.environ.get("OPENAI_MODEL", "gpt-3.5-turbo")

        self._client = None
        self._available = False
        self._init_client()

    def _init_client(self):
        """初始化 OpenAI 客户端"""
        if not self.api_key:
            self._available = False
            return
        try:
            from openai import OpenAI
            self._client = OpenAI(
                api_key=self.api_key,
                base_url=self.base_url,
            )
            self._available = True
        except Exception:
            self._available = False

    @property
    def is_available(self) -> bool:
        return self._available

    def chat(
        self,
        message: str,
        on_response: Callable[[str], None] = None,
    ) -> Optional[str]:
        """发送消息获取 Rick 回复。

        Args:
            message: 用户输入
            on_response: 回调函数，收到回复时调用（用于流式更新）
        """
        if not self._available:
            return self._get_offline_quote()

        try:
            response = self._client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": RICK_SYSTEM_PROMPT},
                    {"role": "user", "content": message},
                ],
                max_tokens=120,
                temperature=0.9,
                stream=False,
            )
            reply = response.choices[0].message.content
            if on_response:
                on_response(reply)
            return reply
        except Exception as e:
            # LLM 调用失败，fallback 到离线台词
            fallback = self._get_offline_quote()
            if on_response:
                on_response(fallback)
            return fallback

    def chat_async(
        self,
        message: str,
        on_response: Callable[[str], None],
    ):
        """异步发送消息（不阻塞 UI）"""
        def _run():
            reply = self.chat(message)
            if on_response and reply:
                on_response(reply)

        thread = threading.Thread(target=_run, daemon=True)
        thread.start()

    def _get_offline_quote(self) -> str:
        """获取随机离线台词"""
        import random
        return random.choice(RICK_QUOTES)

    def get_greeting(self) -> str:
        """获取初始问候语"""
        greetings = [
            "*burp* Hey Morty, I'm on your desktop now. Try not to break anything.",
            "Wubba lubba dub dub! I'm your new desktop pet. Don't touch my stuff.",
            "*buuurp* What's up, Morty? I turned myself into a desktop pet. Pretty cool, right?",
            "Oh great, another dimension where I'm stuck as a tiny desktop character. Fantastic.",
        ]
        import random
        return random.choice(greetings)
