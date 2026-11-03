"""Casos de borda do Amplia com imagens sintéticas. Uso: python bordas.py <raiz_do_amplia> <pasta_saida>"""
import base64
import io
import json
import os
import subprocess
import sys
import time
import unicodedata
from pathlib import Path

from PIL import Image

ROOT, OUT = Path(sys.argv[1]), Path(sys.argv[2])
sys.path.insert(0, str(ROOT))
from amplia import Amplia  # noqa: E402

OUT.mkdir(parents=True, exist_ok=True)
resultados = []


def registrar(caso, passou, detalhe):
    resultados.append(dict(caso=caso, passou=bool(passou), detalhe=detalhe))
    print('PASSOU' if passou else 'FALHOU', '|', caso, '|', detalhe)


def b64(im, fmt='PNG', **kw):
    b = io.BytesIO(); im.save(b, fmt, **kw); return base64.b64encode(b.getvalue()).decode()


def abrir(**params):
    e = Amplia(); return e, e.execute({'comando': 'imagem.abrir', 'parametros': params})


# 1. Imagem muito grande.
lado = 6324  # 39.992.976 pixels, logo abaixo do limite de 40 milhões
t = time.time()
e, r = abrir(dados_base64=b64(Image.new('RGB', (lado, lado), (30, 90, 150))))
ok = r['ok'] and e.execute({'comando': 'poster.configurar', 'parametros': {'colunas': 3, 'linhas': 3}})['ok']
pdf = e.pdf_bytes() if ok else b''
from pypdf import PdfReader  # noqa: E402
paginas = len(PdfReader(io.BytesIO(pdf)).pages) if pdf else 0
registrar('grande 6324x6324 (abaixo de 40 Mpx)', ok and paginas == 9, f'abre e exporta {paginas} folhas em {time.time() - t:.1f} s')
e, r = abrir(dados_base64=b64(Image.new('RGB', (6325, 6325))))
registrar('grande 6325x6325 (acima de 40 Mpx)', not r['ok'] and r['erro']['codigo'] == 'IMAGEM_GRANDE', r.get('erro', {}).get('mensagem'))
grande = OUT / 'grande-41MiB.bmp'
Image.frombytes('RGB', (3750, 3750), os.urandom(3750 * 3750 * 3)).save(grande)
e, r = abrir(caminho=str(grande))
registrar(f'arquivo de {grande.stat().st_size / 2**20:.1f} MiB', not r['ok'] and r['erro']['codigo'] == 'IMAGEM_GRANDE', r.get('erro', {}).get('mensagem'))
grande.unlink()

# 2. Imagem muito pequena.
for tam in ((1, 1), (2, 3)):
    e, r = abrir(dados_base64=b64(Image.new('RGB', tam, (200, 30, 30))))
    c = e.execute({'comando': 'poster.configurar', 'parametros': {'colunas': 2, 'linhas': 2}})
    p = e.execute({'comando': 'previa.gerar', 'parametros': {'pixels': 400}})
    avisos = c['resultado']['folhas']['avisos'] if c['ok'] else []
    registrar(f'pequena {tam[0]}x{tam[1]}', r['ok'] and c['ok'] and p['ok'] and len(e.pdf_bytes()) > 0 and avisos,
              f'abre, gera prévia e PDF; aviso: {avisos}')
e, r = abrir(dados_base64=b64(Image.new('RGB', (1, 3000))))
c = e.execute({'comando': 'poster.configurar', 'parametros': {'largura_mm': 500}})
registrar('fina 1x3000 com largura 500 mm', not c['ok'] and c['erro']['codigo'] == 'TAMANHO_INVALIDO', c.get('erro', {}).get('mensagem'))

# 3. PNG com transparência.
rgba = Image.new('RGBA', (20, 20), (255, 0, 0, 128))
rgba.paste((0, 0, 255, 0), (0, 0, 10, 20))
e, r = abrir(dados_base64=b64(rgba))
meio, vazio = e.image.getpixel((15, 10)), e.image.getpixel((5, 10))
registrar('PNG RGBA semitransparente sobre branco', abs(meio[1] - 127) <= 2 and meio[0] == 255 and vazio == (255, 255, 255),
          f'50% vermelho vira {meio}; transparente vira {vazio}')
pal = Image.new('P', (10, 10), 1); pal.putpalette([0, 0, 0, 0, 128, 0] + [0] * 762); pal.paste(0, (0, 0, 5, 10))
e, r = abrir(dados_base64=b64(pal, transparency=0))
registrar('PNG paleta com tRNS', e.image.getpixel((2, 2)) == (255, 255, 255) and e.image.getpixel((7, 2)) == (0, 128, 0),
          f'{e.image.getpixel((2, 2))} e {e.image.getpixel((7, 2))}')

