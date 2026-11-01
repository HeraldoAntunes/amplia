<!-- Amplia · © 2026 Heraldo Antunes · SPDX-License-Identifier: MIT -->
# Guia de uso

## Abrir o programa

Extraia a pasta portátil completa e abra **Amplia.exe**. Não mova apenas o
executável: as pastas app e runtime fazem parte do aplicativo. A interface é
nativa do Windows e funciona sem navegador, conta ou serviço remoto.

## Abrir uma imagem

Na etapa **Imagem**, use **Escolher imagem…**. Para informar o arquivo
diretamente, clique em **Colar caminho do arquivo…**, cole o caminho completo
e use **Abrir imagem**. O botão **Escolher imagem…** abre a janela do Windows: use a barra de endereço,
os atalhos e as unidades em **Este Computador** para navegar, inclusive no C:.
Dê dois cliques nas pastas para entrar e selecione a imagem com **Abrir**.
O filtro inicial mostra os formatos de imagem aceitos. **Cancelar seleção**
no Amplia fecha somente o seletor e preserva o pôster. Se a janela do Windows
não responder, cancele a seleção e use o caminho diretamente. **Usar imagem de exemplo** abre uma imagem sintética
para conhecer o programa. São aceitos PNG, JPEG, WebP, BMP e TIFF;
animações usam o primeiro quadro.

## Escolher o tamanho

No modo **Por folhas (simples)**, informe folhas na largura e na altura.
Exemplo: 2 × 2 = 4 folhas A4. Os atalhos **1 folha**, **4 folhas** e **9 folhas**
definem grades prontas. A primeira prévia já usa quatro folhas. Alterar a
quantidade de folhas atualiza a prévia automaticamente após uma pequena pausa.
Confira os contornos, as faixas de sobreposição e o tamanho final em centímetros.

**Por medidas (mm)** permite informar largura e altura. Em **Ajustes de impressão…**
ficam a borda branca, a faixa repetida do modo com dobra e as guias de montagem; a posição do A4
é escolhida em **Posição das folhas A4**. O padrão usa o modo com dobra e 10 mm de margem e
sobreposição. Clique em **Atualizar prévia** para aplicar medidas e ajustes
avançados. Mudanças precisam estar aplicadas antes de imprimir ou salvar o PDF.
A imagem fica inteira e centralizada; pode haver espaços brancos se a grade
tiver outra proporção. Não estique a imagem para tentar eliminar esses espaços.

## Conferir e exportar

O seletor **Pôster completo** permite ver cada folha. Use **Continuar**
para chegar à etapa **Imprimir / PDF**. Informe o **Nome do arquivo** e **Salvar na pasta**
separadamente e clique em **Salvar PDF**. A pasta precisa existir; use
**Escolher pasta…** para selecioná-la pela janela do Windows. O programa acrescenta .pdf quando necessário
e pede confirmação antes de substituir um arquivo existente.
Imprima em **100% / tamanho real**, sem ajustar à página.
A sessão não é salva como projeto; guarde o PDF antes de fechar.

## Montar sem recortar

Escolha o modo em **Folhas → Montagem sem recortar**, antes de imprimir. Trocar o
modo muda a divisão da imagem e pode mudar o tamanho do desenho. Não misture
folhas impressas em modos ou configurações diferentes.

Cada folha traz um código: **A1, A2, A3...** na primeira linha; **B1, B2, B3...**
na segunda. A letra é a linha e o número é a coluna. O número de impressão,
como **FOLHA 2/6**, aparece junto. A indicação **CIMA** ajuda a manter todas
as folhas na orientação correta. Imprima em uma face, sem frente e verso.

### Dobrar bordas para trás

Este modo procura manter o desenho contínuo. Use uma régua para ajudar na dobra.

1. Organize todas as folhas conforme os códigos, sem colar ainda. Comece por A1.
2. Nas folhas da segunda coluna em diante, dobre **somente a margem esquerda
   para trás**, pela linha tracejada. Não dobre a borda externa esquerda do cartaz.
3. Coloque A2 **por cima** de A1. A borda dobrada de A2 deve coincidir com os sinais
   **+** de A1. Confira se os traços repetidos do desenho coincidem antes de fixar.
4. Continue a linha: A3 por cima de A2, e assim por diante. Fixe provisoriamente
   com fita pelo verso; mantenha os lados horizontais alinhados.
5. Prepare a linha B. Dobre para trás também sua **margem de cima**, na linha
   tracejada. Coloque a linha B **por cima** da A, alinhando os sinais laterais
   **+** e os traços do desenho. Repita para as próximas linhas.
6. Confira todas as emendas. Fixe com fita pelo verso; se usar cola, aplique pouca
   quantidade na área escondida, depois de alinhar.

