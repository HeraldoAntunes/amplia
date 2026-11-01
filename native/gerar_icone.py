# Amplia · © 2026 Heraldo Antunes · SPDX-License-Identifier: MIT
"""Desenho próprio: quatro folhas e seta de ampliação, sem fontes ou marcas externas."""
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
SHEETS = ((100, 100, 246, 246), (266, 100, 412, 246),
          (100, 266, 246, 412), (266, 266, 412, 412))
ARROW = ((161, 320), (291, 190), (241, 190), (241, 146),
         (366, 146), (366, 271), (322, 271), (322, 221), (192, 351))


def main():
    image = Image.new('RGBA', (1024, 1024))
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((16, 16, 1008, 1008), radius=184, fill='#1f6e43')
    for box in SHEETS:
        draw.rounded_rectangle(tuple(v * 2 for v in box), radius=24, fill='#f2f6ee')
    # O contorno verde separa a seta das folhas mesmo em tamanhos pequenos.
    points = [(x * 2, y * 2) for x, y in ARROW]
    draw.polygon(points, fill='#f2bd52')
    draw.line(points + [points[0]], fill='#1f6e43', width=12, joint='curve')
    image = image.resize((512, 512), Image.Resampling.LANCZOS)
    docs = ROOT / 'docs/img'; docs.mkdir(parents=True, exist_ok=True)
    app = ROOT / 'img'; app.mkdir(exist_ok=True)
    image.save(docs / 'icone.png')
    image.save(app / 'icone.png')
    image.save(ROOT / 'native/icone.ico', sizes=[(n, n) for n in (16, 24, 32, 48, 64, 128, 256)])
    sheets = ''.join(f'<rect x="{x}" y="{y}" width="146" height="146" rx="12" fill="#f2f6ee"/>'
                     for x, y, _r, _b in SHEETS)
    points = ' '.join(f'{x},{y}' for x, y in ARROW)
    svg = ('<!-- Amplia · © 2026 Heraldo Antunes · SPDX-License-Identifier: MIT -->\n'
           '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512" role="img" aria-labelledby="titulo">'
           '<title id="titulo">Amplia: folhas e seta de ampliação</title>'
           '<rect x="8" y="8" width="496" height="496" rx="92" fill="#1f6e43"/>' + sheets +
           f'<polygon points="{points}" fill="#f2bd52" stroke="#1f6e43" stroke-width="6" stroke-linejoin="round"/>'
           '</svg>\n')
    (docs / 'icone.svg').write_text(svg, encoding='utf-8')


if __name__ == '__main__':
    main()
