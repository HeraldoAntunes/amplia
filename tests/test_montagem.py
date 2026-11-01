# Amplia · © 2026 Heraldo Antunes · SPDX-License-Identifier: MIT
"""Geometria de união, cobertura da imagem e instruções realmente impressas."""
import base64
import io
from pathlib import Path
import tempfile
import unittest

from PIL import Image
from pypdf import PdfReader

from amplia import Amplia, MM


class AssemblyTests(unittest.TestCase):
    def setUp(self):
        self.engine = Amplia()
        image = Image.new('RGB', (800, 1200))
        image.putdata([(round(x * 255 / 799), round(y * 255 / 1199), 100)
                       for y in range(1200) for x in range(800)])
        stream = io.BytesIO(); image.save(stream, 'PNG')
        self.call('imagem.abrir', dados_base64=base64.b64encode(stream.getvalue()).decode())

    def call(self, command, **params):
        result = self.engine.execute({'comando': command, 'parametros': params})
        self.assertTrue(result['ok'], result)
        return result['resultado']

    def test_whole_pages_disable_repetition_but_keep_fold_preference(self):
        state = self.call('poster.configurar', colunas=4, linhas=2, orientacao='paisagem', montagem='inteiras')
        layout = state['folhas']
        self.assertEqual(layout['poster_mm'], [1108, 380])
        self.assertEqual(layout['papel_montado_mm'], [1188, 420])
        self.assertEqual(layout['sobreposicao_mm'], 0)
        self.assertEqual(layout['faixa_branca_interna_mm'], 20)
        self.assertEqual(state['configuracao']['sobreposicao_mm'], 10)
        folded = self.call('poster.configurar', montagem='dobrar')['folhas']
        self.assertEqual(folded['poster_mm'], [1078, 370])
        self.assertEqual(folded['sobreposicao_mm'], 10)

    def test_codes_order_and_only_internal_folds(self):
        layout = self.call('poster.configurar', colunas=3, linhas=2)['folhas']
        self.assertEqual([p['codigo'] for p in layout['folhas']], ['A1', 'A2', 'A3', 'B1', 'B2', 'B3'])
        self.assertEqual([p['dobras'] for p in layout['folhas']],
                         [[], ['esquerda'], ['esquerda'], ['cima'], ['esquerda', 'cima'], ['esquerda', 'cima']])
        self.assertEqual(Amplia.page_code(26, 0), 'AA1')
        self.assertEqual(Amplia.page_code(399, 0), 'OJ1')

    def test_registration_targets_match_folded_edges_in_physical_space(self):
        for orientation in ('retrato', 'paisagem'):
            for overlap in (0, 5, 10, 23):
                layout = self.call('poster.configurar', colunas=3, linhas=2, orientacao=orientation,
                                   sobreposicao_mm=overlap)['folhas']
                pw, ph = layout['papel_mm']; m = layout['margem_mm']
                for page in layout['folhas']:
                    if page['coluna'] < layout['colunas']:
                        neighbor = layout['folhas'][page['numero']]
                        receiver = page['papel_x_mm'] + pw - m - overlap
                        folded_edge = neighbor['papel_x_mm'] + m
                        self.assertAlmostEqual(receiver, folded_edge)
                    if page['linha'] < layout['linhas']:
                        neighbor = layout['folhas'][page['numero'] - 1 + layout['colunas']]
                        self.assertAlmostEqual(page['papel_y_mm'] + ph - m - overlap,
                                               neighbor['papel_y_mm'] + m)

    def test_whole_pages_cover_each_image_position_once(self):
        for orientation in ('retrato', 'paisagem'):
            for width, height in ((10, 10), (190, 277), (400, 600), (811, 370), (500, 500)):
                layout = self.call('poster.configurar', largura_mm=width, altura_mm=height,
                                   orientacao=orientation, montagem='inteiras')['folhas']
                self.assertAlmostEqual(sum(p['largura_mm'] * p['altura_mm'] for p in layout['folhas']), width * height)
                for a in layout['folhas']:
                    self.assertEqual(a['dobras'], [])
                    for b in layout['folhas'][a['numero']:]:
                        intersection_w = min(a['x_mm']+a['largura_mm'], b['x_mm']+b['largura_mm']) - max(a['x_mm'], b['x_mm'])
                        intersection_h = min(a['y_mm']+a['altura_mm'], b['y_mm']+b['altura_mm']) - max(a['y_mm'], b['y_mm'])
                        self.assertFalse(intersection_w > 1e-5 and intersection_h > 1e-5)

    def test_folded_papers_reconstruct_continuous_image_with_partial_last_pages(self):
        layout = self.call('poster.configurar', largura_mm=400, altura_mm=600, marcas=False)['folhas']
        mounted = Image.new('RGB', tuple(round(v) for v in layout['papel_montado_mm']), 'white')
        for page in layout['folhas']:
            paper = self.engine.render(297, page['numero'])
            left = 10 if page['coluna'] > 1 else 0
            top = 10 if page['linha'] > 1 else 0
            mounted.paste(paper.crop((left, top, paper.width, paper.height)),
                          (round(page['papel_x_mm'])+left, round(page['papel_y_mm'])+top))
        for x in range(5, 400, 9):
            for y in range(5, 600, 11):
                got = mounted.getpixel((x+10, y+10))
                expected = (round(x*255/400), round(y*255/600), 100)
                self.assertLessEqual(max(abs(a-b) for a, b in zip(got, expected)), 3, (x, y, got))

    def test_whole_papers_keep_visible_white_seams_and_do_not_cover_image(self):
        layout = self.call('poster.configurar', largura_mm=400, altura_mm=600,
                           montagem='inteiras', marcas=False)['folhas']
        image = self.engine.render(round(max(layout['papel_montado_mm'])))
        for x in (201, 205, 214, 218):
            self.assertEqual(image.getpixel((x, 100)), (255, 255, 255))
        self.assertNotEqual(image.getpixel((199, 100)), (255, 255, 255))
        self.assertNotEqual(image.getpixel((220, 100)), (255, 255, 255))

    def test_printed_text_names_page_neighbors_and_actions_in_both_modes(self):
        for mode in ('dobrar', 'inteiras'):
            self.call('poster.configurar', colunas=2, linhas=2, montagem=mode)
            pdf = PdfReader(io.BytesIO(self.engine.pdf_bytes()))
            self.assertEqual(len(pdf.pages), 4)
            a1, a2, b1, b2 = [page.extract_text() for page in pdf.pages]
            self.assertIn('A1 | FOLHA 1/4', a1)
            self.assertIn('PROXIMA: A2', a1)
            self.assertIn('ABAIXO: B1', a1)
            self.assertIn('B2 | FOLHA 4/4', b2)
            if mode == 'dobrar':
                self.assertIn('A2 SOBRE A1', a2)
                self.assertIn('DOBRE A BORDA DE CIMA PARA TRAS', b1)
                self.assertIn('POR CIMA', a1)
            else:
                self.assertIn('NAO CORTAR NEM DOBRAR', a1)
                self.assertNotIn('DOBRE PARA TRAS', a2)
                self.assertNotIn('POR CIMA', b2)

    def test_map_is_separate_one_page_with_order_and_instructions(self):
        for mode in ('dobrar', 'inteiras'):
            self.call('poster.configurar', colunas=3, linhas=2, montagem=mode)
            before = self.engine.state()
            with tempfile.TemporaryDirectory() as temp:
                path = Path(temp) / 'mapa.pdf'
                response = self.call('mapa.exportar', caminho=str(path))
                pdf = PdfReader(path)
                self.assertEqual(response['paginas'], 1)
                self.assertEqual(len(pdf.pages), 1)
                self.assertAlmostEqual(float(pdf.pages[0].mediabox.width) / MM, 210, places=4)
                text = pdf.pages[0].extract_text()
                for code in ('A1', 'A2', 'A3', 'B1', 'B2', 'B3'):
                    self.assertIn(code, text)
                self.assertIn('separado do pôster', text)
                self.assertEqual(before, self.engine.state())
                self.assertFalse(self.engine.execute({'comando': 'mapa.exportar', 'parametros': {'caminho': str(path)}})['ok'])

    def test_help_describes_applied_mode_and_never_tells_user_to_cut(self):
        for mode in ('dobrar', 'inteiras'):
            self.call('poster.configurar', montagem=mode)
            help_data = self.call('ajuda.montagem')
            text = ' '.join(step['texto'] for step in help_data['passos'])
            self.assertNotIn('recorte', text)
            self.assertNotRegex(text, r'\bapare\b')
            if mode == 'inteiras':
                self.assertIn('Não corte, não dobre', text)
                self.assertIn('20 mm', text)
                self.assertEqual(help_data['configuracao']['sobreposicao_mm'], 0)
            else:
                self.assertIn('POR CIMA', text)
                self.assertIn('para trás', text)

    def test_invalid_mode_does_not_change_applied_poster(self):
        before = self.engine.state()
        result = self.engine.execute({'comando': 'poster.configurar', 'parametros': {'montagem': 'inventado'}})
        self.assertFalse(result['ok'])
        self.assertEqual(self.engine.state(), before)

    def test_large_map_is_explicit_summary_with_readable_end_codes(self):
        self.call('poster.configurar', colunas=26, linhas=1)
        page = PdfReader(io.BytesIO(self.engine.map_pdf_bytes())).pages[0]
        text = page.extract_text()
        self.assertIn('Mapa resumido', text)
        self.assertIn('A1', text)
        self.assertIn('A26', text)
        self.assertIn('...', text)


if __name__ == '__main__':
    unittest.main(verbosity=2)
