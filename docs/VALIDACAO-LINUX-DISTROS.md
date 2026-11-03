<!-- Amplia · © 2026 Heraldo Antunes · SPDX-License-Identifier: MIT -->
# Validação do Amplia em outras distribuições Linux

Relatório da Gestão dos Programas Livres. Ramo `validacao-linux-distros`, criado a partir da tag
**v0.6.1-rc.1** (commit `edf5213`). **Nenhum arquivo do programa foi alterado.** Os defeitos estão
descritos, não corrigidos. Os defeitos D1 a D3 do ramo `validacao-linux` (Python 3.10 no Ubuntu 22.04,
botões em 1366x768, acento na ajuda F1) já foram corrigidos numa versão local e **não** são repetidos aqui.

- **Data:** 03/11/2026
- **Onde:** sessão na nuvem, contêineres Docker, tela virtual Xvfb 1920x1080
- **Dados:** só imagens sintéticas geradas pelos roteiros (gradientes, cores lisas, ruído)

## Resumo

| Item | Resultado |
|---|---|
| 1. Suíte em Ubuntu 24.04, Debian 12 e Fedora 45 | **Passou com ressalva** nos três: 68 de 72 passam; os mesmos 3 testes de impressão do Windows falham (`ctypes.WinDLL`); 1 pulado (portátil do Windows) |
| 2. Medidas das folhas e das guias (A4) | **Passou:** 8 PDFs, 48 folhas, 0 falhas; PDFs idênticos byte a byte nos três sistemas |
| 2b. Papel Carta e A3 | **Não se aplica:** o programa só oferece A4 (o README promete A4); o pedido é recusado com erro claro |
| 3. Casos de borda | 11 passaram e 4 falharam nos três sistemas; viraram os defeitos N1, N2 e N3 |
| 4. Defeitos novos | **N1 (alta):** cinza de 16 bits vira branco. **N2 (média):** nome em Latin-1 derruba o `--stdio`. **N3 (baixa):** arquivo inexistente sem código próprio |

## Ambiente

| Sistema | Imagem e digest | Python e Tk | Como o Python foi instalado |
|---|---|---|---|
| Ubuntu 24.04.5 | `ubuntu:24.04` `sha256:fe81560990fae86dc4743202b2cb4d3df98d0bcf949173cecef15ce1127ef852` | 3.12.3, Tk 8.6 | `apt install python3 python3-venv python3-tk xvfb poppler-utils` |
| Debian 12.15 | `python:3.11-bookworm` `sha256:84fa927127b46670e768371d1ad1be271d57ba93a6fbb3479045c7c6c452432f` | 3.11.18, Tk 8.6 | Python da própria imagem oficial |
| Fedora 45 | `fedora:latest` `sha256:a7d72ba2745b100a3351087472e5ee7b2450af7cf331e7673007e3817612839c` | 3.12.16, Tk 9.0 | Python oficial portátil (`uv python install 3.12`) |

Nos três: `pip install -r requirements-validado.txt` instalou Pillow 13.0.0, ReportLab 4.1.0, pypdf 6.21.4 e PyMuPDF 1.27.2.3.
As imagens vieram de `mirror.gcr.io`, porque o Docker Hub limita downloads.

**Limites desta sessão (não são defeitos do Amplia):**

- A política de rede bloqueou `deb.debian.org` e `mirrors.fedoraproject.org` (o proxy respondeu 403).
  Por isso o `apt` do Debian e o `dnf` do Fedora não funcionaram. No Debian foi usado o Python da imagem
  oficial `python:3.11-bookworm`, base Debian 12. No Fedora 45, que não traz Python, foi usado o Python
  portátil do projeto python-build-standalone, instalado pelo `uv`. Vale repetir com `apt install python3-tk`
  e `dnf install python3-tkinter` quando houver acesso a esses repositórios.
- No espelho, o Fedora 43 e o 44 não baixaram; o 40, o 41, o 42 e o `latest` (45) baixaram. Foi usado o 45, o mais novo.
- No Debian e no Fedora a tela Xvfb foi a da máquina hospedeira, pelo soquete `/tmp/.X11-unix`.
- Sem gerenciador de janelas e sem impressora: a impressão direta é só do Windows, como o README avisa.

