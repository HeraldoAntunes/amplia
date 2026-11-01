# Comandos do Amplia

O contrato recebe uma requisição e devolve uma resposta JSON. Amplia.execute é a entrada única para interface, terminal e HTTP. Distâncias usam milímetros. Coordenadas das folhas partem do canto superior esquerdo do pôster. A ordem de impressão percorre cada linha da esquerda para a direita, depois segue para a linha seguinte.

## Protocolo

```json
{"id":"passo-1","comando":"imagem.abrir","parametros":{"caminho":"examples/demo.png"}}
```

Sucesso contém `ok:true`, `comando`, `versao`, `resultado` e o `id`, quando informado. Erros contêm `ok:false` e `erro` com `codigo`, `mensagem` e `detalhes`. O id aceita texto ou inteiro. Parâmetros desconhecidos são rejeitados. Tipos, limites e enumerações são consultáveis em comandos.listar.

Falhas de abertura ou configuração mantêm o estado anterior. Arquivos são gravados por temporário e criação ou troca atômica, sem sobrescrever por padrão. A gravação dentro de original é recusada. Lotes param no primeiro erro; o protocolo --stdio continua para permitir correção pelo agente e termina com código de saída 1 se alguma requisição falhou.

## Operações

- **programa.sobre:** consulta nome, versão, licença, autoria, assistência de IA, privacidade e componentes, mesmo sem imagem. Na interface, exibir (padrão true) abre a aba Sobre; false volta à prévia. Não muda a sessão.

- **comandos.listar:** consulta o catálogo de parâmetros e efeitos.
- **estado.obter:** consulta imagem, configuração, resolução efetiva e folhas atuais.
- **ajuda.montagem:** devolve orientações estruturadas, conceitos, cuidados, passos e exemplo numérico de recorte e alinhamento para a configuração aplicada. Funciona sem imagem e não altera o estado. Na interface, exibir (booleano, padrão true) abre o painel; exibir:false o fecha. O terminal apenas retorna essa preferência e as orientações. Margem zero e sobreposição zero recebem instruções próprias.
- **imagem.abrir:** exige exatamente um entre caminho e dados_base64. Base64 sem prefixo data URL; nome opcional. Normaliza orientação EXIF e compõe transparência sobre branco. Abrir outra imagem inicia sua configuração padrão.
- **poster.configurar:** aceita tamanho por `colunas` e `linhas` (inteiros positivos, sempre juntos) ou por `largura_mm` e/ou `altura_mm`. Não misture contagens e medidas no mesmo pedido. Margem, sobreposição, orientação e marcas continuam opcionais. Uma grade permanece fixa ao mudar orientação, margem ou sobreposição; as medidas são recalculadas. Informar uma medida volta ao modo por mm. Somente largura ou altura deriva a outra dimensão pela proporção da imagem. A imagem inteira é centralizada sem distorção ou corte; podem aparecer faixas brancas. orientacao aceita retrato ou paisagem. Valida tudo antes de aplicar.
- **folhas.listar:** consulta papel, área útil, linhas, colunas e retângulos de cada folha. Não grava arquivos.
- **previa.gerar:** retorna PNG em dados_base64, dimensões e paginação. folha opcional seleciona uma página A4; omitida mostra mosaico. pixels define a maior dimensão, entre 200 e 2400, padrão 1200. caminho opcional salva .png; substituir é false por padrão. Faixas verdes são apenas indicação da prévia geral e não aparecem no PDF.
- **pdf.exportar:** exige caminho terminado em .pdf; substituir é false por padrão. Retorna caminho, páginas, bytes e SHA-256. HTTP acrescenta download_url para baixar os mesmos bytes no navegador. Exporta todas as folhas em tamanho A4 físico, com marcas se habilitadas.
- **sessao.reiniciar:** descarta o estado em memória, sem apagar os arquivos exportados.

## Sequência para IA

Envie estas linhas para **um mesmo processo** `python amplia.py --stdio`, a partir da pasta do projeto:

```json
{"comando":"comandos.listar"}
{"comando":"imagem.abrir","parametros":{"caminho":"examples/demo.png"}}
{"comando":"poster.configurar","parametros":{"largura_mm":370,"altura_mm":544,"margem_mm":10,"sobreposicao_mm":10,"orientacao":"retrato","marcas":true}}
{"comando":"folhas.listar"}
{"comando":"ajuda.montagem"}
{"comando":"previa.gerar","parametros":{"folha":1,"pixels":1200}}
{"comando":"pdf.exportar","parametros":{"caminho":"output/meu-poster.pdf"}}
```

