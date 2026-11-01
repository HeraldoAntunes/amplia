# Amplia · © 2026 Heraldo Antunes · SPDX-License-Identifier: MIT
"""Impressão Windows em tamanho real, usando a paginação do núcleo existente."""
import ctypes as ct
from ctypes import wintypes as wt
import sys


class PrintDialog(ct.Structure):
    if ct.sizeof(ct.c_void_p) == 4:
        _pack_ = 1
    _fields_ = [('size', wt.DWORD), ('owner', wt.HWND),
                ('mode', wt.HGLOBAL), ('names', wt.HGLOBAL), ('dc', wt.HDC),
                ('flags', wt.DWORD), ('first', wt.WORD), ('last', wt.WORD),
                ('minimum', wt.WORD), ('maximum', wt.WORD), ('copies', wt.WORD),
                ('instance', wt.HINSTANCE), ('data', wt.LPARAM),
                ('print_hook', ct.c_void_p), ('setup_hook', ct.c_void_p),
                ('print_template', wt.LPCWSTR), ('setup_template', wt.LPCWSTR),
                ('print_handle', wt.HGLOBAL), ('setup_handle', wt.HGLOBAL)]


class DeviceMode(ct.Structure):
    # Somente o prefixo público que define papel, orientação e escala.
    _fields_ = [('name', wt.WCHAR * 32), ('spec', wt.WORD), ('driver', wt.WORD),
                ('size', wt.WORD), ('extra', wt.WORD), ('fields', wt.DWORD),
                ('orientation', ct.c_short), ('paper', ct.c_short),
                ('length', ct.c_short), ('width', ct.c_short), ('scale', ct.c_short)]


class DocumentInfo(ct.Structure):
    _fields_ = [('size', ct.c_int), ('name', wt.LPCWSTR), ('output', wt.LPCWSTR),
                ('datatype', wt.LPCWSTR), ('flags', wt.DWORD)]


def page_geometry(layout, caps):
    """Coordenadas físicas, sem encolher a imagem à área imprimível do driver."""
    dpi_x, dpi_y, width, height, offset_x, offset_y, printable_w, printable_h = caps
    if min(dpi_x, dpi_y, width, height, printable_w, printable_h) <= 0:
        raise ValueError('A impressora não informou medidas válidas para o papel.')
    expected_w, expected_h = layout['papel_mm']
    actual_w, actual_h = width * 25.4 / dpi_x, height * 25.4 / dpi_y
    if abs(actual_w - expected_w) > 2 or abs(actual_h - expected_h) > 2:
        raise ValueError('Selecione papel A4 e a mesma orientação das folhas nas propriedades da impressora.')
    borders = [offset_x * 25.4 / dpi_x, offset_y * 25.4 / dpi_y,
               (width - offset_x - printable_w) * 25.4 / dpi_x,
               (height - offset_y - printable_h) * 25.4 / dpi_y]
    if max(borders) > layout['margem_mm'] + .3:
        raise ValueError('A impressora exige margem maior. Aumente a borda branca nos ajustes de impressão.')
    if layout.get('marcas') and max(borders) > layout['margem_mm'] - layout['recuo_guias_mm'] + .3:
        raise ValueError('A impressora cortaria as guias de montagem. Aumente a borda branca nos ajustes de impressão.')
    return (-offset_x, -offset_y,
            round(expected_w * dpi_x / 25.4) - offset_x,
            round(expected_h * dpi_y / 25.4) - offset_y)