## 1. Suíte de testes

Mesmo comando do CI: `python -m unittest discover -s tests -v`, com tela virtual.

| Sistema | Executados | Passaram | Erros | Pulados |
|---|---|---|---|---|
| Ubuntu 24.04 | 72 | 68 | 3 | 1 |
| Debian 12 | 72 | 68 | 3 | 1 |
| Fedora 45 | 72 | 68 | 3 | 1 |

Os 3 erros são os mesmos já registrados em `validacao-linux`: em `tests/test_print.py`, os testes fazem
`patch('amplia_print.ct.WinDLL')` e `ctypes.WinDLL` só existe no Windows. O teste pulado precisa do portátil
do Windows. No Fedora, com Tk 9.0 (a mesma versão do portátil do Windows), todos os testes de interface passaram.

## 2. Medidas das folhas e das guias

Roteiro `roteiros/medidas.py`. Imagem sintética de 1200x800 px (gradiente com azul fixo, que não se
confunde com o branco nem com as guias cinza). Grade 3x2, guias ligadas, em 8 combinações:
modo `dobrar` ou `inteiras`, `retrato` ou `paisagem`, margem/faixa de 10/10 mm e de 5/15 mm.
Cada PDF foi lido com **PyMuPDF** (linhas vetoriais e página renderizada a 150 dpi) e com **pdfinfo**.

O programa **não tem guias de corte**: a montagem é sem recorte. As guias reais são o tracejado de dobra
e os sinais **+** de alinhamento, e foram essas que foram medidas.

| O que foi conferido | Esperado (COMANDOS.md e GUIA-DE-USO.md) | Medido |
|---|---|---|
| Tamanho da página (pdfinfo) | A4 | `595.276 x 841.89 pts` em retrato e `841.89 x 595.276 pts` em paisagem, em todas as páginas |
| Tamanho da página (PyMuPDF) | 210 x 297 mm ou 297 x 210 mm | igual, com erro menor que 0,01 mm |
| Área da imagem em cada folha | área útil a partir da margem, cortada onde a imagem centralizada termina | igual, com erro menor que 0,6 mm (resolução da renderização) |
| Tracejado de dobra | margem esquerda a partir da 2ª coluna e margem de cima a partir da 2ª linha | vertical em x = margem - 0,15 mm (9,85 ou 4,85 mm), de y = margem até altura - margem; horizontal em y = margem - 0,15 mm |
| Sinal **+** de alinhamento | na folha anterior, onde chega a borda dobrada da vizinha | x = largura - margem - faixa: 190 mm (retrato) e 277 mm (paisagem), nas duas combinações; y = altura - margem - faixa para a linha de baixo |
| Continuidade do desenho | o ponto do **+** em A1 mostra o mesmo desenho que o início de A2 | cores iguais (diferença de até 6 em 255) em 1, 3 e 5 mm além do sinal |
| Folhas inteiras | sem tracejado; desenho continua sem repetir | nenhum tracejado; a borda de A1 e o início de A2 têm cores vizinhas |
| Guias fora do desenho | guias só na margem branca | nenhum sinal **+** dentro da área da imagem |

**Carta, A3 e Letter:** `poster.configurar` com `papel` é recusado com `PARAMETRO_DESCONHECIDO`
("Parâmetro não reconhecido."). O README, o guia e o catálogo de comandos só falam em A4, então
não é defeito. Se outros papéis forem desejados, é uma funcionalidade nova.

SHA-256 dos 8 PDFs, iguais no Ubuntu 24.04, no Debian 12 e no Fedora 45:

