# test_spell.py
import pygame
import sys
from modules.duel_2_spell import spell_duel
from config import SPELLS_FILE  # 假设 config.py 中定义了咒语文件路径

# 这个脚本用于测试 spell_duel 的语音识别流程。
# 测试内容：
# 1. 启动 pygame 窗口展示三条备选咒语
# 2. 按 1 / 2 / 3 选择一个咒语
# 3. 程序自动开始录音，等待你说出所选咒语（最多 3 秒）
# 4. 识别结果与目标咒语对比，相似度 >= 75 则判定为成功，否则失败
# 5. 最终在控制台输出“测试结果：成功”或“测试结果：失败”

# 预期测试步骤：
# 1. 运行本脚本
# 2. 在 pygame 窗口中看到三条备选咒语
# 3. 按 1 / 2 / 3 选择你要说的咒语
# 4. 听到录音提示后，说出你刚刚选择的咒语（例如: Lumos）
# 5. 等待结果显示，程序会自动显示识别文本与成功/失败状态

# 正确答案示例：
# - 如果目标咒语是 Lumos，且语音识别结果为 Lumos 或非常接近，控制台应显示“测试结果：成功”
# - 如果结果识别为其他内容，或识别失败，控制台应显示“测试结果：失败”
# - 如果按键选择了 2 或 3，同样要说出对应的咒语，才算成功

# 初始化 pygame 显示，因为 spell_duel 可能需要在 screen 上显示文字
pygame.init()
screen = pygame.display.set_mode((800, 600))
pygame.display.set_caption("Spell Test")

print("开始咒语测试...")
print("操作说明：按 1/2/3 选择一个咒语，随后程序会自动开始录音，最多录制 3 秒。")
print("请在听到提示后大声说出你选择的咒语。")
print("测试结束后，控制台将显示“测试结果：成功”或“测试结果：失败”。")

# 调用 spell_duel，返回 True/False 表示成功识别
result = spell_duel(screen, SPELLS_FILE)
print(f"测试结果：{'成功' if result else '失败'}")

pygame.quit()
sys.exit()