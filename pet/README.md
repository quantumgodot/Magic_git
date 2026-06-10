# 🧪 Desktop Rick — 桌面宠物

> *"I turned myself into a desktop pet, Morty! I'm Desktop Rick!"*  
> — Rick Sanchez, Dimension C-137

一个运行在 macOS/Windows/Linux 桌面上的 **Rick Sanchez** 角色宠物。  
**精灵图驱动**（Shimeji 兼容格式），多帧动画，透明置顶窗口，LLM 对话，联网搜索，摄像头面部识别。

---

## 功能列表

| 功能 | 描述 |
|------|------|
| 🖼️ 精灵图动画 | Shimeji 兼容格式：idle(4帧)/walk(8帧)/surprised(2帧)/sleep(2帧) |
| 🚶 自然行走 | 8帧行走循环 + 弹跳效果 + 屏幕边界反弹 |
| 😴 待机/睡觉 | 呼吸动画、Zzz 标记、睡眠状态 |
| 💬 台词气泡 | 点击弹出 Rick 经典台词，渐入渐出动画 |
| 🔊 合成音效 | 正弦波合成（打嗝、传送枪、点击音） |
| 🤖 LLM 对话 | OpenAI 兼容 API，Rick 人格系统提示词 |
| 🌐 联网搜索 | DuckDuckGo/Bing 搜索 |
| 📷 摄像头识别 | MediaPipe/OpenCV 面部检测 |
| 🖱️ 拖拽移动 | 按住 Rick 拖动到任意位置 |
| 📋 右键菜单 | 设置、音效/LLM/摄像头开关、退出 |
| 🔧 系统托盘 | 最小化到托盘 |

---

## 快速开始

### 1. 安装依赖

```bash
cd pet
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. 获取精灵图素材

**方式 A：生成占位精灵图**（立即可用，像素风）

```bash
python download_assets.py --placeholder
```

**方式 B：获取 Rick 原版精灵图**

从以下渠道下载 Rick Sanchez 的 Shimeji 精灵图包：
- **DeviantArt** 搜索 "Rick Sanchez shimeji"
- **GitHub** 搜索 "shimeji rick sprites"  
- **Shimeji-ee** 角色库

将下载的 PNG 文件放入 `assets/sprites/rick/` 目录，覆盖占位图：
```
assets/sprites/rick/
├── config.json
├── idle.png        # 待机（4帧，水平排列，每帧128x128）
├── walk.png        # 行走（8帧）
├── fall.png        # 下落（4帧）
├── surprised.png   # 惊讶（2帧）
├── sleep.png       # 睡觉（2帧）
└── grabbed.png     # 拖拽（2帧）
```

### 3. 启动

```bash
python main.py
```

精灵图引擎自动检测——有素材用精灵图，无素材自动 fallback 到 QPainter 绘制。

---

## 精灵图格式（Shimeji 兼容）

每个动画对应一个 PNG 文件（精灵条），所有帧水平排列：

```
帧宽 = 128px, 帧高 = 128px
idle.png:    [帧0][帧1][帧2][帧3]    = 512x128
walk.png:    [帧0][帧1]...[帧7]      = 1024x128
```

也支持 Shimeji-ee 的独立帧格式（每帧一个 PNG 在子文件夹中）。

---

## 命令行参数

```
python main.py --help

选项:
  --mute, -m         静音模式
  --camera, -c       启动时开启摄像头
  --llm MODEL, -l MODEL  启用 LLM 并指定模型
  --api-key KEY, -k KEY  API 密钥
  --base-url URL, -b URL  API 端点
```

---

## LLM 配置（可选）

```bash
export OPENAI_API_KEY="sk-xxx"
export OPENAI_BASE_URL="https://api.openai.com/v1"  # 或 Ollama/vLLM/DeepSeek
```

---

## 项目结构

```
pet/
├── main.py               # 入口 + CLI 参数
├── pet_app.py            # 主控制器（整合所有模块、托盘、设置窗口）
├── rick_widget.py        # Rick 角色透明窗口（精灵图优先，QPainter fallback）
├── rick_painter.py       # QPainter 手绘 Rick（占位模式，素材缺失时使用）
├── sprite_engine.py      # 🆕 精灵图加载 + 多帧动画引擎
├── download_assets.py    # 🆕 素材下载器（在线+占位生成）
├── behavior.py           # AI 行为状态机
├── speech_bubble.py      # 对话气泡
├── sound_manager.py      # 音效合成
├── llm_chat.py           # LLM 对话 + Rick 人格系统提示词
├── web_search_utils.py   # 联网搜索
├── camera_utils.py       # 摄像头面部识别
├── assets/
│   └── sprites/
│       └── rick/
│           ├── config.json   # 精灵图配置
│           ├── idle.png      # (需自行下载)
│           ├── walk.png
│           └── ...
├── requirements.txt
└── README.md
```

---

## 技术架构

```
┌─────────────────────────────────┐
│           main.py               │  入口 + 参数
└─────────────┬───────────────────┘
              │
┌─────────────▼───────────────────┐
│         PetApp                  │  主控制器
│  ┌──────────────────────────┐   │
│  │  RickWidget (透明窗口)   │   │
│  │  ┌────────────────────┐  │   │
│  │  │  SpriteEngine 🆕   │  │   │  精灵图动画（优先）
│  │  │  RickPainter       │  │   │  QPainter（fallback）
│  │  │  Behavior          │  │   │  行为状态机
│  │  │  SpeechBubble      │  │   │  对话气泡
│  │  └────────────────────┘  │   │
│  ├──────────────────────────┤   │
│  │  SoundManager / LLMChat  │   │
│  │  WebSearch / CameraUtils │   │
│  └──────────────────────────┘   │
└─────────────────────────────────┘
```

---

## 许可

MIT License — 仅供学习和娱乐使用。  
Rick and Morty 角色版权归 Adult Swim / Justin Roiland & Dan Harmon 所有。
