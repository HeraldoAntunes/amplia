# Amplia · © 2026 Heraldo Antunes · SPDX-License-Identifier: MIT
import base64
import hashlib
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

from PIL import Image
from pypdf import PdfReader

from amplia import Amplia, VERSAO
from amplia_desktop import Desktop, assembly_diagram

ROOT = Path(__file__).resolve().parents[1]


class DesktopTests(unittest.TestCase):
    def setUp(self):
        self.engine = Amplia()
        self.worker = object.__new__(Desktop)
        self.worker.engine = self.engine
        stream = io.BytesIO(); Image.new('RGB', (200, 100), '#1f6e43').save(stream, 'PNG')
        self.image = base64.b64encode(stream.getvalue()).decode()

    def test_worker_opens_and_renders_with_same_command_core(self):
        response, state, preview, help_data = self.worker.work({'comando': 'imagem.abrir', 'parametros': {'dados_base64': self.image}})
        self.assertTrue(response['ok'])
        self.assertEqual(state, response['resultado'])
        self.assertTrue(preview['ok'])
        self.assertGreater(len(base64.b64decode(preview['resultado']['dados_base64'])), 100)
        self.assertEqual(help_data['configuracao']['sobreposicao_mm'], 10)
        response, state, preview, _help = self.worker.work({'comando': 'poster.configurar', 'parametros': {'largura_mm': 370, 'altura_mm': 544}})
        self.assertEqual(state['folhas']['total_folhas'], 4)
        self.assertEqual(state, self.engine.state())

    def test_worker_error_does_not_modify_session(self):
        self.worker.work({'comando': 'imagem.abrir', 'parametros': {'dados_base64': self.image}})
        before = self.engine.state()
        response, state, preview, help_data = self.worker.work({'comando': 'poster.configurar', 'parametros': {'margem_mm': 500}})
        self.assertFalse(response['ok'])
        self.assertIsNone(state); self.assertIsNone(preview); self.assertIsNone(help_data)
        self.assertEqual(before, self.engine.state())

    def test_native_help_diagrams_for_overlap_and_edge(self):
        help_data = self.engine.assembly_help()
        overlap = assembly_diagram(help_data)
        self.assertEqual(overlap.size, (1000, 330))
        self.engine.config.update(sobreposicao_mm=0, margem_mm=0, marcas=False)
        edge = assembly_diagram(self.engine.assembly_help())
        self.assertNotEqual(overlap.tobytes(), edge.tobytes())
        self.assertEqual(edge.size, (1000, 330))

    def test_sheet_grid_geometry_and_pdf(self):
        self.worker.work({'comando': 'imagem.abrir', 'parametros': {'dados_base64': self.image}})
        response, state, preview, _ = self.worker.work({'comando': 'poster.configurar', 'parametros': {'colunas': 2, 'linhas': 3}})
        self.assertTrue(response['ok']); self.assertTrue(preview['ok'])
        pages = state['folhas']
        self.assertEqual(pages['poster_mm'], [370, 811])
        self.assertEqual((pages['colunas'], pages['linhas'], pages['total_folhas']), (2, 3, 6))
        self.assertTrue(all(p['largura_mm'] == 190 and p['altura_mm'] == 277 for p in pages['folhas']))
        box = pages['imagem_no_poster_mm']
        self.assertAlmostEqual(box['largura'] / box['altura'], 2)
        self.assertGreaterEqual(box['x'], 0); self.assertGreaterEqual(box['y'], 0)
        self.assertEqual(len(PdfReader(io.BytesIO(self.engine.pdf_bytes())).pages), 6)
        changed = self.engine.execute({'comando': 'poster.configurar', 'parametros': {'orientacao': 'paisagem', 'margem_mm': 15, 'sobreposicao_mm': 5}})
        self.assertTrue(changed['ok'])
        self.assertEqual(changed['resultado']['folhas']['poster_mm'], [529, 530])
        self.assertEqual(changed['resultado']['folhas']['total_folhas'], 6)
        switched = self.engine.execute({'comando': 'poster.configurar', 'parametros': {'largura_mm': 200}})
        self.assertTrue(switched['ok'])
        self.assertNotIn('colunas', switched['resultado']['configuracao'])
        self.assertEqual(switched['resultado']['folhas']['poster_mm'], [200, 100])

    def test_bad_sheet_grid_is_atomic(self):
        self.worker.work({'comando': 'imagem.abrir', 'parametros': {'dados_base64': self.image}})
        before = self.engine.state()
        for args in ({'colunas': 2}, {'linhas': 2}, {'colunas': 2, 'linhas': 2, 'altura_mm': 400},
                     {'colunas': 0, 'linhas': 2}, {'colunas': -1, 'linhas': 2}, {'colunas': 21, 'linhas': 20},
                     {'colunas': 2.5, 'linhas': 2}, {'colunas': True, 'linhas': 2},
                     {'colunas': 2, 'linhas': 2, 'margem_mm': 200}):
            with self.subTest(args=args):
                result = self.engine.execute({'comando': 'poster.configurar', 'parametros': args})
                self.assertFalse(result['ok'])
                self.assertEqual(before, self.engine.state())

    def test_simple_form_hides_advanced_and_dispatches_grid(self):
        import tkinter as tk
        root = tk.Tk(); root.withdraw()
        desktop = Desktop(root, self.engine)
        try:
            self.assertEqual(desktop.tabs.tab(desktop.about_tab, 'text'), 'Sobre')
            self.assertIn('Licença: MIT', desktop.about_text.get('1.0', 'end'))
            self.assertTrue(desktop.size_mode.get().startswith('Por folhas'))
            self.assertEqual(desktop.advanced.winfo_manager(), '')
            self.assertEqual(desktop.mm_fields.winfo_manager(), '')
            sent = []
            desktop.submit = lambda command, params=None: sent.append((command, params))
            desktop.sheet_values['colunas'].set('3'); desktop.sheet_values['linhas'].set('2')
            desktop.configure_poster()
            self.assertEqual(sent[-1][1]['colunas'], 3)
            self.assertEqual(sent[-1][1]['linhas'], 2)
            self.assertNotIn('largura_mm', sent[-1][1])
            desktop.toggle_advanced()
            self.assertEqual(desktop.advanced.winfo_manager(), 'pack')
            desktop.size_mode.set('Por medidas (mm)'); desktop.size_mode_changed()
            self.assertEqual(desktop.mm_fields.winfo_manager(), 'pack')
            desktop.configure_poster()
            self.assertIn('largura_mm', sent[-1][1])
            self.assertNotIn('colunas', sent[-1][1])
        finally:
            desktop.close()

    def test_portable_copy_uses_own_runtime_and_generates_identical_pdf(self):
        package = ROOT / 'dist' / ('Amplia-' + VERSAO)
        if not package.exists():
            package = ROOT / 'dist' / 'Amplia'
        if not (package / 'Amplia.Comandos.exe').exists():
            self.skipTest('Construir o pacote portátil antes deste teste.')
        with tempfile.TemporaryDirectory(prefix='Amplia-qa-') as temp:
            temp = Path(temp)
            copied = temp / 'Amplia copiado com espaço'
            shutil.copytree(package, copied, ignore=shutil.ignore_patterns('__pycache__', 'output'))
            output = temp / 'poster.pdf'
            requests = [dict(comando='imagem.abrir', parametros={'caminho': str(copied / 'app/examples/demo.png')}),
                        dict(comando='poster.configurar', parametros={'colunas': 2, 'linhas': 2}),
                        dict(comando='pdf.exportar', parametros={'caminho': str(output)})]
            env = dict(os.environ, PYTHONHOME='C:/inexistente', PYTHONPATH='C:/inexistente',
                       PATH=str(Path(os.environ['SystemRoot']) / 'System32'))
            process = subprocess.run([str(copied / 'Amplia.Comandos.exe'), '--stdio'],
                                     input='\n'.join(map(json.dumps, requests)) + '\n', capture_output=True,
                                     text=True, encoding='utf-8', cwd=temp, env=env, timeout=40)
            self.assertEqual(process.returncode, 0, process.stderr)
            self.assertTrue(all(json.loads(line)['ok'] for line in process.stdout.splitlines()))
            self.assertEqual(len(PdfReader(output).pages), 4)
            reference = Amplia()
            self.assertTrue(reference.execute({'comando': 'imagem.abrir', 'parametros': {'caminho': str(ROOT / 'examples/demo.png')}})['ok'])
            self.assertTrue(reference.execute({'comando': 'poster.configurar', 'parametros': {'colunas': 2, 'linhas': 2}})['ok'])
            self.assertEqual(hashlib.sha256(output.read_bytes()).hexdigest(),
                             hashlib.sha256(reference.pdf_bytes()).hexdigest())


if __name__ == '__main__':
    unittest.main(verbosity=2)
