# modules/scene_manager.py
# modules/llm_utils.py
# 可选：调用LLM生成动态台词，这里提供简单接口
def get_monster_line(context="battle_start"):
    """返回三头怪的台词（可预先储存或调用API）"""
    lines = {
        "battle_start": "三头怪怒吼：愚蠢的人类，来挑战我吧！",
        "rps_win": "三头怪：不可能，你竟然赢了猜拳！",
        "rps_lose": "三头怪：哈哈哈，你太弱了！",
        "spell_win": "三头怪：啊！可恶的咒语！",
        "spell_lose": "三头怪：你的舌头打结了吗？",
        "dodge_win": "三头怪：不！火球居然打不中你！",
        "dodge_lose": "三头怪：烧成灰烬吧！",
    }
    return lines.get(context, "三头怪：...")