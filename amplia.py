# Amplia · © 2026 Heraldo Antunes · SPDX-License-Identifier: MIT
"""Amplia: núcleo de comandos, terminal JSON e interface local. Python 3.11+."""
from __future__ import annotations

import argparse
import base64
import binascii
import hashlib
import io
import json
import math
import os
from pathlib import Path
import secrets
import sys
import tempfile
import threading
import warnings
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from PIL import Image, ImageDraw, ImageFont, ImageOps, UnidentifiedImageError
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas

ROOT = Path(__file__).resolve().parent
VERSAO = (ROOT / 'VERSION').read_text(encoding='utf-8').strip()
MM = 72 / 25.4
MAX_FILE = 40 * 1024 * 1024
MAX_PIXELS = 40_000_000
MAX_PAGES = 400
Image.MAX_IMAGE_PIXELS = MAX_PIXELS


class CommandError(Exception):
    def __init__(self, code, message, **details):
        super().__init__(message)
        self.code, self.details = code, details


def param(kind, description, required=False, **extra):
    return dict(tipo=kind, descricao=description, obrigatorio=required, **extra)


COMMANDS = {
    'programa.sobre': dict(descricao='Consulta versão, licença, privacidade, autoria e componentes.', efeito='consulta', parametros={
        'exibir': param('boolean', 'Abre a aba Sobre na interface; false volta à prévia. Padrão true.'),
    }),
    'comandos.listar': dict(descricao='Descobre comandos, parâmetros e efeitos.', efeito='consulta', parametros={}),
    'estado.obter': dict(descricao='Consulta imagem, configuração e paginação atuais.', efeito='consulta', parametros={}),
    'ajuda.montagem': dict(descricao='Explica com dados estruturados o recorte e a montagem para a configuração aplicada, mesmo sem imagem.', efeito='consulta', parametros={
        'exibir': param('boolean', 'Mostra ou fecha o painel na interface; no terminal apenas informa essa preferência. Padrão true.'),
    }),
    'imagem.abrir': dict(descricao='Abre PNG, JPEG, WebP, BMP ou TIFF; usa o primeiro quadro.', efeito='alteracao', parametros={
        'caminho': param('string', 'Caminho local da imagem. Exclusivo com dados_base64.'),
        'dados_base64': param('string', 'Bytes da imagem em base64, sem prefixo data:.'),
        'nome': param('string', 'Nome descritivo para imagem em base64.'),
    }),
    'poster.configurar': dict(descricao='Define tamanho, margens e sobreposição em mm; aplica somente após validação.', efeito='alteracao', parametros={
        'colunas': param('integer', 'Folhas na largura. Informe junto com linhas, sem dimensões em mm.'),
        'linhas': param('integer', 'Folhas na altura. Inteiros positivos; até 400 folhas no total.'),
        'largura_mm': param('number', 'Largura final: 10 a 5000 mm.'),
        'altura_mm': param('number', 'Altura final: 10 a 5000 mm. Omitida junto com largura: mantém; só largura ou só altura: deriva pela proporção da imagem.'),
        'margem_mm': param('number', 'Margem uniforme em cada lado da folha A4, >= 0.'),
        'sobreposicao_mm': param('number', 'Faixa repetida entre folhas, >= 0 e menor que a área útil.'),
        'orientacao': param('string', 'Orientação das folhas A4.', valores=['retrato', 'paisagem']),
        'marcas': param('boolean', 'Marcas de recorte e identificação na margem; exige margem >= 5 mm.'),
    }),
    'folhas.listar': dict(descricao='Calcula folhas em ordem de leitura e retângulos no pôster.', efeito='consulta', parametros={}),
    'previa.gerar': dict(descricao='Renderiza prévia PNG do pôster ou de uma folha, sem mudar a configuração.', efeito='consulta_ou_gravacao', parametros={
        'folha': param('integer', 'Número da folha, começando em 1. Omitido: mosaico do pôster.'),
        'pixels': param('integer', 'Maior dimensão da prévia: 200 a 2400 pixels. Padrão 1200.'),
        'caminho': param('string', 'Opcional: salva também o PNG neste caminho.'),
        'substituir': param('boolean', 'Permite substituir arquivo existente. Padrão false.'),
    }),
    'poster.imprimir': dict(descricao='Abre a escolha da impressora no Windows e imprime em tamanho real após confirmação.', efeito='impressao', parametros={}),
    'pdf.exportar': dict(descricao='Exporta PDF A4 em tamanho real, com uma página por folha.', efeito='gravacao', parametros={
        'caminho': param('string', 'Destino .pdf.', required=True),
        'substituir': param('boolean', 'Permite substituir arquivo existente. Padrão false.'),
    }),
    'sessao.reiniciar': dict(descricao='Descarta a imagem e restaura a configuração inicial da sessão.', efeito='alteracao', parametros={}),
}