# 4. Rotação EXIF (JPEG): o canto vermelho deve ir para onde o visualizador mostra.
base = Image.new('RGB', (40, 20), 'white'); base.paste((255, 0, 0), (0, 0, 10, 10))
esperado = {1: 'se', 2: 'sd', 3: 'id', 4: 'ie', 5: 'se', 6: 'sd', 7: 'id', 8: 'ie'}
erros = []
for o in range(1, 9):
    ex = Image.Exif(); ex[0x0112] = o
    e, r = abrir(dados_base64=b64(base, 'JPEG', exif=ex.tobytes(), quality=95))
    im = e.image
    cantos = {'se': (2, 2), 'sd': (im.width - 3, 2), 'ie': (2, im.height - 3), 'id': (im.width - 3, im.height - 3)}
    achado = [k for k, xy in cantos.items() if im.getpixel(xy)[0] > 200 and im.getpixel(xy)[1] < 80]
    tam_ok = im.size == ((40, 20) if o <= 4 else (20, 40))
    if achado != [esperado[o]] or not tam_ok:
        erros.append((o, im.size, achado))
registrar('JPEG com EXIF orientação 1 a 8', not erros, erros or 'as 8 orientações corretas')

# 5. Nomes com acento.
pasta = OUT / 'Pôster Ação'; pasta.mkdir(exist_ok=True)
nfc = pasta / 'coração.png'; Image.new('RGB', (300, 200), (200, 50, 50)).save(nfc)
nfd = pasta / unicodedata.normalize('NFD', 'maçã.png'); Image.new('RGB', (300, 200), (50, 200, 50)).save(nfd)
for rotulo, caminho in (('NFC', nfc), ('NFD', nfd)):
    e, r = abrir(caminho=str(caminho))
    saida = pasta / f'saída {rotulo} é.pdf'
    x = e.execute({'comando': 'pdf.exportar', 'parametros': {'caminho': str(saida), 'substituir': True}}) if r['ok'] else {'ok': False}
    registrar(f'nome com acento {rotulo} (abrir e salvar PDF)', r['ok'] and x['ok'] and saida.exists(), r['resultado']['imagem']['nome'] if r['ok'] else r['erro'])
latin = os.fsencode(OUT) + b'/caf\xe9-latin1.png'
with open(latin, 'wb') as f:
    f.write(nfc.read_bytes())
pedidos = [json.dumps({'comando': 'imagem.abrir', 'parametros': {'caminho': os.fsdecode(latin)}}),
           json.dumps({'comando': 'estado.obter'})]
proc = subprocess.run([sys.executable, str(ROOT / 'amplia.py'), '--stdio'], input='\n'.join(pedidos) + '\n',
                      capture_output=True, text=True, timeout=60)
linhas = proc.stdout.splitlines()
registrar('nome em Latin-1 pelo --stdio (byte 0xE9)', proc.returncode in (0, 1) and len(linhas) == 2,
          f'código de saída {proc.returncode}, {len(linhas)} de 2 respostas; erro: {proc.stderr.strip().splitlines()[-1] if proc.stderr.strip() else "nenhum"}')
os.unlink(latin)

# 6. Profundidade de cor (descoberto nesta validação).
import numpy as np  # noqa: E402
for rotulo, fmt in (('PNG', 'PNG'), ('TIFF', 'TIFF')):
    cinza = Image.fromarray(np.full((20, 20), 20000, dtype=np.uint16))  # 20000/65535 = 30,5% de cinza
    e, r = abrir(dados_base64=b64(cinza, fmt))
    px = e.image.getpixel((10, 10))
    registrar(f'{rotulo} cinza 16 bits (I;16) a 30% de brilho', abs(px[0] - 78) <= 3, f'pixel após abrir: {px}, esperado perto de (78, 78, 78)')

# 7. Arquivo inexistente.
e, r = abrir(caminho=str(OUT / 'não-existe.png'))
registrar('arquivo inexistente tem erro claro', not r['ok'] and r['erro']['codigo'] not in ('OPERACAO_FALHOU',),
          f"{r['erro']['codigo']}: {r['erro']['mensagem']} {r['erro'].get('detalhes')}")

(OUT / 'bordas.json').write_text(json.dumps(resultados, ensure_ascii=False, indent=1), encoding='utf-8')
print('FALHAS:', sum(not x['passou'] for x in resultados))
