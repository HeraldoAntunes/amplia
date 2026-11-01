# Amplia · © 2026 Heraldo Antunes · SPDX-License-Identifier: MIT
import json
from pathlib import Path
import tempfile
import time
import tkinter as tk
from tkinter import ttk
import unittest
from unittest.mock import Mock, patch

from PIL import Image
from pypdf import PdfReader
from amplia import Amplia
from amplia_desktop import Desktop, initial_geometry


class UsabilityTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='amplia-ux-')
        self.folder = Path(self.temp.name)
        self.image = self.folder/'exemplo.png'
        Image.new('RGB', (760,1108), '#1f6e43').save(self.image)
        self.root = tk.Tk(); self.root.withdraw()
        self.app = Desktop(self.root)

    def tearDown(self):
        self.wait()
        self.app.close(force=True)
        self.temp.cleanup()

    def wait(self):
        deadline = time.monotonic()+8
        while self.app.busy or self.app.timer or self.app.picker:
            self.root.update()
            if time.monotonic()>deadline:
                self.fail('A operação da interface não terminou.')
            time.sleep(0.01)

    def open_image(self):
        self.app.path.set(str(self.image)); self.app.open_path(); self.wait()

    def test_opening_image_already_matches_four_full_sheets(self):
        self.open_image()
        state = self.app.engine.state()
        self.assertEqual(state['folhas']['poster_mm'], [370,544])
        self.assertEqual(state['folhas']['total_folhas'], 4)
        self.assertEqual(state['configuracao']['colunas'], 2)
        self.assertTrue(all(page['largura_mm']==190 and page['altura_mm']==277 for page in state['folhas']['folhas']))
        self.assertEqual(self.app.steps.index('current'), 1)
        self.assertNotIn('imagem.abrir', self.app.status.get())

    def test_three_steps_and_save_gated_without_image(self):
        self.assertEqual([self.app.steps.tab(tab,'text') for tab in self.app.steps.tabs()], ['Imagem','Folhas','Imprimir / PDF'])
        self.app.go_pdf()
        self.assertEqual(self.app.steps.index('current'), 0)
        self.assertIn('Escolha uma imagem', self.app.status.get())
        self.assertEqual(str(self.app.next_button.cget('state')), 'disabled')

    def test_initial_window_reserves_space_for_taskbar_and_window_frame(self):
        width, height, x, y = initial_geometry(self.root)
        self.assertLessEqual(width, 1160)
        self.assertLessEqual(height, 740)
        self.assertLess(x + width, self.root.winfo_screenwidth())
        self.assertLess(y + height, self.root.winfo_screenheight())

    def test_count_change_updates_preview_without_extra_click(self):
        self.open_image()
        self.app.sheet_values['colunas'].set('3')
        self.assertTrue(self.app.dirty)
        self.assertEqual(str(self.app.export_button.cget('state')), 'disabled')
        self.wait()
        self.assertFalse(self.app.dirty)
        self.assertEqual(self.app.engine.layout()['total_folhas'], 6)
        self.assertIn('55,0', self.app.metrics.cget('text'))

    def test_inputs_disabled_while_work_runs_then_readonly_restored(self):
        self.app.path.set(str(self.image)); self.app.open_path()
        self.assertTrue(self.app.busy)
        self.assertTrue(all(str(widget.cget('state'))=='disabled' for widget in self.app.inputs))
        self.wait()
        self.assertEqual(str(self.app.view.cget('state')), 'readonly')
        self.assertTrue(any(str(widget.cget('state'))=='normal' for widget in self.app.inputs))

    def test_save_uses_separate_filename_and_folder_and_adds_pdf_extension(self):
        self.open_image(); self.app.go_pdf()
        self.app.output_folder.set(str(self.folder)); self.app.output_name.set('meu-poster')
        self.app.export_pdf(); self.wait()
        pdf=self.folder/'meu-poster.pdf'
        self.assertTrue(pdf.is_file())
        self.assertEqual(len(PdfReader(pdf).pages),4)
        self.assertIn('PDF salvo',self.app.saved_label.cget('text'))
        self.assertFalse(self.app.unsaved)

    def test_existing_file_not_overwritten_when_confirmation_declined(self):
        self.open_image()
        target=self.folder/'guardado.pdf'; target.write_bytes(b'conteudo preservado')
        self.app.output_name.set(target.name); self.app.output_folder.set(str(self.folder))
        with patch('amplia_desktop.messagebox.askyesno', return_value=False) as question:
            self.app.export_pdf()
        question.assert_called_once()
        self.assertEqual(target.read_bytes(), b'conteudo preservado')
        self.assertFalse(self.app.busy)

    def test_invalid_image_keeps_current_poster_and_readable_message(self):
        self.open_image(); before=self.app.engine.state()
        self.app.path.set(str(self.folder/'inexistente.png')); self.app.open_path(); self.wait()
        self.assertEqual(self.app.engine.state(),before)
        self.assertIn('Confira se o arquivo existe',self.app.status.get())
        self.assertNotIn('OPERACAO_FALHOU',self.app.status.get())

    def test_native_image_selection_uses_the_same_open_command(self):
        picker=Mock(); picker.poll.return_value={'caminho':str(self.image),'erro':None}
        with patch('amplia_desktop.NativePicker', return_value=picker):
            self.app.choose_file(); self.wait()
        self.assertEqual(self.app.engine.state()['imagem']['nome'], self.image.name)

    def test_native_folder_selection_and_cancel_keep_poster(self):
        self.open_image(); before=self.app.engine.state()
        picker=Mock(); picker.poll.return_value={'caminho':str(self.folder),'erro':None}
        with patch('amplia_desktop.NativePicker', return_value=picker):
            self.app.choose_folder(); self.wait()
        self.assertEqual(self.app.output_folder.get(),str(self.folder))
        picker.poll.return_value={'caminho':None,'erro':None}
        with patch('amplia_desktop.NativePicker', return_value=picker):
            self.app.choose_file(); self.wait()
        self.assertEqual(self.app.engine.state(),before)

    def test_stalled_picker_does_not_block_manual_opening(self):
        picker=Mock(); picker.poll.return_value=None
        with patch('amplia_desktop.NativePicker', return_value=picker):
            self.app.choose_file()
        self.app.path.set(str(self.image)); self.app.open_path(); self.wait()
        picker.cancel.assert_called_once()
        self.assertIsNone(self.app.picker)
        self.assertIsNotNone(self.app.engine.image)

    def test_picker_error_preserves_poster_and_offers_path(self):
        self.open_image(); before=self.app.engine.state()
        picker=Mock(); picker.poll.return_value={'caminho':None,'erro':'Seletor indisponível.'}
        with patch('amplia_desktop.NativePicker', return_value=picker):
            self.app.choose_file(); self.wait()
        self.assertEqual(self.app.engine.state(),before)
        self.assertTrue(self.app.path_panel.winfo_manager())

    def test_print_is_separate_from_save_and_cancel_preserves_poster(self):
        self.assertEqual(str(self.app.print_button.cget('state')), 'disabled')
        self.open_image()
        self.app.go_pdf(); self.root.update()
        self.assertTrue(self.app.export_button.winfo_manager())
        self.assertTrue(self.app.print_button.winfo_manager())
        before = self.app.engine.state()
        with patch('amplia_print.print_poster', return_value={'cancelada': True, 'folhas_enviadas': 0}):
            self.app.print_poster(); self.wait()
        self.assertEqual(before, self.app.engine.state())
        self.assertIn('cancelada', self.app.status.get())
        self.assertTrue(self.app.unsaved)
        self.assertFalse(list(self.folder.glob('*.pdf')))

    def test_close_warns_about_unsaved_adjustments(self):
        self.open_image()
        with patch('amplia_desktop.messagebox.askyesno', return_value=False) as question:
            self.app.close()
        question.assert_called_once()
        self.assertFalse(self.app.closing)


if __name__=='__main__':
    unittest.main(verbosity=2)