def fail(code, message, **details):
    raise CommandError(code, message, **details)


def clean_float(value):
    return round(value, 6)


def reject_json_constant(value):
    raise ValueError('JSON não admite a constante ' + value)


def atomic_write(path, data, replace=False):
    """Não cria diretórios implicitamente; não sobrescreve por padrão."""
    path = Path(path).expanduser().resolve()
    original = ROOT / 'original'
    if path == original or original in path.parents:
        fail('ORIGINAL_PROTEGIDO', 'A pasta original é reservada para preservação.')
    if not path.parent.is_dir():
        fail('DIRETORIO_INEXISTENTE', 'A pasta de destino não existe.', caminho=str(path.parent))
    fd, temporary = tempfile.mkstemp(prefix='.amplia-', dir=path.parent)
    try:
        with os.fdopen(fd, 'wb') as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        if replace:
            os.replace(temporary, path)
        else:
            # Hard link é atômico e falha se o destino existir, sem truncá-lo.
            os.link(temporary, path)
    except FileExistsError:
        fail('ARQUIVO_EXISTENTE', 'O destino já existe; use substituir=true para substituí-lo.', caminho=str(path))
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
    return str(path)


class Amplia:
    def __init__(self):
        self.image = None
        self.image_info = None
        self.config = self.defaults()

    @staticmethod
    def defaults():
        return dict(largura_mm=400.0, altura_mm=300.0, margem_mm=10.0,
                    sobreposicao_mm=10.0, orientacao='retrato', marcas=True)

    def execute(self, request):
        """Única entrada para UI, HTTP, lote e protocolo JSON Lines."""
        command = request.get('comando') if isinstance(request, dict) else None
        response = dict(ok=False, comando=command, versao=VERSAO)
        if isinstance(request, dict) and type(request.get('id')) in (str, int):
            response['id'] = request['id']
        try:
            if not isinstance(request, dict) or set(request) - {'comando', 'parametros', 'id'}:
                fail('REQUISICAO_INVALIDA', 'Use {comando, parametros, id opcional}.')
            if 'id' in request and type(request['id']) not in (str, int):
                response.pop('id', None)
                fail('ID_INVALIDO', 'id deve ser texto ou inteiro.')
            if not isinstance(command, str) or command not in COMMANDS:
                fail('COMANDO_DESCONHECIDO', 'Consulte comandos.listar para descobrir os comandos.')
            args = request.get('parametros', {})
            self.validate_args(command, args)
            result = self.dispatch(command, args)
            response.update(ok=True, resultado=result)
        except CommandError as exc:
            response['erro'] = dict(codigo=exc.code, mensagem=str(exc), detalhes=exc.details)
        except (OSError, ValueError, OverflowError) as exc:
            response['erro'] = dict(codigo='OPERACAO_FALHOU', mensagem='Não foi possível concluir a operação.', detalhes={'motivo': str(exc)})
        return response

    @staticmethod
    def validate_args(command, args):
        if not isinstance(args, dict):
            fail('PARAMETROS_INVALIDOS', 'parametros deve ser um objeto JSON.')
        spec = COMMANDS[command]['parametros']
        for key in args:
            if key not in spec:
                fail('PARAMETRO_DESCONHECIDO', 'Parâmetro não reconhecido.', parametro=key)
        for key, field in spec.items():
            if key not in args:
                if field['obrigatorio']:
                    fail('PARAMETRO_OBRIGATORIO', 'Informe o parâmetro obrigatório.', parametro=key)
                continue
            value, kind = args[key], field['tipo']
            valid = (kind == 'boolean' and type(value) is bool or
                     kind == 'string' and isinstance(value, str) and bool(value.strip()) or
                     kind == 'number' and type(value) in (int, float) and math.isfinite(value) or
                     kind == 'integer' and type(value) is int)
            if not valid:
                fail('TIPO_INVALIDO', 'Tipo ou valor inválido.', parametro=key, esperado=kind)
            if 'valores' in field and value not in field['valores']:
                fail('VALOR_INVALIDO', 'Valor não admitido.', parametro=key, valores=field['valores'])

    def require_image(self):
        if self.image is None:
            fail('IMAGEM_NAO_ABERTA', 'Abra uma imagem primeiro com imagem.abrir.')

    def dispatch(self, command, args):
        if command == 'programa.sobre':
            return dict(nome='Amplia', versao=VERSAO, licenca='MIT', autoria='Heraldo Antunes',
                        exibir=args.get('exibir', True),
                        descricao='Amplia imagens em pôsteres para imprimir em folhas A4.',
                        privacidade=['A interface nativa processa as imagens no computador.',
                                     'Não há telemetria, envio de imagens ou consulta automática de atualização.',
                                     'A sessão fica na memória; não há recuperação automática após fechar.',
                                     'O PDF e as prévias só são gravados nos destinos solicitados.'],
                        uso_ia='Desenvolvimento com assistência do Codex, da OpenAI, sob direção humana.',
                        terceiros=['Python e Tcl/Tk', 'Pillow', 'ReportLab', 'chardet', 'Runtime Microsoft'],
                        aviso_marcas='As marcas citadas pertencem aos seus donos; o Amplia é um projeto independente, sem vínculo com elas.',
                        distribuicao='Distribuição local; ainda sem instalador ou canal público de atualização.')
        if command == 'comandos.listar':
            return dict(comandos=COMMANDS, protocolo='JSON Lines em --stdio; mesmo objeto via POST /api/comando',
                        unidades='milímetros; coordenadas das folhas a partir do canto superior esquerdo do pôster',
                        limites=dict(bytes_imagem=MAX_FILE, pixels_imagem=MAX_PIXELS, folhas=MAX_PAGES),
                        observacoes=['imagem.abrir exige exatamente um de caminho ou dados_base64.',
                                     'A imagem mantém proporção e fica centralizada dentro do tamanho final.',
                                     'Imprimir PDF em 100%, tamanho real, sem ajustar à página.'])
        if command == 'estado.obter':
            return self.state()
        if command == 'ajuda.montagem':
            return self.assembly_help(args.get('exibir', True))
        if command == 'imagem.abrir':
            return self.open_image(args)
        if command == 'sessao.reiniciar':
            self.image, self.image_info, self.config = None, None, self.defaults()
            return self.state()
        self.require_image()
        if command == 'poster.configurar':
            config = dict(self.config, **args)
            by_sheets = 'colunas' in args or 'linhas' in args
            by_mm = 'largura_mm' in args or 'altura_mm' in args
            if by_sheets and (by_mm or not {'colunas', 'linhas'} <= args.keys()):
                fail('TAMANHO_AMBIGUO', 'Informe colunas e linhas juntas, ou dimensões em mm, sem misturar.')
            if by_mm:
                config.pop('colunas', None); config.pop('linhas', None)
            if 'colunas' in config:
                cols, rows = config['colunas'], config['linhas']
                if min(cols, rows) < 1 or cols * rows > MAX_PAGES:
                    fail('GRADE_INVALIDA', 'Use quantidades positivas e no máximo 400 folhas no total.')
                pw, ph = (210, 297) if config['orientacao'] == 'retrato' else (297, 210)
                uw, uh = pw - 2 * config['margem_mm'], ph - 2 * config['margem_mm']
                overlap = config['sobreposicao_mm']
                config['largura_mm'] = uw + (cols - 1) * (uw - overlap)
                config['altura_mm'] = uh + (rows - 1) * (uh - overlap)
            ratio = self.image.width / self.image.height
            if 'largura_mm' in args and 'altura_mm' not in args:
                config['altura_mm'] = args['largura_mm'] / ratio
            elif 'altura_mm' in args and 'largura_mm' not in args:
                config['largura_mm'] = args['altura_mm'] * ratio
            self.layout(config)  # Valida tudo antes de trocar o estado.
            self.config = config
            return self.state()
        if command == 'folhas.listar':
            return self.layout()
        if command == 'previa.gerar':
            return self.preview(args)
        if command == 'poster.imprimir':
            self.require_image()
            from amplia_print import print_poster
            return print_poster(self)
        if command == 'pdf.exportar':
            if Path(args['caminho']).suffix.lower() != '.pdf':
                fail('EXTENSAO_INVALIDA', 'O destino precisa terminar em .pdf.')
            data = self.pdf_bytes()
            output = atomic_write(args['caminho'], data, args.get('substituir', False))
            return dict(caminho=output, paginas=self.layout()['total_folhas'], bytes=len(data),
                        sha256=hashlib.sha256(data).hexdigest(), impressao='100% / tamanho real; desativar ajuste à página')
        raise AssertionError(command)

    def assembly_help(self, show=True):
        margin, overlap = self.config['margem_mm'], self.config['sobreposicao_mm']
        paper_width = 210 if self.config['orientacao'] == 'retrato' else 297
        usable = paper_width - 2 * margin
        cut = ('Na folha que ficará por cima, apare somente a margem branca direita, no limite da imagem. '
               'Não corte a faixa de imagem repetida.' if margin else
               'A margem configurada é zero: não há margem de papel reservada para aparar. Preserve a imagem.')
        align = ('Coloque a folha à direita por baixo e alinhe os mesmos traços na faixa repetida. '
                 'Fixe provisoriamente antes de colar.' if overlap else
                 'Sem sobreposição, una as bordas da imagem diretamente, sem deixar frestas. '
                 'Não existe faixa repetida para ajuste.')
        return dict(exibir=show, titulo='Como cortar e montar sem perder imagem',
                    modo='sobrepor' if overlap else 'borda_a_borda',
                    configuracao=dict(margem_mm=margin, sobreposicao_mm=overlap,
                                      orientacao=self.config['orientacao'], marcas=self.config['marcas']),
                    conceitos=dict(margem='Borda do papel fora do retângulo do pôster impresso naquela folha.',
                                   sobreposicao='Faixa do desenho impressa nas duas folhas vizinhas para alinhamento.',
                                   previa='Faixas verdes e números sobre o desenho são apenas da prévia; não entram no PDF.'),
                    exemplo_horizontal_mm=dict(primeira_folha=[0, clean_float(usable)],
                                                segunda_comeca=clean_float(usable - overlap),
                                                faixa_repetida=[clean_float(usable - overlap), clean_float(usable)] if overlap else None,
                                                esquema_sem_escala=True),
                    passos=[dict(titulo='Imprima em tamanho real', texto='Use 100% / tamanho real e desative ajustar à página. Organize as folhas por linha e coluna.'),
                            dict(titulo='Prepare a borda da folha de cima', texto=cut),
                            dict(titulo='Alinhe e una as folhas', texto=align),
                            dict(titulo='Repita entre as linhas', texto=('Para uma emenda vertical, apare apenas a margem inferior da linha de cima e alinhe a próxima linha por baixo.' if margin else 'Na vertical, una as linhas preservando a imagem; não há margem reservada para aparar.'))],
                    cuidados=['Não elimine a faixa repetida das duas folhas.',
                              'Não corte brancos que façam parte do desenho ou da centralização do pôster.',
                              'Com marcas habilitadas, recorte pelo limite indicado; elas não mandam eliminar a sobreposição.',
                              'O desenho pode ficar contínuo e a emenda física do papel ainda ser visível.'],
                    folha_unica=bool(self.image is not None and self.layout()['total_folhas'] == 1),
                    impressao_fisica_validada=False)

    def open_image(self, args):
        if ('caminho' in args) == ('dados_base64' in args):
            fail('ORIGEM_INVALIDA', 'Informe exatamente um de caminho ou dados_base64.')
        if 'caminho' in args:
            path = Path(args['caminho']).expanduser().resolve()
            if path.stat().st_size > MAX_FILE:
                fail('IMAGEM_GRANDE', 'Arquivo excede 40 MiB.')
            with path.open('rb') as stream:
                raw = stream.read(MAX_FILE + 1)
            name = path.name
        else:
            if len(args['dados_base64']) > (MAX_FILE * 4 // 3 + 8):
                fail('IMAGEM_GRANDE', 'Arquivo excede 40 MiB.')
            try:
                raw = base64.b64decode(args['dados_base64'], validate=True)
            except (ValueError, binascii.Error):
                fail('BASE64_INVALIDO', 'dados_base64 não contém base64 válido.')
            name = args.get('nome', 'imagem')
        if len(raw) > MAX_FILE:
            fail('IMAGEM_GRANDE', 'Arquivo excede 40 MiB.')
        try:
            with warnings.catch_warnings():
                warnings.simplefilter('error', Image.DecompressionBombWarning)
                with Image.open(io.BytesIO(raw), formats=['PNG', 'JPEG', 'WEBP', 'BMP', 'TIFF']) as source:
                    if source.format not in {'PNG', 'JPEG', 'WEBP', 'BMP', 'TIFF'}:
                        fail('FORMATO_NAO_SUPORTADO', 'Use PNG, JPEG, WebP, BMP ou TIFF.')
                    if source.width * source.height > MAX_PIXELS:
                        fail('IMAGEM_GRANDE', 'A imagem excede 40 milhões de pixels.')
                    image_format = source.format
                    frame_count = getattr(source, 'n_frames', 1)
                    normalized = ImageOps.exif_transpose(source).convert('RGBA')
                    image = Image.new('RGB', normalized.size, 'white')
                    image.paste(normalized, mask=normalized.getchannel('A'))
        except (Image.DecompressionBombError, Image.DecompressionBombWarning):
            fail('IMAGEM_GRANDE', 'A imagem excede o limite de pixels.')
        except (UnidentifiedImageError, OSError, SyntaxError):
            fail('IMAGEM_INVALIDA', 'Não foi possível decodificar a imagem.')
        config = self.defaults()
        # A primeira prévia já corresponde às quatro folhas do modo simples.
        useful_w, useful_h = 210 - 2 * config['margem_mm'], 297 - 2 * config['margem_mm']
        config.update(colunas=2, linhas=2,
                      largura_mm=2 * useful_w - config['sobreposicao_mm'],
                      altura_mm=2 * useful_h - config['sobreposicao_mm'])
        info = dict(nome=name, largura_px=image.width, altura_px=image.height,
                    formato=image_format, quadros=frame_count, sha256=hashlib.sha256(raw).hexdigest())
        self.image, self.image_info, self.config = image, info, config
        return self.state()

    def state(self):
        return dict(imagem=self.image_info, configuracao=dict(self.config),
                    folhas=self.layout() if self.image is not None else None)

    def layout(self, config=None):
        cfg = config if config is not None else self.config
        w, h, margin, overlap = (float(cfg[k]) for k in ('largura_mm', 'altura_mm', 'margem_mm', 'sobreposicao_mm'))
        if not 10 <= w <= 5000 or not 10 <= h <= 5000:
            fail('TAMANHO_INVALIDO', 'Largura e altura devem ficar entre 10 e 5000 mm.')
        pw, ph = (210.0, 297.0) if cfg['orientacao'] == 'retrato' else (297.0, 210.0)
        uw, uh = pw - 2 * margin, ph - 2 * margin
        if margin < 0 or min(uw, uh) <= 0:
            fail('MARGEM_INVALIDA', 'A margem deve ser não negativa e deixar área útil na folha.')
        if cfg['marcas'] and margin < 5:
            fail('MARGEM_PARA_MARCAS', 'Use margem de pelo menos 5 mm ou desative as marcas.')
        if overlap < 0 or overlap >= min(uw, uh):
            fail('SOBREPOSICAO_INVALIDA', 'A sobreposição deve ser não negativa e menor que a largura e altura úteis.')
        cols = max(1, math.ceil((w - overlap) / (uw - overlap) - 1e-10))
        rows = max(1, math.ceil((h - overlap) / (uh - overlap) - 1e-10))
        if cols * rows > MAX_PAGES:
            fail('FOLHAS_DEMAIS', 'O pôster excede o limite de 400 folhas; reduza tamanho, margem ou sobreposição.', folhas=cols * rows)
        pages = []
        for row in range(rows):
            for col in range(cols):
                x, y = col * (uw - overlap), row * (uh - overlap)
                pages.append(dict(numero=len(pages) + 1, linha=row + 1, coluna=col + 1,
                                  x_mm=clean_float(x), y_mm=clean_float(y),
                                  largura_mm=clean_float(min(uw, w - x)), altura_mm=clean_float(min(uh, h - y))))
        scale = min(w / self.image.width, h / self.image.height) if self.image is not None else 1
        iw, ih = (self.image.width * scale, self.image.height * scale) if self.image is not None else (w, h)
        dpi = 25.4 / scale if self.image is not None else 0
        return dict(papel='A4', papel_mm=[pw, ph], area_util_mm=[clean_float(uw), clean_float(uh)],
                    poster_mm=[w, h], margem_mm=margin, sobreposicao_mm=overlap,
                    colunas=cols, linhas=rows, total_folhas=cols * rows,
                    imagem_no_poster_mm=dict(x=clean_float((w - iw) / 2), y=clean_float((h - ih) / 2),
                                            largura=clean_float(iw), altura=clean_float(ih)),
                    resolucao_efetiva_dpi=round(dpi, 1),
                    avisos=['Resolução abaixo de 100 dpi no tamanho final.'] if dpi and dpi < 100 else [], folhas=pages)

    @staticmethod
    def font(size):
        try:
            return ImageFont.truetype('DejaVuSans.ttf', size)
        except OSError:
            return ImageFont.load_default(size=size)

    def render(self, pixels, page_number=None):
        layout = self.layout()
        w, h = layout['poster_mm']
        box = layout['imagem_no_poster_mm']
        if page_number is None:
            scale = pixels / max(w, h)
            image = Image.new('RGB', (max(1, round(w * scale)), max(1, round(h * scale))), 'white')
            image.paste(self.image.resize((max(1, round(box['largura'] * scale)), max(1, round(box['altura'] * scale))), Image.Resampling.LANCZOS),
                        (round(box['x'] * scale), round(box['y'] * scale)))
            draw = ImageDraw.Draw(image, 'RGBA')
            for page in layout['folhas']:
                x, y = page['x_mm'] * scale, page['y_mm'] * scale
                right, bottom = (page['x_mm'] + page['largura_mm']) * scale, (page['y_mm'] + page['altura_mm']) * scale
                if page['coluna'] > 1 and layout['sobreposicao_mm']:
                    draw.rectangle((x, y, min(right, x + layout['sobreposicao_mm'] * scale), bottom), fill=(31, 110, 67, 45))
                if page['linha'] > 1 and layout['sobreposicao_mm']:
                    draw.rectangle((x, y, right, min(bottom, y + layout['sobreposicao_mm'] * scale)), fill=(31, 110, 67, 45))
                # Uma faixa final menor que um pixel ainda precisa de contorno válido.
                draw.rectangle((x, y, max(x, right - 1), max(y, bottom - 1)), outline=(31, 110, 67, 220), width=2)
                draw.rectangle((x + 4, y + 4, x + 58, y + 29), fill=(255, 255, 255, 230))
                draw.text((x + 10, y + 6), str(page['numero']), font=self.font(17), fill=(20, 60, 40, 255))
            return image
        page = layout['folhas'][page_number - 1]
        pw, ph = layout['papel_mm']
        scale = pixels / max(pw, ph)
        image = Image.new('RGB', (round(pw * scale), round(ph * scale)), 'white')
        # Transforma diretamente a imagem original: evita um bitmap gigante do pôster.
        margin = self.config['margem_mm']
        target = (max(1, round(page['largura_mm'] * scale)), max(1, round(page['altura_mm'] * scale)))
        sx, sy = self.image.width / box['largura'], self.image.height / box['altura']
        region = self.image.transform(target, Image.Transform.AFFINE,
            (sx / scale, 0, (page['x_mm'] - box['x']) * sx,
             0, sy / scale, (page['y_mm'] - box['y']) * sy), Image.Resampling.BICUBIC, fillcolor='white')
        image.paste(region, (round(margin * scale), round(margin * scale)))
        if self.config['marcas']:
            draw = ImageDraw.Draw(image)
            self.draw_raster_marks(draw, page, layout, scale)
        return image

    def draw_raster_marks(self, draw, page, layout, scale):
        margin = self.config['margem_mm']
        pw, ph = layout['papel_mm']
        for x in (margin, margin + page['largura_mm']):
            for y in (margin, margin + page['altura_mm']):
                # As marcas ficam do lado de fora do retângulo da imagem.
                dx = -1 if x == margin else 1
                dy = -1 if y == margin else 1
                draw.line(((x + dx * .5) * scale, y * scale, (x + dx * 3) * scale, y * scale), fill='#666666')
                draw.line((x * scale, (y + dy * .5) * scale, x * scale, (y + dy * 3) * scale), fill='#666666')
        draw.text((margin * scale, (ph - margin / 2) * scale),
                  f"Amplia | {page['numero']}/{layout['total_folhas']} | L{page['linha']} C{page['coluna']} | 100%",
                  font=self.font(max(9, round(2.4 * scale))), fill='#555555', anchor='lm')

    def preview(self, args):
        pixels = args.get('pixels', 1200)
        if not 200 <= pixels <= 2400:
            fail('PREVIA_INVALIDA', 'pixels deve ficar entre 200 e 2400.')
        number = args.get('folha')
        layout = self.layout()
        if number is not None and not 1 <= number <= layout['total_folhas']:
            fail('FOLHA_INVALIDA', 'A folha solicitada não existe.', total=layout['total_folhas'])
        if 'caminho' in args and Path(args['caminho']).suffix.lower() != '.png':
            fail('EXTENSAO_INVALIDA', 'O destino da prévia precisa terminar em .png.')
        image = self.render(pixels, number)
        stream = io.BytesIO()
        image.save(stream, 'PNG')
        data = stream.getvalue()
        result = dict(formato='png', largura_px=image.width, altura_px=image.height, folha=number,
                      dados_base64=base64.b64encode(data).decode('ascii'), folhas=layout)
        if 'caminho' in args:
            result['caminho'] = atomic_write(args['caminho'], data, args.get('substituir', False))
        return result

    def pdf_bytes(self):
        layout = self.layout()
        pw, ph = layout['papel_mm']
        margin = self.config['margem_mm']
        box = layout['imagem_no_poster_mm']
        output = io.BytesIO()
        pdf = canvas.Canvas(output, pagesize=(pw * MM, ph * MM), invariant=True, pageCompression=1)
        pdf.setTitle('Amplia - pôster em folhas A4')
        pdf.setAuthor('Amplia')
        reader = ImageReader(self.image)
        for page in layout['folhas']:
            pdf.saveState()
            clip = pdf.beginPath()
            clip.rect(margin * MM, (ph - margin - page['altura_mm']) * MM,
                      page['largura_mm'] * MM, page['altura_mm'] * MM)
            pdf.clipPath(clip, stroke=0)
            pdf.drawImage(reader, (margin + box['x'] - page['x_mm']) * MM,
                          (ph - margin - box['y'] + page['y_mm'] - box['altura']) * MM,
                          width=box['largura'] * MM, height=box['altura'] * MM)
            pdf.restoreState()
            if self.config['marcas']:
                pdf.setStrokeColorRGB(.4, .4, .4)
                pdf.setLineWidth(.25)
                for x in (margin, margin + page['largura_mm']):
                    for y in (margin, margin + page['altura_mm']):
                        dx = -1 if x == margin else 1
                        dy = -1 if y == margin else 1
                        pdf.line((x + dx * .5) * MM, (ph - y) * MM, (x + dx * 3) * MM, (ph - y) * MM)
                        pdf.line(x * MM, (ph - y - dy * .5) * MM, x * MM, (ph - y - dy * 3) * MM)
                pdf.setFont('Helvetica', 7)
                pdf.setFillColorRGB(.3, .3, .3)
                pdf.drawString(margin * MM, (margin / 2 - 1) * MM,
                               f"Amplia | {page['numero']}/{layout['total_folhas']} | L{page['linha']} C{page['coluna']} | 100% tamanho real")
            pdf.showPage()
        pdf.save()
        return output.getvalue()


class LocalServer(ThreadingHTTPServer):
    daemon_threads = True

    def __init__(self, address):
        super().__init__(address, Handler)
        self.engine = Amplia()
        self.lock = threading.Lock()
        self.token = secrets.token_urlsafe(32)
        self.last_pdf = None


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *_args):
        pass

    def valid_host(self):
        return self.headers.get('Host') in {f'127.0.0.1:{self.server.server_port}', f'localhost:{self.server.server_port}'}

    def send(self, status, data, content_type='application/json; charset=utf-8', **headers):
        self.send_response(status)
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Length', str(len(data)))
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('X-Frame-Options', 'DENY')
        self.send_header('Referrer-Policy', 'no-referrer')
        self.send_header('Cross-Origin-Resource-Policy', 'same-origin')
        self.send_header('Content-Security-Policy', "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; connect-src 'self'; object-src 'none'; form-action 'none'; frame-ancestors 'none'; base-uri 'none'")
        for key, value in headers.items():
            self.send_header(key.replace('_', '-'), value)
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        if not self.valid_host():
            return self.send(403, b'{"ok":false}')
        if self.path == '/':
            body = (ROOT / 'web' / 'index.html').read_text(encoding='utf-8').replace('__TOKEN__', self.server.token)
            return self.send(200, body.encode('utf-8'), 'text/html; charset=utf-8')
        if self.path == '/app.js':
            return self.send(200, (ROOT / 'web' / 'app.js').read_bytes(), 'text/javascript; charset=utf-8')
        if self.path == '/style.css':
            return self.send(200, (ROOT / 'web' / 'style.css').read_bytes(), 'text/css; charset=utf-8')
        if self.path == '/poster.pdf' and self.server.last_pdf is not None:
            return self.send(200, self.server.last_pdf, 'application/pdf', Content_Disposition='attachment; filename="amplia-poster.pdf"')
        self.send(404, b'{"ok":false,"erro":{"codigo":"NAO_ENCONTRADO"}}')

    def do_POST(self):
        origin = self.headers.get('Origin')
        allowed_origin = {f'http://127.0.0.1:{self.server.server_port}', f'http://localhost:{self.server.server_port}'}
        if (not self.valid_host() or not secrets.compare_digest(self.headers.get('X-Amplia-Token', '').encode('utf-8'), self.server.token.encode('ascii'))
                or self.headers.get('Sec-Fetch-Site') == 'cross-site'
                or origin is not None and origin not in allowed_origin):
            # No Windows, fechar com um corpo pequeno ainda pendente pode apagar o 403
            # com um reset TCP. Drena só até 8 KiB, com prazo curto e sem interpretar JSON.
            try:
                pending = int(self.headers.get('Content-Length', '0'))
                if 0 < pending <= 8192:
                    self.connection.settimeout(.25)
                    self.rfile.read(pending)
            except (ValueError, OSError):
                self.close_connection = True
            return self.send(403, b'{"ok":false,"erro":{"codigo":"ACESSO_NEGADO"}}')
        if self.path != '/api/comando':
            return self.send(404, b'{"ok":false}')
        try:
            length = int(self.headers.get('Content-Length', '0'))
            if not 0 < length <= MAX_FILE * 4 // 3 + 8192:
                return self.send(413, b'{"ok":false,"erro":{"codigo":"REQUISICAO_GRANDE"}}')
            request = json.loads(self.rfile.read(length), parse_constant=reject_json_constant)
            with self.server.lock:
                response = self.server.engine.execute(request)
                if response['ok'] and request['comando'] == 'pdf.exportar':
                    self.server.last_pdf = Path(response['resultado']['caminho']).read_bytes()
                    response['resultado']['download_url'] = '/poster.pdf'
                elif response['ok'] and request['comando'] in {'imagem.abrir', 'poster.configurar', 'sessao.reiniciar'}:
                    self.server.last_pdf = None
            return self.send(200, json.dumps(response, ensure_ascii=False).encode('utf-8'))
        except (ValueError, UnicodeDecodeError):
            return self.send(400, b'{"ok":false,"erro":{"codigo":"JSON_INVALIDO"}}')


