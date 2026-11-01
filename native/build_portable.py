# Amplia · © 2026 Heraldo Antunes · SPDX-License-Identifier: MIT
"""Constrói um pacote Windows local com componentes existentes; não instala nem baixa."""
import hashlib
import importlib.metadata
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / 'dist' / ('Amplia-' + (ROOT / 'VERSION').read_text(encoding='utf-8').strip())


def copy_tree(source, destination):
    shutil.copytree(source, destination, ignore=shutil.ignore_patterns('__pycache__', '*.pyc', 'test', 'tests', 'idlelib', 'ensurepip', 'turtledemo', 'pydoc_data', 'venv', 'site-packages'))


def copy_documentation(target):
    names = ['README.md', 'AUTORES.md', 'CITATION.cff', 'CHANGELOG.md',
             'docs/GUIA-DE-USO.md', 'docs/ARQUITETURA.md', 'docs/COMANDOS.md',
             '.github/SECURITY.md', '.github/CONTRIBUTING.md',
             'docs/img/icone.png', 'docs/img/fluxo.png', 'docs/img/capa.png']
    for name in names:
        destination = target / name
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / name, destination)
    licenses = target / 'licencas'
    licenses.mkdir(exist_ok=True)
    index = []
    runtime = target / 'runtime'
    for path in sorted(runtime.rglob('*')):
        if not path.is_file():
            continue
        if 'license' in path.name.lower() or 'copying' in path.name.lower():
            relative = path.relative_to(runtime).as_posix()
            name = relative.replace('/', '__')
            shutil.copy2(path, licenses / name)
            index.append(f'{name} <- runtime/{relative}')
        elif path.parent == runtime / 'tcl' and path.suffix == '.zip':
            with zipfile.ZipFile(path) as archive:
                for member in archive.infolist():
                    if member.is_dir() or member.file_size > 1_000_000:
                        continue
                    if 'license' in Path(member.filename).name.lower() or 'copying' in Path(member.filename).name.lower():
                        name = path.stem + '__' + member.filename.replace('/', '__')
                        (licenses / name).write_bytes(archive.read(member))
                        index.append(f'{name} <- runtime/tcl/{path.name}:{member.filename}')
    (licenses / 'INDICE.txt').write_text('\n'.join(index) + '\n', encoding='utf-8')


