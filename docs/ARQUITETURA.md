<!-- Amplia · © 2026 Heraldo Antunes · SPDX-License-Identifier: MIT -->
# Arquitetura

O Amplia mantém um núcleo único de comandos, uma interface nativa e um
protocolo de terminal. Não há serviço remoto nem framework de aplicação.

- **amplia.py:** catálogo, validação, estado da imagem, paginação, prévia e PDF.
  `Amplia.execute` recebe o objeto JSON e devolve resultado ou erro estruturado.
- **amplia_desktop.py:** formulário Tk, prévia, montagem, Sobre e console JSON.
  Operações demoradas passam por uma fila com um trabalhador; a janela recebe
  os resultados pelo laço de eventos do Tk.
- **amplia_picker.py:** diálogo nativo do Windows por Tk, em processo auxiliar
  sem console. A interface continua respondendo; cancelar encerra apenas esse
  processo. A seleção retorna um caminho, validado depois pelo mesmo núcleo.
- **native/launcher.c e native/boot.py:** inicialização do Python incluído no
  portátil, sem depender de variáveis ou pacotes Python da conta.
- **native/build_portable.py:** montagem local do runtime, aplicativo, guias,
  avisos de licença e manifesto de hashes, usando componentes já disponíveis.
- **web/:** interface de desenvolvimento anterior, opcional, fora do portátil.
- **examples/:** gerador e imagem sintética de calibração, sem dados pessoais.
- **tests/:** núcleo, interface, comandos, paginação, protocolo e conferências.

## Cada operação é um comando

Mouse e terminal chamam o mesmo núcleo. O catálogo de parâmetros fica em
`COMMANDS`, com nome, tipo e efeito. A consulta `programa.sobre` retorna versão,
licença e privacidade sem precisar abrir imagem. Gestos de apresentação da
janela não reimplementam a paginação.

O protocolo JSON Lines mantém uma sessão por processo. Erros de configuração
preservam o estado anterior. Não renomeie comandos nem campos existentes:
eles podem estar sendo usados por scripts de impressão.

## Paginação

O papel A4 tem margens uniformes. O avanço é a área útil menos a sobreposição.
Uma faixa da imagem aparece nas duas folhas vizinhas; a escala é igual em
todas as páginas. A imagem é encaixada inteira no retângulo escolhido, sem
distorção ou corte automático. O PDF usa milímetros convertidos para pontos.

## Montagem e validação

`VERSION` é a fonte única do número do programa. O mesmo número aparece no
protocolo, na janela, no manifesto e nos metadados de citação. O pacote precisa
ser recompilado se o lançador mudar; atualizar fontes não recompila o C.
Consulte o [guia de uso](GUIA-DE-USO.md) e os [comandos](COMANDOS.md).

## Impressão direta

`poster.imprimir` passa por Amplia.execute. O módulo amplia_print.py apresenta
PrintDlgW e usa o contexto GDI retornado, com ctypes e Pillow já incluídos.
A interface executa o comando fora do laço do Tk, desabilita as edições até
concluir e não fecha durante o envio. O driver controla cópias e colação;
o Amplia respeita o intervalo escolhido e reaproveita Amplia.render por folha,
a 300 dpi, sem bitmap do pôster inteiro. Os milímetros são convertidos pelos
dpi do driver e compensados pelos deslocamentos físicos, sem ajustar à área útil.
Falhas após StartDoc abortam o trabalho; contexto e memória do diálogo são liberados.
Nenhum visualizador PDF, navegador, pacote novo ou serviço de rede é necessário.
