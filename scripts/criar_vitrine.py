# Amplia · © 2026 Heraldo Antunes · SPDX-License-Identifier: MIT
"""Gera o exemplo didático e a capa documental com captura real do aplicativo."""
import argparse
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter

ROOT = Path(__file__).resolve().parents[1]
IMG = ROOT / 'docs/img'


def font(size, bold=False):
    return ImageFont.truetype(str(Path('C:/Windows/Fonts') / ('seguisb.ttf' if bold else 'segoeui.ttf')), size)


def example():
    image = Image.new('RGB', (3244, 1480), '#f3f0e8')
    d = ImageDraw.Draw(image)
    d.text((78, 48), 'GEOMETRIA', fill='#1f5f49', font=font(142, True))
    d.text((82, 228), 'Áreas e perímetros', fill='#324a41', font=font(78))
    cards = [(72, 'Retângulo'), (1120, 'Quadrado'), (2168, 'Triângulo retângulo')]
    for x, title in cards:
        d.rounded_rectangle((x, 380, x+1004, 1322), radius=28, fill='white', outline='#d9dfd5', width=3)
        d.text((x+44, 414), title, fill='#234d3c', font=font(66, True))
    x, y = 72, 380
    d.rectangle((x+262, y+240, x+742, y+560), fill='#e1eee6', outline='#24634a', width=10)
    d.text((x+390, y+585), '12 cm', fill='#3e5149', font=font(54))
    d.text((x+770, y+355), '8 cm', fill='#3e5149', font=font(54))
    d.text((x+60, y+736), 'A = 12 × 8 = 96 cm²', fill='#1e6146', font=font(63, True))
    d.text((x+60, y+824), 'P = 2 × (12 + 8) = 40 cm', fill='#324a41', font=font(54))
    x = 1120
    d.rectangle((x+342, y+240, x+662, y+560), fill='#fcf0da', outline='#ae7738', width=10)
    d.text((x+413, y+585), '8 cm', fill='#6d522c', font=font(54))
    d.text((x+105, y+736), 'A = 8² = 64 cm²', fill='#1e6146', font=font(63, True))
    d.text((x+105, y+824), 'P = 4 × 8 = 32 cm', fill='#324a41', font=font(54))
    x = 2168
    points=[(x+246,y+590),(x+726,y+590),(x+246,y+230)]
    d.polygon(points, fill='#e3eaf5', outline='#3d608d', width=10)
    d.line((x+246,y+548,x+288,y+548,x+288,y+590),fill='#3d608d',width=6)
    d.text((x+390,y+607),'12 cm',fill='#3e536f',font=font(54))
    d.text((x+55,y+373),'9 cm',fill='#3e536f',font=font(54))
    d.text((x+547,y+332),'15 cm',fill='#3e536f',font=font(54))
    d.text((x+62,y+736),'A = (12 × 9) ÷ 2 = 54 cm²',fill='#1e6146',font=font(57,True))
    d.text((x+62,y+824),'P = 9 + 12 + 15 = 36 cm',fill='#324a41',font=font(54))
    d.text((82, 1374), 'A = área    ·    P = perímetro', fill='#526257', font=font(44))
    d.line((2720,1425,3120,1425),fill='#234d3c',width=4)
    d.line((2720,1411,2720,1439),fill='#234d3c',width=4)
    d.line((3120,1411,3120,1439),fill='#234d3c',width=4)
    d.text((2848,1362),'10 cm',fill='#234d3c',font=font(40))
    image.save(IMG/'cartaz-geometria.png', optimize=True)


def cover(full=False):
    canvas=Image.new('RGB',(1640,820),'#f3f0e8')
    d=ImageDraw.Draw(canvas)
    icon=Image.open(IMG/'icone.png').convert('RGBA');icon.thumbnail((84,84),Image.Resampling.LANCZOS)
    canvas.paste(icon,(96,300),icon)
    d.text((96,385),'Amplia',fill='#1b1f1d',font=font(92,True))
    d.text((99,512),'Pôsteres em folhas A4,\npara imprimir ou salvar em PDF.',fill='#4b524e',font=font(29),spacing=6)
    capture=Image.open(IMG/'capa-quadro.png').convert('RGB')
    width=960 if full else 1080
    capture=capture.resize((width,round(capture.height*width/capture.width)),Image.Resampling.LANCZOS)
    x,y=640,140 if full else 96
    shadow=Image.new('RGBA',canvas.size,(0,0,0,0));sd=ImageDraw.Draw(shadow)
    sd.rounded_rectangle((x,y+18,x+capture.width,y+capture.height+18),radius=14,fill=(0,0,0,65))
    canvas=Image.alpha_composite(canvas.convert('RGBA'),shadow.filter(ImageFilter.GaussianBlur(17)))
    mask=Image.new('L',capture.size,0);ImageDraw.Draw(mask).rounded_rectangle((0,0,capture.width-1,capture.height-1),radius=14,fill=255)
    canvas.paste(capture,(x,y),mask)
    return canvas.convert('RGB')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--so-exemplo',action='store_true')
    args=parser.parse_args();example()
    if args.so_exemplo:return
    # A janela inteira preserva a última coluna do cartaz e os controles à direita.
    image=cover(full=True);image.save(IMG/'capa.png',optimize=True)
    image.resize((1280,640),Image.Resampling.LANCZOS).save(IMG/'capa-social.png',optimize=True)


if __name__=='__main__':main()