# modules/game_card.py
from PIL import Image, ImageDraw, ImageFont
import os
from config import FONT_PATH, PLAYER_CARD

def create_card(player_img_path, name, house, features_text, output_path=PLAYER_CARD):
    card = Image.new('RGB', (400, 200), color=(244, 229, 192))  # 羊皮纸色
    # 加载头像并裁剪圆形
    face = Image.open(player_img_path).resize((100, 100))
    mask = Image.new('L', (100, 100), 0)
    draw_mask = ImageDraw.Draw(mask)
    draw_mask.ellipse((0, 0, 100, 100), fill=255)
    card.paste(face, (20, 20), mask)

    draw = ImageDraw.Draw(card)
    try:
        font = ImageFont.truetype(FONT_PATH, 22)
    except:
        font = ImageFont.load_default()

    draw.text((140, 25), f"Name: {name}", font=font, fill=(50, 30, 20))
    draw.text((140, 55), f"House: {house}", font=font, fill=(50, 30, 20))
    # 多行显示特征
    lines = features_text.split('，')
    y = 85
    for line in lines:
        draw.text((140, y), line, font=font, fill=(80, 60, 40))
        y += 25

    card.save(output_path)
    return output_path