# Amplia · © 2026 Heraldo Antunes · SPDX-License-Identifier: MIT
"""Gera uma imagem autoral de calibração, sem downloads ou dados pessoais."""
from pathlib import Path
import sys
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
SCALE = 6  # 6 pixels por mm no pôster demonstrativo de 370 x 544 mm.


def font(size, bold=False):
    windows = Path('C:/Windows/Fonts') / ('segoeuib.ttf' if bold else 'segoeui.ttf')
    if windows.exists():
        return ImageFont.truetype(str(windows), size)
    return ImageFont.load_default(size=size)


def main():
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    image = Image.new('RGB', (370 * SCALE, 544 * SCALE), '#f7f4e9')
    draw = ImageDraw.Draw(image)
    for x in range(0, image.width, 10 * SCALE):
        draw.line((x, 0, x, image.height), fill='#e3e1d4', width=2)
    for y in range(0, image.height, 10 * SCALE):
        draw.line((0, y, image.width, y), fill='#e3e1d4', width=2)
    draw.text((100, 120), 'AMPLIA', font=font(270, True), fill='#1f6e43')
    draw.text((110, 490), 'DO ARQUIVO À PAREDE', font=font(68), fill='#384a3c')
    draw.text((110, 610), '370 × 544 mm  /  4 folhas A4', font=font(53), fill='#7e806c')
    draw.ellipse((1150, 950, 1900, 1700), fill='#c87a4e')
    draw.polygon([(0, 2300), (880, 1180), (1770, 2300)], fill='#356a4d')
    draw.polygon([(570, 2450), (1590, 1490), (2220, 2150), (2220, 2690), (0, 2690)], fill='#91a57e')
    draw.rectangle((0, 2540, 2220, 2790), fill='#1f6e43')
    draw.text((110, 2600), 'UMA IMAGEM. MUITAS POSSIBILIDADES.', font=font(56, True), fill='white')
    x, y = 120, 3020
    draw.line((x, y, x + 100 * SCALE, y), fill='#263a2c', width=9)
    for end in (x, x + 100 * SCALE):
        draw.line((end, y - 35, end, y + 35), fill='#263a2c', width=9)
    draw.text((x, y + 55), 'Esta linha mede 100 mm na impressão em 100%.', font=font(43), fill='#384a3c')
    image.save(ROOT / 'examples' / 'demo.png')
    (ROOT / 'output').mkdir(exist_ok=True)
    print('examples/demo.png: 2220 x 3264 pixels; pôster de 370 x 544 mm.')


if __name__ == '__main__':
    main()
