# Amplia · © 2026 Heraldo Antunes · SPDX-License-Identifier: MIT
import base64
import io
from pathlib import Path
import tempfile
import threading
import unittest
from unittest.mock import patch
import urllib.error
import urllib.request

from PIL import Image
from amplia import Amplia, LocalServer, atomic_write


class SafetyTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='amplia-seguranca-')
        self.addCleanup(self.temp.cleanup)
        self.folder = Path(self.temp.name)
        self.engine = Amplia()
        image = io.BytesIO()
        Image.new('RGB', (80, 100), '#1f6e43').save(image, 'PNG')
        self.raw = image.getvalue()
        response = self.engine.execute({'comando': 'imagem.abrir', 'parametros': {
            'dados_base64': base64.b64encode(self.raw).decode()}})
        self.assertTrue(response['ok'])

    def test_preview_with_subpixel_last_column_and_row(self):
        for width, height in ((190.001, 277), (190, 277.001), (190.001, 277.001)):
            with self.subTest(width=width, height=height):
                configured = self.engine.execute({'comando': 'poster.configurar', 'parametros': {
                    'largura_mm': width, 'altura_mm': height, 'sobreposicao_mm': 0}})
                self.assertTrue(configured['ok'])
                preview = self.engine.execute({'comando': 'previa.gerar', 'parametros': {'pixels': 200}})
                self.assertTrue(preview['ok'], preview)
                with Image.open(io.BytesIO(base64.b64decode(preview['resultado']['dados_base64']))) as image:
                    self.assertEqual(max(image.size), 200)

    def test_decoder_allowlist_is_applied_before_opening(self):
        with patch('amplia.Image.open', wraps=Image.open) as opened:
            response = self.engine.execute({'comando': 'imagem.abrir', 'parametros': {
                'dados_base64': base64.b64encode(self.raw).decode()}})
        self.assertTrue(response['ok'])
        self.assertEqual(opened.call_args.kwargs['formats'], ['PNG', 'JPEG', 'WEBP', 'BMP', 'TIFF'])

    def test_all_advertised_formats_keep_working(self):
        for format_name in ('PNG', 'JPEG', 'WEBP', 'BMP', 'TIFF'):
            with self.subTest(format=format_name):
                stream = io.BytesIO()
                Image.new('RGB', (80, 100), '#1f6e43').save(stream, format_name)
                response = self.engine.execute({'comando': 'imagem.abrir', 'parametros': {
                    'dados_base64': base64.b64encode(stream.getvalue()).decode()}})
                self.assertTrue(response['ok'], response)
                self.assertEqual(response['resultado']['imagem']['formato'], format_name)
                self.assertTrue(self.engine.execute({'comando': 'previa.gerar'})['ok'])
                self.assertTrue(self.engine.pdf_bytes().startswith(b'%PDF-'))

    def test_failed_sync_preserves_existing_destination_and_removes_temporary(self):
        target = self.folder / 'preservado.pdf'
        target.write_bytes(b'conteudo anterior')
        with patch('amplia.os.fsync', side_effect=OSError('falha simulada')):
            with self.assertRaises(OSError):
                atomic_write(target, b'conteudo novo', replace=True)
        self.assertEqual(target.read_bytes(), b'conteudo anterior')
        self.assertEqual(list(self.folder.glob('.amplia-*')), [])

    def test_optional_http_rejects_cross_site_even_with_valid_token(self):
        server = LocalServer(('127.0.0.1', 0))
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        self.addCleanup(server.server_close)
        self.addCleanup(server.shutdown)
        origin = f'http://127.0.0.1:{server.server_port}'
        # Corpo vazio testa a recusa antes do JSON sem reset TCP por bytes ainda não lidos no Windows.
        request = urllib.request.Request(origin + '/api/comando', data=b'', headers={
            'X-Amplia-Token': server.token, 'Origin': origin, 'Sec-Fetch-Site': 'cross-site'})
        with self.assertRaises(urllib.error.HTTPError) as caught:
            urllib.request.urlopen(request, timeout=5)
        self.assertEqual(caught.exception.code, 403)
        caught.exception.close()
        with urllib.request.urlopen(origin, timeout=5) as response:
            self.assertEqual(response.headers['X-Frame-Options'], 'DENY')
            self.assertEqual(response.headers['Referrer-Policy'], 'no-referrer')
            self.assertIn("object-src 'none'", response.headers['Content-Security-Policy'])


if __name__ == '__main__':
    unittest.main(verbosity=2)
