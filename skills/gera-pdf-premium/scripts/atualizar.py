#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gera-pdf-premium · atualização da skill (só biblioteca padrão)

  gerar atualizar             confere a última versão publicada no GitHub e, se houver uma mais nova, atualiza
  gerar atualizar --verificar só confere, sem instalar nada

Saída em linhas `CHAVE valor`, terminando em `RESULTADO <estado>`:
  ultima-versao  já está na versão mais recente
  atualizado     pasta da skill substituída pela nova versão (backup e aprendizados preservados)
  disponivel     há versão nova (com --verificar, ou quando a atualização precisa ser feita por outro caminho)
  erro           não foi possível consultar ou instalar

Como atualiza, conforme a forma de instalação:
  plugin         `claude plugin marketplace update` + `claude plugin update` (reiniciar o Claude Code)
  pasta copiada  baixa a release, guarda um backup da versão atual e preserva APRENDIZADOS.md e aprendizados/
  repositório    clone do código-fonte (tem .git): não mexe, orienta a usar `git pull`
"""
import json
import os
import shutil
import ssl
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
import zipfile
from pathlib import Path

REPO = "jesmarcelo/gera-pdf-premium"
MARKETPLACE = "jesmarcelo"
PLUGIN = "gera-pdf-premium"
SKILL_DIR = Path(__file__).resolve().parent.parent
PRESERVAR = ("APRENDIZADOS.md", "aprendizados")
WIN = os.name == "nt"


def linha(chave, valor=""):
    print(f"{chave} {valor}".rstrip(), flush=True)


def fim(estado, codigo=0):
    linha("RESULTADO", estado)
    sys.exit(codigo)


def versao_tupla(v):
    try:
        return tuple(int(p) for p in v.strip().lstrip("vV").split("."))
    except ValueError:
        return ()


def versao_local():
    arq = SKILL_DIR / "VERSAO"
    return arq.read_text(encoding="utf-8").strip() if arq.exists() else "0.0.0"


def baixar(url, destino=None):
    """GET com urllib; se o Python não tiver certificados (comum no macOS), tenta o curl."""
    req = urllib.request.Request(url, headers={"User-Agent": PLUGIN, "Accept": "application/vnd.github+json"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            dados = r.read()
    except urllib.error.HTTPError:
        raise
    except (urllib.error.URLError, ssl.SSLError, TimeoutError) as e:
        curl = shutil.which("curl")
        if not curl:
            raise RuntimeError(f"sem conexão com o GitHub ({e})")
        r = subprocess.run([curl, "-fsSL", "--max-time", "60", "-H", f"User-Agent: {PLUGIN}", url],
                           capture_output=True)
        if r.returncode != 0:
            raise RuntimeError(f"sem conexão com o GitHub ({r.stderr.decode(errors='replace').strip() or e})")
        dados = r.stdout
    if destino:
        Path(destino).write_bytes(dados)
    return dados


def ultima_release():
    try:
        info = json.loads(baixar(f"https://api.github.com/repos/{REPO}/releases/latest"))
    except urllib.error.HTTPError as e:
        if e.code == 404:
            raise RuntimeError("nenhuma versão publicada no GitHub ainda")
        if e.code == 403:
            raise RuntimeError("o GitHub limitou as consultas por hora; tente de novo mais tarde")
        raise RuntimeError(f"o GitHub respondeu {e.code}")
    return info["tag_name"], info.get("html_url", f"https://github.com/{REPO}/releases")


def forma_de_instalacao():
    partes = [p.lower() for p in SKILL_DIR.parts]
    if "plugins" in partes and ("cache" in partes or "marketplaces" in partes):
        return "plugin"
    for p in (SKILL_DIR, *SKILL_DIR.parents[:3]):
        if (p / ".git").exists():
            return "repositorio"
    return "pasta"


def atualizar_plugin():
    claude = shutil.which("claude")
    cmds = [["plugin", "marketplace", "update", MARKETPLACE],
            ["plugin", "update", f"{PLUGIN}@{MARKETPLACE}"]]
    if not claude:
        linha("AVISO", "comando `claude` não encontrado no PATH; rode no terminal:")
        for c in cmds:
            linha("COMANDO", "claude " + " ".join(c))
        fim("disponivel")
    for c in cmds:
        r = subprocess.run([claude, *c], capture_output=True, text=True)
        if r.returncode != 0:
            saida = (r.stderr or r.stdout).strip().splitlines()
            linha("ERRO", saida[-1] if saida else f"falhou: claude {' '.join(c)}")
            linha("COMANDO", "claude " + " ".join(c))
            fim("erro", 1)
    linha("REINICIAR", "feche e abra o Claude Code para carregar a nova versão")
    fim("atualizado")


def extrair(zip_path, destino):
    """Extrai preservando as permissões Unix gravadas no zip (scripts executáveis)."""
    with zipfile.ZipFile(zip_path) as z:
        for info in z.infolist():
            alvo = z.extract(info, destino)
            modo = (info.external_attr >> 16) & 0o777
            if modo and not WIN and not info.is_dir():
                os.chmod(alvo, modo)
    candidatos = list(Path(destino).glob("*/skills/gera-pdf-premium/SKILL.md"))
    if not candidatos:
        raise RuntimeError("o pacote baixado não tem a pasta skills/gera-pdf-premium")
    return candidatos[0].parent


def pasta_backups():  # dentro do projeto, como o ambiente (gerar.py passa GERA_PDF_PREMIUM_BASE)
    base = os.environ.get("GERA_PDF_PREMIUM_BASE") or Path.cwd() / ".gera-pdf-premium"
    return Path(base) / "backups"


def atualizar_pasta(tag, atual):
    with tempfile.TemporaryDirectory(prefix="gera-pdf-premium-") as tmp:
        zip_path = Path(tmp) / "release.zip"
        baixar(f"https://codeload.github.com/{REPO}/zip/refs/tags/{tag}", zip_path)
        nova = extrair(zip_path, Path(tmp) / "x")

        backup = pasta_backups() / f"{atual}-{time.strftime('%Y%m%d-%H%M%S')}"
        backup.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(SKILL_DIR, backup)
        linha("BACKUP", backup)

        try:
            for item in SKILL_DIR.iterdir():
                if item.name in PRESERVAR:
                    continue
                shutil.rmtree(item) if item.is_dir() else item.unlink()
            for item in nova.iterdir():
                alvo = SKILL_DIR / item.name
                if item.name in PRESERVAR and alvo.exists():
                    continue
                shutil.copytree(item, alvo) if item.is_dir() else shutil.copy2(item, alvo)
        except OSError as e:
            linha("ERRO", f"falha ao copiar a nova versão ({e}); restaurando o backup")
            for item in SKILL_DIR.iterdir():
                if item.name not in PRESERVAR:
                    shutil.rmtree(item) if item.is_dir() else item.unlink()
            for item in backup.iterdir():
                if item.name not in PRESERVAR:
                    alvo = SKILL_DIR / item.name
                    shutil.copytree(item, alvo) if item.is_dir() else shutil.copy2(item, alvo)
            fim("erro", 1)
    linha("PRESERVADOS", ", ".join(PRESERVAR))
    fim("atualizado")


def main():
    so_verificar = "--verificar" in sys.argv[1:]
    atual = versao_local()
    forma = forma_de_instalacao()
    linha("INSTALACAO", forma)
    linha("PASTA", SKILL_DIR)
    linha("ATUAL", atual)
    try:
        tag, url = ultima_release()
    except RuntimeError as e:
        linha("ERRO", e)
        fim("erro", 2)
    linha("ULTIMA", tag.lstrip("vV"))
    if versao_tupla(tag) <= versao_tupla(atual):
        fim("ultima-versao")
    linha("NOVIDADES", url)
    if so_verificar:
        fim("disponivel")
    if forma == "plugin":
        atualizar_plugin()
    if forma == "repositorio":
        linha("AVISO", "esta pasta é um clone do repositório; atualize com `git pull`")
        fim("disponivel")
    try:
        atualizar_pasta(tag, atual)
    except (RuntimeError, urllib.error.HTTPError, zipfile.BadZipFile) as e:
        linha("ERRO", e)
        fim("erro", 1)


if __name__ == "__main__":
    main()