def main(argv=None):
    parser = argparse.ArgumentParser(description='Amplia: pôster A4 por mouse ou comandos JSON.')
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('--serve', action='store_true', help='Abre o servidor local da interface.')
    mode.add_argument('--stdio', action='store_true', help='Uma requisição e uma resposta JSON por linha; mantém a sessão.')
    mode.add_argument('--batch', type=Path, help='Arquivo JSON contendo uma lista de comandos; mantém a sessão.')
    parser.add_argument('--port', type=int, default=8765)
    args = parser.parse_args(argv)
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stdin.reconfigure(encoding='utf-8')
    if args.serve:
        (ROOT / 'output').mkdir(exist_ok=True)
        server = LocalServer(('127.0.0.1', args.port))
        print(f'Amplia em http://127.0.0.1:{server.server_port} - Ctrl+C para encerrar.', flush=True)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass
        finally:
            server.server_close()
        return 0
    engine = Amplia()
    failed = False
    if args.batch:
        try:
            requests = json.loads(args.batch.read_text(encoding='utf-8-sig'), parse_constant=reject_json_constant)
            if not isinstance(requests, list):
                raise ValueError('O lote precisa ser uma lista JSON.')
        except (OSError, ValueError) as exc:
            print(json.dumps(dict(ok=False, erro=dict(codigo='LOTE_INVALIDO', mensagem=str(exc))), ensure_ascii=False))
            return 1
        for request in requests:
            result = engine.execute(request)
            print(json.dumps(result, ensure_ascii=False, allow_nan=False))
            if not result['ok']:
                return 1  # Não continua gravando com parâmetros anteriores após erro.
    else:
        for line in sys.stdin:
            if not line.strip():
                continue
            try:
                result = engine.execute(json.loads(line, parse_constant=reject_json_constant))
            except ValueError:
                result = dict(ok=False, erro=dict(codigo='JSON_INVALIDO', mensagem='Envie um objeto JSON válido por linha.'))
            failed |= not result['ok']
            print(json.dumps(result, ensure_ascii=False, allow_nan=False), flush=True)
    return int(failed)


if __name__ == '__main__':
    raise SystemExit(main())