| PDF | SHA-256 |
|---|---|
| dobrar, retrato, 10/10 | `26ac3c3ce22824e0deee0245e40eec357bf8ac85f55626768273fa13490fe692` |
| dobrar, retrato, 5/15 | `f55a47ab7d14eb5bd44829a2975d17f889ce494394d9649820cb9c593b62c0d1` |
| dobrar, paisagem, 10/10 | `4f3955c40190a8a18f8f5aec5bc6061f55bd00e2fbe26aeb264cbc2b8f0d3918` |
| dobrar, paisagem, 5/15 | `41d50382428755f778beac0294334ef38e99b103311cbe084777f782cf0729ca` |
| inteiras, retrato, 10/10 | `79fa3cb4563a8358349cbb5236f88180f81ee5999619271bf8e69d17d05da731` |
| inteiras, retrato, 5/15 | `2a0b290633a733199b3a4c79b25c58493d3a2268183be6b4e15d80d753c3d2f1` |
| inteiras, paisagem, 10/10 | `8a84b493b3b36337812ab070d1039224ddaacc59f2a35d8de67567bc33b1b8c4` |
| inteiras, paisagem, 5/15 | `a090b7604dc76a377d32c1606d858d47500c9978ddb7be0c82cf68f382e0ee1c` |

## 3. Casos de borda

Roteiros `roteiros/bordas.py` (núcleo e `--stdio`) e `roteiros/gui_acentos.py` (interface).
O resultado foi o mesmo nos três sistemas.

| Caso | Resultado | Detalhe |
|---|---|---|
| Imagem grande 6324x6324 (39,99 milhões de px) | Passou | abre e exporta 9 folhas em 3 a 4,5 s |
| Imagem 6325x6325 (acima de 40 milhões) | Passou | recusa: "A imagem excede o limite de pixels." |
| Arquivo de 40,2 MiB | Passou | recusa: "Arquivo excede 40 MiB." |
| Imagem 1x1 e 2x3 px | Passou | abre, gera prévia e PDF, com aviso de resolução baixa |
| Imagem 1x3000 px com largura de 500 mm | Passou | recusa: a altura derivada passaria de 5000 mm |
| PNG RGBA com 50% de transparência | Passou | vermelho a 50% vira (255, 127, 127) sobre branco; transparente vira branco |
| PNG de paleta com tRNS | Passou | índice transparente vira branco; os outros mantêm a cor |
| JPEG com EXIF de orientação 1 a 8 | Passou | tamanho e canto marcado corretos nas 8; também em PNG, WebP e TIFF com orientação 6 |
| Nome com acento (NFC), pasta "Pôster Ação" | Passou | abre e salva "saída NFC é.pdf" pelo núcleo e pela interface |
| Nome com acento em NFD (como vem do macOS) | Passou | abre e salva |
| Interface: nome sugerido do PDF | Passou | `coração.png` sugere `coração-poster.pdf` e salva |
| Interface: nome em Latin-1 (`caf\xe9.png`) | Passou | abre e salva `caf\xe9-poster.pdf` |
| `--stdio`: nome em Latin-1 | **Falhou** | o processo cai (N2) |
| PNG e TIFF em cinza de 16 bits | **Falhou** | a imagem vira branca (N1) |
| Arquivo inexistente pelo contrato JSON | **Falhou** (baixa) | erro genérico `OPERACAO_FALHOU` (N3) |

## Defeitos novos

Os testes que falham estão em `docs/validacao-linux-distros/test_defeitos_distros.py`, fora de `tests/`
para não quebrar o CI antes da correção. Na raiz do repositório:

```bash
python docs/validacao-linux-distros/test_defeitos_distros.py -v
```

Resultado na v0.6.1-rc.1: `Ran 4 tests` e `FAILED (failures=4)`.

### N1. Imagem em cinza de 16 bits vira página branca

**Gravidade:** alta. A saída fica errada sem nenhum aviso: o PDF sai com as folhas em branco.
Não depende do Linux (acontece na mesma linha de código no Windows). Scanners e programas de
fotografia e de ciência gravam com frequência TIFF e PNG em cinza de 16 bits.

Passo a passo:

1. Crie um PNG ou TIFF em cinza de 16 bits, por exemplo com valor 20000 de 65535 (cerca de 30% de brilho):
   `python -c "from PIL import Image; im=Image.new('I;16',(200,200)); im.putdata([20000]*40000); im.save('cinza16.png')"`
2. Abra no Amplia: `{"comando":"imagem.abrir","parametros":{"caminho":"cinza16.png"}}`.
3. Exporte: `{"comando":"pdf.exportar","parametros":{"caminho":"cinza16.pdf"}}`.

