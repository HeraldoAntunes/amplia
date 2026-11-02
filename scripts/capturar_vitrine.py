# Amplia · © 2026 Heraldo Antunes · SPDX-License-Identifier: MIT
"""Fotografa uma sessão nova do aplicativo com o cartaz de demonstração próprio."""
import json
import sys
import time
from pathlib import Path
import tkinter as tk
from PIL import ImageGrab
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from amplia_desktop import Desktop
from amplia import VERSAO


def main():
    (ROOT/'output').mkdir(exist_ok=True)
    out=ROOT/'docs/img';out.mkdir(exist_ok=True)
    root=tk.Tk();
    if root.winfo_screenwidth()<1640 or root.winfo_screenheight()<1000:
        root.destroy();raise SystemExit('Use uma tela de teste de pelo menos 1920 × 1080.')
    app=Desktop(root);root.geometry('1560x878+40+40');root.update()
    def wait():
        until=time.monotonic()+20
        while app.busy or app.timer:
            root.update();time.sleep(.015)
            assert time.monotonic()<until,'Prazo da interface excedido'
        root.update();root.update_idletasks()
    def capture(name):
        root.update();root.update_idletasks();time.sleep(.15);root.update()
        x,y=root.winfo_rootx(),root.winfo_rooty()
        ImageGrab.grab(bbox=(x,y,x+root.winfo_width(),y+root.winfo_height())).save(out/(name+'.png'))
    try:
        app.path.set(str(ROOT/'examples/mapa-serra-clara.png'));app.open_path();wait()
        app._syncing=True;app.orientation.set('Deitadas (paisagem)')
        app.sheet_values['colunas'].set('3');app.sheet_values['linhas'].set('2');app._syncing=False
        app.configure_poster();wait()
        app.output_folder.set('examples');app.output_name.set('geometria-A4.pdf')
        app.steps.select(0);capture('imagem')
        app.steps.select(1);capture('folhas');capture('capa-quadro')
        app.steps.select(2);capture('imprimir-pdf')
        app.view.current(2);app.change_view();wait();capture('folha-individual')
        app.submit('ajuda.montagem');wait();capture('montagem')
        app.submit('ajuda.montagem', {'exibir':False});wait()
        app.assembly_mode.set('Folhas inteiras (faixas brancas)');app.configure_poster();wait()
        app.steps.select(1);capture('folhas-inteiras')
        app.assembly_mode.set('Dobrar bordas para trás');app.configure_poster();wait()
        layout=app.engine.layout();assert layout['total_folhas']==6 and layout['papel_mm']==[297,210]
        (ROOT/'output/vitrine-capturas.json').write_text(json.dumps({'versao':VERSAO,'janela_cliente':[root.winfo_width(),root.winfo_height()],'papel_mm':layout['papel_mm'],'poster_mm':layout['poster_mm'],'folhas':layout['total_folhas'],'origem':'Sessão real do aplicativo com cartaz próprio','dados_sinteticos':True},ensure_ascii=False,indent=2),encoding='utf-8')
    finally:app.close(force=True)


if __name__=='__main__':main()
