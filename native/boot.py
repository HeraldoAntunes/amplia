# Amplia · © 2026 Heraldo Antunes · SPDX-License-Identifier: MIT
"""Bootstrap do pacote portátil; não usa Python, pacotes ou variáveis externos."""
from pathlib import Path
import os
import sys

APP = Path(__file__).resolve().parent
BASE = APP.parent
sys.path[:0] = [str(APP), str(BASE / 'runtime' / 'Lib' / 'site-packages')]
os.environ['TCL_LIBRARY'] = str(BASE / 'runtime' / 'tcl' / 'tcl9.0')
os.environ['TK_LIBRARY'] = str(BASE / 'runtime' / 'tcl' / 'tk9.0')

if '--serve' in sys.argv:
    raise SystemExit('Este pacote é desktop. Use Amplia.exe ou Amplia.Comandos.exe --stdio.')
if '--stdio' in sys.argv or '--batch' in sys.argv:
    from amplia import main
    raise SystemExit(main())
else:
    from amplia_desktop import main
    main()
