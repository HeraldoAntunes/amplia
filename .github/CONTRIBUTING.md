<!-- Amplia · © 2026 Heraldo Antunes · SPDX-License-Identifier: MIT -->
# Como contribuir

O Amplia está em desenvolvimento. Relate problemas e sugestões nas issues e
apresente mudanças pequenas por pull request. Antes de trabalho extenso, combine
o escopo com o mantenedor.

Antes de alterar código, consulte o [guia técnico](../docs/ARQUITETURA.md).
Faça mudanças pequenas, com o motivo e a forma de verificar o resultado.
Preserve os comandos existentes e acrescente testes para comportamentos novos.

## Testar

Com Python e as dependências já disponíveis, execute na raiz do código:

```powershell
python -m unittest discover -s tests -v
```

A CI monta o portátil antes de testar. Para reproduzir essa conferência, use
Python 3.14.7/Tk 9, as versões de requirements-validado.txt e GCC/windres
disponíveis no Windows. Execute `python native/build_portable.py` antes dos testes.
As verificações do Windows não equivalem a teste em Linux ou macOS.

Não inclua imagens pessoais, credenciais, certificados, caminhos de perfil ou
dados reais nos testes. Use exemplos sintéticos e pastas temporárias isoladas.
Feche os processos iniciados pelos testes e limpe somente seus próprios rascunhos.

## Assistência de IA

Declare a assistência utilizada. A responsabilidade pela revisão e submissão
é da pessoa. Não atribua coautoria à ferramenta. Quando houver commits
autorizados, registre a assistência como `Assisted-by: ferramenta:modelo`.

Não publique nem instale dependências como efeito colateral de um teste.
