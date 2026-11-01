# Amplia · © 2026 Heraldo Antunes · SPDX-License-Identifier: MIT
"""Interface Windows do Amplia: mesma execução JSON, sem navegador ou servidor."""
from __future__ import annotations

import base64
from concurrent.futures import ThreadPoolExecutor
import ctypes
from ctypes import wintypes
import io
import json
from pathlib import Path
import sys
import tkinter as tk
from tkinter import messagebox, ttk
from amplia_picker import NativePicker

from PIL import Image, ImageDraw, ImageFont, ImageTk
from amplia import Amplia, VERSAO

BASE = Path(__file__).resolve().parent
GREEN = '#1f6e43'


def initial_geometry(root):
    left, top, right, bottom = 0, 0, root.winfo_screenwidth(), root.winfo_screenheight()
    horizontal, vertical = 40, 110
    if sys.platform == 'win32':
        area = wintypes.RECT()
        user32 = ctypes.windll.user32
        if user32.SystemParametersInfoW(48, 0, ctypes.byref(area), 0):
            left, top, right, bottom = area.left, area.top, area.right, area.bottom
        # Reserva espaço também para título, menu e bordas, fora da área cliente do Tk.
        horizontal = 2 * user32.GetSystemMetrics(32) + 32
        vertical = user32.GetSystemMetrics(4) + user32.GetSystemMetrics(15) + 2 * user32.GetSystemMetrics(33) + 32
    width = max(1, min(1160, right - left - horizontal))
    height = max(1, min(740, bottom - top - vertical))
    return width, height, left + 16, top + 16


def assembly_diagram(help_data):
    """Esquema didático próprio; posições e dimensões são ilustrativas."""
    image = Image.new('RGB', (1000, 330), '#f7faf5')
    draw = ImageDraw.Draw(image)
    def font(size):
        path = Path('C:/Windows/Fonts/segoeui.ttf')
        return ImageFont.truetype(str(path), size) if path.exists() else ImageFont.load_default(size=size)
    whole = help_data['montagem'] == 'inteiras'
    draw.text((25, 12), 'Folhas inteiras: encoste o papel' if whole else
              'Sem faixa repetida: encoste as imagens' if help_data['modo'] == 'borda_a_borda' else
              'Dobre a margem esquerda de A2 para trás', font=font(26), fill=GREEN)
    art = Image.new('RGB', (660, 150), '#f3efdc')
    painter = ImageDraw.Draw(art)
    painter.polygon([(0,150),(240,15),(480,150)], fill='#39764f')
    painter.ellipse((430,20,490,80), fill='#c87a4e')
    if whole:
        draw.rectangle((90,70,440,260),fill='white',outline='#65765f',width=2)
        draw.rectangle((440,70,790,260),fill='white',outline='#65765f',width=2)
        image.paste(art.crop((0,0,330,150)),(100,90))
        image.paste(art.crop((330,0,660,150)),(450,90))
        draw.text((105,65),'A1',font=font(20),fill=GREEN)
        draw.text((455,65),'A2',font=font(20),fill=GREEN)
        draw.text((75,285),'Sem cortar, dobrar ou sobrepor. As faixas brancas ficam visíveis.',font=font(22),fill=GREEN)
    else:
        draw.rectangle((75,70,465,260),fill='white',outline='#65765f',width=2)
        image.paste(art.crop((0,0,350,150)),(95,90))
        # A folha nova fica por cima; a margem esquerda está dobrada para trás.
        draw.rectangle((415,70,805,260),fill='white',outline='#65765f',width=2)
        image.paste(art.crop((320,0,660,150)),(415,90))
        for y in range(75,255,14):
            draw.line((415,y,415,y+7),fill='#333333',width=2)
        draw.text((110,65),'A1: por baixo',font=font(19),fill=GREEN)
        draw.text((480,65),'A2: por cima',font=font(19),fill=GREEN)
        draw.text((75,280),'Tracejado = dobra para trás. Alinhe o desenho e fixe pelo verso.',font=font(22),fill=GREEN)
    return image


