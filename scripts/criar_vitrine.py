# Amplia · © 2026 Heraldo Antunes · SPDX-License-Identifier: MIT
"""Monta a capa do repositório a partir da captura real e do ícone próprios."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]


def font(size, bold=False):
    name = 'segoeuib.ttf' if bold else 'segoeui.ttf'
    return ImageFont.truetype(str(Path('C:/Windows/Fonts') / name), size)


def main():
    canvas = Image.new('RGB', (1640, 820), '#eef3ec')
    draw = ImageDraw.Draw(canvas)
    icon = Image.open(ROOT / 'docs/img/icone.png').convert('RGBA')
    icon.thumbnail((150, 150), Image.Resampling.LANCZOS)
    canvas.paste(icon, (62, 75), icon)
    draw.text((60, 250), 'Amplia', fill='#1f6e43', font=font(76, True))
    draw.text((64, 370), 'Pôsteres em\nfolhas A4', fill='#263b2c', font=font(43, True), spacing=10)
    draw.rounded_rectangle((64, 558, 439, 612), radius=12, fill='#dce7d6')
    draw.text((82, 567), 'Versão em desenvolvimento', fill='#1f6e43', font=font(23))
    draw.text((64, 681), 'Windows · offline · licença MIT', fill='#50654f', font=font(22))
    capture = Image.open(ROOT / 'docs/img/fluxo.png').convert('RGB')
    capture.thumbnail((1050, 700), Image.Resampling.LANCZOS)
    x, y = 550, (820 - capture.height) // 2
    draw.rounded_rectangle((x-2, y-2, x+capture.width+2, y+capture.height+2), radius=7, fill='#c4d0be')
    canvas.paste(capture, (x, y))
    canvas.save(ROOT / 'docs/img/capa.png', optimize=True)


if __name__ == '__main__':
    main()