Esperado: folhas cinza-escuro, perto de (78, 78, 78). Obtido: (255, 255, 255) na imagem aberta e no PDF.
O mesmo vale para TIFF em 16 bits e para inteiros de 32 bits (modo `I`).
A abertura responde `ok:true`, sem aviso.

Causa provável: `amplia.py:340` faz `ImageOps.exif_transpose(source).convert('RGBA')`. O Pillow converte
`I;16` e `I` para 8 bits cortando os valores acima de 255, sem reescalar; quase todo cinza de 16 bits passa de 255 e vira branco.

Testes que falham: `test_n1_png_cinza_16_bits_mantem_o_brilho` e `test_n1_tiff_cinza_16_bits_mantem_o_brilho_no_pdf`.

### N2. Nome de arquivo em Latin-1 derruba o processo `--stdio`

**Gravidade:** média. Atinge automações (`--stdio`, `--batch`, console de comandos) no Linux e no macOS.
A interface não é afetada. Nomes em Latin-1 aparecem em arquivos vindos de ZIP, pendrive ou servidores antigos.

Passo a passo:

1. Crie um arquivo cujo nome tenha o byte 0xE9 (é em Latin-1):
   `python -c "open(b'caf\xe9.png','wb').write(open('examples/demo.png','rb').read())"`
2. Envie para um mesmo processo `python amplia.py --stdio`:
   `{"comando":"imagem.abrir","parametros":{"caminho":"caf\udce9.png"}}` e depois `{"comando":"estado.obter"}`.

Esperado: duas respostas JSON e o processo continua. Obtido: nenhuma resposta, código de saída 1 e
`UnicodeEncodeError: 'utf-8' codec can't encode character '\udce9' ... surrogates not allowed` em
`amplia.py:794`, no `print(json.dumps(result, ensure_ascii=False, ...))` de `main()`. A imagem chega a
abrir, mas o nome (`resultado.imagem.nome`) não pode ser escrito em UTF-8, e a sessão inteira se perde.

Teste que falha: `test_n2_stdio_com_nome_em_latin1_responde_e_continua`.

### N3. Arquivo inexistente responde com erro genérico no contrato JSON

**Gravidade:** baixa. A interface já troca a mensagem por "Não foi possível abrir a imagem. Confira se o
arquivo existe e se você tem acesso." O problema fica só para automações e agentes.

Passo a passo:

1. `{"comando":"imagem.abrir","parametros":{"caminho":"nao-existe.png"}}` no `--stdio`.

Esperado: um código próprio (por exemplo de arquivo não encontrado), como já existe para `IMAGEM_GRANDE`
e `IMAGEM_INVALIDA`. Obtido: `OPERACAO_FALHOU`, "Não foi possível concluir a operação.", e o motivo em inglês
nos detalhes (`[Errno 2] No such file or directory`). O mesmo acontece quando o caminho é uma pasta (`[Errno 21] Is a directory`).
Causa: `amplia.py:315` (`path.stat()`) fica fora do tratamento de erro e cai no `except (OSError, ...)` genérico de `execute`.

Teste que falha: `test_n3_arquivo_inexistente_tem_codigo_proprio`.

## Como repetir

Os roteiros estão em `docs/validacao-linux-distros/roteiros/`. Exemplo para o Ubuntu 24.04, na raiz do repositório:

```bash
docker run --rm --network host -e MODO=apt \
  -v "$PWD":/src:ro -v "$PWD/docs/validacao-linux-distros/roteiros":/val:ro -v "$PWD/saida":/out \
  ubuntu:24.04 bash /val/dentro.sh ubuntu-24.04
```

Para o Debian use `-e MODO=imagem` com `python:3.11-bookworm`; para o Fedora use `-e MODO=uv` com o
binário do `uv` montado em `/usr/local/bin/uv`. Sem tela no contêiner, passe `-e DISPLAY_EXTERNO=:88`
e `-v /tmp/.X11-unix:/tmp/.X11-unix` com um Xvfb rodando fora. Nesta sessão foi preciso também
`-e PIP_CERT=/ca.crt`, só por causa do proxy da nuvem.
