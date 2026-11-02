# Amplia · © 2026 Heraldo Antunes · SPDX-License-Identifier: MIT
"""Desenha exemplos fictícios de relevo e de peça, sem dados ou marcas externas."""
from pathlib import Path
import math
import shutil
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
SIZE = (3244, 1480)
INK = '#203d47'


def font(size, bold=False):
    return ImageFont.truetype('C:/Windows/Fonts/' + ('seguisb.ttf' if bold else 'segoeui.ttf'), size)


def elevation(x, y):
    return (480 + 340 * math.exp(-((x-.30)**2/.032 + (y-.35)**2/.14))
            + 430 * math.exp(-((x-.76)**2/.037 + (y-.48)**2/.17))
            + 65 * math.sin(x * 6 + y * 2) + 35 * y)


def map_example():
    image = Image.new('RGB', SIZE, '#f4f2e8'); d = ImageDraw.Draw(image)
    d.text((86, 40), 'PARQUE SERRA CLARA', font=font(104, True), fill=INK)
    d.text((90, 175), 'Mapa de trilhas e relevo', font=font(49), fill='#607268')
    d.rounded_rectangle((2650, 80, 3155, 165), radius=20, fill='#dce8d9')
    d.text((2690, 95), 'EXEMPLO FICTÍCIO', font=font(39, True), fill='#385a43')
    left, top, width, height = 90, 310, 2460, 1010
    # As isolinhas saem de uma superfície contínua, sem cruzamentos desenhados à mão.
    nx, ny = 245, 101
    values = [[elevation(x/nx, y/ny) for x in range(nx+1)] for y in range(ny+1)]
    terrain = Image.new('RGB', (nx+1, ny+1)); pixels = terrain.load()
    for y in range(ny+1):
        for x in range(nx+1):
            t = max(0, min(1, (values[y][x]-440)/530))
            pixels[x,y] = (round(227+18*t), round(238-21*t), round(215-34*t))
    image.paste(terrain.resize((width,height), Image.Resampling.BICUBIC),(left,top))
    for level in range(460, 1021, 20):
        major = level % 100 == 0
        segments = []
        for y in range(ny):
            for x in range(nx):
                corners = [(x,y,values[y][x]),(x+1,y,values[y][x+1]),
                           (x+1,y+1,values[y+1][x+1]),(x,y+1,values[y+1][x])]
                hits=[]
                for a,b in zip(corners,corners[1:]+corners[:1]):
                    if (a[2]<level) != (b[2]<level):
                        t=(level-a[2])/(b[2]-a[2])
                        hits.append((left+(a[0]+t*(b[0]-a[0]))/nx*width,
                                     top+(a[1]+t*(b[1]-a[1]))/ny*height))
                for i in range(0,len(hits)-1,2):
                    d.line((hits[i],hits[i+1]),fill='#9b7f53' if major else '#bba986',width=4 if major else 2)
                    segments.append(hits[i])
        if major and segments:
            p=segments[len(segments)//3];label=f'{level} m';box=d.textbbox(p,label,font=font(25))
            d.rounded_rectangle((box[0]-7,box[1]-4,box[2]+7,box[3]+4),radius=4,fill='#f4f2e8')
            d.text(p,label,font=font(25),fill='#81643d')
    for i in range(1,4):
        x=left+width*i/4;d.line((x,top,x,top+height),fill='#c9d3c1',width=1)
    for i in range(1,3):
        y=top+height*i/3;d.line((left,y,left+width,y),fill='#c9d3c1',width=1)
    stream=[(left+width*t/160,top+height*(.84+.055*math.sin(t/12))) for t in range(161)]
    d.line(stream,fill='#f6faf5',width=23,joint='curve');d.line(stream,fill='#78b4c2',width=13,joint='curve')
    trail=[(left+120,top+810),(left+405,top+680),(left+680,top+420),
           (left+1080,top+650),(left+1520,top+430),(left+1890,top+250),(left+2180,top+435)]
    d.line(trail,fill='#fff9ed',width=24,joint='curve')
    for a,b in zip(trail,trail[1:]):
        length=math.dist(a,b)
        for start in range(0,round(length),33):
            t=start/length;u=min(1,(start+19)/length)
            d.line((a[0]+t*(b[0]-a[0]),a[1]+t*(b[1]-a[1]),a[0]+u*(b[0]-a[0]),a[1]+u*(b[1]-a[1])),fill='#bd643d',width=9)
    for point,label,offset in [(trail[0],'PORTAL',(-50,40)),(trail[2],'MIRANTE OESTE',(-170,-80)),
                               (trail[3],'PASSO DO VALE',(-135,35)),(trail[5],'MIRANTE LESTE',(-170,-80))]:
        x,y=point;d.ellipse((x-17,y-17,x+17,y+17),fill='#fffdf6',outline='#3b6554',width=7)
        tx,ty=x+offset[0],y+offset[1];box=d.textbbox((tx,ty),label,font=font(29,True))
        d.rounded_rectangle((box[0]-12,box[1]-9,box[2]+12,box[3]+9),radius=7,fill='#fffdf6')
        d.text((tx,ty),label,font=font(29,True),fill=INK)
    d.rectangle((left,top,left+width,top+height),outline='#a9b7a5',width=3)
    x=2650
    d.text((x,320),'LEIA O TERRENO',font=font(40,True),fill=INK)
    d.text((x,395),'Curvas de nível a cada 20 m.\nLinhas próximas indicam\nencostas mais inclinadas.',font=font(31),fill='#52695f',spacing=12)
    for i,(color,label) in enumerate([('#9b7f53','Curva de nível'),('#bd643d','Trilha ilustrativa'),('#78b4c2','Curso d’água')]):
        y=625+i*90;d.line((x,y+20,x+100,y+20),fill=color,width=7);d.text((x+128,y),label,font=font(30),fill=INK)
    d.polygon([(2890,945),(2865,1040),(2890,1020),(2915,1040)],fill=INK);d.text((2870,885),'N',font=font(44,True),fill=INK)
    d.text((x,1110),'DISTÂNCIA ILUSTRATIVA',font=font(26,True),fill=INK)
    bar=width*250/1600
    d.line((x,1195,x+bar,1195),fill=INK,width=7)
    for bx in (x,x+bar):d.line((bx,1180,bx,1210),fill=INK,width=4)
    d.text((x,1230),'0',font=font(25),fill=INK);d.text((x+bar-65,1230),'250 m',font=font(25),fill=INK)
    d.text((90,1380),'Terreno sintético · sem georreferenciamento · não usar para navegação',font=font(32),fill='#607268')
    image.save(ROOT/'examples/mapa-serra-clara.png',optimize=True)
    # O botão de exemplo continua o mesmo e abre uma imagem mais representativa.
    shutil.copy2(ROOT/'examples/mapa-serra-clara.png',ROOT/'examples/demo.png')


def piece_example():
    image=Image.new('RGB',SIZE,'#f3f6f8');d=ImageDraw.Draw(image)
    d.text((90,45),'SUPORTE DE FIXAÇÃO',font=font(102,True),fill=INK)
    d.text((95,180),'Desenho técnico ilustrativo · medidas em milímetros',font=font(45),fill='#5c7480')
    d.rounded_rectangle((75,300,2050,1325),radius=24,fill='white')
    d.rounded_rectangle((2115,300,3170,1325),radius=24,fill='#e3edf0')
    d.text((135,340),'VISTA SUPERIOR',font=font(33,True),fill='#5c7480')
    plate=(480,590,1600,1110)
    d.rounded_rectangle(plate,radius=64,fill='#e8f0f4',outline='#254d66',width=9)
    for x in (640,1440):
        for y in (750,950):
            d.ellipse((x-48,y-48,x+48,y+48),fill='white',outline='#254d66',width=7)
            d.line((x-78,y,x+78,y),fill='#85a0b0',width=2);d.line((x,y-78,x,y+78),fill='#85a0b0',width=2)
    def dimension(a,b,label,vertical=False):
        d.line((a,b),fill='#526e7e',width=3)
        if vertical:
            x,y=a;d.polygon([(x,y),(x-10,y+25),(x+10,y+25)],fill='#526e7e')
            x,y=b;d.polygon([(x,y),(x-10,y-25),(x+10,y-25)],fill='#526e7e')
            d.text((x+25,(a[1]+b[1])/2-28),label,font=font(44),fill=INK)
        else:
            x,y=a;d.polygon([(x,y),(x+25,y-10),(x+25,y+10)],fill='#526e7e')
            x,y=b;d.polygon([(x,y),(x-25,y-10),(x-25,y+10)],fill='#526e7e')
            box=d.textbbox((0,0),label,font=font(44));tx=(a[0]+b[0])/2-(box[2]-box[0])/2
            d.text((tx,a[1]-64),label,font=font(44),fill=INK)
    for x in (480,1600):d.line((x,470,x,575),fill='#91a5b0',width=3)
    dimension((480,500),(1600,500),'140')
    for y in (590,1110):d.line((1615,y,1815,y),fill='#91a5b0',width=3)
    dimension((1770,590),(1770,1110),'65',True)
    for x in (640,1440):d.line((x,1125,x,1230),fill='#91a5b0',width=3)
    dimension((640,1200),(1440,1200),'100')
    d.line((1450,740,1640,400,1880,400),fill='#526e7e',width=3)
    d.text((1635,340),'4 × Ø12',font=font(40),fill=INK)
    d.text((2190,355),'VISTA ISOMÉTRICA',font=font(37,True),fill=INK)
    a=(2340,680);b=(3020,680);c=(2880,970);e=(2200,970)
    depth=52;d.polygon([e,c,(c[0],c[1]+depth),(e[0],e[1]+depth)],fill='#93afbd',outline='#254d66',width=5)
    d.polygon([b,c,(c[0],c[1]+depth),(b[0],b[1]+depth)],fill='#7093a6',outline='#254d66',width=5)
    d.polygon([a,b,c,e],fill='#d1e1e9',outline='#254d66',width=6)
    for u in (20/140,120/140):
        for v in (20/65,45/65):
            x=a[0]+u*(b[0]-a[0])+v*(e[0]-a[0]);y=a[1]+v*(e[1]-a[1])
            d.ellipse((x-30,y-17,x+30,y+17),fill='#f3f6f8',outline='#254d66',width=4)
    d.text((2190,1110),'Uma peça, muitos detalhes.',font=font(40,True),fill=INK)
    d.text((2190,1180),'Amplie para enxergar melhor.',font=font(32),fill='#5c7480')
    d.text((90,1380),'Exemplo fictício · sem tolerâncias de fabricação · a escala muda ao ampliar',font=font(32),fill='#5c7480')
    image.save(ROOT/'examples/peca-suporte.png',optimize=True)


def main():
    map_example();piece_example()
    print('Mapa e peça fictícios gerados. Exemplo padrão: mapa Serra Clara.')


if __name__=='__main__':main()
