# Amplia · © 2026 Heraldo Antunes · SPDX-License-Identifier: MIT
import unittest
from unittest.mock import patch

from amplia_desktop import diagram_font


class DiagramFontTests(unittest.TestCase):
    def test_font_and_bitmap_fallback_preserve_portuguese_accents(self):
        with patch('amplia_desktop.ImageFont.truetype', side_effect=OSError):
            fallback = diagram_font(22)
        for font in (diagram_font(22), fallback):
            for accent, plain in zip('áéíóúãõç', 'aeiouaoc'):
                with self.subTest(accent=accent):
                    self.assertNotEqual(bytes(font.getmask(accent)), bytes(font.getmask(plain)))
                    self.assertNotEqual(bytes(font.getmask(accent)), bytes(font.getmask('?')))
