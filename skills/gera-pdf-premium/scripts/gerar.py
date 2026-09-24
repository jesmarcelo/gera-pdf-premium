#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gera-pdf-premium · ponto de entrada multiplataforma (só biblioteca padrão)

  gerar setup                                  prepara/atualiza o ambiente (idempotente)
  gerar converter <arquivo.(md|txt|docx|pdf|srt|vtt)>  qualquer formato → <nome>-ebook/fonte.md
  gerar analisar  <fonte.md>
  gerar redigir-diff <fonte.md> <texto-editado.md>
  gerar build     <fonte.md|texto-editado.md> [--plano P] [--saida X.pdf]
  gerar preview   <arquivo.pdf> [--paginas "1-8,20"] [--saida DIR]
  gerar ocorrencias [--todas] [--marcar-revisadas]
  gerar atualizar [--verificar]                busca a versão mais nova no GitHub e atualiza a skill
  gerar limpar                                 apaga os temporários do projeto (e as folhas do preview)

Nada é gravado fora do projeto (/tmp, /var/folders, /private, ~/.cache…), que pode estar bloqueado.
Tudo fica em <diretório atual>/.gera-pdf-premium/:
  venv/     ambiente Python com as bibliotecas (fica: é usado em toda geração)
  python/   Python baixado pelo `uv`, quando não há um no sistema (fica)
  cache/    cache de downloads do uv e do pip (fica)
  backups/  versões anteriores da skill guardadas pelo `atualizar` (fica)
  tmp/      temporários (TMPDIR/TEMP/TMP apontam para lá): cada execução apaga os seus;
            as folhas do preview ficam em tmp/preview/ até `gerar limpar`