**Tracejado significa dobra; + significa alinhamento.** Não corte. Não dobre
brancos que fazem parte da imagem ou da centralização. Não dobre as bordas
externas do cartaz. A faixa de imagem repetida é intencional: fica por baixo
da folha nova e ajuda a alinhar. As dobras e a espessura do papel ainda podem
ficar perceptíveis. Com margem zero não há borda reservada para dobrar;
com sobreposição zero não há faixa repetida para ajuste.

### Folhas inteiras, com faixas brancas

Este modo evita tanto a tesoura quanto as dobras. As faixas brancas fazem parte
do resultado e aparecem na prévia.

1. Organize A1, A2, A3... e depois B1, B2, B3... como no mapa.
2. Encoste os lados do **papel**, sem sobrepor. Não procure coincidir desenhos
   por cima de outra folha: cada trecho da imagem aparece uma única vez.
3. Não corte nem dobre. Una as folhas com fita pelo verso, sem cobrir o desenho.

Com margem de 10 mm por lado, duas folhas vizinhas deixam uma faixa branca de
**20 mm** entre os desenhos. A repetição fica desativada neste modo. O tamanho
**do desenho** é a soma das áreas úteis; o **papel montado** inclui as margens
e pode ser maior. A última folha pode conter espaço branco adicional quando
as medidas escolhidas não completam uma área útil inteira.

### Mapa de montagem e conferência

Em **Imprimir / PDF**, **Salvar mapa de montagem (PDF)** cria um arquivo com
sufixo **-mapa.pdf**, separado do PDF do pôster. Ele contém a grade, os códigos,
a ordem e as instruções do modo aplicado. Pode ser impresso pelo seu leitor
PDF. Não cole essa folha ao cartaz. Salvar o mapa não salva o pôster.

**Ajuda → Como montar as folhas** ou **F1** mostra as mesmas orientações.
As guias e os códigos saem em preto nas margens quando **Guias de montagem e
códigos das folhas** está habilitado. O verde do modo com dobra pertence só
à prévia; não é impresso sobre o desenho. Mantenha pelo menos os 10 mm de
borda padrão; se a impressora não alcançar as guias, aumente essa borda.
Na impressão direta, o Amplia confere também se as guias cabem na área imprimível.

A geometria e a impressão virtual são verificadas separadamente da experiência
em papel. A primeira impressão da versão anterior revelou montagem confusa;
os novos modos continuam em teste até a conferência física de clareza e alinhamento.

## Sobre e comandos

**Ajuda → Sobre o Amplia** mostra versão, licença, componentes e privacidade. Também é
possível consultar essas informações com `{"comando":"programa.sobre"}`.
**Ferramentas → Comandos para automação…** e **Amplia.Comandos.exe --stdio** usam o mesmo núcleo.
Veja o [contrato de comandos](COMANDOS.md).

## Limites e perguntas comuns

- **Há instalador?** Esta preparação oferece somente a pasta portátil.
- **Procura atualizações?** Não há consulta automática. As candidatas estão no GitHub, no endereço informado no README.
- **Funciona em outro sistema?** A validação automatizada usa Windows 11 em VM e Windows Server 2025 na CI;
  Linux, macOS e outro computador físico continuam pendentes.
- **A ampliação ficou borrada?** A qualidade depende da resolução da imagem.
  O comando de estado informa a resolução efetiva e avisos abaixo de 100 dpi.
- **Posso fechar e retomar?** A sessão fica na memória; não há recuperação automática.
- **As emendas já foram testadas no papel?** A montagem anterior foi considerada confusa; os novos modos aguardam conferência física.

## Imprimir diretamente

As abas **Imagem**, **Folhas** e **Imprimir / PDF** indicam partes do trabalho;
os números aparecem somente nas quantidades e na identificação das folhas.
Na última aba, **Imprimir…** abre a janela do Windows para escolher impressora,
propriedades, intervalo de folhas e cópias. O atalho é **Ctrl+P**.
Não é preciso salvar o PDF antes. Cancelar mantém o pôster na sessão.

O Amplia prepara A4 na orientação configurada e escala 100%. Confira essas
opções nas propriedades da impressora. Se o driver informar outro tamanho,
escala diferente ou margem que cortaria a imagem, o programa pede correção
antes de enviar folhas. A impressão direta usa 300 dpi e as mesmas posições,
margens e sobreposição do núcleo. Cada página é desenhada separadamente.

**Salvar PDF** continua independente da impressão: nome e pasta só são usados
para salvar o arquivo. O PDF preserva a imagem original, sem o raster intermediário
de 300 dpi da impressão direta. O envio ao Windows não comprova a saída em papel;
confira a fila de impressão. A qualidade e a cor dependem da impressora e do driver.

O Python incluído serve somente para executar o Amplia. Não é uma instalação
de desenvolvimento e não inclui os utilitários de ambientes virtuais ou ajuda
interativa do Python. Para desenvolver, use uma instalação separada de Python.
