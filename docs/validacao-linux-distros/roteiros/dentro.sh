#!/bin/bash
# Roda dentro do contêiner. /src = Amplia v0.6.1-rc.1 (só leitura), /val = roteiros, /out = resultados.
# MODO=apt (Ubuntu), MODO=imagem (Python da própria imagem), MODO=uv (Python oficial portátil via uv).
set -u
export DEBIAN_FRONTEND=noninteractive
NOME="$1"; OUT="/out/$NOME"; rm -rf "$OUT"; mkdir -p "$OUT"
exec > >(tee "$OUT/log.txt") 2>&1
echo "== sistema"; cat /etc/os-release | grep -E '^(PRETTY_NAME|VERSION_ID)='
case "$MODO" in
  apt) apt-get update -qq && apt-get install -y -qq python3 python3-venv python3-tk xvfb xauth poppler-utils >/dev/null; PY=python3 ;;
  imagem) PY=python3 ;;
  uv) uv python install 3.12 >/dev/null 2>&1; PY=$(uv python find 3.12) ;;
esac
$PY -c "import sys, tkinter; print('Python', sys.version.split()[0], '| Tk', tkinter.TkVersion)"
cp -r /src /work && cd /work
$PY -m venv /venv && . /venv/bin/activate
pip install -q --upgrade pip >/dev/null 2>&1
if pip install -q -r requirements-validado.txt numpy; then echo "REQ_VALIDADO=ok"; else echo "REQ_VALIDADO=falhou"; fi
pip freeze | grep -iE "^(pillow|reportlab|pypdf|pymupdf)=="
if [ -n "${DISPLAY_EXTERNO:-}" ]; then export DISPLAY=$DISPLAY_EXTERNO; RODA=""; else RODA="xvfb-run -a -s -screen\ 0\ 1920x1080x24"; fi
echo "== testes"
eval $RODA python -m unittest discover -s tests -v > "$OUT/testes.txt" 2>&1; echo "TESTES_SAIDA=$?"
tail -3 "$OUT/testes.txt"; grep -E "^(ERROR|FAIL):" "$OUT/testes.txt"
echo "== medidas"
python -I /val/medidas.py /work "$OUT/medidas" | tail -6
echo "== bordas"
python -I /val/bordas.py /work "$OUT/bordas"
echo "== interface com acentos"
eval $RODA python -I /val/gui_acentos.py /work "$OUT/gui" 2>&1 | tail -8