Caminhos relativos usam a pasta de trabalho do processo, que pode variar conforme
o programa foi aberto. Em automações, prefira caminhos absolutos ou defina a pasta
de trabalho ao iniciar o processo. A pasta de destino deve existir; use um caminho
novo ou substituir:true quando desejar substituir um arquivo. A interface oferece
o mesmo objeto no console JSON.

## Cálculo próprio da paginação

Para o modo simples: `{"comando":"poster.configurar","parametros":{"colunas":2,"linhas":2}}`. Com os padrões, isso gera exatamente 4 folhas, 370 × 544 mm. O mesmo comando funciona no console nativo e em `dist/Amplia/Amplia.Comandos.exe --stdio`, sem navegador ou Python externo.

Para uma grade C × R, a largura é u + (C − 1) × (u − s) e a altura é v + (R − 1) × (v − s), considerando margem e faixa repetida. Não basta multiplicar a largura do papel pelo número de folhas. O tamanho calculado e a grade aplicada retornam em configuracao e folhas. Quantidades inválidas, grade acima de 400 folhas ou mistura de formas de tamanho retornam erro estruturado e preservam o estado.

A4 em retrato mede 210 × 297 mm. Com margem m, a área útil mede u = 210 - 2m na horizontal e v = 297 - 2m na vertical. Com sobreposição s, o avanço entre folhas é u - s e v - s.

Para pôster de largura L e altura A, colunas = max(1, ceil((L-s)/(u-s))) e linhas = max(1, ceil((A-s)/(v-s))). A primeira folha começa em (0,0). As seguintes avançam pelo passo calculado. Na última linha ou coluna, o retângulo é limitado ao tamanho restante do pôster; o restante do A4 fica branco.

Exemplo: margem de 10 mm e sobreposição de 10 mm deixam área útil de 190 × 277 mm e avanços de 180 × 267 mm. O pôster de 370 × 544 mm usa quatro folhas com origens (0,0), (180,0), (0,267) e (180,267). A imagem recebe a mesma escala em todas as páginas, que recortam apenas seu retângulo. Isso mantém a continuidade nas emendas e evita ampliar a última folha.

## Sobreposição e montagem

O parâmetro sobreposicao_mm define uma faixa de **imagem repetida**, não um espaço branco entre páginas. No exemplo acima, a primeira coluna contém o trecho horizontal de 0 a 190 mm e a segunda começa em 180 mm: o intervalo de 180 a 190 mm é impresso nas duas folhas. A mesma regra vale para as linhas, na vertical.

A prévia geral destaca a repetição em verde; essa indicação e os números sobre o desenho não entram no PDF. Com marcas:true, o PDF acrescenta marcas de recorte e identificação nas margens. Essas marcas delimitam o retângulo impresso e não indicam que toda a faixa repetida deva ser removida.

Na montagem, a margem interna da folha que ficará por cima é aparada, e a imagem repetida da vizinha fica por baixo para alinhamento. Não se deve eliminar a faixa repetida das duas folhas. Com sobreposicao_mm igual a zero, a união é feita borda a borda, sem essa faixa de ajuste. O procedimento completo está em [Recortar e montar as folhas](GUIA-DE-USO.md#recortar-e-montar-as-folhas).

## HTTP local

--serve recebe os mesmos objetos por POST /api/comando, restrito ao loopback. O navegador fornece um identificador efêmero em X-Amplia-Token; Host ou origem externos são recusados. O identificador não é gravado em arquivos do projeto. Agentes externos ao navegador devem preferir --stdio, sem servidor ou identificador HTTP.

## Impressão no Windows

`{"comando":"poster.imprimir"}` abre o diálogo nativo da impressora e aguarda
confirmação. Exige uma imagem e usa a configuração atual da sessão.
Não recebe nome de impressora nem imprime sem a escolha na janela.
Retorna `cancelada` e `folhas_enviadas`; envio bem-sucedido informa também
`escala` (100%) e `resolucao_raster_dpi` (300). O número de folhas enviadas
não inclui as cópias que o driver aplica. Não representa confirmação física.
Em ambiente sem área de trabalho, prefira `pdf.exportar`.
