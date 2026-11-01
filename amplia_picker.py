# Amplia · © 2026 Heraldo Antunes · SPDX-License-Identifier: MIT
"""Seletor nativo em processo separado para não bloquear a interface principal."""
import argparse
import json
from pathlib import Path
import queue
import subprocess
import sys
import threading


class NativePicker:
    def __init__(self, initial, folder=False):
        executable = Path(sys.executable)
        if executable.name.lower() == 'pythonw.exe':
            executable = executable.with_name('python.exe')
        command = [str(executable), '-I', '-S', '-B', '-X', 'utf8', str(Path(__file__).resolve()),
                   '--native', '--initial', str(initial)]
        if folder:
            command.append('--folder')
        self.results = queue.SimpleQueue()
        self.process = subprocess.Popen(command, stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding='utf-8',
            creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
        # Drena os dois canais, inclusive para caminhos longos, fora do laço do Tk.
        threading.Thread(target=self.collect, daemon=True).start()

    def collect(self):
        try:
            output, _errors = self.process.communicate()
            result = json.loads(output)
            path = result.get('caminho')
            if self.process.returncode != 0 or set(result) != {'caminho'} or path is not None and not isinstance(path, str):
                raise ValueError('Resposta inválida do seletor.')
            self.results.put({'caminho': path or None, 'erro': None})
        except (OSError, ValueError, TypeError, AttributeError):
            self.results.put({'caminho': None, 'erro': 'O seletor do Windows não respondeu corretamente. Use o caminho do arquivo ou da pasta.'})

    def poll(self):
        try:
            return self.results.get_nowait()
        except queue.Empty:
            return None

    def cancel(self):
        if self.process.poll() is None:
            self.process.terminate()


def native_main():
    parser = argparse.ArgumentParser(description='Seletor nativo do Amplia.')
    parser.add_argument('--native', action='store_true', required=True)
    parser.add_argument('--initial', required=True)
    parser.add_argument('--folder', action='store_true')
    args = parser.parse_args()
    from tkinter import Tk, TclError, PhotoImage, filedialog
    root = None
    try:
        root = Tk()
        root.withdraw()
        icon = PhotoImage(file=str(Path(__file__).resolve().parent / 'img' / 'icone.png'))
        root.iconphoto(True, icon)
        root.update_idletasks()
        if args.folder:
            selected = filedialog.askdirectory(parent=root, title='Escolher pasta - Amplia',
                                                initialdir=args.initial, mustexist=True)
        else:
            selected = filedialog.askopenfilename(parent=root, title='Abrir imagem - Amplia', initialdir=args.initial,
                filetypes=[('Imagens', ('*.png', '*.jpg', '*.jpeg', '*.webp', '*.bmp', '*.tif', '*.tiff')),
                           ('Todos os arquivos', '*.*')])
        print(json.dumps({'caminho': selected or None}, ensure_ascii=False), flush=True)
        return 0
    except (OSError, TclError):
        print(json.dumps({'erro': 'Não foi possível abrir o seletor nativo.'}), flush=True)
        return 1
    finally:
        if root is not None:
            root.destroy()


if __name__ == '__main__':
    raise SystemExit(native_main())
