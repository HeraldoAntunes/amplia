"""Mede folhas, guias e continuidade dos PDFs do Amplia com PyMuPDF e pdfinfo.

Uso: python medidas.py <raiz_do_amplia> <pasta_saida>
"""
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

import fitz  # PyMuPDF
from PIL import Image

ROOT, OUT = Path(sys.argv[1]), Path(sys.argv[2])
sys.path.insert(0, str(ROOT))
from amplia import Amplia  # noqa: E402

OUT.mkdir(parents=True, exist_ok=True)
PT = 72 / 25.4
falhas, linhas = [], []


def checar(cond, texto):
    if not cond:
        falhas.append(texto)
    return cond


def sintetica(w, h):
    """Gradiente sintético: cada coluna e linha tem cor própria, sem branco nem cinza."""
    im = Image.new('RGB', (w, h))
    px = im.load()
    for x in range(w):
        for y in range(h):
            px[x, y] = (20 + 200 * x // w, 20 + 200 * y // h, 255)
    return im


IMG = OUT / 'sintetica-1200x800.png'
sintetica(1200, 800).save(IMG)


def pdfinfo_tamanho(path):
    if not shutil.which('pdfinfo'):
        return None
    saida = subprocess.run(['pdfinfo', '-f', '1', '-l', '999', str(path)], capture_output=True, text=True).stdout
    return sorted({l.split(':', 1)[1].split('pts')[0].strip() for l in saida.splitlines() if 'size:' in l and 'Page' in l})


def area_imagem(pix, dpi):
    """Caixa (mm) dos pixels da imagem (azul 255 e vermelho/verde até 220; guias são cinza escuro)."""
    w, h = pix.width, pix.height
    s = pix.samples
    xs, ys = [], []
    for y in range(0, h, 2):
        for x in range(0, w, 2):
            i = (y * w + x) * pix.n
            r, g, b = s[i], s[i + 1], s[i + 2]
            if b > 230 and min(r, g) < 230:
                xs.append(x); ys.append(y)
    f = 25.4 / dpi
    return (min(xs) * f, min(ys) * f, (max(xs) + 2) * f, (max(ys) + 2) * f) if xs else None


def cor(pix, x_mm, y_mm, dpi):
    x, y = int(x_mm / 25.4 * dpi), int(y_mm / 25.4 * dpi)
    i = (y * pix.width + x) * pix.n
    return pix.samples[i:i + 3]


casos = []
for ori in ('retrato', 'paisagem'):
    for modo in ('dobrar', 'inteiras'):
        for margem, sobre in ((10, 10), (5, 15)):
            casos.append(dict(orientacao=ori, montagem=modo, margem_mm=margem, sobreposicao_mm=sobre))

DPI = 150
for c in casos:
    nome = f"{c['montagem']}-{c['orientacao']}-m{c['margem_mm']}-s{c['sobreposicao_mm']}"
    e = Amplia()
    assert e.execute({'comando': 'imagem.abrir', 'parametros': {'caminho': str(IMG)}})['ok']
    r = e.execute({'comando': 'poster.configurar', 'parametros': dict(colunas=3, linhas=2, marcas=True, **c)})
    if not checar(r['ok'], f'{nome}: configurar falhou {r}'):
        continue
    lay = e.layout()
    destino = OUT / f'{nome}.pdf'
    res = e.execute({'comando': 'pdf.exportar', 'parametros': {'caminho': str(destino), 'substituir': True}})
    checar(res['ok'], f'{nome}: exportar falhou')
    pw, ph = lay['papel_mm']
    m, s = c['margem_mm'], lay['sobreposicao_mm']
    doc = fitz.open(destino)
    tam_pdfinfo = pdfinfo_tamanho(destino)
    medidas = dict(nome=nome, papel_mm=[pw, ph], pdfinfo=tam_pdfinfo, folhas=[])
    pixes = []
    for i, page in enumerate(doc):
        folha = lay['folhas'][i]
        row, col = folha['linha'] - 1, folha['coluna'] - 1
        largura, altura = page.rect.width / PT, page.rect.height / PT
        checar(abs(largura - pw) < .01 and abs(altura - ph) < .01, f'{nome} {folha["codigo"]}: página {largura:.2f} x {altura:.2f} mm')
        pix = page.get_pixmap(dpi=DPI)
        pixes.append(pix)
        caixa = area_imagem(pix, DPI)
        # Interseção da área útil da folha com a caixa da imagem centralizada no pôster.
        box = lay['imagem_no_poster_mm']
        x0, x1 = max(folha['x_mm'], box['x']), min(folha['x_mm'] + folha['largura_mm'], box['x'] + box['largura'])
        y0, y1 = max(folha['y_mm'], box['y']), min(folha['y_mm'] + folha['altura_mm'], box['y'] + box['altura'])
        esperado = (m + x0 - folha['x_mm'], m + y0 - folha['y_mm'], m + x1 - folha['x_mm'], m + y1 - folha['y_mm'])
        tem_imagem = esperado[2] > esperado[0] and esperado[3] > esperado[1]
        if checar(caixa is not None or not tem_imagem, f'{nome} {folha["codigo"]}: imagem ausente na folha; esperada {esperado}'):
            if caixa is not None:
                checar(all(abs(a - b) < 0.6 for a, b in zip(caixa, esperado)),
                       f'{nome} {folha["codigo"]}: área da imagem {tuple(round(v, 2) for v in caixa)} esperada {esperado}')
        # Guias vetoriais.
        tracejadas, sinais = [], []
        for d in page.get_drawings():
            for item in d['items']:
                if item[0] != 'l':
                    continue
                p1, p2 = item[1], item[2]
                seg = (round(p1.x / PT, 2), round(p1.y / PT, 2), round(p2.x / PT, 2), round(p2.y / PT, 2))
                (tracejadas if d.get('dashes') not in (None, '[] 0', '[] 0.0') and '[]' not in str(d.get('dashes')) else sinais).append(seg)
        info = dict(codigo=folha['codigo'], area_imagem_mm=caixa and [round(v, 2) for v in caixa],
                    tracejadas_mm=tracejadas, sinais_mm=sinais)
        medidas['folhas'].append(info)
        if c['montagem'] == 'dobrar':
            esperadas = []
            if col:
                esperadas.append(('v', m - .15))
            if row:
                esperadas.append(('h', m - .15))
            achadas = [('v', t[0]) if abs(t[0] - t[2]) < .01 else ('h', t[1]) for t in tracejadas]
            checar(sorted(achadas) == sorted(esperadas), f'{nome} {folha["codigo"]}: tracejadas {achadas} esperadas {esperadas}')
            if col + 1 < lay['colunas']:
                x_alvo = pw - m - s
                checar(any(abs(t[0] - x_alvo) < .01 and abs(t[0] - t[2]) < .01 for t in sinais),
                       f'{nome} {folha["codigo"]}: falta sinal + vertical em x={x_alvo}')
            if row + 1 < lay['linhas']:
                y_alvo = ph - m - s
                checar(any(abs(t[1] - y_alvo) < .01 and abs(t[1] - t[3]) < .01 for t in sinais),
                       f'{nome} {folha["codigo"]}: falta sinal + horizontal em y={y_alvo}')
        else:
            checar(not tracejadas, f'{nome} {folha["codigo"]}: tracejado no modo inteiras')
        # Guias não invadem a área útil (o segmento inteiro, nos dois modos).
        ux0, uy0, ux1, uy1 = m + .3, m + .3, m + folha['largura_mm'] - .3, m + folha['altura_mm'] - .3
        for t in tracejadas + sinais:
            sx0, sx1 = sorted((t[0], t[2]))
            sy0, sy1 = sorted((t[1], t[3]))
            dentro = sx0 < ux1 and sx1 > ux0 and sy0 < uy1 and sy1 > uy0
            checar(not dentro, f'{nome} {folha["codigo"]}: guia dentro da área útil {t}')
    # Continuidade entre A1 e A2: o ponto onde chega a borda dobrada de A2 mostra o mesmo desenho em A1.
    a1, a2 = pixes[0], pixes[1]
    y = m + 60
    if c['montagem'] == 'dobrar':
        pares = [(pw - m - s + d, m + d) for d in (1, 3, 5)]
    else:
        pares = [(pw - m - .7, m + .7)]
    for xa1, xa2 in pares:
        c1, c2 = cor(a1, xa1, y, DPI), cor(a2, xa2, y, DPI)
        checar(max(abs(p - q) for p, q in zip(c1, c2)) <= 6,
               f'{nome}: A1 x={xa1:.1f} {tuple(c1)} difere de A2 x={xa2:.1f} {tuple(c2)}')
    medidas['sha256'] = hashlib.sha256(destino.read_bytes()).hexdigest()
    linhas.append(medidas)
    print(nome, 'pdfinfo', tam_pdfinfo, medidas['sha256'][:16])

# Outros tamanhos de papel: o programa só oferece A4.
for papel in ('Carta', 'A3', 'Letter'):
    e = Amplia()
    e.execute({'comando': 'imagem.abrir', 'parametros': {'caminho': str(IMG)}})
    r = e.execute({'comando': 'poster.configurar', 'parametros': {'colunas': 2, 'linhas': 2, 'papel': papel}})
    linhas.append(dict(nome=f'papel-{papel}', ok=r['ok'], erro=r.get('erro')))
    print('papel', papel, r['ok'], (r.get('erro') or {}).get('codigo'))

(OUT / 'medidas.json').write_text(json.dumps(dict(linhas=linhas, falhas=falhas), ensure_ascii=False, indent=1), encoding='utf-8')
print('FALHAS:', len(falhas))
for f in falhas:
    print(' -', f)
sys.exit(1 if falhas else 0)
