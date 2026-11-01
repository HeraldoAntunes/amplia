# Amplia · © 2026 Heraldo Antunes · SPDX-License-Identifier: MIT
import ctypes
import unittest
from unittest.mock import Mock, patch
from PIL import Image
from amplia import Amplia
from amplia_print import PrintDialog, page_geometry, print_poster


class PrintTests(unittest.TestCase):
    def setUp(self):
        self.engine = Amplia()
        self.engine.image = Image.new('RGB', (200, 300), 'white')
        self.caps = [300, 300, 2480, 3508, 59, 59, 2362, 3390]

    def tearDown(self):
        self.engine.image.close()

    def test_physical_scale_compensates_offsets_without_shrinking(self):
        rect = page_geometry(self.engine.layout(), self.caps)
        self.assertEqual(rect, (-59, -59, 2421, 3449))
        self.assertAlmostEqual(100 * (rect[2] - rect[0]) / 210, 1181, delta=1)
        bad = list(self.caps); bad[2] = 2550
        with self.assertRaisesRegex(ValueError, 'A4'):
            page_geometry(self.engine.layout(), bad)
        self.engine.config['margem_mm'] = 0
        self.engine.config['marcas'] = False
        with self.assertRaisesRegex(ValueError, 'margem maior'):
            page_geometry(self.engine.layout(), self.caps)

    def driver(self, cancelled=False, fail_page=False):
        api, gdi, kernel = Mock(), Mock(), Mock()
        def select(pointer):
            dialog = ctypes.cast(pointer, ctypes.POINTER(PrintDialog)).contents
            if dialog.flags == 0x400:
                return True
            if cancelled:
                return False
            dialog.dc = 123
            dialog.flags |= 2
            dialog.first = dialog.last = 2
            return True
        api.PrintDlgW.side_effect = select
        api.CommDlgExtendedError.return_value = 0
        gdi.GetDeviceCaps.side_effect = lambda dc, key: self.caps[[88, 90, 110, 111, 112, 113, 8, 10].index(key)]
        gdi.StartDocW.return_value = gdi.EndDoc.return_value = gdi.EndPage.return_value = 1
        gdi.StartPage.return_value = 0 if fail_page else 1
        return api, gdi, kernel

    def test_cancel_sends_no_job_and_keeps_configuration(self):
        api, gdi, kernel = self.driver(cancelled=True)
        before = dict(self.engine.config)
        with patch('amplia_print.ct.WinDLL', side_effect=[api, gdi, kernel]):
            self.assertTrue(print_poster(self.engine)['cancelada'])
        gdi.StartDocW.assert_not_called()
        self.assertEqual(before, self.engine.config)

    def test_selected_range_uses_core_page_renderer_and_releases_dc(self):
        api, gdi, kernel = self.driver()
        with patch('amplia_print.ct.WinDLL', side_effect=[api, gdi, kernel]), \
             patch.object(self.engine, 'render', wraps=self.engine.render) as render, \
             patch('PIL.ImageWin.Dib') as dib:
            result = print_poster(self.engine)
        self.assertEqual(result['folhas_enviadas'], 1)
        self.assertEqual(render.call_args.args[1], 2)
        self.assertEqual(dib.return_value.draw.call_args.args[1], (-59, -59, 2421, 3449))
        gdi.EndDoc.assert_called_once(); gdi.DeleteDC.assert_called_once_with(123)
        gdi.AbortDoc.assert_not_called()

    def test_driver_failure_aborts_started_job_and_releases_dc(self):
        api, gdi, kernel = self.driver(fail_page=True)
        with patch('amplia_print.ct.WinDLL', side_effect=[api, gdi, kernel]):
            with self.assertRaises(OSError):
                print_poster(self.engine)
        gdi.AbortDoc.assert_called_once_with(123)
        gdi.DeleteDC.assert_called_once_with(123)

    def test_command_requires_image_and_returns_structured_error(self):
        self.assertFalse(Amplia().execute({'comando': 'poster.imprimir'})['ok'])
        with patch('amplia_print.print_poster', side_effect=ValueError('Selecione A4.')):
            result = self.engine.execute({'comando': 'poster.imprimir'})
        self.assertFalse(result['ok'])
        self.assertEqual(result['erro']['detalhes']['motivo'], 'Selecione A4.')

    def test_driver_must_preserve_assembly_guides_as_well_as_image(self):
        caps = [300, 300, 2480, 3508, 83, 83, 2314, 3342]
        with self.assertRaisesRegex(ValueError, 'guias de montagem'):
            page_geometry(self.engine.layout(), caps)
        self.engine.config['marcas'] = False
        page_geometry(self.engine.layout(), caps)
