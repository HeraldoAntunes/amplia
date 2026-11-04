# Amplia · © 2026 Heraldo Antunes · SPDX-License-Identifier: MIT
import base64
import io
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import unittest
import urllib.error
import urllib.request

from PIL import Image, ImageDraw
from pypdf import PdfReader

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from amplia import Amplia, LocalServer, MM, ROOT, atomic_write


def image_bytes(size=(760, 1108)):
    image = Image.new('RGB', size, '#e1c88c')
    draw = ImageDraw.Draw(image)
    # Quadrantes e faixas permitem verificar recortes e alinhamento.
    draw.rectangle((0, 0, size[0] // 2, size[1] // 2), fill='#26734d')
    draw.rectangle((size[0] // 2, size[1] // 2, size[0], size[1]), fill='#ad5148')
    for y in range(0, size[1], 50):
        draw.line((0, y, size[0], y), fill='#ffffff', width=3)
    stream = io.BytesIO()
    image.save(stream, 'PNG')
    return stream.getvalue()


class Fixture(unittest.TestCase):
    def setUp(self):
        self.engine = Amplia()
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.directory = Path(self.temp.name)
        self.raw = image_bytes()
        self.path = self.directory / 'imagem.png'
        self.path.write_bytes(self.raw)
        self.call('imagem.abrir', caminho=str(self.path))

    def call(self, command, **params):
        result = self.engine.execute(dict(comando=command, parametros=params))
        self.assertTrue(result['ok'], result)
        return result['resultado']


class CoreTests(Fixture):
    def test_catalog_and_state(self):
        catalog = self.call('comandos.listar')['comandos']
        self.assertIn('pdf.exportar', catalog)
        self.assertIn('ajuda.montagem', catalog)
        self.assertEqual(self.call('estado.obter')['imagem']['largura_px'], 760)

    def test_help_without_image_and_cli(self):
        engine = Amplia()
        before = engine.state()
        result = engine.execute({'comando': 'ajuda.montagem'})
        self.assertTrue(result['ok'])
        help_data = result['resultado']
        self.assertEqual(help_data['modo'], 'sobrepor')
        self.assertEqual(help_data['exemplo_horizontal_mm']['faixa_repetida'], [180, 190])
        self.assertTrue(help_data['exibir'])
        closed = engine.execute({'comando': 'ajuda.montagem', 'parametros': {'exibir': False}})
        self.assertFalse(closed['resultado']['exibir'])
        self.assertEqual(before, engine.state())
        process = subprocess.run([sys.executable, str(ROOT / 'amplia.py'), '--stdio'],
                                 input='{"comando":"ajuda.montagem"}\n', text=True, encoding='utf-8',
                                 capture_output=True, timeout=30)
        self.assertEqual(process.returncode, 0, process.stderr)
        self.assertEqual(json.loads(process.stdout)['resultado'], help_data)

    def test_help_matches_applied_configuration(self):
        self.call('poster.configurar', margem_mm=0, marcas=False, sobreposicao_mm=0, orientacao='paisagem',
                  largura_mm=100, altura_mm=100)
        before = self.call('estado.obter')
        help_data = self.call('ajuda.montagem')
        self.assertEqual(help_data['modo'], 'borda_a_borda')
        self.assertIsNone(help_data['exemplo_horizontal_mm']['faixa_repetida'])
        self.assertEqual(help_data['exemplo_horizontal_mm']['segunda_comeca'], 297)
        self.assertIn('não há margem', help_data['passos'][1]['texto'])
        self.assertIn('Sem sobreposição', help_data['passos'][2]['texto'])
        self.assertTrue(help_data['folha_unica'])
        self.assertEqual(before, self.call('estado.obter'))

    def test_exact_grid_and_overlap(self):
        result = self.call('poster.configurar', largura_mm=370, altura_mm=544,
                           margem_mm=10, sobreposicao_mm=10)['folhas']
        self.assertEqual((result['colunas'], result['linhas']), (2, 2))
        self.assertEqual(result['area_util_mm'], [190, 277])
        a, b, c, d = result['folhas']
        self.assertEqual(b['x_mm'], 180)
        self.assertEqual(c['y_mm'], 267)
        self.assertEqual(a['largura_mm'] - b['x_mm'], 10)
        self.assertEqual(a['altura_mm'] - c['y_mm'], 10)
        self.assertEqual(d['x_mm'] + d['largura_mm'], 370)
        self.assertEqual(d['y_mm'] + d['altura_mm'], 544)

    def test_partial_last_pages_and_coverage(self):
        result = self.call('poster.configurar', largura_mm=400, altura_mm=600)['folhas']
        self.assertEqual((result['colunas'], result['linhas']), (3, 3))
        self.assertEqual(result['folhas'][-1]['largura_mm'], 40)
        self.assertEqual(result['folhas'][-1]['altura_mm'], 66)
        for w in (10, 189.99, 190, 190.01, 370, 370.01, 800):
            for h in (10, 277, 277.001, 544, 800):
                layout = self.call('poster.configurar', largura_mm=w, altura_mm=h)['folhas']
                last = layout['folhas'][-1]
                self.assertAlmostEqual(last['x_mm'] + last['largura_mm'], w, places=5)
                self.assertAlmostEqual(last['y_mm'] + last['altura_mm'], h, places=5)
                self.assertTrue(all(p['largura_mm'] > 0 and p['altura_mm'] > 0 for p in layout['folhas']))

    def test_orientation_and_zero_overlap(self):
        result = self.call('poster.configurar', largura_mm=554, altura_mm=380,
                           orientacao='paisagem', sobreposicao_mm=0)['folhas']
        self.assertEqual(result['papel_mm'], [297, 210])
        self.assertEqual(result['total_folhas'], 4)
        self.assertEqual(result['folhas'][1]['x_mm'], 277)

    def test_single_dimension_keeps_ratio_and_two_dimensions_contain(self):
        state = self.call('poster.configurar', largura_mm=380)
        self.assertAlmostEqual(state['configuracao']['altura_mm'], 554)
        layout = self.call('poster.configurar', largura_mm=500, altura_mm=500)['folhas']
        box = layout['imagem_no_poster_mm']
        self.assertAlmostEqual(box['largura'] / box['altura'], 760 / 1108, places=6)
        self.assertGreater(box['x'], 0)

    def test_validation_does_not_change_state(self):
        previous = self.call('estado.obter')
        invalid = [dict(margem_mm=110), dict(sobreposicao_mm=190), dict(largura_mm=0),
                   dict(margem_mm=0), dict(largura_mm=5000, altura_mm=5000),
                   dict(orientacao='diagonal'), dict(largura_mm=True), dict(altura_mm=float('nan')),
                   dict(largura_mm=5001), dict(sobreposicao_mm=-1), dict(margem_mm=-1), dict(largura_mm='400')]
        for args in invalid:
            response = self.engine.execute(dict(comando='poster.configurar', parametros=args))
            self.assertFalse(response['ok'], args)
            self.assertEqual(self.call('estado.obter'), previous)

    def test_protocol_validation(self):
        for request in (None, [], {'comando': []}, {'comando': 'x'},
                        {'comando': 'estado.obter', 'parametros': []},
                        {'comando': 'estado.obter', 'parametros': {'extra': 1}},
                        {'comando': 'estado.obter', 'id': float('nan')}):
            self.assertFalse(self.engine.execute(request)['ok'])
        self.assertEqual(self.engine.execute({'comando': 'estado.obter', 'id': 'teste'})['id'], 'teste')

    def test_open_invalid_preserves_previous_image(self):
        previous = self.call('estado.obter')
        for params in ({}, {'dados_base64': '!'}, {'dados_base64': base64.b64encode(b'bad').decode()},
                       {'caminho': str(self.path), 'dados_base64': 'AA=='}):
            self.assertFalse(self.engine.execute(dict(comando='imagem.abrir', parametros=params))['ok'])
            self.assertEqual(self.call('estado.obter'), previous)

    def test_path_and_base64_equivalence(self):
        other = Amplia()
        result = other.execute(dict(comando='imagem.abrir', parametros=dict(dados_base64=base64.b64encode(self.raw).decode(), nome='imagem.png')))
        self.assertEqual(result['resultado'], self.call('estado.obter'))
        self.assertEqual(other.pdf_bytes(), self.engine.pdf_bytes())

    def test_transparency_and_exif_orientation(self):
        source = Image.new('RGBA', (100, 50), (255, 0, 0, 0))
        stream = io.BytesIO(); source.save(stream, 'PNG')
        self.call('imagem.abrir', dados_base64=base64.b64encode(stream.getvalue()).decode())
        self.assertEqual(self.engine.image.getpixel((0, 0)), (255, 255, 255))
        source = Image.new('RGB', (100, 50), 'red')
        exif = source.getexif(); exif[274] = 6
        stream = io.BytesIO(); source.save(stream, 'JPEG', exif=exif)
        state = self.call('imagem.abrir', dados_base64=base64.b64encode(stream.getvalue()).decode())
        self.assertEqual((state['imagem']['largura_px'], state['imagem']['altura_px']), (50, 100))

    def test_preview_grid_and_pages(self):
        self.call('poster.configurar', largura_mm=370, altura_mm=544)
        for params in ({}, {'folha': 1}, {'folha': 4}):
            result = self.call('previa.gerar', pixels=600, **params)
            image = Image.open(io.BytesIO(base64.b64decode(result['dados_base64'])))
            self.assertEqual(max(image.size), 600)
        self.assertFalse(self.engine.execute(dict(comando='previa.gerar', parametros={'folha': 5}))['ok'])
        self.assertFalse(self.engine.execute(dict(comando='previa.gerar', parametros={'pixels': 2500}))['ok'])

    def test_pdf_page_size_count_and_marks(self):
        self.call('poster.configurar', largura_mm=370, altura_mm=544)
        output = self.directory / 'poster.pdf'
        self.assertEqual(self.call('pdf.exportar', caminho=str(output))['paginas'], 4)
        reader = PdfReader(output)
        self.assertEqual(len(reader.pages), 4)
        for index, page in enumerate(reader.pages):
            self.assertAlmostEqual(float(page.mediabox.width) / MM, 210, places=4)
            self.assertAlmostEqual(float(page.mediabox.height) / MM, 297, places=4)
            self.assertIn(f'{index + 1}/4', page.extract_text())
        self.assertEqual(reader.pages[0]['/Resources']['/XObject'].keys(), reader.pages[1]['/Resources']['/XObject'].keys())

    def test_pdf_render_margin_overlap_scale_and_page_preview(self):
        # PyMuPDF é apenas ferramenta de teste já existente, não dependência do aplicativo.
        try:
            import fitz
        except ImportError:
            self.skipTest('PyMuPDF indisponível para inspeção de pixels.')
        self.call('poster.configurar', largura_mm=380, altura_mm=554, sobreposicao_mm=10, marcas=False)
        doc = fitz.open(stream=self.engine.pdf_bytes(), filetype='pdf')
        pages = [Image.frombytes('RGB', (p.width, p.height), p.samples)
                 for p in (page.get_pixmap(matrix=fitz.Matrix(2, 2)) for page in doc)]
        scale = 2 * MM
        first, second = pages[0], pages[1]
        self.assertEqual(first.getpixel((2, 2)), (255, 255, 255))
        # Mesmos pontos físicos na faixa de sobreposição: folha 1 x=195; folha 2 x=15 mm.
        for y in (30, 70, 120, 200):
            a = first.getpixel((round(195 * scale), round(y * scale)))
            b = second.getpixel((round(15 * scale), round(y * scale)))
            self.assertLess(max(abs(x - z) for x, z in zip(a, b)), 8)
        preview = self.engine.render(round(297 * scale), 1)
        for x, y in ((30, 30), (120, 50), (30, 240)):
            a = first.getpixel((round(x * scale), round(y * scale)))
            b = preview.getpixel((round(x * scale), round(y * scale)))
            self.assertLess(max(abs(v - u) for v, u in zip(a, b)), 8)

    def test_no_overwrite_and_original_protection(self):
        output = self.directory / 'existing.pdf'; output.write_bytes(b'preservar')
        result = self.engine.execute(dict(comando='pdf.exportar', parametros=dict(caminho=str(output))))
        self.assertEqual(result['erro']['codigo'], 'ARQUIVO_EXISTENTE')
        self.assertEqual(output.read_bytes(), b'preservar')
        self.call('pdf.exportar', caminho=str(output), substituir=True)
        self.assertTrue(output.read_bytes().startswith(b'%PDF'))
        result = self.engine.execute(dict(comando='pdf.exportar', parametros=dict(caminho=str(ROOT / 'original' / 'teste.pdf'))))
        self.assertEqual(result['erro']['codigo'], 'ORIGINAL_PROTEGIDO')

    def test_reset(self):
        self.assertIsNone(self.call('sessao.reiniciar')['imagem'])
        self.assertEqual(self.engine.execute({'comando': 'folhas.listar'})['erro']['codigo'], 'IMAGEM_NAO_ABERTA')

    def test_stdio_end_to_end(self):
        output = self.directory / 'cli.pdf'
        requests = [dict(comando='imagem.abrir', parametros={'caminho': str(self.path)}),
                    dict(comando='poster.configurar', parametros={'largura_mm': 370, 'altura_mm': 544}),
                    dict(comando='folhas.listar'), dict(comando='pdf.exportar', parametros={'caminho': str(output)})]
        process = subprocess.run([sys.executable, str(ROOT / 'amplia.py'), '--stdio'],
                                 input='\n'.join(map(json.dumps, requests)) + '\n', text=True,
                                 encoding='utf-8', capture_output=True, timeout=30)
        self.assertEqual(process.returncode, 0, process.stderr)
        results = [json.loads(line) for line in process.stdout.splitlines()]
        self.assertTrue(all(result['ok'] for result in results))
        self.assertEqual(results[-1]['resultado']['paginas'], 4)
        self.assertTrue(output.exists())
        invalid = subprocess.run([sys.executable, str(ROOT / 'amplia.py'), '--stdio'],
                                 input='{"comando":"estado.obter","id":NaN,"extra":true}\n{"comando":"estado.obter"}\n',
                                 text=True, encoding='utf-8', capture_output=True, timeout=30)
        answers = [json.loads(line) for line in invalid.stdout.splitlines()]
        self.assertEqual(invalid.returncode, 1)
        self.assertEqual(answers[0]['erro']['codigo'], 'JSON_INVALIDO')
        self.assertTrue(answers[1]['ok'])

    def test_batch_stops_on_error(self):
        output = self.directory / 'should-not-exist.pdf'
        batch = self.directory / 'batch.json'
        batch.write_text(json.dumps([{'comando': 'imagem.abrir', 'parametros': {'caminho': str(self.path)}},
                                     {'comando': 'poster.configurar', 'parametros': {'largura_mm': -1}},
                                     {'comando': 'pdf.exportar', 'parametros': {'caminho': str(output)}}]), encoding='utf-8')
        process = subprocess.run([sys.executable, str(ROOT / 'amplia.py'), '--batch', str(batch)], capture_output=True, timeout=30)
        self.assertEqual(process.returncode, 1)
        self.assertFalse(output.exists())


class HTTPTests(Fixture):
    def test_rejected_post_with_body_keeps_http_403_and_state(self):
        server = LocalServer(('127.0.0.1', 0))
        threading.Thread(target=server.serve_forever, daemon=True).start()
        self.addCleanup(server.server_close); self.addCleanup(server.shutdown)
        origin = f'http://127.0.0.1:{server.server_port}'
        before = server.engine.state()
        for index in range(12):
            request = urllib.request.Request(origin + '/api/comando',
                data=json.dumps({'comando': 'sessao.reiniciar', 'id': index}).encode(),
                headers={'Origin': origin, 'Content-Type': 'application/json'})
            with self.assertRaises(urllib.error.HTTPError) as caught:
                urllib.request.urlopen(request, timeout=3)
            self.assertEqual(caught.exception.code, 403)
            caught.exception.close()
            self.assertEqual(server.engine.state(), before)

    def test_static_routes_use_only_fixed_files(self):
        server = LocalServer(('127.0.0.1', 0))
        threading.Thread(target=server.serve_forever, daemon=True).start()
        self.addCleanup(server.server_close); self.addCleanup(server.shutdown)
        origin = f'http://127.0.0.1:{server.server_port}'
        for name in ('app.js', 'style.css'):
            with urllib.request.urlopen(origin + '/' + name) as response:
                self.assertEqual(response.read(), (ROOT / 'web' / name).read_bytes())
        for path in ('/app.js/../amplia.py', '/app.js%2f..%2famplia.py', '/amplia.py'):
            with self.assertRaises(urllib.error.HTTPError) as caught:
                urllib.request.urlopen(origin + path)
            self.assertEqual(caught.exception.code, 404)
            caught.exception.close()

    def test_http_same_commands_and_download(self):
        server = LocalServer(('127.0.0.1', 0))
        thread = threading.Thread(target=server.serve_forever, daemon=True); thread.start()
        self.addCleanup(server.server_close); self.addCleanup(server.shutdown)
        origin = f'http://127.0.0.1:{server.server_port}'
        def post(request, headers=None):
            data = json.dumps(request).encode()
            return urllib.request.urlopen(urllib.request.Request(origin + '/api/comando', data=data,
                headers=headers if headers is not None else {'X-Amplia-Token': server.token, 'Content-Type': 'application/json', 'Origin': origin}))
        with self.assertRaises(urllib.error.HTTPError) as caught:
            post({'comando': 'estado.obter'}, {})
        self.assertEqual(caught.exception.code, 403)
        caught.exception.close()
        with self.assertRaises(urllib.error.HTTPError) as caught:
            post({'comando': 'estado.obter'}, {'X-Amplia-Token': server.token, 'Origin': 'https://example.com'})
        caught.exception.close()
        for request in ({'comando': 'ajuda.montagem'},
                        {'comando': 'imagem.abrir', 'parametros': {'caminho': str(self.path)}},
                        {'comando': 'poster.configurar', 'parametros': {'largura_mm': 370, 'altura_mm': 544}},
                        {'comando': 'ajuda.montagem', 'parametros': {'exibir': False}}):
            with post(request) as response:
                remote = json.load(response)
            local = self.engine.execute(request)
            self.assertEqual(remote, local)
        with post({'comando': 'pdf.exportar', 'parametros': {'caminho': str(self.directory / 'http.pdf')}}) as response:
            result = json.load(response)
        self.assertTrue(result['ok'])
        with urllib.request.urlopen(origin + '/poster.pdf') as response:
            self.assertEqual(response.read(), self.engine.pdf_bytes())
        with post({'comando': 'sessao.reiniciar'}) as response:
            json.load(response)
        with self.assertRaises(urllib.error.HTTPError) as caught:
            urllib.request.urlopen(origin + '/poster.pdf')
        caught.exception.close()


class ImageInputTests(unittest.TestCase):
    def test_16_bit_png_keeps_tones_and_transparency(self):
        source = Image.new('I;16', (5, 1))
        source.putdata([0, 20000, 20001, 32768, 65535])
        raw = io.BytesIO()
        source.save(raw, 'PNG', transparency=20000)
        engine = Amplia()
        result = engine.execute({'comando': 'imagem.abrir', 'parametros': {
            'dados_base64': base64.b64encode(raw.getvalue()).decode('ascii')}})
        self.assertTrue(result['ok'], result)
        self.assertEqual([engine.image.getpixel((x, 0)) for x in range(5)],
                         [(gray,) * 3 for gray in (0, 255, 78, 128, 255)])

    def test_16_bit_big_endian_tiff_keeps_gray_in_pdf(self):
        source = Image.new('I;16B', (30, 20), 20000)
        raw = io.BytesIO()
        source.save(raw, 'TIFF')
        engine = Amplia()
        result = engine.execute({'comando': 'imagem.abrir', 'parametros': {
            'dados_base64': base64.b64encode(raw.getvalue()).decode('ascii')}})
        self.assertTrue(result['ok'], result)
        page = PdfReader(io.BytesIO(engine.pdf_bytes())).pages[0]
        self.assertEqual(page.images[0].image.getpixel((15, 10)), (78, 78, 78))

    @unittest.skipUnless(os.name == 'posix', 'Nomes com bytes brutos exigem sistema de arquivos POSIX.')
    def test_legacy_filename_keeps_stdio_session_and_round_trips(self):
        with tempfile.TemporaryDirectory() as directory:
            raw_path = os.fsencode(directory) + b'/caf\xe9.png'
            with open(raw_path, 'wb') as output:
                output.write(image_bytes())
            requests = [
                {'comando': 'imagem.abrir', 'parametros': {'caminho': os.fsdecode(raw_path)}},
                {'comando': 'estado.obter'},
            ]
            process = subprocess.run([sys.executable, str(ROOT / 'amplia.py'), '--stdio'],
                                     input=''.join(json.dumps(request) + '\n' for request in requests),
                                     capture_output=True, text=True, encoding='utf-8', timeout=30)
            self.assertEqual(process.returncode, 0, process.stderr)
            first, second = map(json.loads, process.stdout.splitlines())
            self.assertTrue(first['ok'], first)
            self.assertTrue(second['ok'], second)
            self.assertEqual(first['resultado'], second['resultado'])
            self.assertEqual(os.fsencode(second['resultado']['imagem']['nome']), b'caf\xe9.png')

    def test_missing_image_has_own_code_and_keeps_state(self):
        engine = Amplia()
        original = engine.execute({'comando': 'imagem.abrir', 'parametros': {
            'dados_base64': base64.b64encode(image_bytes()).decode('ascii')}})['resultado']
        with tempfile.TemporaryDirectory() as directory:
            for path, code in [(Path(directory) / 'ausente.png', 'IMAGEM_NAO_ENCONTRADA'),
                               (Path(directory), 'IMAGEM_NAO_E_ARQUIVO')]:
                with self.subTest(code=code):
                    result = engine.execute({'comando': 'imagem.abrir', 'parametros': {'caminho': str(path)}})
                    self.assertFalse(result['ok'])
                    self.assertEqual(result['erro']['codigo'], code)
                    self.assertEqual(engine.state(), original)


if __name__ == '__main__':
    unittest.main(verbosity=2)
