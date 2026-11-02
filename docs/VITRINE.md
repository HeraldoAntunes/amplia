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

## Exemplos

A capa e a galeria usam o **Mapa Serra Clara**, 3244 × 1480 px: relevo sintético,
curvas de nível de 20 em 20 metros, trilha e mirantes. O mapa é fictício e não
georreferenciado. É gerado por `examples/criar_exemplos.py`, junto do desenho
**Suporte de fixação**, com cotas e perspectiva ilustrativas. O mapa é também
`examples/demo.png`, aberto pelo botão de exemplo existente.

O cartaz **Festa entre estrelas** foi gerado com a ferramenta de imagens da
OpenAI, sem imagem de referência, e revisado visualmente. O pedido descreveu
um cartaz horizontal de aniversário em ilustração de papel e guache, fundo
azul noturno, foguete verde, planetas e balões, com os textos “FESTA ENTRE
ESTRELAS”, “Uma aventura para comemorar!”, “Prepare o espaço. A diversão vai
decolar.” e “EXEMPLO FICTÍCIO”, sem nomes, datas, marcas ou personagens conhecidos.
A imagem pronta é distribuída; o script não a regenera.

Os três arquivos acompanham o portátil em `app/examples`. A documentação e as
limitações ficam em [examples/README.md](../examples/README.md). O programa não
usa IA ou conexão para abrir esses arquivos.

Na captura principal: **3 colunas × 2 linhas de A4 em paisagem**, margens de
10 mm e repetição de 10 mm, modo com dobra. A imagem permanece inteira; a escala
gráfica do desenho é ilustrativa e muda de tamanho junto com o pôster.

## Reproduzir

Use uma cópia de desenvolvimento e uma tela ou ambiente de teste de pelo menos
1920 × 1080, com Python, Tk e Pillow já disponíveis.

1. Gere mapa e peça: `python scripts/criar_vitrine.py --so-exemplo`.
2. Capture o programa: `python scripts/capturar_vitrine.py`.
3. Gere as capas: `python scripts/criar_vitrine.py`.

O capturador abre uma sessão nova com o cartaz sintético, escolhe as seis folhas,
visita as abas e a ajuda e fecha somente a sessão criada por ele. Não usa imagens
pessoais. Os arquivos ficam em `docs/img`.

As fotos locais mostram o código 0.6.1 em teste, com o ícone de duas folhas,
em Windows 11 virtual; o README distingue essa preparação da candidata
0.6.1-rc.1 preparada para publicação. Capa e prévia social foram regeneradas com o ícone aprovado. A galeria inclui os dois modos.
A capa foi conferida no tamanho original, em miniatura (820 e 410 px) e sobre fundo escuro.
A prévia social é o arquivo `capa-social.png`; seu envio nas configurações do
repositório é uma ação separada.

## Bandeira e autoria

A bandeira é o SVG compartilhado, sem alteração de desenho, cores ou proporções.
No README, usa 20 × 14 px ao lado do nome. Sua origem consta em
[THIRD-PARTY-NOTICES.md](../THIRD-PARTY-NOTICES.md).
O ícone, o cartaz e o layout do gerador são distribuídos sob a licença do código
próprio. As fontes Segoe UI são acessadas no Windows, não incluídas no projeto.

## Ícone

Uma folha menor na origem da seta e uma maior no destino representam a ampliação.
A paleta e a seta anteriores foram mantidas. SVG/PNG/ICO são gerados por
`native/gerar_icone.py`. O ícone entra também no recurso dos dois executáveis,
que precisam ser recompilados quando o ICO mudar.