class Desktop:
    def __init__(self, root, engine=None):
        self.root = root
        self.engine = engine or Amplia()
        self.pool = ThreadPoolExecutor(max_workers=1, thread_name_prefix='amplia')
        self.busy = False
        self.dirty = False
        self.closing = False
        self.photo = None
        self.diagram_photo = None
        self.preview_image = None
        self.future = None
        self.help_data = self.engine.execute({'comando': 'ajuda.montagem'})['resultado']
        self.controls = []
        self.inputs = []
        self.input_states = []
        self._syncing = True
        self.timer = None
        self.advance_after_config = False
        self.unsaved = False
        self.picker = None
        self.picker_folder = False
        self.picker_poll_id = None
        self.icon = tk.PhotoImage(file=str(BASE / 'img' / 'icone.png'))
        root.iconphoto(True, self.icon)
        root.title('Amplia · aplicativo Windows')
        width, height, x, y = initial_geometry(root)
        root.geometry(f'{width}x{height}+{x}+{y}')
        root.minsize(min(900, width), min(620, height))
        root.configure(bg='#eef3ec')
        root.protocol('WM_DELETE_WINDOW', self.close)
        self.style()
        self.build()
        self.apply_state(self.engine.execute({'comando': 'estado.obter'})['resultado'])
        self.render_help(self.help_data)
        self._syncing = False

    def style(self):
        style = ttk.Style(self.root)
        style.theme_use('clam')
        style.configure('.', font=('Segoe UI', 10))
        style.configure('TFrame', background='#ffffff')
        style.configure('TLabel', background='#ffffff', foreground='#263b2c')
        style.configure('TButton', padding=(10, 9), background='#edf3e9')
        style.configure('Primary.TButton', background=GREEN, foreground='white')
        style.map('Primary.TButton', background=[('active', '#185935'), ('disabled', '#bac9b6')])
        style.configure('Title.TLabel', font=('Segoe UI', 25, 'bold'), foreground=GREEN)
        style.configure('Heading.TLabel', font=('Segoe UI', 13, 'bold'))
        style.configure('Hint.TLabel', font=('Segoe UI', 9), foreground='#62735f')
        style.configure('TNotebook', background='#eef3ec', borderwidth=0)
        style.configure('TNotebook.Tab', padding=(12, 10))

    def button(self, parent, text, callback, primary=False):
        button = ttk.Button(parent, text=text, command=callback, style='Primary.TButton' if primary else 'TButton')
        self.controls.append(button)
        return button

    def build(self):
        menu = tk.Menu(self.root)
        file_menu = tk.Menu(menu, tearoff=False)
        file_menu.add_command(label='Abrir imagem…', accelerator='Ctrl+O', command=self.choose_file)
        file_menu.add_command(label='Salvar PDF…', accelerator='Ctrl+Shift+S', command=self.go_pdf)
        file_menu.add_command(label='Imprimir…', accelerator='Ctrl+P', command=self.print_poster)
        file_menu.add_separator(); file_menu.add_command(label='Sair', command=self.close)
        menu.add_cascade(label='Arquivo', menu=file_menu)
        tools = tk.Menu(menu, tearoff=False)
        tools.add_command(label='Comandos para automação…', command=lambda: self.submit('comandos.listar'))
        menu.add_cascade(label='Ferramentas', menu=tools)
        help_menu = tk.Menu(menu, tearoff=False)
        help_menu.add_command(label='Como montar as folhas', accelerator='F1', command=lambda: self.submit('ajuda.montagem'))
        help_menu.add_command(label='Sobre o Amplia', command=lambda: self.submit('programa.sobre'))
        menu.add_cascade(label='Ajuda', menu=help_menu); self.root.configure(menu=menu)
        self.root.bind('<Control-o>', lambda _event: self.choose_file())
        self.root.bind('<Control-Shift-S>', lambda _event: self.go_pdf())
        self.root.bind('<Control-p>', lambda _event: self.print_poster())
        self.root.bind('<F1>', lambda _event: self.submit('ajuda.montagem'))
        header = ttk.Frame(self.root, padding=(20, 12)); header.pack(fill='x')
        ttk.Label(header, text='Amplia', style='Title.TLabel').pack(side='left')
        ttk.Label(header, text='Sua imagem em folhas A4', style='Hint.TLabel').pack(side='left', padx=20)
        ttk.Label(header, text=f'Versão {VERSAO} · em teste', style='Hint.TLabel').pack(side='right')
        main = tk.Frame(self.root, bg='#eef3ec'); main.pack(fill='both', expand=True, padx=14, pady=10)
        side = ttk.Frame(main, width=340); side.pack(side='left', fill='y', padx=(0, 12)); side.pack_propagate(False)
        self.steps = ttk.Notebook(side); self.steps.pack(fill='both', expand=True)
        self.image_page = ttk.Frame(self.steps, padding=14)
        self.size_page = ttk.Frame(self.steps, padding=14)
        self.pdf_page = ttk.Frame(self.steps, padding=14)
        for page, title in ((self.image_page, 'Imagem'), (self.size_page, 'Folhas'), (self.pdf_page, 'Imprimir / PDF')):
            self.steps.add(page, text=title)
        footer = ttk.Frame(side, padding=10); footer.pack(fill='x')
        self.back_button = self.button(footer, 'Voltar', self.previous_step); self.back_button.pack(side='left')
        self.next_button = self.button(footer, 'Continuar', self.next_step, True); self.next_button.pack(side='right')
        self.export_button = self.button(footer, 'Salvar PDF', self.export_pdf)
        self.print_button = self.button(footer, 'Imprimir…', self.print_poster, True)
        self.steps.bind('<<NotebookTabChanged>>', self.step_changed)
        page = self.image_page
        ttk.Label(page, text='Escolha a imagem do pôster', style='Heading.TLabel', wraplength=285).pack(anchor='w', pady=(0, 12))
        self.button(page, 'Escolher imagem…', self.choose_file, True).pack(fill='x')
        ttk.Label(page, text='PNG, JPG, WebP, BMP ou TIFF.\nSua imagem original não será alterada.', style='Hint.TLabel', wraplength=285).pack(anchor='w', pady=10)
        self.image_label = ttk.Label(page, text='Nenhuma imagem escolhida.', wraplength=285)
        self.image_label.pack(anchor='w', pady=(10, 16))
        self.button(page, 'Usar imagem de exemplo', self.open_example).pack(fill='x', pady=4)
        self.button(page, 'Colar caminho do arquivo…', self.toggle_path).pack(fill='x', pady=4)
        self.path_panel = ttk.Frame(page)
        ttk.Label(self.path_panel, text='Caminho completo da imagem', style='Hint.TLabel').pack(anchor='w', pady=6)
        self.path = tk.StringVar()
        path_entry = ttk.Entry(self.path_panel, textvariable=self.path); path_entry.pack(fill='x')
        path_entry.bind('<Return>', lambda _event: self.open_path()); self.inputs.append(path_entry)
        self.button(self.path_panel, 'Abrir imagem', self.open_path).pack(fill='x', pady=6)
        page = self.size_page
        ttk.Label(page, text='Quantas folhas você quer usar?', style='Heading.TLabel', wraplength=285).pack(anchor='w', pady=(0, 10))
        self.size_mode = tk.StringVar(value='Por folhas (simples)')
        mode = ttk.Combobox(page, textvariable=self.size_mode, state='readonly', values=('Por folhas (simples)', 'Por medidas (mm)'))
        mode.pack(fill='x', pady=(0, 8)); self.inputs.append(mode)
        mode.bind('<<ComboboxSelected>>', lambda _event: self.size_mode_changed())
        self.sheet_fields = ttk.Frame(page); self.sheet_fields.pack(fill='x')
        presets = ttk.Frame(self.sheet_fields); presets.pack(fill='x', pady=(0, 7))
        for count, label in ((1, '1 folha'), (2, '4 folhas'), (3, '9 folhas')):
            self.button(presets, label, lambda n=count: self.preset(n)).pack(side='left', expand=True, fill='x', padx=1)
        fields = ttk.Frame(self.sheet_fields); fields.pack(fill='x')
        self.sheet_values = {}
        for row, (key, label) in enumerate((('colunas', 'Na horizontal'), ('linhas', 'Na vertical'))):
            ttk.Label(fields, text=label).grid(row=row, column=0, sticky='w', pady=4)
            value = tk.StringVar(value='2'); self.sheet_values[key] = value
            spin = ttk.Spinbox(fields, from_=1, to=400, width=7, textvariable=value)
            spin.grid(row=row, column=1, padx=14, pady=4); self.inputs.append(spin)
            value.trace_add('write', lambda *_args: self.sheet_count_changed())
        self.sheet_summary = tk.StringVar(value='2 × 2 = 4 folhas A4')
        ttk.Label(self.sheet_fields, textvariable=self.sheet_summary, style='Hint.TLabel').pack(anchor='w', pady=5)
        self.mm_fields = ttk.Frame(page); self.values = {}
        for row, (key, label) in enumerate((('largura_mm', 'Largura (mm)'), ('altura_mm', 'Altura (mm)'))):
            ttk.Label(self.mm_fields, text=label).grid(row=row, column=0, sticky='w', pady=4)
            value = tk.StringVar(); self.values[key] = value
            entry = ttk.Entry(self.mm_fields, textvariable=value, width=10)
            entry.grid(row=row, column=1, padx=10, pady=4); entry.bind('<KeyRelease>', self.mark_dirty); self.inputs.append(entry)
        self.size_anchor = ttk.Frame(page); self.size_anchor.pack(fill='x')
        ttk.Label(page, text='Posição das folhas A4', style='Hint.TLabel').pack(anchor='w', pady=(8, 4))
        self.orientation = tk.StringVar(value='Em pé (retrato)')
        orientation = ttk.Combobox(page, textvariable=self.orientation, values=('Em pé (retrato)', 'Deitadas (paisagem)'), state='readonly')
        orientation.pack(fill='x'); orientation.bind('<<ComboboxSelected>>', lambda _event: self.orientation_changed()); self.inputs.append(orientation)
        ttk.Label(page, text='Montagem sem recortar', style='Hint.TLabel').pack(anchor='w', pady=(8, 4))
        self.assembly_mode = tk.StringVar(value='Dobrar bordas para trás')
        mode = ttk.Combobox(page, textvariable=self.assembly_mode,
                            values=('Dobrar bordas para trás', 'Folhas inteiras (faixas brancas)'), state='readonly')
        mode.pack(fill='x'); mode.bind('<<ComboboxSelected>>', lambda _event: self.orientation_changed()); self.inputs.append(mode)
        self.assembly_hint = tk.StringVar()
        self.assembly_hint_label = ttk.Label(page, textvariable=self.assembly_hint, style='Hint.TLabel', wraplength=285)
        self.assembly_hint_label.pack(anchor='w', pady=4)
        self.advanced_button = self.button(page, 'Ajustes de impressão…', self.toggle_advanced); self.advanced_button.pack(fill='x', pady=8)
        self.advanced = ttk.Frame(page)
        for row, (key, label) in enumerate((('margem_mm', 'Borda branca (mm)'), ('sobreposicao_mm', 'Faixa para colar (mm)'))):
            ttk.Label(self.advanced, text=label).grid(row=row, column=0, sticky='w', pady=3)
            value = tk.StringVar(); self.values[key] = value
            entry = ttk.Entry(self.advanced, textvariable=value, width=8)
            entry.grid(row=row, column=1, padx=8, pady=3); entry.bind('<KeyRelease>', self.mark_dirty); self.inputs.append(entry)
        self.marks = tk.BooleanVar(value=True)
        marks = ttk.Checkbutton(self.advanced, text='Guias de montagem e códigos das folhas', variable=self.marks, command=self.mark_dirty)
        marks.grid(row=2, column=0, columnspan=2, sticky='w', pady=6); self.inputs.append(marks)
        self.apply_button = self.button(page, 'Atualizar prévia', self.configure_poster); self.apply_button.pack(fill='x')
        ttk.Label(page, text='A imagem fica inteira, sem esticar.\nPode sobrar espaço branco.', style='Hint.TLabel', wraplength=285).pack(anchor='w', pady=8)
        page = self.pdf_page
        ttk.Label(page, text='Imprima ou salve o PDF', style='Heading.TLabel', wraplength=285).pack(anchor='w', pady=(0, 12))
        self.pdf_summary = tk.StringVar(value='Escolha uma imagem antes de salvar.')
        ttk.Label(page, textvariable=self.pdf_summary, wraplength=285).pack(anchor='w', pady=(0, 14))
        ttk.Label(page, text='Nome do arquivo (para salvar PDF)', style='Hint.TLabel').pack(anchor='w')
        self.output_name = tk.StringVar(value='amplia-poster.pdf')
        name_entry = ttk.Entry(page, textvariable=self.output_name); name_entry.pack(fill='x', pady=(4, 12)); self.inputs.append(name_entry)
        ttk.Label(page, text='Salvar na pasta', style='Hint.TLabel').pack(anchor='w')
        self.output_folder = tk.StringVar(value=str(BASE / 'output'))
        folder_entry = ttk.Entry(page, textvariable=self.output_folder); folder_entry.pack(fill='x', pady=4); self.inputs.append(folder_entry)
        self.button(page, 'Escolher pasta…', self.choose_folder).pack(fill='x', pady=(0, 12))
        self.output = tk.StringVar()
        self.output_name.trace_add('write', lambda *_args: self.sync_output())
        self.output_folder.trace_add('write', lambda *_args: self.sync_output()); self.sync_output()
        self.map_button = self.button(page, 'Salvar mapa de montagem (PDF)', lambda: self.export_pdf(mapa=True))
        self.map_button.pack(fill='x', pady=4)
        self.saved_label = ttk.Label(page, text='', wraplength=285, foreground=GREEN); self.saved_label.pack(anchor='w', pady=8)
        ttk.Label(page, text='Ao imprimir, escolha 100% ou Tamanho real.\nDesative Ajustar à página.', style='Hint.TLabel', wraplength=285).pack(anchor='w', pady=8)
        self.status = tk.StringVar(value='Escolha uma imagem para começar.')
        right = ttk.Frame(main, padding=12); right.pack(side='left', fill='both', expand=True)
        ttk.Label(right, textvariable=self.status, wraplength=700, style='Hint.TLabel').pack(anchor='w', pady=(0, 8))
        self.picker_cancel = self.button(right, 'Cancelar seleção', self.cancel_picker)
        style = ttk.Style(self.root); style.layout('Workspace.TNotebook.Tab', [])
        self.tabs = ttk.Notebook(right, style='Workspace.TNotebook'); self.tabs.pack(fill='both', expand=True)
        self.preview_tab = ttk.Frame(self.tabs, padding=10)
        self.help_tab = ttk.Frame(self.tabs, padding=12)
        self.command_tab = ttk.Frame(self.tabs, padding=12)
        self.about_tab = ttk.Frame(self.tabs, padding=12)
        for tab, title in ((self.preview_tab,'Prévia'),(self.help_tab,'Como montar'),(self.command_tab,'Comandos'),(self.about_tab,'Sobre')):
            self.tabs.add(tab, text=title)
        self.metrics = ttk.Label(self.preview_tab, text='', style='Heading.TLabel', wraplength=650); self.metrics.pack(anchor='w')
        self.view = ttk.Combobox(self.preview_tab, values=('Pôster completo',), state='readonly', width=30)
        self.view.current(0); self.view.pack(anchor='e', pady=8); self.inputs.append(self.view)
        self.view.bind('<<ComboboxSelected>>', lambda _event: self.change_view())
        self.preview_canvas = tk.Canvas(self.preview_tab, bg='#eaf0e5', highlightthickness=0)
        self.preview_canvas.pack(fill='both', expand=True)
        self.preview_canvas.bind('<Configure>', lambda _event: self.paint_preview())
        self.preview_notice = tk.StringVar(value='')
        ttk.Label(self.preview_tab, textvariable=self.preview_notice, style='Hint.TLabel', wraplength=650).pack(anchor='w', pady=6)
        self.legend = ttk.Label(self.preview_tab, text='', style='Hint.TLabel', wraplength=650); self.legend.pack(anchor='w')
        ttk.Label(self.help_tab, text='Como montar as folhas', style='Heading.TLabel').pack(anchor='w')
        self.help_config = ttk.Label(self.help_tab, text='', style='Hint.TLabel'); self.help_config.pack(anchor='w', pady=8)
        self.help_image = ttk.Label(self.help_tab); self.help_image.pack(fill='x')
        self.help_text = tk.Text(self.help_tab, wrap='word', font=('Segoe UI',10), relief='flat', height=12, padx=10, pady=8)
        self.help_text.pack(fill='both', expand=True, pady=8); self.help_text.configure(state='disabled')
        self.button(self.help_tab, 'Voltar à prévia', lambda: self.submit('ajuda.montagem', {'exibir':False})).pack(anchor='e')
        ttk.Label(self.command_tab, text='Comandos para automação', style='Heading.TLabel').pack(anchor='w')
        ttk.Label(self.command_tab, text='Recurso técnico para scripts e assistentes de IA.', style='Hint.TLabel').pack(anchor='w', pady=6)
        self.request_text = tk.Text(self.command_tab, height=4, font=('Consolas',10), wrap='word'); self.request_text.pack(fill='x')
        self.request_text.insert('1.0','{"comando":"estado.obter"}')
        row=ttk.Frame(self.command_tab); row.pack(fill='x', pady=8)
        self.button(row,'Executar comando',self.execute_json,True).pack(side='left')
        self.button(row,'Consultar comandos',lambda:self.submit('comandos.listar')).pack(side='left',padx=8)
        self.button(row,'Voltar à prévia',lambda:self.tabs.select(self.preview_tab)).pack(side='right')
        self.response_text = tk.Text(self.command_tab,font=('Consolas',9),wrap='word',bg='#f3f6ef',relief='flat',padx=10,pady=10)
        self.response_text.pack(fill='both',expand=True); self.response_text.configure(state='disabled')
        self.about_text = tk.Text(self.about_tab,wrap='word',font=('Segoe UI',11),relief='flat',padx=14,pady=12)
        self.about_text.pack(fill='both',expand=True)
        self.render_about(self.engine.execute({'comando':'programa.sobre'})['resultado'])
        self.button(self.about_tab,'Voltar à prévia',lambda:self.submit('programa.sobre',{'exibir':False})).pack(anchor='e')

    def step_changed(self, _event=None):
        if not hasattr(self, 'status'):
            return
        step = self.steps.index('current')
        self.back_button.configure(state='normal' if step > 0 and not self.busy else 'disabled')
        self.next_button.pack_forget(); self.export_button.pack_forget(); self.print_button.pack_forget()
        if step == 2:
            self.print_button.pack(side='right')
            self.export_button.pack(side='right', padx=(0, 6))
            self.export_button.configure(state='normal' if self.engine.image is not None and not self.busy and not self.dirty else 'disabled')
            self.print_button.configure(state=self.export_button.cget('state'))
            if self.dirty:
                self.status.set('Atualize a prévia na etapa Folhas antes de imprimir ou salvar o PDF.')
        else:
            self.next_button.pack(side='right')
            self.next_button.configure(text='Continuar' if step == 1 else 'Continuar', state='normal' if self.engine.image is not None and not self.busy else 'disabled')
        if step > 0 and self.engine.image is None:
            self.status.set('Primeiro, escolha a imagem na aba Imagem.')

    def previous_step(self):
        self.steps.select(max(0, self.steps.index('current')-1))

    def next_step(self):
        if self.busy or self.engine.image is None:
            return
        if self.steps.index('current') == 0:
            self.steps.select(1)
        else:
            self.go_pdf()

    def go_pdf(self):
        if self.engine.image is None:
            self.steps.select(0); self.status.set('Escolha uma imagem antes de imprimir ou salvar o PDF.')
        elif self.dirty:
            self.advance_after_config = True; self.configure_poster()
        else:
            self.steps.select(2)

    def toggle_path(self):
        if self.path_panel.winfo_manager():
            self.path_panel.pack_forget()
        else:
            self.path_panel.pack(fill='x', pady=6)

    def open_example(self):
        self.path.set(str(BASE/'examples'/'demo.png')); self.open_path()

    def choose_folder(self):
        if self.busy:
            return
        self.start_picker(self.output_folder.get(), folder=True)

    def start_picker(self, initial, folder=False):
        self.cancel_picker()
        try:
            self.picker = NativePicker(initial, folder=folder)
        except OSError:
            self.status.set('Não foi possível abrir o seletor do Windows. Informe o caminho diretamente.')
            return
        self.picker_folder = folder
        self.picker_cancel.pack(anchor='e', pady=(0, 6), before=self.tabs)
        self.status.set('Escolha a pasta na janela do Windows.' if folder else 'Escolha a imagem na janela do Windows. Você pode navegar pelas pastas e unidades.')
        self.picker_poll_id = self.root.after(80, self.poll_picker)

    def poll_picker(self):
        self.picker_poll_id = None
        if self.picker is None or self.closing:
            return
        result = self.picker.poll()
        if result is None:
            self.picker_poll_id = self.root.after(80, self.poll_picker)
            return
        folder = self.picker_folder
        self.picker = None
        self.picker_cancel.pack_forget()
        if result['erro']:
            self.status.set(result['erro'])
            if not folder and not self.path_panel.winfo_manager():
                self.toggle_path()
        elif result['caminho']:
            if folder:
                self.output_folder.set(result['caminho'])
                self.status.set('Pasta de destino selecionada.')
            else:
                self.path.set(result['caminho'])
                self.open_path()
        else:
            self.status.set('Seleção cancelada.')

    def cancel_picker(self):
        if self.picker_poll_id:
            self.root.after_cancel(self.picker_poll_id)
            self.picker_poll_id = None
        if self.picker is not None:
            self.picker.cancel()
            self.picker = None
            self.status.set('Seleção cancelada.')
        if hasattr(self, 'picker_cancel'):
            self.picker_cancel.pack_forget()

    def sync_output(self):
        self.output.set(str(Path(self.output_folder.get().strip().strip('"')) / self.output_name.get().strip()))

    def preset(self, count):
        self._syncing = True
        self.size_mode.set('Por folhas (simples)')
        for value in self.sheet_values.values(): value.set(str(count))
        self._syncing = False
        self.size_mode_changed(); self.configure_poster()

    def orientation_changed(self):
        self.mark_dirty(); self.schedule_preview()

    def schedule_preview(self):
        if self.timer:
            self.root.after_cancel(self.timer)
        self.timer = self.root.after(550, self.auto_preview)

    def auto_preview(self):
        self.timer = None
        if self.busy or not self.dirty or self.engine.image is None or not self.size_mode.get().startswith('Por folhas'):
            return
        try:
            cols, rows = (int(self.sheet_values[key].get()) for key in ('colunas','linhas'))
            if min(cols,rows) < 1 or cols*rows > 400:
                return
        except ValueError:
            return
        self.configure_poster()

    def success_message(self, command):
        return {'imagem.abrir':'Imagem pronta. Escolha as folhas e confira a prévia.',
                'poster.configurar':'Prévia atualizada. Se estiver como você quer, continue para o PDF.',
                'previa.gerar':'Prévia pronta. Escolha uma folha ou veja o pôster completo.',
                'sessao.reiniciar':'Escolha uma imagem para começar.',
                'programa.sobre':'Sobre o Amplia.',
                'ajuda.montagem':'Confira o modo, a ordem e a união das folhas.',
                'comandos.listar':'Comandos disponíveis para automação.'}.get(command,'Pronto.')


    def size_mode_changed(self):
        self.sheet_fields.pack_forget(); self.mm_fields.pack_forget()
        panel = self.sheet_fields if self.size_mode.get().startswith('Por folhas') else self.mm_fields
        panel.pack(fill='x', before=self.size_anchor)
        self.sheet_count_changed()

    def sheet_count_changed(self):
        if self._syncing:
            return
        try:
            cols, rows = (int(self.sheet_values[key].get()) for key in ('colunas', 'linhas'))
            text = f'{cols} × {rows} = {cols * rows} folhas A4' if min(cols, rows) > 0 else 'Escolha quantidades maiores que zero.'
        except ValueError:
            text = 'Informe quantidades inteiras de folhas.'
        self.sheet_summary.set(text)
        self.mark_dirty()
        self.schedule_preview()

    def toggle_advanced(self):
        if self.advanced.winfo_manager():
            self.advanced.pack_forget(); self.advanced_button.configure(text='Ajustes de impressão…')
            self.assembly_hint_label.pack(anchor='w', pady=4, before=self.advanced_button)
        else:
            self.assembly_hint_label.pack_forget()
            self.advanced.pack(fill='x', before=self.apply_button)
            self.advanced_button.configure(text='Ocultar ajustes de impressão')

    def mark_dirty(self, _event=None):
        if self._syncing:
            return
        self.dirty = True
        self.export_button.configure(state='disabled')
        self.print_button.configure(state='disabled')
        self.map_button.configure(state='disabled')
        self.status.set('Ajustes pendentes. Clique em Atualizar prévia para aplicá-los.' if not self.size_mode.get().startswith('Por folhas') else 'A prévia será atualizada com os novos ajustes.')
        self.preview_notice.set('Há alterações para aplicar.')

    def choose_file(self):
        if self.busy:
            return
        path = self.path.get().strip().strip('"')
        initial = Path(path).parent if path else Path.home()
        self.start_picker(initial)

    def open_path(self):
        self.submit('imagem.abrir', {'caminho': self.path.get().strip().strip('"')})

    def configure_poster(self):
        try:
            values = {key: float(self.values[key].get().replace(',', '.')) for key in ('margem_mm', 'sobreposicao_mm')}
            if self.size_mode.get().startswith('Por folhas'):
                values.update({key: int(value.get()) for key, value in self.sheet_values.items()})
            else:
                values.update({key: float(self.values[key].get().replace(',', '.')) for key in ('largura_mm', 'altura_mm')})
        except ValueError:
            self.advance_after_config = False
            self.status.set('Confira os campos: use números inteiros nas folhas e números válidos nas medidas.'); return
        values.update(orientacao='paisagem' if 'paisagem' in self.orientation.get() else 'retrato', marcas=self.marks.get(),
                      montagem='inteiras' if self.assembly_mode.get().startswith('Folhas inteiras') else 'dobrar')
        self.submit('poster.configurar', values)

    def print_poster(self):
        if self.busy:
            return
        if self.engine.image is None:
            self.go_pdf()
            return
        if self.dirty:
            self.go_pdf()
            return
        self.steps.select(2)
        self.submit('poster.imprimir')

    def export_pdf(self, mapa=False):
        if self.dirty:
            self.go_pdf(); return
        name = self.output_name.get().strip()
        if not name or any(char in name for char in '/\\:') or name in ('.','..'):
            self.status.set('Informe apenas o nome do PDF, sem o caminho da pasta.'); return
        if not name.lower().endswith('.pdf'):
            name += '.pdf'; self.output_name.set(name)
        folder = Path(self.output_folder.get().strip().strip('"'))
        if not folder.is_dir():
            self.status.set('A pasta de destino não existe. Clique em Escolher pasta ou confira o caminho.'); return
        if mapa:
            name = Path(name).stem + '-mapa.pdf'
        path = folder/name
        replace = path.exists()
        if replace and not messagebox.askyesno('Substituir PDF?', f'Já existe um arquivo chamado {name}. Deseja substituí-lo?', parent=self.root, default='no'):
            return
        self.submit('mapa.exportar' if mapa else 'pdf.exportar', {'caminho':str(path), 'substituir':replace})

    def change_view(self):
        selected = self.view.current()
        self.submit('previa.gerar', {'pixels': 1400, **({'folha': selected} if selected > 0 else {})})

    def execute_json(self):
        try:
            request = json.loads(self.request_text.get('1.0', 'end'))
        except ValueError:
            self.status.set('JSON inválido.'); return
        self.submit_request(request)

    def tab_changed(self, _event):
        if self.tabs.select() == str(self.help_tab) and not self.busy:
            self.submit('ajuda.montagem')
        elif self.tabs.select() == str(self.about_tab) and not self.busy:
            self.submit('programa.sobre')

    def render_about(self, data):
        text = f"{data['nome']} {data['versao']}\n\n{data['descricao']}\n\nLicença: {data['licenca']}\nAutoria: {data['autoria']}"
        text += '\n\nPrivacidade\n' + '\n'.join('• ' + item for item in data['privacidade'])
        text += '\n\nComo foi feito\n' + data['uso_ia']
        text += '\n\nComponentes de terceiros\n' + ', '.join(data['terceiros'])
        text += '\nOs textos de licença estão na pasta licencas do pacote.\n\n' + data['aviso_marcas'] + '\n\n' + data['distribuicao']
        self.about_text.configure(state='normal')
        self.about_text.delete('1.0', 'end'); self.about_text.insert('1.0', text)
        self.about_text.configure(state='disabled')

    def submit(self, command, params=None):
        self.submit_request(dict(comando=command, parametros=params or {}))

    def submit_request(self, request):
        if self.busy or self.closing:
            return
        self.cancel_picker()
        if self.timer:
            self.root.after_cancel(self.timer); self.timer = None
        self.busy = True
        command = request.get('comando') if isinstance(request, dict) else None
        self.status.set({'imagem.abrir':'Abrindo a imagem…','poster.configurar':'Atualizando a prévia…','pdf.exportar':'Salvando o PDF…','poster.imprimir':'Escolha a impressora na janela do Windows. Confira A4 e escala 100%.'}.get(command,'Carregando…'))
        self.input_states = []
        for control in self.controls + self.inputs:
            self.input_states.append((control, str(control.cget('state'))))
            control.configure(state='disabled')
        self.future = self.pool.submit(self.work, request)
        self.root.after(40, self.poll)

    def work(self, request):
        response = self.engine.execute(request)
        state = preview = help_data = None
        if response['ok']:
            command = response['comando']
            if command in {'imagem.abrir', 'poster.configurar', 'sessao.reiniciar', 'estado.obter'}:
                state = self.engine.execute({'comando': 'estado.obter'})['resultado']
                if state['imagem']:
                    preview = self.engine.execute({'comando': 'previa.gerar', 'parametros': {'pixels': 1400}})
                help_data = self.engine.execute({'comando': 'ajuda.montagem'})['resultado']
            elif command == 'previa.gerar':
                preview = response
            elif command == 'ajuda.montagem':
                help_data = response['resultado']
        return response, state, preview, help_data

    def poll(self):
        if self.closing:
            return
        if not self.future.done():
            self.root.after(40, self.poll); return
        try:
            response, state, preview, help_data = self.future.result()
            self.log(response)
            for control, old_state in self.input_states:
                control.configure(state=old_state)
            if state is not None:
                self.apply_state(state)
            if preview is not None:
                if preview['ok']:
                    self.preview_image = Image.open(io.BytesIO(base64.b64decode(preview['resultado']['dados_base64']))).convert('RGB')
                    self.paint_preview()
                else:
                    self.status.set(preview['erro']['mensagem'])
            if help_data is not None:
                self.render_help(help_data)
            if response['ok']:
                command = response['comando']
                if command == 'ajuda.montagem':
                    self.tabs.select(self.help_tab if response['resultado']['exibir'] else self.preview_tab)
                if command == 'programa.sobre':
                    self.render_about(response['resultado'])
                    self.tabs.select(self.about_tab if response['resultado']['exibir'] else self.preview_tab)
                if command == 'mapa.exportar':
                    self.status.set('Mapa salvo. É uma folha de instruções separada; não entra no cartaz.')
                    self.saved_label.configure(text='Mapa: ' + Path(response['resultado']['caminho']).name)
                elif command == 'pdf.exportar':
                    result = response['resultado']
                    self.unsaved = False
                    self.status.set(f"PDF salvo em {result['caminho']}. Imprima em 100% ou Tamanho real.")
                    self.saved_label.configure(text=f"PDF salvo: {Path(result['caminho']).name}\n{result['paginas']} folhas A4. Pronto para imprimir.")
                elif command == 'poster.imprimir':
                    result = response['resultado']
                    self.status.set('Impressão cancelada. O pôster foi mantido.' if result['cancelada'] else
                                    f"{result['folhas_enviadas']} folhas enviadas à impressora em tamanho real. Confira a fila do Windows.")
                else:
                    self.status.set(self.success_message(command))
                if command == 'imagem.abrir':
                    self.unsaved = True
                    self.steps.select(1)
                    source = Path(self.path.get())
                    if source.is_file(): self.output_folder.set(str(source.parent))
                    name = Path(state['imagem']['nome']).stem + '-poster.pdf'
                    folder = Path(self.output_folder.get()); candidate = name; number = 2
                    while (folder/candidate).exists():
                        candidate = Path(name).stem + f'-{number}.pdf'; number += 1
                    self.output_name.set(candidate); self.saved_label.configure(text='')
                elif command == 'poster.configurar':
                    self.unsaved = True
                    if self.advance_after_config:
                        self.advance_after_config = False; self.steps.select(2)
                elif command == 'comandos.listar':
                    self.tabs.select(self.command_tab)
                elif command == 'sessao.reiniciar':
                    self.steps.select(0)
            else:
                self.advance_after_config = False
                code = response['erro']['codigo']
                message = {'MARGEM_INVALIDA':'A borda branca está muito grande. Reduza-a para deixar espaço para a imagem.',
                           'MARGEM_PARA_MARCAS':'As guias de montagem precisam de borda branca de pelo menos 5 mm. Aumente a borda ou desative as marcas.',
                           'SOBREPOSICAO_INVALIDA':'A faixa para colar deve ser menor que a área impressa da folha.',
                           'GRADE_INVALIDA':'Use pelo menos uma folha em cada direção e até 400 no total.'}.get(code, response['erro']['mensagem'])
                if code == 'OPERACAO_FALHOU' and response['comando'] == 'imagem.abrir':
                    message = 'Não foi possível abrir a imagem. Confira se o arquivo existe e se você tem acesso.'
                if code == 'OPERACAO_FALHOU' and response['comando'] == 'poster.imprimir':
                    message = response['erro']['detalhes']['motivo']
                self.status.set(message)
        except Exception as exc:
            self.status.set('Falha na operação: ' + str(exc))
            for control, old_state in self.input_states:
                control.configure(state=old_state)
        finally:
            self.busy = False
            if self.engine.image is None:
                self.apply_button.configure(state='disabled'); self.export_button.configure(state='disabled')
            elif self.dirty:
                self.export_button.configure(state='disabled')
            self.step_changed()

    def apply_state(self, state):
        self._syncing = True
        self.dirty = False
        for key, value in self.values.items():
            value.set(f"{state['configuracao'][key]:g}".replace('.',','))
        self.orientation.set('Deitadas (paisagem)' if state['configuracao']['orientacao']=='paisagem' else 'Em pé (retrato)')
        self.marks.set(state['configuracao']['marcas'])
        whole = state['configuracao']['montagem'] == 'inteiras'
        self.assembly_mode.set('Folhas inteiras (faixas brancas)' if whole else 'Dobrar bordas para trás')
        self.assembly_hint.set('Encoste as folhas; fita pelo verso. As faixas brancas ficam visíveis.' if whole else
                               'Dobre só esquerda/cima nas folhas indicadas. A folha nova vai por cima.')
        self.legend.configure(text='Folhas inteiras e faixas brancas reais da montagem.' if whole else
                              'O verde localiza a faixa repetida; não sai no PDF. Códigos iguais aos das folhas.')
        image = state['imagem']
        self.image_label.configure(text=f"{image['nome']}\n{image['largura_px']} × {image['altura_px']} pixels" if image else 'Nenhuma imagem escolhida.')
        pages = state['folhas']
        self.view.configure(values=['Pôster completo'] + ([f"{p['codigo']} · Folha {p['numero']} · L{p['linha']} C{p['coluna']}" for p in pages['folhas']] if pages else []))
        self.view.current(0)
        if pages:
            for key in ('colunas', 'linhas'):
                self.sheet_values[key].set(str(pages[key]))
            self.sheet_summary.set(f"{pages['colunas']} × {pages['linhas']} = {pages['total_folhas']} folhas A4")
            dimensions = ' × '.join(f'{value/10:.1f}'.replace('.',',') for value in pages['poster_mm'])
            summary = f"{pages['colunas']} × {pages['linhas']} = {pages['total_folhas']} folhas A4 · desenho {dimensions} cm"
            self.metrics.configure(text=summary)
            mounted = ' × '.join(f'{value/10:.1f}'.replace('.', ',') for value in pages['papel_montado_mm'])
            self.pdf_summary.set(summary+'\nPapel montado: '+mounted+' cm.\nUma página do PDF por folha; mapa separado.')
            self.preview_notice.set('A imagem pode perder nitidez neste tamanho.' if pages['avisos'] else 'Imagem inteira, sem cortes.')
        else:
            self.metrics.configure(text='Sua imagem aparecerá aqui.')
            self.pdf_summary.set('Escolha uma imagem antes de salvar.')
            self.preview_notice.set('')
            self.preview_image = None; self.paint_preview()
        self.apply_button.configure(state='normal' if image else 'disabled')
        self.export_button.configure(state='normal' if image else 'disabled')
        self.print_button.configure(state='normal' if image else 'disabled')
        self.map_button.configure(state='normal' if image else 'disabled')
        self._syncing = False
        self.step_changed()

    def paint_preview(self):
        self.preview_canvas.delete('all')
        width, height = self.preview_canvas.winfo_width(), self.preview_canvas.winfo_height()
        if self.preview_image is None:
            self.preview_canvas.create_text(width / 2, height / 2, text='Escolha uma imagem para ver o pôster.', fill='#66765f', font=('Segoe UI', 12), width=max(100, width-40))
            return
        if min(width, height) < 20:
            return
        image = self.preview_image.copy()
        image.thumbnail((width - 24, height - 24), Image.Resampling.LANCZOS)
        self.photo = ImageTk.PhotoImage(image, master=self.root)
        self.preview_canvas.create_image(width / 2, height / 2, image=self.photo)

    def render_help(self, data):
        self.help_data = data
        cfg = data['configuracao']
        self.help_config.configure(text=f"Margem {cfg['margem_mm']:g} mm · sobreposição {cfg['sobreposicao_mm']:g} mm · A4 {cfg['orientacao']} · esquema sem escala")
        text = '\n\n'.join(f"{i}. {step['titulo']}\n{step['texto']}" for i, step in enumerate(data['passos'], 1))
        text += '\n\nCUIDADOS\n' + '\n'.join('• ' + item for item in data['cuidados'])
        text += '\n\n' + data['conceitos']['previa']
        self.help_text.configure(state='normal'); self.help_text.delete('1.0', 'end'); self.help_text.insert('1.0', text); self.help_text.configure(state='disabled')
        self.paint_help()

    def paint_help(self):
        if not hasattr(self, 'help_image') or self.closing:
            return
        image = assembly_diagram(self.help_data)
        image.thumbnail((max(600, self.help_tab.winfo_width() - 35), 285), Image.Resampling.LANCZOS)
        self.diagram_photo = ImageTk.PhotoImage(image, master=self.root)
        self.help_image.configure(image=self.diagram_photo)

    def log(self, response):
        safe = dict(response)
        if isinstance(safe.get('resultado'), dict) and 'dados_base64' in safe['resultado']:
            safe['resultado'] = dict(safe['resultado'], dados_base64='[PNG omitido apenas nesta exibição]')
        self.response_text.configure(state='normal'); self.response_text.delete('1.0', 'end')
        self.response_text.insert('1.0', json.dumps(safe, ensure_ascii=False, indent=2)); self.response_text.configure(state='disabled')

    def close(self, force=False):
        if self.busy and not force:
            self.status.set('Conclua ou cancele a operação em andamento antes de fechar.')
            return
        if not force and self.engine.image is not None and (self.unsaved or self.dirty):
            if not messagebox.askyesno('Fechar sem salvar o PDF?', 'Os ajustes deste pôster ficam só nesta sessão. Deseja fechar sem salvar o PDF?', parent=self.root, default='no'):
                return
        self.closing = True
        self.cancel_picker()
        if self.timer: self.root.after_cancel(self.timer)
        self.pool.shutdown(wait=False, cancel_futures=True)
        self.root.destroy()


def main():
    (BASE / 'output').mkdir(exist_ok=True)
    root = tk.Tk()
    Desktop(root)
    root.mainloop()


if __name__ == '__main__':
    main()
