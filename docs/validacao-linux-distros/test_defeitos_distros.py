# Amplia · © 2026 Heraldo Antunes · SPDX-License-Identifier: MIT
"""Testes que falham na v0.6.1-rc.1: um por defeito de docs/VALIDACAO-LINUX-DISTROS.md.

Ficam fora de tests/ de propósito, para não quebrar a suíte do CI antes da correção.
Rodar na raiz do repositório:  python docs/validacao-linux-distros/test_defeitos_distros.py -v
Depois de corrigir, podem ser movidos para tests/.
"""
import base64
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from PIL import Image  # noqa: E402
from amplia import Amplia  # noqa: E402


def cinza_16_bits(formato):
    """Imagem 20x20 em cinza 16 bits (modo I;16) com valor 20000 de 65535, isto é, 30,5% de brilho."""
    im = Image.new('I;16', (20, 20))
    im.putdata([20000] * 400)
    buffer = io.BytesIO()
    im.save(buffer, formato)
    return base64.b64encode(buffer.getvalue()).decode()


class DefeitosDistros(unittest.TestCase):
    def abrir_cinza(self, formato):
        engine = Amplia()
        resposta = engine.execute({'comando': 'imagem.abrir', 'parametros': {'dados_base64': cinza_16_bits(formato)}})
        self.assertTrue(resposta['ok'], resposta)
        return engine

    def test_n1_png_cinza_16_bits_mantem_o_brilho(self):
        engine = self.abrir_cinza('PNG')
        valor = engine.image.getpixel((10, 10))[0]
        self.assertAlmostEqual(valor, 78, delta=3, msg=f'PNG 16 bits virou {engine.image.getpixel((10, 10))}')

    def test_n1_tiff_cinza_16_bits_mantem_o_brilho_no_pdf(self):
        engine = self.abrir_cinza('TIFF')
        engine.execute({'comando': 'poster.configurar', 'parametros': {'colunas': 1, 'linhas': 1}})
        try:
            import fitz
        except ImportError:
            self.skipTest('PyMuPDF ausente')
        pagina = fitz.open(stream=engine.pdf_bytes(), filetype='pdf')[0]
        pix = pagina.get_pixmap(dpi=30)
        centro = pix.pixel(pix.width // 2, pix.height // 2)
        self.assertAlmostEqual(centro[0], 78, delta=6, msg=f'centro da folha no PDF: {centro}')

    def test_n2_stdio_com_nome_em_latin1_responde_e_continua(self):
        with tempfile.TemporaryDirectory() as pasta:
            caminho = os.fsencode(pasta) + b'/caf\xe9.png'
            with open(caminho, 'wb') as arquivo:
                buffer = io.BytesIO()
                Image.new('RGB', (30, 20), 'red').save(buffer, 'PNG')
                arquivo.write(buffer.getvalue())
            pedidos = [json.dumps({'comando': 'imagem.abrir', 'parametros': {'caminho': os.fsdecode(caminho)}}),
                       json.dumps({'comando': 'estado.obter'})]
            processo = subprocess.run([sys.executable, str(ROOT / 'amplia.py'), '--stdio'], input='\n'.join(pedidos) + '\n',
                                      capture_output=True, text=True, encoding='utf-8', timeout=60)
            self.assertNotIn('Traceback', processo.stderr, processo.stderr)
            self.assertEqual(len(processo.stdout.splitlines()), 2, 'o processo deve responder às duas linhas')

    def test_n3_arquivo_inexistente_tem_codigo_proprio(self):
        resposta = Amplia().execute({'comando': 'imagem.abrir', 'parametros': {'caminho': str(ROOT / 'nao-existe.png')}})
        self.assertFalse(resposta['ok'])
        self.assertNotEqual(resposta['erro']['codigo'], 'OPERACAO_FALHOU', resposta['erro'])


if __name__ == '__main__':
    unittest.main()
