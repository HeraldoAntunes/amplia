<!-- Amplia · © 2026 Heraldo Antunes · SPDX-License-Identifier: MIT -->
# Segurança e privacidade

## Interface nativa

A imagem é processada no computador com Python, Pillow e ReportLab. Não há
telemetria, conta ou envio da imagem para um servidor. A interface nativa não
abre servidor HTTP, não usa WebView2 nem consulta atualizações automaticamente.
Ao imprimir, as folhas são enviadas à impressora escolhida, que pode ser local
ou de rede. Não há envio automático a um serviço de impressão.
O estado da sessão fica na memória; fechar o aplicativo perde os ajustes não
exportados. O programa não oferece recuperação automática de projeto.

Prévia e PDF só são gravados quando solicitados. Arquivos existentes não são
substituídos sem a opção correspondente. As gravações usam temporário e troca
ou criação atômica, para evitar truncar um destino existente.

## Imagens e comandos

A abertura é restrita aos decodificadores dos formatos aceitos. As imagens são limitadas a 40 MiB e 40 milhões de pixels; o pôster admite até
400 folhas. Tipos e faixas de parâmetros são validados. Arquivos malformados
podem produzir erros dos decodificadores; mantenha as dependências atualizadas
por um processo de revisão e teste.

O terminal JSON opera com as permissões da conta que o executa. Não é uma
caixa isolada para agentes: permita somente o acesso necessário aos arquivos.

## Interface web alternativa

O código de desenvolvimento conserva um servidor HTTP opcional, ligado
explicitamente com `--serve`. Ele escuta no loopback, verifica Host, origem e
um código de acesso criado para a sessão. Outros processos ou contas com acesso ao loopback podem ler a página e obter
o código de sessão: ele protege contra páginas externas, não isola contas locais.
O servidor opera com os acessos a arquivos da conta que o iniciou. Use-o apenas
num ambiente de desenvolvimento confiável; não o exponha na rede. O portátil nativo não inicia esse servidor.

## Correção de dependência na 0.3.2

O portátil inclui Pillow 13.0.0. Essa versão corrige o aviso
[GHSA-c6hw-5grf-ff96](https://github.com/python-pillow/Pillow/security/advisories/GHSA-c6hw-5grf-ff96),
que afetava versões até 12.3.0 durante a decodificação de TIFF. O runtime
anterior foi substituído em uma cópia isolada e o fluxo de imagens/PDF foi
retestado. Os limites de tamanho e a lista de formatos continuam ativos.
Isso não significa ausência de outras falhas; novas dependências precisam
de revisão de avisos e testes antes de entrar no pacote.

## Integridade e autoria dos arquivos

O SHA-256 permite conferir integridade; não comprova a identidade de quem
distribuiu o arquivo. Os anexos publicados recebem um arquivo .sigstore.json, que pode ser
verificado com a identidade do workflow de assinatura deste repositório. Essa
assinatura não equivale a um certificado digital de editor do Windows.
Os resultados de antivírus, quando disponíveis, correspondem aos hashes exatos
indicados nas notas de cada versão.
O pré-lançamento não equivale a certificação de segurança ou validação física.

## Relato de falhas

Use o [relato privado de vulnerabilidade](https://github.com/HeraldoAntunes/amplia/security/advisories/new).
Informe a versão e os passos para reproduzir,
sem anexar documentos pessoais. Não publique uma falha sensível com dados reais.
