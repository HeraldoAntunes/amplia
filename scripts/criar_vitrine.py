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
    import sys
    sys.path.insert(0, str(ROOT))
    from examples.criar_exemplos import main as create_examples
    create_examples()


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