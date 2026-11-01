# Histórico do Amplia

## Em desenvolvimento

## 0.5.0 — Em preparação

- Abas Imagem, Folhas e Imprimir / PDF, sem números que se confundam com a quantidade de folhas.
- Impressão direta com escolha da impressora, intervalo de páginas e cópias na janela do Windows.
- Impressão em tamanho real, com conferência de papel A4, orientação e margens antes do envio.
- Salvar PDF continua disponível separadamente, sem exigir impressão.

## 0.4.0 · candidata local, não publicada

- Escolha de imagem e pasta pela janela do Windows, com navegação por unidades,
  pastas e atalhos, além de filtros dos formatos aceitos.
- A seleção funciona separadamente para manter o programa responsivo e pode
  ser cancelada sem descartar o pôster aberto.

## 0.3.3 · candidata local, não publicada

- Ajusta o tamanho inicial da janela à área útil do Windows, mantendo os botões
  inferiores acessíveis em telas com barra de tarefas e menor altura.

## 0.3.2 · candidata local, não publicada

- Atualiza o processador de imagens para Pillow 13.0.0, que corrige falhas de
  segurança da biblioteca, incluindo a leitura de arquivos TIFF malformados.
- Mantém a abertura restrita aos formatos aceitos e os limites de imagem e folhas.

## 0.3.1 · candidata local, não publicada

- Corrige a prévia quando a última folha tem uma faixa muito estreita da imagem.
- Limita a abertura aos decodificadores dos cinco formatos aceitos.
- Confere a gravação do temporário antes de concluir a troca do arquivo.
- Reforça as verificações do servidor opcional de desenvolvimento.
- Inclui ícone próprio na janela e nos executáveis, com informações de versão.
- Atualiza o guia para o fluxo Imagem, Folhas e PDF e esclarece as licenças das fontes.
- Prepara testes e análise de código para um futuro repositório público.

## 0.3.0 — candidata local, não publicada

- Fluxo em três etapas: Imagem, Folhas e PDF, com prévia sempre no espaço principal.
- Botões de continuar e salvar em área fixa, sem rolagem do formulário inteiro.
- Tamanhos rápidos de 1, 4 e 9 folhas e atualização automática da prévia.
- Primeira prévia já configurada para quatro folhas, igual à opção mostrada.
- Seletor simples do próprio aplicativo, sem extensões do Explorador.
- Nome e pasta do PDF separados, sugestão de nome livre e confirmação de substituição.
- Mensagens em linguagem de uso, atalhos de teclado e recursos de automação no menu Ferramentas.
- Campos bloqueados durante o processamento para não perder ajustes digitados.


## 0.2.0 — candidata local, não publicada

- Crédito público de Heraldo Antunes na licença, citação, cabeçalhos e Sobre.
- Tela Sobre com versão, licença, privacidade e informações de autoria e IA,
  acessível também pelo comando programa.sobre.
- Guia de uso, arquitetura e informações de segurança organizados separadamente.
- Preparação local de fontes distribuíveis com seleção explícita de arquivos.
- Conferência automática de versão e separação entre candidata e estável.
- Avisos de terceiros e documentação incluídos no pacote portátil.

A versão estável local anterior, 0.1.0, continua preservada.
Não há instalador, atualização automática ou publicação pública nesta candidata.

## 0.1.0 — 13/10/2026 — estável local

Primeira base estável local com prévia, paginação e exportação PDF.
Não publicada no GitHub e ainda não depositada no INPI.

- Aplicativo portátil Windows x64 com interface nativa e runtime incluído.
- Abertura de PNG, JPEG, WebP, BMP e TIFF, por caminho ou seletor de arquivo.
- Modo simples de tamanho por quantidade de folhas na largura e na altura.
- Medidas em mm e opções avançadas recolhidas: margens, sobreposição e orientação.
- Paginação A4, proporção preservada, prévia geral e por folha, PDF em tamanho real.
- Ajuda visual de recorte e montagem sem eliminar a imagem nas emendas.
- Nove comandos com respostas JSON, compartilhados entre interface e terminal.
- Código próprio sob licença MIT.
- Arquivo local de fontes com SHA-512, portátil com SHA-256 e documentação congelada.

Validação funcional: 27 testes aprovados, sem skips, antes da consolidação;
a validação adicional do arquivamento está registrada no pacote desta versão.
PDF por folhas exportado pela interface conferido com o núcleo. Sem impressão
física nem teste em outro computador. O seletor do Windows apresentou travamento;
a causa permanece indeterminada, com abertura por caminho como alternativa.

O histórico de versões preservadas começa nesta base.