def main():
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    source_only = '--somente-fontes' in sys.argv
    updating = '--atualizar-fontes' in sys.argv or source_only
    if TARGET.exists() and not updating:
        raise SystemExit('O pacote desta versão já existe. Preserve-o antes de criar outro.')
    if updating and not (TARGET / 'MANIFESTO.json').exists():
        raise SystemExit('Pacote existente não identificado para atualização localizada.')
    if source_only and json.loads((TARGET / 'MANIFESTO.json').read_text(encoding='utf-8'))['versao'] != (ROOT / 'VERSION').read_text().strip():
        raise SystemExit('VERSION mudou. Use --atualizar-fontes para recompilar os recursos dos executáveis.')
    compiler = shutil.which('gcc')
    windres = shutil.which('windres')
    if (not compiler or not windres) and not source_only:
        raise SystemExit('GCC/windres existentes não encontrados. Nenhuma instalação foi realizada.')
    runtime = Path(sys.base_prefix)
    # Verifica a versão e os componentes antes de criar o destino.
    if sys.version_info[:2] != (3, 14) or not (runtime / 'tcl' / 'tk9.0').is_dir():
        raise SystemExit('Este construtor foi validado com Python 3.14 e Tcl/Tk 9 do Windows.')
    expected_pillow = next(line.split('==', 1)[1].strip() for line in
                           (ROOT / 'requirements-validado.txt').read_text(encoding='utf-8').splitlines()
                           if line.startswith('Pillow=='))
    if updating:
        versions = [d.version for d in importlib.metadata.distributions(path=[str(TARGET / 'runtime/Lib/site-packages')])
                    if d.metadata['Name'].lower() == 'pillow']
    else:
        versions = [importlib.metadata.version('Pillow')]
    if versions != [expected_pillow]:
        raise SystemExit(f'Pillow do runtime difere da montagem validada ({expected_pillow}). '
                         'Prepare um ambiente isolado; nenhuma dependência foi instalada.')
    required = ['PIL', 'reportlab', 'chardet']
    packages = {name: Path(importlib.util.find_spec(name).origin).parent for name in required}
    TARGET.mkdir(parents=True, exist_ok=True)
    app = TARGET / 'app'; app.mkdir(exist_ok=True)
    bundle = TARGET / 'runtime'
    if not updating:
        bundle.mkdir()
        for name in ['python.exe', 'pythonw.exe', 'python3.dll', 'python314.dll', 'vcruntime140.dll', 'vcruntime140_1.dll', 'LICENSE.txt']:
            shutil.copy2(runtime / name, bundle / name)
        copy_tree(runtime / 'Lib', bundle / 'Lib')
        copy_tree(runtime / 'DLLs', bundle / 'DLLs')
        copy_tree(runtime / 'tcl', bundle / 'tcl')
        site = bundle / 'Lib' / 'site-packages'; site.mkdir()
        for name, source in packages.items():
            copy_tree(source, site / source.name)
            for extra in source.parent.glob(name.lower() + '*.libs'):
                copy_tree(extra, site / extra.name)
        for dist_name in ['Pillow', 'reportlab', 'chardet']:
            distribution = importlib.metadata.distribution(dist_name)
            for item in distribution.files or []:
                if '.dist-info' in str(item) and ('LICENSE' in str(item).upper() or 'COPYING' in str(item).upper() or str(item).endswith('METADATA')):
                    source = Path(distribution.locate_file(item)); destination = site / str(item)
                    destination.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(source, destination)
    for name in ['amplia.py', 'amplia_desktop.py', 'amplia_picker.py', 'amplia_print.py', 'VERSION']:
        shutil.copy2(ROOT / name, app / name)
    for name in ['LICENSE', 'THIRD-PARTY-NOTICES.md']:
        shutil.copy2(ROOT / name, TARGET / name)
    shutil.copy2(ROOT / 'native' / 'boot.py', app / 'boot.py')
    (app / 'examples').mkdir(exist_ok=True); shutil.copy2(ROOT / 'examples' / 'demo.png', app / 'examples' / 'demo.png')
    (app / 'output').mkdir(exist_ok=True)
    copy_documentation(TARGET)
    for base in ('app/img', 'docs/img'):
        (TARGET / base).mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / 'docs/img/icone.png', TARGET / base / 'icone.png')
    shutil.copy2(ROOT / 'native/icone.ico', TARGET / 'icone.ico')
    if not source_only:
        version = (ROOT / 'VERSION').read_text(encoding='utf-8').strip()
        template = (ROOT / 'native/amplia.rc.in').read_text(encoding='utf-8')
        resource = template.replace('@VERSION_NUM@', version.replace('.', ',') + ',0').replace('@VERSION@', version)
        resource = resource.replace('@ICON@', (ROOT / 'native/icone.ico').as_posix())
        with tempfile.TemporaryDirectory(prefix='amplia-recurso-') as temporary:
            rc = Path(temporary) / 'amplia.rc'
            obj = Path(temporary) / 'amplia.o'
            rc.write_text(resource, encoding='utf-8')
            subprocess.run([windres, '--codepage=65001', str(rc), '-O', 'coff', '-o', str(obj)], check=True)
            for cli in (False, True):
                output = TARGET / ('Amplia.Comandos.exe' if cli else 'Amplia.exe')
                subprocess.run([compiler, str(ROOT / 'native/launcher.c'), str(obj), '-O2', '-static', '-municode',
                                *(['-DCLI'] if cli else ['-mwindows']), '-o', str(output), '-luser32'], check=True)
    (TARGET / 'LEIA-ME.txt').write_text('AMPLIA DESKTOP\n\nAbra Amplia.exe com duplo clique. Não usa navegador ou servidor.\nMantenha toda esta pasta junta: app e runtime fazem parte do aplicativo.\nNão é necessário instalar Python. Windows x64.\n\nIA: Amplia.Comandos.exe --stdio (JSON por linha).\nA interface e os comandos usam o mesmo núcleo.\nO campo de caminho evita depender do seletor de arquivos do Windows.\nPDF em 100% / tamanho real.\n', encoding='utf-8')
    records = []
    for file in sorted(TARGET.rglob('*')):
        if file.is_file() and file.name != 'MANIFESTO.json' and '__pycache__' not in file.parts and not file.is_relative_to(app / 'output'):
            records.append(dict(arquivo=file.relative_to(TARGET).as_posix(), bytes=file.stat().st_size,
                                sha256=hashlib.sha256(file.read_bytes()).hexdigest()))
    manifest = dict(projeto='Amplia', versao=(ROOT / 'VERSION').read_text().strip(), plataforma='Windows x64', python=sys.version.split()[0],
                    modo='pasta portátil com runtime incluído', arquivos=records,
                    bytes_total=sum(record['bytes'] for record in records), dependencias_instaladas=False)
    (TARGET / 'MANIFESTO.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f'Pacote criado: {TARGET} — {len(records)} arquivos, {manifest["bytes_total"] / 1024**2:.1f} MiB')


if __name__ == '__main__':
    main()
