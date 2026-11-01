<!-- Amplia · © 2026 Heraldo Antunes · SPDX-License-Identifier: MIT -->
# Imagens e capa do README

A capa segue o modelo visual comum dos Programas Livres: fundo creme liso,
ícone real, nome e uma descrição curta à esquerda; captura real do programa
à direita. O [Giz Livre](https://github.com/HeraldoAntunes/giz-livre) usa o mesmo
modelo. A variante com a janela inteira preserva a última coluna do cartaz e
os controles do Amplia.

## Capa

- Imagem principal: **1640 × 820 px**; prévia social: **1280 × 640 px**.
- Fundo `#f3f0e8`, texto `#1b1f1d`, descrição `#4b524e`.
- Ícone em `(96, 300)`, com 84 px; nome em Segoe UI Semibold, 92 px.
- Descrição em `(99, 512)`, Segoe UI 29 px, em duas linhas.
- Janela em `(640, 140)`, largura de 960 px, cantos de 14 px e sombra discreta.
- Sem número de versão, contadores ou frase promocional fora da captura.

`capa-quadro.png` é uma captura do aplicativo, não uma interface desenhada ou
reconstruída para a imagem. O gerador apenas coloca essa captura e o ícone no
layout. O aplicativo continua identificado como versão de teste nas próprias telas.

## Exemplo didático

O cartaz **Geometria: áreas e perímetros** é próprio e tem 3244 × 1480 px.
Usa três figuras com cálculos verificáveis: retângulo de 12 × 8 cm, quadrado
de lado 8 cm e triângulo retângulo de lados 9, 12 e 15 cm.

Foi preparado para **3 colunas e 2 linhas de A4 em paisagem**, margem de
10 mm e sobreposição de 10 mm, no modo com dobra. Isso produz um pôster de **811 × 370 mm**.
Nessa configuração, os 400 px da régua correspondem a 100 mm no arquivo;
a confirmação da medida em papel exige impressão física. Outra configuração
muda a escala dos desenhos.

## Reproduzir

Use uma cópia de desenvolvimento e uma tela ou ambiente de teste de pelo menos
1920 × 1080, com Python, Tk e Pillow já disponíveis.

1. Gere o cartaz: `python scripts/criar_vitrine.py --so-exemplo`.
2. Capture o programa: `python scripts/capturar_vitrine.py`.
3. Gere as capas: `python scripts/criar_vitrine.py`.

O capturador abre uma sessão nova com o cartaz sintético, escolhe as seis folhas,
visita as abas e a ajuda e fecha somente a sessão criada por ele. Não usa imagens
pessoais. Os arquivos ficam em `docs/img`.

As fotos mostram o código 0.6.0 em teste, em Windows 11 virtual; o README distingue
essa preparação do ZIP anterior disponível. A galeria inclui os dois modos.
A capa foi conferida no tamanho original, em miniatura (820 e 410 px) e sobre fundo escuro.
A prévia social é o arquivo `capa-social.png`; seu envio nas configurações do
repositório é uma ação separada.

## Bandeira e autoria

A bandeira é o SVG compartilhado, sem alteração de desenho, cores ou proporções.
No README, usa 20 × 14 px ao lado do nome. Sua origem consta em
[THIRD-PARTY-NOTICES.md](../THIRD-PARTY-NOTICES.md).
O ícone, o cartaz e o layout do gerador são distribuídos sob a licença do código
próprio. As fontes Segoe UI são acessadas no Windows, não incluídas no projeto.