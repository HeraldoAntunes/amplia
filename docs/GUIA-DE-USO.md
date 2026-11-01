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
ficam a borda branca, a faixa para colar e as marcas de corte; a posição do A4
é escolhida em **Posição das folhas A4**. O padrão usa 10 mm de margem e
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

## Recortar e montar as folhas


Na interface, use **Ajuda → Como montar as folhas** ou pressione **F1**.
O painel mostra o recorte da margem da folha de cima e a folha vizinha por
baixo, com a imagem repetida alinhada. Os desenhos são didáticos, sem escala,
e as medidas seguem a configuração aplicada. A ajuda também funciona antes
de abrir uma imagem. **Voltar à prévia** fecha essa visualização.

Ao aplicar outra configuração, o painel aberto é atualizado. Com margem zero, não manda aparar uma margem inexistente; com sobreposição zero, mostra a união borda a borda. O comando JSON correspondente é `{"comando":"ajuda.montagem"}`. Para fechar o painel pelo console, use `{"comando":"ajuda.montagem","parametros":{"exibir":false}}`.

**A sobreposição preserva a continuidade da imagem nas emendas:** uma faixa do desenho é impressa nas duas folhas vizinhas. Na prévia geral, as faixas verdes destacam essa repetição e os contornos mostram os limites das folhas. Essas marcações verdes e os números sobre o desenho não entram no PDF. Quando habilitadas, as marcas de recorte e a identificação das folhas são impressas nas margens.

Margem e sobreposição têm funções diferentes. A **margem** reserva espaço nas bordas do papel, fora do retângulo do pôster impresso naquela folha. A **sobreposição** contém imagem repetida para alinhar e colar as folhas. Não é um intervalo vazio nem uma parte descartada pelo programa.

Com margem e sobreposição de 10 mm, a área útil horizontal do A4 em retrato é de 190 mm. A primeira folha imprime o trecho de 0 a 190 mm do pôster; a segunda começa em 180 mm. Portanto, os 10 mm entre 180 e 190 mm aparecem nas duas folhas. Um desenho que atravessa essa emenda fica completo depois do alinhamento.

Para montar:

1. Imprima todas as páginas em **100% / tamanho real**, sem ajustar à página. Se usar o exemplo de calibração, confira com uma régua se a linha indicada mede 100 mm.
2. Organize as folhas pelos números, linhas e colunas, antes de cortar ou colar. Confira também a prévia individual de cada folha.
3. Monte uma linha por vez. Se a folha à esquerda ficar por cima da vizinha, corte somente sua **margem branca direita**, no limite indicado pelas marcas de recorte. Preserve a faixa de imagem repetida da folha à direita, que ficará por baixo.
4. Deslize a folha de baixo até que os traços do desenho coincidam na sobreposição. Fixe provisoriamente e confira o alinhamento antes de colar.
5. Para unir as linhas, siga o mesmo princípio: apare a margem branca inferior da linha que ficará por cima e alinhe a faixa repetida da linha seguinte por baixo.

**Não remova a faixa de sobreposição das duas folhas.** As marcas de recorte indicam o limite do retângulo impresso naquela folha; não mandam eliminar toda a imagem repetida. Também não corte automaticamente áreas brancas que pertençam ao próprio desenho ou às faixas de centralização do pôster.

Com sobreposição igual a zero, não existe faixa repetida para ajuste: as bordas precisam se encontrar diretamente depois do recorte das margens internas. Para a montagem com faixa de alinhamento, configure uma sobreposição maior que zero; o padrão do Amplia é 10 mm.

O alinhamento correto evita perder partes do desenho, mas a emenda física do papel ainda pode ficar visível. A montagem e a medida final em papel continuam pendentes de validação por impressão física.


## Sobre e comandos

**Ajuda → Sobre o Amplia** mostra versão, licença, componentes e privacidade. Também é
possível consultar essas informações com `{"comando":"programa.sobre"}`.
**Ferramentas → Comandos para automação…** e **Amplia.Comandos.exe --stdio** usam o mesmo núcleo.
Veja o [contrato de comandos](COMANDOS.md).

## Limites e perguntas comuns

- **Há instalador?** Esta preparação oferece somente a pasta portátil.
- **Procura atualizações?** Não há consulta automática nem endereço de publicação.
- **Funciona em outro sistema?** A validação atual foi feita no Windows desta máquina;
  não há validação em Linux, macOS ou outro computador.
- **A ampliação ficou borrada?** A qualidade depende da resolução da imagem.
  O comando de estado informa a resolução efetiva e avisos abaixo de 100 dpi.
- **Posso fechar e retomar?** A sessão fica na memória; não há recuperação automática.
- **As emendas já foram testadas no papel?** A impressão física continua pendente.

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