def print_poster(engine):
    if sys.platform != 'win32':
        raise OSError('A impressão direta está disponível no Windows. Use Salvar PDF neste sistema.')
    from PIL import ImageWin
    dialog_api = ct.WinDLL('comdlg32', use_last_error=True)
    gdi = ct.WinDLL('gdi32', use_last_error=True)
    kernel = ct.WinDLL('kernel32', use_last_error=True)
    dialog_api.PrintDlgW.argtypes = [ct.POINTER(PrintDialog)]
    dialog_api.PrintDlgW.restype = wt.BOOL
    dialog_api.CommDlgExtendedError.restype = wt.DWORD
    kernel.GlobalLock.argtypes = [wt.HGLOBAL]; kernel.GlobalLock.restype = ct.c_void_p
    kernel.GlobalUnlock.argtypes = [wt.HGLOBAL]
    kernel.GlobalFree.argtypes = [wt.HGLOBAL]; kernel.GlobalFree.restype = wt.HGLOBAL
    gdi.GetDeviceCaps.argtypes = [wt.HDC, ct.c_int]
    gdi.StartDocW.argtypes = [wt.HDC, ct.POINTER(DocumentInfo)]
    for name in ['StartPage', 'EndPage', 'EndDoc', 'AbortDoc', 'DeleteDC']:
        getattr(gdi, name).argtypes = [wt.HDC]
    layout = engine.layout()
    dialog = PrintDialog()
    dialog.size = ct.sizeof(dialog)
    dialog.minimum = dialog.first = dialog.copies = 1
    dialog.maximum = dialog.last = layout['total_folhas']
    started = False
    try:
        # A leitura do padrão não muda as preferências globais da impressora.
        dialog.flags = 0x400  # PD_RETURNDEFAULT
        if not dialog_api.PrintDlgW(ct.byref(dialog)):
            raise OSError('Não foi possível consultar uma impressora. Confira as impressoras do Windows.')
        if dialog.mode:
            pointer = kernel.GlobalLock(dialog.mode)
            if not pointer:
                raise OSError('Não foi possível preparar as opções da impressora.')
            try:
                mode = ct.cast(pointer, ct.POINTER(DeviceMode)).contents
                if mode.size < ct.sizeof(DeviceMode):
                    raise OSError('A impressora não forneceu opções de papel compatíveis.')
                mode.fields = (mode.fields & ~0x0c) | 0x13  # DM_ORIENTATION | DM_PAPERSIZE | DM_SCALE
                mode.orientation = 1 if layout['papel_mm'][0] < layout['papel_mm'][1] else 2
                mode.paper = 9  # DMPAPER_A4
                mode.scale = 100
            finally:
                kernel.GlobalUnlock(dialog.mode)
        # Cópias são aplicadas pelo driver, uma única vez; seleção avulsa e arquivo desativados.
        dialog.flags = 0x100 | 0x4 | 0x80000 | 0x40000  # RETURNDC, NOSELECTION, DISABLEPRINTTOFILE, USEDEVMODECOPIESANDCOLLATE
        if not dialog_api.PrintDlgW(ct.byref(dialog)):
            if dialog_api.CommDlgExtendedError():
                raise OSError('Não foi possível abrir a janela de impressão do Windows.')
            return {'cancelada': True, 'folhas_enviadas': 0}
        caps = [gdi.GetDeviceCaps(dialog.dc, key) for key in [88, 90, 110, 111, 112, 113, 8, 10]]
        rectangle = page_geometry(layout, caps)
        # Confere a escala novamente, pois o usuário pode mudar propriedades no diálogo.
        pointer = kernel.GlobalLock(dialog.mode) if dialog.mode else None
        if pointer:
            try:
                mode = ct.cast(pointer, ct.POINTER(DeviceMode)).contents
                if mode.fields & 0x10 and mode.scale != 100:
                    raise ValueError('Selecione escala 100% nas propriedades da impressora.')
            finally:
                kernel.GlobalUnlock(dialog.mode)
        first, last = (dialog.first, dialog.last) if dialog.flags & 2 else (1, layout['total_folhas'])
        if not 1 <= first <= last <= layout['total_folhas']:
            raise ValueError('O intervalo de folhas selecionado não é válido.')
        info = DocumentInfo(ct.sizeof(DocumentInfo), 'Amplia - pôster A4', None, None, 0)
        if gdi.StartDocW(dialog.dc, ct.byref(info)) <= 0:
            raise OSError('Impressão não iniciada. A seleção pode ter sido cancelada ou o destino estar indisponível.')
        started = True
        for number in range(first, last + 1):
            # Uma folha por vez a 300 dpi: não monta um bitmap gigante do pôster.
            image = engine.render(round(max(layout['papel_mm']) * 300 / 25.4), number)
            try:
                if gdi.StartPage(dialog.dc) <= 0:
                    raise OSError('Não foi possível iniciar a próxima folha.')
                ImageWin.Dib(image).draw(ImageWin.HDC(dialog.dc), rectangle)
                if gdi.EndPage(dialog.dc) <= 0:
                    raise OSError('Não foi possível enviar uma folha à impressora.')
            finally:
                image.close()
        if gdi.EndDoc(dialog.dc) <= 0:
            raise OSError('O Windows não confirmou o envio da impressão.')
        started = False
        return {'cancelada': False, 'folhas_enviadas': last - first + 1,
                'escala': '100%', 'resolucao_raster_dpi': 300}
    finally:
        if dialog.dc:
            if started:
                gdi.AbortDoc(dialog.dc)
            gdi.DeleteDC(dialog.dc)
        for handle in [dialog.mode, dialog.names]:
            if handle:
                kernel.GlobalFree(handle)
