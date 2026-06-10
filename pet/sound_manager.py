"""
音效管理器 — 生成 Rick 风格的电子音效（无需外部音频文件）。
使用正弦波合成：burp、传送枪、吐槽语气。
"""
import math
import struct
import io
import wave
import os
import threading


class SoundManager:
    """管理桌面宠物的音效。

    在没有外部音频文件的情况下，使用正弦波合成生成简单的音效。
    如果检测到 pygame，则使用 pygame.mixer 播放；
    否则 fallback 到系统播放器（afplay / aplay）。
    """

    SAMPLE_RATE = 44100
    AMPLITUDE = 0.4

    # 音效类型
    BURP = "burp"
    PORTAL = "portal"
    CLICK = "click"
    WUBBA = "wubba"
    ANGRY = "angry"

    def __init__(self, mute: bool = False):
        self.mute = mute
        self._sounds = {}
        self._pygame_available = False

        try:
            import pygame
            pygame.mixer.init(frequency=self.SAMPLE_RATE, size=-16, channels=1)
            self._pygame_available = True
        except Exception:
            pass

        self._generate_sounds()

    def _generate_sounds(self):
        """预生成所有音效"""
        self._sounds = {
            self.BURP: self._gen_burp(),
            self.PORTAL: self._gen_portal(),
            self.CLICK: self._gen_click(),
            self.WUBBA: self._gen_wubba(),
            self.ANGRY: self._gen_angry(),
        }

    def _make_wav(self, samples: list) -> bytes:
        """将浮点采样列表打包为 WAV 字节"""
        buf = io.BytesIO()
        with wave.open(buf, 'wb') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(self.SAMPLE_RATE)
            data = b''.join(
                struct.pack('<h', max(-32767, min(32767, int(s * 32767))))
                for s in samples
            )
            wf.writeframes(data)
        return buf.getvalue()

    def _gen_burp(self) -> bytes:
        """生成 Rick 打嗝音效（低频噪声 + 频谱滑动）"""
        duration = 0.4
        n = int(self.SAMPLE_RATE * duration)
        samples = []
        for i in range(n):
            t = i / self.SAMPLE_RATE
            # 基频从 150Hz 滑到 80Hz
            freq = 150 - t * 180
            # 加噪声
            noise = (math.sin(2 * math.pi * freq * t) * 0.6 +
                     math.sin(2 * math.pi * freq * 2.3 * t) * 0.3 +
                     (hash(i) % 1000) / 1000.0 * 0.4)
            envelope = 1.0 - t / duration
            samples.append(noise * envelope * 0.7)
        return self._make_wav(samples)

    def _gen_portal(self) -> bytes:
        """传送枪音效（上升琶音 + 高频谐振）"""
        duration = 0.3
        n = int(self.SAMPLE_RATE * duration)
        samples = []
        for i in range(n):
            t = i / self.SAMPLE_RATE
            freq = 800 + t * 2000
            s = (math.sin(2 * math.pi * freq * t) * 0.5 +
                 math.sin(2 * math.pi * freq * 1.5 * t) * 0.2)
            envelope = 1.0 - t / duration
            samples.append(s * envelope * 0.6)
        return self._make_wav(samples)

    def _gen_click(self) -> bytes:
        """点击音效（尖锐短促）"""
        duration = 0.05
        n = int(self.SAMPLE_RATE * duration)
        samples = []
        for i in range(n):
            t = i / self.SAMPLE_RATE
            freq = 2000 - t * 8000
            s = math.sin(2 * math.pi * freq * t)
            envelope = 1.0 - t / duration
            samples.append(s * envelope * 0.5)
        return self._make_wav(samples)

    def _gen_wubba(self) -> bytes:
        """Wubba lubba dub dub 语气音效（多音节）"""
        duration = 0.6
        n = int(self.SAMPLE_RATE * duration)
        samples = []
        notes = [(300, 0.15), (350, 0.15), (280, 0.15), (320, 0.15)]
        for i in range(n):
            t = i / self.SAMPLE_RATE
            # 找到当前音节
            acc = 0
            freq = 300
            for note_freq, note_dur in notes:
                if t < acc + note_dur:
                    freq = note_freq
                    break
                acc += note_dur
            s = math.sin(2 * math.pi * freq * t) * 0.5
            envelope = max(0, 1.0 - t / duration)
            samples.append(s * envelope * 0.5)
        return self._make_wav(samples)

    def _gen_angry(self) -> bytes:
        """愤怒音效（低频锯齿波）"""
        duration = 0.25
        n = int(self.SAMPLE_RATE * duration)
        samples = []
        for i in range(n):
            t = i / self.SAMPLE_RATE
            freq = 100 + t * 50
            phase = (freq * t) % 1.0
            s = (phase - 0.5) * 2  # 锯齿波
            envelope = 1.0 - t / duration
            samples.append(s * envelope * 0.6)
        return self._make_wav(samples)

    def play(self, sound_type: str):
        """播放指定音效"""
        if self.mute:
            return
        wav_data = self._sounds.get(sound_type)
        if not wav_data:
            return

        def _play():
            if self._pygame_available:
                import pygame
                sound = pygame.mixer.Sound(buffer=wav_data)
                sound.play()
            else:
                # Fallback: 写入临时文件用系统播放器
                tmp_path = os.path.join(
                    os.path.dirname(__file__), ".rick_sound_tmp.wav"
                )
                try:
                    with open(tmp_path, 'wb') as f:
                        f.write(wav_data)
                    if os.name == 'posix':
                        os.system(f"afplay '{tmp_path}' &")
                    else:
                        os.system(f"start /min '' '{tmp_path}' >nul 2>&1")
                except Exception:
                    pass

        threading.Thread(target=_play, daemon=True).start()

    def play_random(self, types: list = None):
        """随机播放一个音效"""
        if types is None:
            types = [self.CLICK, self.WUBBA, self.BURP]
        import random
        self.play(random.choice(types))
