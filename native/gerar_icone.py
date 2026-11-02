# Amplia · © 2026 Heraldo Antunes · SPDX-License-Identifier: MIT
"""Desenho próprio: uma folha menor ampliada para outra maior, na mesma paleta."""
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
SMALL_SHEET = (108, 258, 228, 428)
LARGE_SHEET = ((220, 96), (368, 96), (404, 132), (404, 352), (220, 352))
FOLD = ((368, 96), (368, 132), (404, 132))
ARROW = ((161, 320), (291, 190), (241, 190), (241, 146),
         (366, 146), (366, 271), (322, 271), (322, 221), (192, 351))


def main():
    image = Image.new('RGBA', (2048, 2048))
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((32, 32, 2016, 2016), radius=368, fill='#1f6e43')
    draw.rounded_rectangle(tuple(v * 4 for v in SMALL_SHEET), radius=48,
                           fill='#f2f6ee', outline='#1f6e43', width=40)
    large = [(x * 4, y * 4) for x, y in LARGE_SHEET]
    draw.polygon(large, fill='#f2f6ee')
    draw.line(large + [large[0]], fill='#1f6e43', width=40, joint='curve')
    draw.polygon([(x * 4, y * 4) for x, y in FOLD], fill='#bfd7c6')
    # O contorno verde separa a seta das folhas mesmo em tamanhos pequenos.
    points = [(x * 4, y * 4) for x, y in ARROW]
    draw.polygon(points, fill='#f2bd52')
    draw.line(points + [points[0]], fill='#1f6e43', width=24, joint='curve')
    image = image.resize((512, 512), Image.Resampling.LANCZOS)
    docs = ROOT / 'docs/img'; docs.mkdir(parents=True, exist_ok=True)
    app = ROOT / 'img'; app.mkdir(exist_ok=True)
    image.save(docs / 'icone.png')
    image.save(app / 'icone.png')
    image.save(ROOT / 'native/icone.ico', sizes=[(n, n) for n in (16, 24, 32, 48, 64, 128, 256)])
    x, y, right, bottom = SMALL_SHEET
    large_points = ' '.join(f'{x},{y}' for x, y in LARGE_SHEET)
    fold_points = ' '.join(f'{x},{y}' for x, y in FOLD)
    sheets = (f'<rect x="{x}" y="{y}" width="{right-x}" height="{bottom-y}" rx="12" '
              'fill="#f2f6ee" stroke="#1f6e43" stroke-width="10"/>'
              f'<polygon points="{large_points}" fill="#f2f6ee" stroke="#1f6e43" '
              'stroke-width="10" stroke-linejoin="round"/>'
              f'<polygon points="{fold_points}" fill="#bfd7c6"/>')
    points = ' '.join(f'{x},{y}' for x, y in ARROW)
    svg = ('<!-- Amplia · © 2026 Heraldo Antunes · SPDX-License-Identifier: MIT -->\n'
           '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512" role="img" aria-labelledby="titulo">'
           '<title id="titulo">Amplia: da folha menor para a maior, com seta de ampliação</title>'
           '<rect x="8" y="8" width="496" height="496" rx="92" fill="#1f6e43"/>' + sheets +
           f'<polygon points="{points}" fill="#f2bd52" stroke="#1f6e43" stroke-width="6" stroke-linejoin="round"/>'
           '</svg>\n')
    (docs / 'icone.svg').write_text(svg, encoding='utf-8')


if __name__ == '__main__':
    main()
