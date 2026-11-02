<!-- Amplia · © 2026 Heraldo Antunes · SPDX-License-Identifier: MIT -->
# Exemplos para ampliar

Os três exemplos acompanham o portátil em `app/examples`. Use **Escolher imagem…**
para abrir um deles. **Usar imagem de exemplo** abre o mapa Serra Clara.

- [Mapa Serra Clara](mapa-serra-clara.png): 3244 × 1480 px, curvas de nível de
  20 em 20 metros, trilha, mirantes e escala gráfica ilustrativa. Terreno sintético,
  criado por uma função matemática. Não representa local real ou levantamento
  topográfico e não deve ser usado para navegação.
- [Suporte de fixação](peca-suporte.png): 3244 × 1480 px, placa de referência
  140 × 65 mm e quatro furos de 12 mm. A vista superior usa 8 pixels por milímetro;
  a perspectiva é ilustrativa. Não inclui tolerâncias, material ou dimensionamento
  estrutural e não é um projeto para fabricação.
- [Festa entre estrelas](festa-entre-estrelas.png): cartaz de aniversário com
  foguete, planetas e balões, sem nomes, datas ou dados de pessoas reais.

Uma configuração inicial útil é **3 colunas × 2 linhas, A4 deitado**, para os
exemplos horizontais. Confira a prévia: a imagem permanece inteira, sem esticar,
e pode sobrar espaço. Para o cartaz de festa, 2 × 2 também é uma opção.

As escalas e cotas dos desenhos são ilustrativas: a ampliação altera o tamanho
impresso. Imprima em **100% / tamanho real** para manter o tamanho configurado
no Amplia. Teste de PDF não comprova a medida em uma impressora física.

## Origem e licença

Mapa e peça foram desenhados para o Amplia por código próprio, em
`criar_exemplos.py`, com assistência do Codex. O cartaz de festa foi gerado com
assistência de IA da OpenAI e revisado visualmente. Não foram usados mapas,
desenhos industriais ou personagens de terceiros como referência.

Estes arquivos são distribuídos com o Amplia sob a licença MIT. O programa não
precisa de IA nem de internet para abrir ou ampliar os exemplos.

Para reproduzir mapa e peça em uma cópia de desenvolvimento no Windows, com
Pillow já disponível: `python examples/criar_exemplos.py`. As fontes Segoe UI são
lidas do Windows e não acompanham o pacote. A ilustração da festa é um arquivo
pronto; não é regenerada pelo script.
