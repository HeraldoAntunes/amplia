# Componentes de terceiros

O código próprio do Amplia usa a licença MIT. A autorização não altera as
licenças dos componentes abaixo. Eles não integram o ZIP de código próprio
preparado para o INPI.

Inventário do portátil conferido em 01/11/2026 (Python 3.14.7):

- Python 3.14.7: runtime incluído, com licença em runtime/LICENSE.txt.
- Tcl/Tk 9.0.4: interface nativa; distribuído com o runtime Python. Seus arquivos
  estão em runtime/tcl, incluindo os arquivos ZIP das bibliotecas e os avisos de licença.
- Pillow 13.0.0: metadados identificam MIT-CMU; licença em
  runtime/Lib/site-packages/pillow-13.0.0.dist-info/licenses/LICENSE.
  Esse mesmo arquivo contém os avisos das bibliotecas incorporadas:
  brotli-1.2.0;
  freetype-2.14.3;
  harfbuzz-14.5.0;
  lcms2-2.19.1;
  libavif-1.4.2;
  libjpeg-turbo-3.2.0;
  libpng-1.6.58;
  libwebp-1.6.0;
  openjpeg-2.5.4;
  tiff-4.7.2;
  xz-5.8.4;
  zlib-ng-2.3.3;
  cada seção preserva seus próprios termos. Não são declaradas MIT-CMU
  apenas por integrarem o Pillow. Este software utiliza o FreeType, do
  FreeType Project, sob a FreeType License reproduzida nesse arquivo.
  Os avisos acompanham também a pasta licencas.
- ReportLab 4.1.0: BSD, com licença em
  runtime/Lib/site-packages/reportlab-4.1.0.dist-info/LICENSE. A distribuição também
  contém fontes sob licenças próprias, preservadas integralmente:
  - Bitstream Vera: licença Bitstream Vera, em fonts/bitstream-vera-license.txt.
  - Dark Garden: GPL-2.0-or-later com exceção de incorporação de fontes,
    em fonts/DarkGarden-copying.txt e fonts/DarkGarden-copying-gpl.txt.
    A fonte editável fonts/DarkGarden.sfd acompanha a distribuição sem alteração.
    O Amplia não usa Dark Garden no pôster; sua presença vem do pacote ReportLab.
    A exceção e os avisos devem permanecer com os arquivos correspondentes.
  - Fontes Type 1 incluídas pelo ReportLab: consultar fonts/00readme.txt e
    os avisos do próprio pacote; não são declaradas como fontes MIT do Amplia.
- chardet 7.4.3: metadados identificam 0BSD; licença em
  runtime/Lib/site-packages/chardet-7.4.3.dist-info/licenses/LICENSE.
- DLLs de runtime Microsoft incluídas com Python: componentes de terceiros,
  sujeitos às condições de redistribuição da distribuição Python/Windows.

Os lançadores foram compilados com GCC existente na máquina, sem distribuir o
compilador. O construtor e seu código C fazem parte do código próprio; não há
atribuição de autoria sobre runtime, compilador ou bibliotecas de terceiros.

As fontes Segoe UI usadas pela interface e pelos esquemas são acessadas no
Windows do usuário; o Amplia não distribui esses arquivos de fonte.

A pasta licencas do pacote reúne cópias dos avisos encontrados no runtime
incluído e seu índice de origem. Os componentes preservam as condições
respectivas; a licença MIT do Amplia cobre somente o código próprio.

As marcas citadas pertencem aos seus donos; o Amplia é um projeto independente,
sem vínculo com elas. O inventário identifica os componentes incluídos, sem
atribuir ao Amplia autoria sobre suas bibliotecas ou fontes.

O ícone do Amplia e suas versões SVG, PNG e ICO são desenhos próprios, sob MIT.
Não usam logotipo de outro produto nem uma fonte incorporada.
PyMuPDF e pypdf são ferramentas locais de teste; não integram o portátil nem
os arquivos distribuídos ao usuário. A licença de ferramentas de desenvolvimento
não deve ser anunciada como licença do código próprio.