GERA_PDF_PREMIUM_VENV troca a pasta do ambiente. Usa `uv` quando existe; senão, `python -m venv` + pip.
"""
import hashlib
import os
import shutil
import subprocess
import sys
from pathlib import Path

DIR = Path(__file__).resolve().parent
DEPS = ["weasyprint>=62", "markdown-it-py", "mdit-py-plugins", "pypdfium2", "pillow",
        "python-docx", "pdfplumber", "charset-normalizer"]
BASE = Path.cwd() / ".gera-pdf-premium"  # tudo o que a skill grava fora da pasta de trabalho do livro
TMP_RAIZ = BASE / "tmp"
IMPORTS = "import weasyprint, markdown_it, mdit_py_plugins, pypdfium2, PIL, docx, pdfplumber, charset_normalizer"
WIN = os.name == "nt"


def pasta_venv():
    if os.environ.get("GERA_PDF_PREMIUM_VENV"):
        return Path(os.environ["GERA_PDF_PREMIUM_VENV"]).expanduser()
    return BASE / "venv"


VENV = pasta_venv()
PY = VENV / ("Scripts/python.exe" if WIN else "bin/python")
MARCA = VENV / ".gera-pdf-premium-deps"
ASSINATURA = hashlib.sha256("\n".join(DEPS).encode()).hexdigest()[:16]


def achar_uv():
    uv = shutil.which("uv")
    if uv:
        return uv
    for c in (Path.home() / ".local/bin/uv", Path.home() / ".cargo/bin/uv",
              Path.home() / ".local/bin/uv.exe", Path.home() / ".cargo/bin/uv.exe"):
        if c.exists():
            return str(c)
    return None


def erro(msg, codigo=1):
    print(f"ERRO: {msg}", file=sys.stderr)
    sys.exit(codigo)


def dica_pango():
    if sys.platform == "darwin":
        return "brew install pango"
    if WIN:
        return ("instale o GTK3 runtime (MSYS2: `pacman -S mingw-w64-x86_64-pango`) e ponha a pasta bin "
                "no PATH — passo a passo no README.md da skill")
    return "sudo apt install libpango-1.0-0 libpangoft2-1.0-0  (ou: sudo dnf install pango)"


def ambiente_ok():
    if not PY.exists() or not MARCA.exists() or MARCA.read_text().strip() != ASSINATURA:
        return False
    r = subprocess.run([str(PY), "-c", IMPORTS], capture_output=True)
    return r.returncode == 0


def env_projeto(tmp):
    """Ambiente em que temporários e caches (Python, WeasyPrint, Tesseract, uv, pip) caem dentro do projeto."""
    return dict(os.environ, PYTHONIOENCODING="utf-8", PYTHONUTF8="1", TMPDIR=str(tmp), TEMP=str(tmp),
                TMP=str(tmp), UV_CACHE_DIR=str(BASE / "cache" / "uv"), PIP_CACHE_DIR=str(BASE / "cache" / "pip"),
                UV_PYTHON_INSTALL_DIR=str(BASE / "python"), GERA_PDF_PREMIUM_BASE=str(BASE),
                GERA_PDF_PREMIUM_TMP=str(TMP_RAIZ))


def preparar_base():
    BASE.mkdir(exist_ok=True)
    ign = BASE / ".gitignore"  # o ambiente nunca entra no git do projeto
    if not ign.exists():
        ign.write_text("*\n")


def limpar(tudo=False):
    if tudo:
        shutil.rmtree(TMP_RAIZ, ignore_errors=True)
        return
    if not any(TMP_RAIZ.glob("exec-*")):  # 'boot' (do wrapper) só sai sem outra execução em curso
        shutil.rmtree(TMP_RAIZ / "boot", ignore_errors=True)
    try:  # a raiz só sai se ficou vazia (o preview pode estar lá)
        TMP_RAIZ.rmdir()
    except OSError:
        pass


def setup(env=None):
    uv = achar_uv()
    VENV.parent.mkdir(parents=True, exist_ok=True)
    if uv:
        if not PY.exists():
            subprocess.run([uv, "venv", "--quiet", "--python", "3.12", str(VENV)], check=True, env=env)
        subprocess.run([uv, "pip", "install", "--quiet", "--python", str(PY), *DEPS], check=True, env=env)
    else:
        if sys.version_info < (3, 10):
            erro("é preciso Python 3.10+ ou o `uv` — rode `gerar verificar` para ver como instalar")
        if not PY.exists():
            subprocess.run([sys.executable, "-m", "venv", str(VENV)], check=True, env=env)
        subprocess.run([str(PY), "-m", "pip", "install", "--quiet", "--upgrade", "pip"], check=True, env=env)
        subprocess.run([str(PY), "-m", "pip", "install", "--quiet", *DEPS], check=True, env=env)
    r = subprocess.run([str(PY), "-c", IMPORTS + "; print(weasyprint.__version__)"],
                       capture_output=True, text=True, env=env)
    if r.returncode != 0:
        detalhe = (r.stderr.strip().splitlines() or [""])[-1]
        erro(f"o WeasyPrint precisa da biblioteca Pango do sistema ({detalhe}).\n"
             f"       Instale com: {dica_pango()}")
    MARCA.write_text(ASSINATURA)
    print(f"gera-pdf-premium: ambiente OK · WeasyPrint {r.stdout.strip()} · {VENV}")


def main():
    args = sys.argv[1:]
    if args[:1] == ["limpar"]:
        limpar(tudo=True)
        print(f"gera-pdf-premium: {TMP_RAIZ} apagada")
        return
    preparar_base()
    tmp = TMP_RAIZ / f"exec-{os.getpid()}"
    tmp.mkdir(parents=True, exist_ok=True)
    env = env_projeto(tmp)
    os.environ.update(env)  # ambiente_ok e qualquer outro subprocesso herdam
    try:
        if args[:1] == ["setup"]:
            setup(env)
            return
        if args[:1] == ["atualizar"]:
            r = subprocess.run([sys.executable, str(DIR / "atualizar.py"), *args[1:]], env=env)
            sys.exit(r.returncode)
        if not ambiente_ok():
            print("gera-pdf-premium: preparando o ambiente (só na primeira vez)…", file=sys.stderr)
            setup(env)
        r = subprocess.run([str(PY), str(DIR / "motor.py"), *args], env=env)
        sys.exit(r.returncode)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
        limpar()


if __name__ == "__main__":
    main()
