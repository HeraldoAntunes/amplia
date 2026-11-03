"""Interface com nomes acentuados. Uso (com tela): python gui_acentos.py <raiz_do_amplia> <pasta_saida>"""
import json
import os
import sys
import time
from pathlib import Path

ROOT, OUT = Path(sys.argv[1]), Path(sys.argv[2])
sys.path.insert(0, str(ROOT))
import tkinter as tk  # noqa: E402
from PIL import Image  # noqa: E402
from amplia import Amplia  # noqa: E402
from amplia_desktop import Desktop  # noqa: E402

pasta = OUT / 'Interface Ação'
pasta.mkdir(parents=True, exist_ok=True)
resultados = []


def esperar(root, cond, limite=30):
    fim = time.time() + limite
    while time.time() < fim:
        root.update()
        if cond():
            return True
        time.sleep(.05)
    return False


def caso(rotulo, caminho):
    root = tk.Tk(); root.withdraw()
    engine = Amplia()
    d = Desktop(root, engine)
    try:
        try:
            d.path.set(caminho)
        except tk.TclError as exc:
            return dict(caso=rotulo, passou=False, detalhe=f'TclError ao colar o caminho: {exc}')
        d.open_path()
        if not esperar(root, lambda: engine.image is not None and not d.busy):
            return dict(caso=rotulo, passou=False, detalhe=f'não abriu; status: {d.status.get()}')
        esperar(root, lambda: not d.dirty and not d.busy, 10)
        sugerido = d.output_name.get()
        d.output_folder.set(str(pasta))
        d.export_pdf()
        alvo = pasta / sugerido
        ok = esperar(root, lambda: alvo.exists(), 30)
        return dict(caso=rotulo, passou=ok, detalhe=f'nome sugerido: {sugerido}; status: {d.status.get()}')
    finally:
        d.close()


nfc = pasta / 'coração.png'
Image.new('RGB', (300, 200), (200, 50, 50)).save(nfc)
resultados.append(caso('interface: imagem coração.png na pasta Interface Ação', str(nfc)))
latin = os.fsencode(pasta) + b'/caf\xe9.png'
with open(latin, 'wb') as f:
    f.write(nfc.read_bytes())
resultados.append(caso('interface: imagem com nome em Latin-1 (caf\\xe9.png)', os.fsdecode(latin)))
for r in resultados:
    print('PASSOU' if r['passou'] else 'FALHOU', '|', r['caso'], '|', ascii(r['detalhe']))
(OUT / 'gui_acentos.json').write_text(json.dumps(resultados, indent=1), encoding='utf-8')
