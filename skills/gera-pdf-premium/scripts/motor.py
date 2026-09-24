#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gera-pdf-premium · motor de composição editorial (qualquer texto → ebook PDF premium)

Subcomandos
  converter <arquivo.(md|txt|docx|pdf)>          normaliza para <nome>-ebook/fonte.md + conversao.md
  analisar  <fonte.md>                            relatório estrutural + pasta de trabalho
  redigir-diff <fonte.md> <texto-editado.md>      diff parágrafo a parágrafo da melhoria de redação
  build     <fonte.md> [--plano P] [--saida X]    compõe HTML, verifica integridade, gera PDF
  preview   <arquivo.pdf> [--paginas "1-8,20"]    folhas de contato PNG + auditoria do PDF
  ocorrencias [--todas] [--marcar-revisadas]      falhas registradas (memória da skill)

Princípio inegociável
  O texto da fonte é apenas RE-FLUÍDO e ESTILIZADO — fora os cortes e as
  pequenas correções declarados no plano, aplicados em memória e registrados
  em cortes.md / correcoes.md. Todo elemento do HTML
  final que carrega texto da fonte recebe o atributo `data-src`; tudo o mais é
  editorial (capa, sumário, títulos de navegação, rótulos, glossário, figuras).
  O build extrai o texto de todos os `data-src` do HTML FINAL e compara com o
  texto do Markdown renderizado — ignorando apenas espaços em branco e a forma
  das aspas. Qualquer divergência aborta o build (código 3). A fonte (e o
  arquivo original de onde ela foi convertida) nunca é aberta para escrita;
  o SHA-256 é conferido antes e depois.
"""

import argparse
import collections
import datetime
import hashlib
import html
import json
import os
import re
import sys
import unicodedata
from html.parser import HTMLParser
from pathlib import Path

SKILL = Path(__file__).resolve().parent.parent
CSS_BASE = SKILL / "assets" / "ebook.css"

# ============================================================
# TEMAS
# ============================================================
PRESETS = {
    # espiritualidade, esoterismo, filosofia, luxo
    "noite-ouro": dict(escuro="#101627", escuro2="#1B2440", acento="#B08A3E",
                       acento_claro="#D9BE7E", acento_lavado="#F1E7D2",
                       papel="#FCFAF6", claro="#F3E9D2", texto_caixa="#4A3A18"),
    # tecnologia, negócios, relatórios executivos
    "grafite-cobre": dict(escuro="#1C1F24", escuro2="#2B3038", acento="#B4693E",
                          acento_claro="#E3A57A", acento_lavado="#F6E6DA",
                          papel="#FBFAF8", claro="#F4ECE6", texto_caixa="#4E2C18"),
    # saúde, natureza, bem-estar, educação
    "floresta-latao": dict(escuro="#13261F", escuro2="#1F3A2F", acento="#A68A3A",
                           acento_claro="#D6C07A", acento_lavado="#EFE9D2",
                           papel="#FAF9F4", claro="#EFEBDD", texto_caixa="#3F3714"),
    # literatura, história, direito, humanidades
    "bordo-creme": dict(escuro="#3A1420", escuro2="#52202E", acento="#A8743A",
                        acento_claro="#DDB57E", acento_lavado="#F4E6D6",
                        papel="#FCF8F2", claro="#F6EBDD", texto_caixa="#4A2E14"),
    # ciência, dados, engenharia, software
    "oceano-prata": dict(escuro="#0F2233", escuro2="#1A3349", acento="#3D7EA6",
                         acento_claro="#9CC7E0", acento_lavado="#E3EFF6",
                         papel="#FAFBFC", claro="#EAF2F7", texto_caixa="#173247"),
}
# Fontes livres (OFL) embutidas em assets/fontes: o PDF sai igual em macOS, Linux e Windows.
# As do sistema ficam só como reserva para caracteres fora do latim (hebraico, grego…).
FONTES_PADRAO = {
    "serif": '"GP Source Serif 4", "Iowan Old Style", "Noto Serif", Georgia, serif',
    "display": '"GP Cormorant Garamond", "Didot", "Noto Serif Display", Garamond, serif',
    "sans": '"GP Inter", "Avenir Next", "Noto Sans", Helvetica, sans-serif',
    "mono": '"GP JetBrains Mono", "Menlo", "DejaVu Sans Mono", monospace',
}
DIR_FONTES = SKILL / "assets" / "fontes"
FAMILIAS_EMBUTIDAS = {"GP Source Serif 4": "source-serif-4", "GP Cormorant Garamond": "cormorant-garamond",
                      "GP Inter": "inter", "GP JetBrains Mono": "jetbrains-mono"}
FAIXAS = {"latin": "U+0000-00FF, U+0131, U+0152-0153, U+02BB-02BC, U+02C6, U+02DA, U+02DC, U+0304, U+0308, "
                   "U+0329, U+2000-206F, U+20AC, U+2122, U+2191, U+2193, U+2212, U+2215, U+FEFF, U+FFFD",
          "latin-ext": "U+0100-02BA, U+02BD-02C5, U+02C7-02CC, U+02CE-02D7, U+02DD-02FF, U+0304, U+0308, "
                       "U+0329, U+1D00-1DBF, U+1E00-1E9F, U+1EF2-1EFF, U+2020, U+20A0-20AB, U+20AD-20C0, "
                       "U+2113, U+2C60-2C7F, U+A720-A7FF"}


def css_fontes():
    """@font-face para cada arquivo em assets/fontes (<familia>-<faixa>-<peso>-<estilo>.woff2)."""
    regras = []
    for fam, pref in FAMILIAS_EMBUTIDAS.items():
        for arq in sorted(DIR_FONTES.glob(f"{pref}-*.woff2")):
            m = re.match(rf"{re.escape(pref)}-(latin-ext|latin)-(\d+)-(normal|italic)\.woff2$", arq.name)
            if not m:
                continue
            faixa, peso, estilo = m.groups()
            regras.append(f'@font-face {{ font-family: "{fam}"; src: url("{arq.as_uri()}") format("woff2"); '
                          f"font-weight: {peso}; font-style: {estilo}; unicode-range: {FAIXAS[faixa]}; }}")
    return "\n".join(regras) + "\n"
FIXAS = {"tinta": "#1B1E28", "tinta_suave": "#4A5163", "tinta_fraca": "#8A90A2"}
FORMATOS = {"152x229": (152, 229), "6x9": (152, 229), "a5": (148, 210),
            "b5": (176, 250), "a4": (210, 297), "quadrado": (200, 200)}

ROTULO_ALERTA = {"NOTE": "Nota", "TIP": "Dica", "IMPORTANT": "Importante",
                 "WARNING": "Atenção", "CAUTION": "Cuidado"}
RE_ALERTA = re.compile(r"\[!(NOTE|TIP|IMPORTANT|WARNING|CAUTION)\]", re.I)
TIPOS_CAIXA = {"ritual", "dialogo", "nota", "alerta", "exemplo", "termos"}


# ============================================================
# UTILITÁRIOS
# ============================================================
# Memória da skill: toda falha do motor é registrada aqui para a retrospectiva
# (SKILL.md, passo 8). `gerar ocorrencias` lista o que ainda não foi revisado.
DIR_APRENDIZADOS = Path(__file__).resolve().parent.parent / "aprendizados"
LOG_OCORRENCIAS = DIR_APRENDIZADOS / "ocorrencias.jsonl"
MARCA_REVISAO = DIR_APRENDIZADOS / "revisado_ate.txt"
CONTEXTO = {"cmd": None, "arquivo": None}


def registrar_ocorrencia(tipo, msgs, codigo=None):
    try:
        import time
        DIR_APRENDIZADOS.mkdir(parents=True, exist_ok=True)
        reg = {"data": time.strftime("%Y-%m-%dT%H:%M:%S"), "tipo": tipo, "codigo": codigo,
               **CONTEXTO, "mensagens": [str(m) for m in msgs]}
        with LOG_OCORRENCIAS.open("a", encoding="utf-8") as f:
            f.write(json.dumps(reg, ensure_ascii=False) + "\n")
    except Exception:
        pass  # o registro nunca pode derrubar o build


def falhar(msgs, codigo=2):
    msgs = [msgs] if isinstance(msgs, str) else list(msgs)
    registrar_ocorrencia("erro", msgs, codigo)
    for m in msgs:
        print(f"ERRO: {m}", file=sys.stderr)
    sys.exit(codigo)


def nome_arquivo(s):
    """Nome de arquivo legível (mantém acentos e espaços), seguro para o sistema de arquivos."""
    return re.sub(r'[\\/:*?"<>|]+', "-", norm_ws(s)).strip(" .-") or "ebook"


def esc(s):
    return html.escape(str(s), quote=False)


def esc_attr(s):
    return html.escape(str(s), quote=True)


def pl(n, singular, plural):
    """Concordância de número: pl(1, 'trecho', 'trechos') → 'trecho'."""
    return singular if n == 1 else plural


def sha256(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def slug(s):
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()
    return re.sub(r"[^A-Za-z0-9]+", "-", s).strip("-") or "ebook"


def norm_ws(s):
    return " ".join(str(s).split())


def texto_de_html(h):
    return html.unescape(re.sub(r"<[^>]+>", "", h))


def pasta_trabalho(md_path):
    # fonte.md / texto-editado.md criados por `converter` já moram na pasta de trabalho
    if (md_path.parent / "conversao.json").exists():
        return md_path.parent
    return md_path.parent / f"{md_path.stem}-ebook"


def info_conversao(md_path):
    """Dados de `converter` (original, hash, tipo de fonte, base das imagens) ou {} para um .md avulso."""
    p = md_path.parent / "conversao.json"
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {}


def base_imagens(md_path):
    b = info_conversao(md_path).get("base_imagens")
    return Path(b) if b else md_path.parent


# ============================================================
# MARKDOWN
# ============================================================
def criar_md(tipografia=True):
    from markdown_it import MarkdownIt
    from mdit_py_plugins.footnote import footnote_plugin
    from mdit_py_plugins.front_matter import front_matter_plugin
    from mdit_py_plugins.tasklists import tasklists_plugin

    md = MarkdownIt("commonmark", {"typographer": tipografia, "html": True})
    md.enable(["table", "strikethrough"])
    if tipografia:
        md.enable(["replacements", "smartquotes"])
    md.use(front_matter_plugin).use(footnote_plugin).use(tasklists_plugin)
    return md


def juntar_linhas(raw):
    """Quebras de linha 'moles' do Markdown viram espaço; quebras duras ficam."""
    linhas = raw.split("\n")
    out = []
    for k, ln in enumerate(linhas):
        out.append(ln)
        if k < len(linhas) - 1:
            out.append("\n" if (ln.endswith("  ") or ln.endswith("\\")) else " ")
    return "".join(out)


TIPO_BLOCO = {
    "bullet_list_open": "lista", "ordered_list_open": "lista",
    "table_open": "tabela", "fence": "codigo", "code_block": "codigo",
    "blockquote_open": "citacao", "hr": "hr", "html_block": "html",
    "footnote_block_open": "notas", "front_matter": "frontmatter",
}


def extrair_unidades(md, texto):
    """Quebra o documento em unidades de nível superior, na ordem da fonte."""
    env = {}
    tokens = md.parse(texto, env)
    unidades = []
    i = 0
    while i < len(tokens):
        t = tokens[i]
        if t.nesting == 1:
            # casa pelo TIPO de fechamento, com profundidade: footnote_open/close
            # também vivem no nível 0 dentro de footnote_block
            fecha = t.type[:-5] + "_close" if t.type.endswith("_open") else None
            j, prof = i + 1, 1
            while j < len(tokens):
                if tokens[j].type == t.type:
                    prof += 1
                elif tokens[j].type == fecha:
                    prof -= 1
                    if prof == 0:
                        break
                j += 1
            fim = j + 1
        else:
            fim = i + 1
        fatia = tokens[i:fim]

        if t.type == "heading_open":
            inline = tokens[i + 1]
            h = md.renderer.render([inline], md.options, env)
            unidades.append(dict(tipo="h", nivel=int(t.tag[1]), raw=inline.content,
                                 inner=h, plano=norm_ws(texto_de_html(h)), ancoras=set()))
        elif t.type == "paragraph_open":
            inline = tokens[i + 1]
            filhos = [c for c in (inline.children or [])
                      if not (c.type == "softbreak" or (c.type == "text" and not c.content.strip()))]
            h = md.renderer.render([inline], md.options, env)
            if len(filhos) == 1 and filhos[0].type == "image":
                img = filhos[0]
                unidades.append(dict(tipo="img", inner=h, alt=img.content,
                                     titulo=img.attrs.get("title") or "", ancoras=set()))
            else:
                unidades.append(dict(tipo="p", raw=juntar_linhas(inline.content), inner=h,
                                     nota="[^" in inline.content, ancoras=set()))
        else:
            tipo = TIPO_BLOCO.get(t.type, "bloco")
            h = md.renderer.render(fatia, md.options, env)
            u = dict(tipo=tipo, html=h, ancoras=set())
            if tipo == "codigo":
                u["lang"] = (t.info or "").strip().split(" ")[0]
            if tipo == "citacao":
                primeiro = next((x for x in fatia if x.type == "inline"), None)
                m = RE_ALERTA.match(primeiro.content.lstrip()) if primeiro else None
                if m:
                    u["tipo"] = "alerta"
                    u["alerta"] = m.group(1).upper()
                    u["html"] = RE_ALERTA.sub("", h, count=1)
            if tipo != "frontmatter":
                unidades.append(u)
        i = fim
    return unidades, env


# ============================================================
# REFLUXO (texto corrido → parágrafos) — nunca altera caracteres
# ============================================================
ABREV = {"sr", "sra", "srta", "dr", "dra", "prof", "profa", "p", "pp", "ex", "etc",
         "fig", "cap", "vol", "n", "art", "obs", "av", "sto", "sta", "s", "esq",
         "dir", "min", "máx", "mín", "aprox", "tel", "vs", "cf", "ed", "org"}
RE_CORTE = re.compile(r'[.!?…]["”’»)\]]*\s+(?=\S)')


def equilibrado(pre):
    sem_duplo = pre.replace("**", "")
    return (pre.count("`") % 2 == 0 and pre.count("**") % 2 == 0
            and sem_duplo.count("*") % 2 == 0 and pre.count("[") == pre.count("]")
            and pre.count('"') % 2 == 0 and pre.count("<") == pre.count(">"))


def cortes_de_frase(s):
    pos = []
    for m in RE_CORTE.finditer(s):
        fim = m.end()
        prox = s[fim:fim + 1]
        if prox.islower() or prox.isdigit():
            continue
        if s[m.start()] == ".":
            w = re.search(r"(\w+)$", s[max(0, m.start() - 15):m.start()])
            if w and w.group(1).lower() in ABREV:
                continue
        if not equilibrado(s[:fim]):
            continue
        pos.append(fim)
    return pos


def refluir(s, alvo, maximo):
    paras, ini, n = [], 0, 0
    for p in cortes_de_frase(s):
        n += 1
        tam = p - ini
        if tam >= alvo and (tam >= maximo or n >= 3):
            paras.append(s[ini:p])
            ini, n = p, 0
    paras.append(s[ini:])
    return [x.strip() for x in paras if x.strip()]


def aplicar_ancoras(md, env, unidades, ancoras, rf, erros):
    """Localiza cada âncora (literal e única), corta parágrafos nela e reflui."""
    ocorr = {a: 0 for a in ancoras}
    for u in unidades:
        if u["tipo"] == "p":
            for a in ancoras:
                ocorr[a] += u["raw"].count(a)
    for a, n in ocorr.items():
        if n == 0:
            erros.append(f"âncora não encontrada: {a[:90]!r} — copie o trecho LITERAL do .md, "
                         "dentro de um único parágrafo, sem marcação Markdown")
        elif n > 1:
            erros.append(f"âncora ambígua ({n}×): {a[:90]!r} — estenda o trecho até ficar único")
    if erros:
        return unidades

    novas = []
    for u in unidades:
        if u["tipo"] != "p":
            novas.append(u)
            continue
        raw = u["raw"]
        presentes = [a for a in ancoras if a in raw]
        cortes = sorted({raw.index(a) for a in presentes} - {0})
        for c in cortes:
            if not equilibrado(raw[:c]):
                erros.append(f"âncora cai dentro de marcação (negrito/link/código/aspas): "
                             f"{raw[c:c + 70]!r}")
        if u["nota"] and (cortes or len(raw) > rf["limite"]):
            if cortes:
                erros.append("âncora dentro de parágrafo com nota de rodapé [^…] — escolha "
                             f"outro ponto: {raw[cortes[0]:cortes[0] + 60]!r}")
            u["ancoras"] = {a for a in presentes if raw.startswith(a)}
            novas.append(u)
            continue

        # Cada âncora pertence ao pedaço que começa na POSIÇÃO dela — não ao pedaço cujo
        # texto começa com ela. Assim uma âncora que começa dentro de outra (ex.: caixa
        # "Para um…" dentro do capítulo "Vamos ver. Perguntas aqui. Para um…") não
        # apaga a de fora.
        pos = {a: raw.index(a) for a in presentes}
        bordas = [0] + cortes + [len(raw)]
        pedacos = []  # (posição em raw, texto)
        for x, y in zip(bordas, bordas[1:]):
            seg = raw[x:y]
            pe = seg.strip()
            if not pe:
                continue
            base = x + len(seg) - len(seg.lstrip())
            cur = 0
            for pp in (refluir(pe, rf["alvo"], rf["maximo"]) if len(pe) > rf["limite"] else [pe]):
                i = pe.find(pp, cur)
                i = cur if i < 0 else i
                pedacos.append((base + i, pp))
                cur = i + len(pp)

        if len(pedacos) == 1 and pedacos[0][1] == raw.strip():
            u["ancoras"] = {a for a in presentes if pos[a] == pedacos[0][0]}
            novas.append(u)
            continue
        for off, pe in pedacos:
            novas.append(dict(tipo="p", raw=pe, inner=md.renderInline(pe, env), nota=False,
                              refluido=True, ancoras={a for a in presentes if pos[a] == off}))
    return novas


# ============================================================
# ORNAMENTOS
# ============================================================
def ornamento(cor, w=54):
    return (f'<svg width="{w}" height="10" viewBox="0 0 54 10" xmlns="http://www.w3.org/2000/svg">'
            f'<line x1="0" y1="5" x2="19" y2="5" stroke="{cor}" stroke-width=".6"/>'
            f'<line x1="35" y1="5" x2="54" y2="5" stroke="{cor}" stroke-width=".6"/>'
            f'<path d="M27 .6 L31 5 L27 9.4 L23 5 Z" fill="none" stroke="{cor}" stroke-width=".7"/></svg>')


def selo(tipo, cor):
    base = ('<svg width="46" height="46" viewBox="0 0 46 46" xmlns="http://www.w3.org/2000/svg">'
            f'<circle cx="23" cy="23" r="22" fill="none" stroke="{cor}" stroke-width=".6" opacity=".55"/>'
            f'<circle cx="23" cy="23" r="17.5" fill="none" stroke="{cor}" stroke-width=".4" opacity=".35"/>')
    miolo = {
        "hexagrama": f'<path d="M23 8 L36 30.5 L10 30.5 Z M23 38 L10 15.5 L36 15.5 Z" fill="none" '
                     f'stroke="{cor}" stroke-width=".7" opacity=".85"/>',
        "losango": f'<path d="M23 9 L32 23 L23 37 L14 23 Z" fill="none" stroke="{cor}" '
                   f'stroke-width=".8" opacity=".85"/><circle cx="23" cy="23" r="2" fill="{cor}" opacity=".7"/>',
        "estrela": f'<path d="M23 9 L27 19 L37 23 L27 27 L23 37 L19 27 L9 23 L19 19 Z" fill="none" '
                   f'stroke="{cor}" stroke-width=".7" opacity=".85"/>',
        "circulo": f'<circle cx="23" cy="23" r="9" fill="none" stroke="{cor}" stroke-width=".7" opacity=".8"/>'
                   f'<circle cx="23" cy="23" r="2.2" fill="{cor}" opacity=".8"/>',
    }
    if tipo == "nenhum":
        return ""
    return base + miolo.get(tipo, miolo["losango"]) + "</svg>"


# ============================================================
# FIGURAS
# ============================================================
def figura_html(fig, base_plano, md, env):
    larg = float(fig.get("largura_mm", 95))
    alt_max = float(fig.get("altura_max_mm", 105))
    rot = fig.get("rotulo", "")
    leg = fig.get("legenda", "")

    if "svg" in fig:
        caminho = (base_plano / fig["svg"]).resolve()
        if not caminho.exists():
            falhar(f"figura SVG não encontrada: {caminho}")
        svg = caminho.read_text(encoding="utf-8")
        svg = re.sub(r"<\?xml.*?\?>", "", svg, flags=re.S)
        svg = re.sub(r"<!DOCTYPE.*?>", "", svg, flags=re.S).strip()
        raiz = re.match(r"<svg\b[^>]*>", svg)
        if not raiz:
            falhar(f"arquivo não parece SVG: {caminho}")
        tag = raiz.group(0)
        vb = re.search(r'viewBox="\s*([-\d.]+)[\s,]+([-\d.]+)[\s,]+([-\d.]+)[\s,]+([-\d.]+)\s*"', tag)
        if vb:
            w, h = float(vb.group(3)), float(vb.group(4))
        else:
            wm = re.search(r'\swidth="([\d.]+)', tag)
            hm = re.search(r'\sheight="([\d.]+)', tag)
            if not (wm and hm):
                falhar(f"SVG sem viewBox nem width/height: {caminho}")
            w, h = float(wm.group(1)), float(hm.group(1))
            tag = tag.replace("<svg", f'<svg viewBox="0 0 {w:g} {h:g}"', 1)
        W, H = larg, larg * h / w
        if H > alt_max:
            H, W = alt_max, alt_max * w / h
        nova = re.sub(r'\s(width|height)="[^"]*"', "", tag)
        nova = nova.replace("<svg", f'<svg width="{W:.1f}mm" height="{H:.1f}mm"', 1)
        corpo = nova + svg[raiz.end():]
    elif "imagem" in fig:
        from PIL import Image
        caminho = (base_plano / fig["imagem"]).resolve()
        if not caminho.exists():
            falhar(f"figura não encontrada: {caminho}")
        with Image.open(caminho) as im:
            w, h = im.size
        W, H = larg, larg * h / w
        if H > alt_max:
            H, W = alt_max, alt_max * w / h
        corpo = f'<img src="{caminho.as_uri()}" alt="" style="width:{W:.1f}mm;height:{H:.1f}mm">'
    else:
        falhar(f"figura sem 'svg' nem 'imagem': {fig}")

    cap = ""
    if leg or rot:
        cap = (f"<figcaption>{f'<b>{esc(rot)}</b>' if rot else ''}"
               f"{md.renderInline(leg, env) if leg else ''}</figcaption>")
    return f'<figure class="fig-editorial">{corpo}{cap}</figure>'


# ============================================================
# INTEGRIDADE
# ============================================================
class Extrator(HTMLParser):
    VAZIOS = {"img", "br", "hr", "meta", "link", "input", "source", "wbr", "col",
              "area", "base", "embed", "param", "track"}

    def __init__(self, so_fonte):
        super().__init__(convert_charrefs=True)
        self.so_fonte = so_fonte
        self.pilha = []
        self.partes = []

    def _ativo(self):
        if not self.so_fonte:
            return True
        return bool(self.pilha) and self.pilha[-1][0] and not self.pilha[-1][1]

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        src = (self.pilha[-1][0] if self.pilha else False) or ("data-src" in a)
        ed = (self.pilha[-1][1] if self.pilha else False) or ("data-editorial" in a)
        if tag == "img" and (not self.so_fonte or (src and not ed)):
            self.partes.append(a.get("alt") or "")
        if tag in self.VAZIOS:
            return
        self.pilha.append((src, ed, tag))

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag not in self.VAZIOS and self.pilha and self.pilha[-1][2] == tag:
            self.pilha.pop()

    def handle_endtag(self, tag):
        for k in range(len(self.pilha) - 1, -1, -1):
            if self.pilha[k][2] == tag:
                del self.pilha[k:]
                break

    def handle_data(self, d):
        if self._ativo():
            self.partes.append(d)


ASPAS = str.maketrans({"“": '"', "”": '"', "„": '"', "«": '"', "»": '"', "″": '"',
                       "‘": "'", "’": "'", "‚": "'", "‹": "'", "›": "'", "′": "'"})


def para_comparar(s):
    s = unicodedata.normalize("NFC", s).translate(ASPAS)
    return re.sub(r"\s+", "", s)


def _padrao_literal(s):
    """Trecho literal do .md; qualquer sequência de espaços/quebras casa com \\s+."""
    return re.compile(r"\s+".join(re.escape(p) for p in s.split()))


def aplicar_cortes(fonte, cortes):
    """Remove da fonte, em memória, os trechos declarados em plano["cortes"].
    O .md em disco nunca é tocado; a integridade passa a valer contra o texto cortado.
    Cada corte: {"inicio"|"trecho": literal, "fim": literal exclusivo (opcional),
    "ate_fim_do_paragrafo": bool, "ocorrencia": n (1…), "motivo": str}."""
    if not cortes:
        return fonte, [], []
    spans, erros = [], []
    for n, c in enumerate(cortes, 1):
        ini = (c.get("inicio") or c.get("trecho") or "").strip()
        if not ini:
            erros.append(f"corte {n}: falta \"inicio\" (ou \"trecho\")")
            continue
        achados = list(_padrao_literal(ini).finditer(fonte))
        oc = c.get("ocorrencia")
        if not achados:
            erros.append(f"corte {n}: início não encontrado: {ini[:70]!r}")
            continue
        if oc is None and len(achados) > 1:
            erros.append(f"corte {n}: início aparece {len(achados)}× — use \"ocorrencia\" ou estenda o trecho: {ini[:70]!r}")
            continue
        if oc is not None and not 1 <= oc <= len(achados):
            erros.append(f"corte {n}: \"ocorrencia\" {oc} fora de 1–{len(achados)}")
            continue
        m = achados[(oc or 1) - 1]
        s = m.start()
        if c.get("fim"):
            mf = _padrao_literal(c["fim"].strip()).search(fonte, m.end())
            if not mf:
                erros.append(f"corte {n}: fim não encontrado depois do início: {c['fim'][:70]!r}")
                continue
            e = mf.start()
        elif c.get("ate_fim_do_paragrafo"):
            mp = re.compile(r"\n[ \t]*\n").search(fonte, m.end())
            e = mp.start() if mp else len(fonte)
        else:
            e = m.end()
            # leva o espaço seguinte junto, sem nunca engolir uma linha em branco
            e += re.match(r"[ \t]*(?:\n(?![ \t]*\n)[ \t]*)?", fonte[e:]).end()
        spans.append((s, e, c.get("motivo", "").strip(), n))
    spans.sort()
    for a, b in zip(spans, spans[1:]):
        if b[0] < a[1]:
            erros.append(f"cortes {a[3]} e {b[3]} se sobrepõem")
    if erros:
        return fonte, [], erros
    registros, out = [], fonte
    for s, e, motivo, n in reversed(spans):
        trecho = fonte[s:e]
        registros.append({"n": n, "motivo": motivo, "texto": " ".join(trecho.split()),
                          "palavras": len(trecho.split())})
        out = out[:s] + out[e:]
    registros.reverse()
    return out, registros, []


def _palavras(s):
    return re.findall(r"[^\W\d_]+", unicodedata.normalize("NFC", s).lower())


def aplicar_correcoes(fonte, correcoes):
    """Aplica, em memória, as pequenas correções declaradas em plano["correcoes"]
    (ortografia, gramática, erros evidentes de transcrição). O .md nunca é tocado;
    a integridade passa a valer contra o texto corrigido e cada troca é registrada.
    Cada correção: {"de": literal, "para": texto, "ocorrencia": n (1…) | "todas": true,
    "motivo": str}. Trava contra reescrita: "de" com no máximo 40 palavras e "para"
    com no máximo 3 palavras novas (ou 25% das palavras de "para", o que for maior)."""
    if not correcoes:
        return fonte, [], []
    spans, erros = [], []
    for n, c in enumerate(correcoes, 1):
        de = (c.get("de") or "").strip()
        para = c.get("para")
        if not de or para is None:
            erros.append(f"correção {n}: exige \"de\" e \"para\"")
            continue
        para = " ".join(para.split())
        if len(de.split()) > 40:
            erros.append(f"correção {n}: \"de\" com {len(de.split())} palavras (máx. 40) — "
                         f"correção não é reescrita: {de[:70]!r}")
            continue
        novas = [w for w in _palavras(para) if w not in set(_palavras(de))]
        if len(novas) > max(3, len(_palavras(para)) // 4):
            erros.append(f"correção {n}: {len(novas)} palavras novas ({', '.join(novas[:8])}) — "
                         f"isso é paráfrase, não correção: {de[:70]!r}")
            continue
        achados = list(_padrao_literal(de).finditer(fonte))
        oc = c.get("ocorrencia")
        if not achados:
            erros.append(f"correção {n}: trecho não encontrado (depois dos cortes): {de[:70]!r}")
            continue
        if c.get("todas"):
            alvos = achados
        elif oc is None and len(achados) > 1:
            erros.append(f"correção {n}: trecho aparece {len(achados)}× — use \"ocorrencia\", "
                         f"\"todas\": true ou estenda o trecho: {de[:70]!r}")
            continue
        elif oc is not None and not 1 <= oc <= len(achados):
            erros.append(f"correção {n}: \"ocorrencia\" {oc} fora de 1–{len(achados)}")
            continue
        else:
            alvos = [achados[(oc or 1) - 1]]
        for m in alvos:
            spans.append((m.start(), m.end(), para, c.get("motivo", "").strip(), n))
    spans.sort()
    for a, b in zip(spans, spans[1:]):
        if b[0] < a[1]:
            erros.append(f"correções {a[4]} e {b[4]} se sobrepõem")
    if erros:
        return fonte, [], erros
    por_n, out = {}, fonte
    for s, e, para, motivo, n in reversed(spans):
        r = por_n.setdefault(n, {"n": n, "motivo": motivo, "de": " ".join(fonte[s:e].split()),
                                 "para": para, "vezes": 0})
        r["vezes"] += 1
        out = out[:s] + para + out[e:]
    return out, [por_n[k] for k in sorted(por_n)], []


def verificar_integridade(md, fonte, doc_html):
    e1 = Extrator(so_fonte=False)
    e1.feed(md.render(fonte, {}))
    esperado = para_comparar(RE_ALERTA.sub("", "".join(e1.partes)))
    e2 = Extrator(so_fonte=True)
    e2.feed(doc_html)
    obtido = para_comparar("".join(e2.partes))
    if esperado == obtido:
        return True, len(esperado), ""
    i = 0
    while i < min(len(esperado), len(obtido)) and esperado[i] == obtido[i]:
        i += 1
    return False, len(esperado), (
        f"primeira divergência no caractere {i} de {len(esperado)} (sem espaços)\n"
        f"  fonte : …{esperado[max(0, i - 60):i + 60]}…\n"
        f"  ebook : …{obtido[max(0, i - 60):i + 60]}…\n"
        f"  (fonte {len(esperado)} × ebook {len(obtido)} caracteres)")


# ============================================================
# ANALISAR
# ============================================================
# ============================================================
# CONVERTER — qualquer formato → fonte.md
# ============================================================
def cmd_converter(args):
    from conversores import ErroConversao, converter
    orig = Path(args.arquivo).expanduser().resolve()
    if not orig.exists() or orig.is_dir():
        falhar(f"arquivo não encontrado: {orig}")
    wd = orig.parent / f"{orig.stem}-ebook"
    cj = wd / "conversao.json"
    if cj.exists():
        try:
            ant = json.loads(cj.read_text(encoding="utf-8")).get("original")
        except Exception:
            ant = None
        if ant and Path(ant) != orig:  # "Aula.md" e "Aula.pdf" na mesma pasta
            wd = orig.parent / f"{orig.stem} ({orig.suffix[1:].lower()})-ebook"
    wd.mkdir(exist_ok=True)
    (wd / "figuras").mkdir(exist_ok=True)

    h = sha256(orig)
    try:
        md, info = converter(orig, wd, getattr(args, "idioma", None))
    except ErroConversao as e:
        falhar(str(e))
    if sha256(orig) != h:
        falhar("o arquivo original mudou durante a conversão — isso nunca deveria acontecer", 4)

    fonte = wd / "fonte.md"
    antigo = fonte.read_bytes() if fonte.exists() else None
    if info.get("copia_exata"):
        fonte.write_bytes(orig.read_bytes())
    else:
        fonte.write_text(md, encoding="utf-8")
    texto = fonte.read_text(encoding="utf-8")
    info.update(original=str(orig), sha256=h, fonte=str(fonte), fonte_sha256=sha256(fonte),
                base_imagens=str(orig.parent if info["formato"] == "markdown" else wd),
                data=datetime.datetime.now().isoformat(timespec="seconds"))

    # sugestões para o questionário
    m_h1 = re.search(r"(?m)^# +(.+?)\s*#*\s*$", texto)
    titulos = []
    for t in (info["metadados"].get("titulo"), m_h1.group(1) if m_h1 else None,
              re.sub(r"[_]+", " ", orig.stem).strip()):
        t = norm_ws(re.sub(r"[*_`\\]", "", t or ""))
        if t and t not in titulos and len(t) <= 120:
            titulos.append(t)
    info["sugestoes"] = {"titulos": titulos,
                         "autores": [a for a in [info["metadados"].get("autor")] if a]}
    serie = []
    for irma in sorted(orig.parent.glob("*-ebook")):
        pl = irma / "plano.json"
        if irma != wd and pl.exists():
            try:
                pj = json.loads(pl.read_text(encoding="utf-8"))
                serie.append({"plano": str(pl), "titulo": pj.get("meta", {}).get("titulo"),
                              "subtitulo": pj.get("meta", {}).get("subtitulo"),
                              "autores": pj.get("meta", {}).get("autores"), "tema": pj.get("tema", {})})
            except Exception:
                pass
    info["serie"] = serie
    cj = wd / "conversao.json"
    cj.write_text(json.dumps(info, ensure_ascii=False, indent=2), encoding="utf-8")

    rel = [f"# Conversão — {orig.name}", "",
           f"- Original: `{orig}` (SHA-256 `{h}`), nunca modificado",
           f"- Formato: {info['formato']}" + (" · cópia byte a byte" if info.get("copia_exata") else ""),
           f"- Fonte normalizada: `{fonte.name}` (SHA-256 `{info['fonte_sha256']}`)",
           f"- Tipo de fonte: **{info['tipo_fonte']}** — {info['tipo_descricao']}",
           f"- Indícios: {'; '.join(info['indicios'])}", ""]
    if info["limpeza"]:
        rel += ["## Limpeza técnica da extração", "",
                "Artefatos do formato de origem, não conteúdo. Nada do texto em si foi alterado.", ""]
        for it in info["limpeza"]:
            rel.append(f"- **{it['acao']}** · {it['n']}×"
                       + (": " + " · ".join(f"“{e}”" for e in it["exemplos"]) if it["exemplos"] else ""))
        rel.append("")
    if info["avisos"]:
        rel += ["## Avisos", ""] + [f"- {a}" for a in info["avisos"]] + [""]
    (wd / "conversao.md").write_text("\n".join(rel), encoding="utf-8")

    palavras = len(re.findall(r"\w+", texto))
    print(f"ORIGINAL  {orig}  ({info['formato']}, sha256 {h[:12]}…, inalterado)")
    print(f"FONTE     {fonte}  ({palavras:,} palavras)".replace(",", "."))
    print(f"TIPO      {info['tipo_fonte']} — {info['tipo_descricao']}")
    print(f"          {'; '.join(info['indicios'])}")
    if info["metadados"]:
        print("METADADOS " + " · ".join(f"{k}: {v}" for k, v in info["metadados"].items()))
    if info["limpeza"]:
        print("LIMPEZA TÉCNICA DECLARADA")
        for it in info["limpeza"]:
            print(f"  · {it['acao']} ({it['n']}×)" + (f" — ex.: “{it['exemplos'][0]}”" if it["exemplos"] else ""))
    for a in info["avisos"]:
        print(f"AVISO     {a}")
    print("SUGESTÕES título: " + (" | ".join(titulos) or "—")
          + " · autor: " + (" | ".join(info["sugestoes"]["autores"]) or "— (procure no texto)"))
    if serie:
        print("SÉRIE     volumes irmãos com plano.json (herde identidade, créditos e grafias):")
        for v in serie:
            print(f"  · {v['titulo']} — {v['subtitulo']} · {v['tema'].get('preset')} · {v['plano']}")
    if antigo is not None and antigo != fonte.read_bytes():
        print("AVISO     fonte.md mudou em relação à conversão anterior — âncoras de plano.json e "
              "texto-editado.md antigos podem não bater mais", file=sys.stderr)
    print(f"PASTA     {wd}")
    print(f"RELATÓRIO {wd / 'conversao.md'}")


# ============================================================
# REDIGIR-DIFF — melhoria de redação, para aprovação do usuário
# ============================================================
def _blocos_md(t):
    return [b.strip() for b in re.split(r"\n[ \t]*\n", t.replace("\r\n", "\n")) if b.strip()]


def _diff_palavras(a, b):
    import difflib
    wa, wb = a.split(), b.split()
    out = []
    for op, i1, i2, j1, j2 in difflib.SequenceMatcher(None, wa, wb, autojunk=False).get_opcodes():
        if op == "equal":
            out.append(esc(" ".join(wa[i1:i2])))
        if op in ("delete", "replace"):
            out.append(f"<del>{esc(' '.join(wa[i1:i2]))}</del>")
        if op in ("insert", "replace"):
            out.append(f"<ins>{esc(' '.join(wb[j1:j2]))}</ins>")
    return " ".join(out)


def cmd_redigir_diff(args):
    import difflib
    fa = Path(args.fonte).expanduser().resolve()
    fb = Path(args.editado).expanduser().resolve()
    for f in (fa, fb):
        if not f.exists():
            falhar(f"arquivo não encontrado: {f}")
    if fb.name != "texto-editado.md" or fb.parent != fa.parent:
        falhar("o texto editado precisa se chamar texto-editado.md e ficar na mesma pasta de fonte.md")
    ta, tb = fa.read_text(encoding="utf-8"), fb.read_text(encoding="utf-8")
    ba, bb = _blocos_md(ta), _blocos_md(tb)
    na = [" ".join(x.split()) for x in ba]
    nb = [" ".join(x.split()) for x in bb]
    pa, pb = ta.split(), tb.split()
    sm_total = difflib.SequenceMatcher(None, pa, pb, autojunk=False)
    mudou = 1 - sm_total.ratio()

    linhas, html_linhas, alertas = [], [], []
    n_alt = n_novos = n_removidos = 0
    for op, i1, i2, j1, j2 in difflib.SequenceMatcher(None, na, nb, autojunk=False).get_opcodes():
        if op == "equal":
            continue
        pares = list(zip(range(i1, i2), range(j1, j2))) if op == "replace" else []
        sobra_a = list(range(i1 + len(pares), i2))
        sobra_b = list(range(j1 + len(pares), j2))
        for i, j in pares:
            n_alt += 1
            r = difflib.SequenceMatcher(None, na[i].split(), nb[j].split(), autojunk=False).ratio()
            nums_a, nums_b = re.findall(r"\d+(?:[.,]\d+)?", na[i]), re.findall(r"\d+(?:[.,]\d+)?", nb[j])
            avisos = []
            if r < .5:
                avisos.append(f"mudança grande ({(1 - r) * 100:.0f}% das palavras) — verifique se virou paráfrase")
            if sorted(nums_a) != sorted(nums_b):
                avisos.append("números diferentes do original")
            if na[i].startswith("#") or nb[j].startswith("#"):
                if na[i] != nb[j]:
                    avisos.append("título alterado — títulos da fonte ficam como estão")
            ca = len(na[i].split())
            if ca and abs(len(nb[j].split()) - ca) / ca > .35:
                avisos.append(f"tamanho mudou {len(nb[j].split()) - ca:+d} palavras")
            for a in avisos:
                alertas.append(f"parágrafo {j + 1}: {a}")
            linhas += [f"## Parágrafo {j + 1}" + (" ⚠ " + "; ".join(avisos) if avisos else ""), "",
                       f"**Original:** {ba[i]}", "", f"**Editado:** {bb[j]}", ""]
            html_linhas.append(f'<section{" class=alerta" if avisos else ""}><h2>Parágrafo {j + 1}</h2>'
                               + "".join(f"<p class=aviso>⚠ {esc(a)}</p>" for a in avisos)
                               + f"<p>{_diff_palavras(na[i], nb[j])}</p></section>")
        for i in sobra_a:
            n_removidos += 1
            alertas.append(f"parágrafo original removido: “{na[i][:80]}…”")
            linhas += ["## Parágrafo removido ⚠", "", f"**Original:** {ba[i]}", ""]
            html_linhas.append(f"<section class=alerta><h2>Parágrafo removido</h2><p><del>{esc(na[i])}</del></p></section>")
        for j in sobra_b:
            n_novos += 1
            alertas.append(f"parágrafo novo {j + 1}: “{nb[j][:80]}…” — redação não acrescenta conteúdo")
            linhas += [f"## Parágrafo novo {j + 1} ⚠", "", f"**Editado:** {bb[j]}", ""]
            html_linhas.append(f"<section class=alerta><h2>Parágrafo novo {j + 1}</h2><p><ins>{esc(nb[j])}</ins></p></section>")

    resumo = (f"{len(pa):,} → {len(pb):,} palavras ({len(pb) - len(pa):+,}) · {mudou * 100:.1f}% do texto alterado · "
              f"{n_alt} parágrafos editados · {n_novos} novos · {n_removidos} removidos · "
              f"{len(ba) - n_alt - n_removidos} idênticos").replace(",", ".")
    if len(pa) and (len(pa) - len(pb)) / len(pa) > .15:
        alertas.insert(0, f"o texto encolheu {(len(pa) - len(pb)) * 100 / len(pa):.0f}% — risco de resumo")
    cab = [f"# Melhoria de redação — {fa.parent.name}", "", f"- Original: `{fa.name}` · Editado: `{fb.name}`",
           f"- {resumo}", ""]
    if alertas:
        cab += ["## Alertas", ""] + [f"- ⚠ {a}" for a in alertas] + [""]
    wd = fa.parent
    (wd / "diff-redacao.md").write_text("\n".join(cab + linhas), encoding="utf-8")
    estilo = ("body{font:15px/1.6 Georgia,serif;max-width:52em;margin:2em auto;padding:0 1em;color:#222}"
              "del{background:#fbe3e3;color:#8a1f1f}ins{background:#e2f4e5;color:#1d5e2a;text-decoration:none}"
              "section{border-top:1px solid #ddd;padding:.5em 0}section.alerta{border-left:4px solid #d08a00;padding-left:1em}"
              ".aviso{color:#9a6400;font:13px sans-serif}h2{font:600 13px sans-serif;color:#666}")
    (wd / "diff-redacao.html").write_text(
        f"<!doctype html><meta charset=utf-8><title>Diff de redação</title><style>{estilo}</style>"
        f"<h1>Melhoria de redação</h1><p>{esc(resumo)}</p>"
        + ("<ul>" + "".join(f"<li>⚠ {esc(a)}</li>" for a in alertas) + "</ul>" if alertas else "")
        + "".join(html_linhas), encoding="utf-8")
    print(f"[redação] {resumo}")
    for a in alertas:
        print(f"  ⚠ {a}")
    print(f"[arquivos] {wd / 'diff-redacao.md'} · {wd / 'diff-redacao.html'}")


# ============================================================
# ANÁLISE
# ============================================================
def cmd_analisar(args):
    md_path = Path(args.arquivo).expanduser().resolve()
    if not md_path.exists():
        falhar(f"arquivo não encontrado: {md_path}")
    texto = md_path.read_text(encoding="utf-8")
    md = criar_md(True)
    unidades, _ = extrair_unidades(md, texto)

    cont = {}
    for u in unidades:
        cont[u["tipo"]] = cont.get(u["tipo"], 0) + 1
    paras = [u for u in unidades if u["tipo"] == "p"]
    tams = sorted((len(u["raw"]) for u in paras), reverse=True)
    heads = [u for u in unidades if u["tipo"] == "h"]
    palavras = len(re.findall(r"\w+", texto))

    print(f"ARQUIVO   {md_path}")
    print(f"TAMANHO   {len(texto):,} caracteres · {palavras:,} palavras · "
          f"{texto.count(chr(10)) + 1:,} linhas".replace(",", "."))
    print(f"SHA-256   {sha256(md_path)}")
    titulo = heads[0]["plano"] if unidades and unidades[0]["tipo"] == "h" and unidades[0]["nivel"] == 1 else None
    print(f"TÍTULO    {titulo or '(o documento não começa com # título)'}")
    print("\nBLOCOS")
    nomes = dict(p="parágrafos", h="títulos", lista="listas", tabela="tabelas", codigo="código",
                 citacao="citações", alerta="alertas [!NOTE]", img="imagens", hr="separadores",
                 html="HTML bruto", notas="notas de rodapé", bloco="outros")
    for k, v in sorted(cont.items(), key=lambda kv: -kv[1]):
        print(f"  {nomes.get(k, k):<20} {v}")

    print("\nÁRVORE DE TÍTULOS" + (" (nenhum)" if not heads else ""))
    for u in heads[:120]:
        print(f"  {'  ' * (u['nivel'] - 1)}{'#' * u['nivel']} {u['plano']}")
    if len(heads) > 120:
        print(f"  … mais {len(heads) - 120}")

    if tams:
        print(f"\nPARÁGRAFOS  média {sum(tams) // len(tams)} · maior {tams[0]} caracteres")
    muralhas = [(k, u) for k, u in enumerate(unidades) if u["tipo"] == "p" and len(u["raw"]) > 3000]
    if muralhas:
        print(f"  ⚠ {len(muralhas)} parágrafo(s) com mais de 3.000 caracteres (texto corrido):")
        for k, u in muralhas:
            print(f"    unidade {k}: {len(u['raw']):,} car. · “{u['raw'][:90]}…”".replace(",", "."))

    imgs = re.findall(r"!\[[^\]]*\]\(([^)\s]+)", texto)
    if imgs:
        print("\nIMAGENS")
        for s in imgs:
            ok = s.startswith(("http://", "https://")) or (base_imagens(md_path) / s).exists()
            print(f"  {'✓' if ok else '✗ FALTANDO'} {s}")

    frases = re.findall(r"[^.!?…]{40,}[.!?…]", " ".join(u["raw"] for u in paras))
    rep = {}
    for f in frases:
        f = f.strip()
        rep[f] = rep.get(f, 0) + 1
    repetidas = [(f, n) for f, n in rep.items() if n > 1]
    if repetidas:
        print("\nFRASES REPETIDAS (evite como âncora; um bloco inteiro repetido em sequência é "
              "duplicação da transcrição → candidato a corte com \"ocorrencia\")")
        for f, n in repetidas[:12]:
            print(f"  {n}× “{f[:100]}”")

    conv = info_conversao(md_path)
    tipo = conv.get("tipo_fonte")
    if not tipo:
        from conversores import classificar
        tipo, _ = classificar(texto)
    print(f"\nTIPO DE FONTE  {tipo}" + (f"  ({conv['tipo_descricao']})" if conv.get("tipo_descricao") else ""))
    sinais_oralidade = [
        r"\bbem-vind", r"\bboa noite\b", r"\bboa tarde\b", r"\bbom dia\b", r"\bobrigad", r"\bagrade[cç]",
        r"\btchau\b", r"\bat[ée] (a )?(semana que vem|pr[óo]xima)", r"\b[áa]udio\b", r"\bsom t[áa]\b",
        r"\bmicrofone\b", r"\bc[âa]mera\b", r"\bchat\b", r"\blevantou a m[ãa]o\b", r"\bgrava[çc][ãa]o\b",
        r"\btranscri[çc][ãa]o\b", r"\bwhatsapp\b", r"\bborracha\b", r"\bentrar aqui\b",
        r"\bdeixa eu (s[óo] )?(abrir|dispor|jogar|achar)\b", r"\bme (ouvem|escutam)\b",
        r"\bpr[óo]xim[ao] (aula|m[óo]dulo)\b"]
    sinais_documento = [
        r"\brascunho\b", r"\bTODO\b", r"\bFIXME\b", r"\bp[áa]gina (deixada )?em branco\b",
        r"\bconfidencial\b", r"\bvers[ãa]o \d", r"\brevis[ãa]o \d", r"\bcoment[áa]rio do revisor\b",
        r"\b(ver|vide) p[áa]gina \d", r"\bcopyright\b", r"\btodos os direitos reservados\b",
        r"\[inaud[íi]vel\]", r"\bxxx+\b"]
    sinais = re.compile("|".join(sinais_oralidade + sinais_documento if tipo == "transcricao"
                                 else sinais_documento), re.I)
    texto_corrido = " ".join(" ".join(u["raw"].split()) for u in paras)
    candidatos = [f.strip() for f in re.findall(r"[^.!?…]+[.!?…]+", texto_corrido) if sinais.search(f)]
    if candidatos:
        print(f"\nPOSSÍVEIS CORTES ({len(candidatos)} frases com sinais de ruído fora do conteúdo — "
              "confirme na leitura; o contexto decide)")
        for f in candidatos[:40]:
            print(f"  · {f[:110]}")
    if tipo == "transcricao":
        sonoras = collections.Counter(re.findall(r"\\?\[[^\]\n]{1,40}?\\?\]", texto_corrido))
        if sonoras:
            print("\nANOTAÇÕES SONORAS (candidatas a corte; use o literal como está no .md, "
                  "no JSON com a barra dobrada)")
            for a, n in sonoras.most_common(20):
                print(f"  {n}× {a}")

    corpo = sum(len(u.get("raw", "")) for u in unidades)
    n_caps = max(1, sum(1 for u in heads if u["nivel"] <= 2))
    est = int(corpo / 1300 + n_caps * 0.7 + 10)
    modo = "ancoras" if (muralhas or len(heads) < 3) else "titulos"
    print(f"\nESTIMATIVA  ~{est} páginas no formato 152×229 mm")
    print(f"MODO SUGERIDO  {modo}  "
          + ("(texto sem estrutura suficiente: defina capítulos por âncoras literais)"
             if modo == "ancoras" else "(use os títulos do Markdown como capítulos)"))

    wd = pasta_trabalho(md_path)
    wd.mkdir(exist_ok=True)
    (wd / "figuras").mkdir(exist_ok=True)
    print(f"\nPASTA DE TRABALHO  {wd}")
    print(f"PLANO ESPERADO     {wd / 'plano.json'}")


# ============================================================
# BUILD
# ============================================================
def resolver_tema(plano):
    t = plano.get("tema", {})
    preset = t.get("preset", "noite-ouro")
    if preset not in PRESETS:
        falhar(f"preset de tema desconhecido: {preset}. Opções: {', '.join(PRESETS)}")
    cores = dict(FIXAS)
    cores.update(PRESETS[preset])
    cores.update(t.get("cores", {}))
    fmt = str(t.get("formato", "152x229")).lower()
    if fmt in FORMATOS:
        L, A = FORMATOS[fmt]
    else:
        m = re.match(r"^(\d+)\s*x\s*(\d+)$", fmt)
        if not m:
            falhar(f"formato inválido: {fmt} (use 152x229, a5, b5, a4, quadrado ou LxA em mm)")
        L, A = int(m.group(1)), int(m.group(2))
    fontes = dict(FONTES_PADRAO)
    fontes.update(t.get("fontes", {}))
    return dict(preset=preset, cores=cores, L=L, A=A, fontes=fontes,
                selo=t.get("selo", "losango"), capitular=t.get("capitular", True))


def montar_css(tema, extra):
    css = css_fontes() + CSS_BASE.read_text(encoding="utf-8")
    css = css.replace("__LARGURA__", f"{tema['L']}mm").replace("__ALTURA__", f"{tema['A']}mm")
    for k, v in {**tema["cores"], **tema["fontes"]}.items():
        css = css.replace("{{" + k + "}}", v)
    raiz = ":root {\n" + "".join(f"  --{k.replace('_', '-')}: {v};\n" for k, v in tema["cores"].items())
    raiz += "".join(f"  --{k}: {v};\n" for k, v in tema["fontes"].items()) + "}\n"
    css += "\n/* ---------- tema do plano ---------- */\n" + raiz
    if extra:
        css += "\n/* ---------- css_extra do plano ---------- */\n" + extra + "\n"
    return css


def resolver_capitulos(unidades, plano, meta, erros):
    est = plano.get("estrutura", {})
    cfg = est.get("capitulos") or []
    inicio_ancora = {}
    for k, u in enumerate(unidades):
        for a in u.get("ancoras", ()):
            inicio_ancora.setdefault(a, k)

    caps = []
    if not cfg:
        niveis = [u["nivel"] for u in unidades if u["tipo"] == "h"]
        if not niveis:
            caps.append(dict(inicio=0, fonte=False, titulo=est.get("titulo_unico") or meta.get("titulo", "Texto")))
        else:
            L = min(niveis)
            idx = [k for k, u in enumerate(unidades) if u["tipo"] == "h" and u["nivel"] == L]
            if idx[0] > 0:
                caps.append(dict(inicio=0, fonte=False, titulo=est.get("titulo_preambulo", "Abertura")))
            caps += [dict(inicio=k, fonte=True) for k in idx]
    else:
        for n, c in enumerate(cfg):
            base = dict(parte=c.get("parte"), apendice=bool(c.get("apendice")))
            if c.get("titulo_fonte"):
                alvo = norm_ws(c["titulo_fonte"])
                hits = [k for k, u in enumerate(unidades) if u["tipo"] == "h"
                        and (u["plano"] == alvo or norm_ws(u["raw"]) == alvo)]
                if len(hits) != 1:
                    erros.append(f"capítulo {n + 1}: título da fonte {alvo!r} encontrado {len(hits)}× (precisa ser 1)")
                    continue
                caps.append(dict(inicio=hits[0], fonte=True, **base))
            elif c.get("ancora"):
                a = c["ancora"].strip()
                if a not in inicio_ancora:
                    continue  # erro já registrado na localização de âncoras
                if not c.get("titulo"):
                    erros.append(f"capítulo {n + 1}: âncora de texto exige 'titulo'")
                caps.append(dict(inicio=inicio_ancora[a], fonte=False, titulo=c.get("titulo", ""), **base))
            else:
                if n != 0:
                    erros.append(f"capítulo {n + 1}: só o primeiro capítulo pode não ter âncora")
                caps.append(dict(inicio=0, fonte=False, titulo=c.get("titulo", ""), **base))
        if caps and caps[0]["inicio"] != 0:
            u0 = unidades[0]
            erros.append("há conteúdo antes do primeiro capítulo "
                         f"({texto_de_html(u0.get('inner', u0.get('html', '')))[:60]!r}…) — "
                         "defina o primeiro capítulo com \"ancora\": null")
        inicios = [c["inicio"] for c in caps]
        if inicios != sorted(inicios) or len(set(inicios)) != len(inicios):
            erros.append("capítulos fora da ordem do texto (ou dois começando no mesmo ponto)")

    for k, c in enumerate(caps):
        c["fim"] = caps[k + 1]["inicio"] if k + 1 < len(caps) else len(unidades)
        c.setdefault("parte", None)
        c.setdefault("apendice", False)
        if c["fonte"]:
            h = unidades[c["inicio"]]
            c["titulo_html"], c["plano"], c["corpo_ini"] = h["inner"], h["plano"], c["inicio"] + 1
        else:
            c["titulo_html"], c["plano"], c["corpo_ini"] = esc(c["titulo"]), c["titulo"], c["inicio"]
    return caps


def construir(md_path, plano_path, saida_pdf):
    fonte = md_path.read_text(encoding="utf-8")
    plano = json.loads(plano_path.read_text(encoding="utf-8")) if plano_path.exists() else None
    if plano is None:
        falhar(f"plano não encontrado: {plano_path}\n"
               "Escreva o plano editorial (ver PLANO.md da skill gera-pdf-premium).")
    modo = plano.get("modo")
    if modo not in (None, "integra", "lingua", "limpeza", "redacao"):
        falhar(f"modo desconhecido no plano: {modo!r} (use integra, lingua, limpeza ou redacao)")
    if modo in ("integra", "redacao") and (plano.get("cortes") or plano.get("correcoes")):
        falhar(f"o modo '{modo}' não admite cortes nem correções no plano — retire-os ou mude o modo")
    if modo == "lingua" and plano.get("cortes"):
        falhar("o modo 'lingua' só admite correções — retire os cortes ou use o modo 'limpeza'")
    if modo == "redacao" and md_path.name != "texto-editado.md":
        falhar("o modo 'redacao' compõe a partir de texto-editado.md (aprovado pelo usuário), não de "
               f"{md_path.name}")
    if modo == "redacao":
        dif = md_path.parent / "diff-redacao.md"
        if not dif.exists() or dif.stat().st_mtime < md_path.stat().st_mtime:
            falhar("texto-editado.md mudou depois do último diff — rode `gerar redigir-diff` e peça a "
                   "aprovação do usuário antes de compor")
    fonte, cortes_reg, erros_c = aplicar_cortes(fonte, plano.get("cortes", []))
    if erros_c:
        falhar("problemas nos cortes do plano:\n  " + "\n  ".join(erros_c))
    fonte, corr_reg, erros_k = aplicar_correcoes(fonte, plano.get("correcoes", []))
    if erros_k:
        falhar("problemas nas correções do plano:\n  " + "\n  ".join(erros_k))
    base_plano = plano_path.parent
    meta = plano.get("meta", {})
    tema = resolver_tema(plano)
    rf = {"limite": 1000, "alvo": 560, "maximo": 900, **plano.get("refluxo", {})}
    tipografia = plano.get("tipografia", True)
    md = criar_md(tipografia)
    unidades, env_doc = extrair_unidades(md, fonte)
    # Renderizações inline avulsas (pedaços re-fluídos, glossário, legendas) usam
    # só as referências de link: com as notas de rodapé no env, o plugin de
    # footnote anexaria o bloco de notas (↩︎) a cada chamada. Parágrafos com
    # [^nota] nunca são re-fluídos, então nada se perde.
    env = {k: v for k, v in env_doc.items() if k != "footnotes"}
    n_par_fonte = sum(1 for u in unidades if u["tipo"] == "p")

    # ---- título da fonte ----
    titulo_fonte = None
    if plano.get("estrutura", {}).get("consumir_titulo", True) and unidades \
            and unidades[0]["tipo"] == "h" and unidades[0]["nivel"] == 1:
        titulo_fonte = unidades.pop(0)

    # ---- âncoras ----
    est = plano.get("estrutura", {})
    caixas_cfg = plano.get("caixas", [])
    destaques = [d.strip() for d in plano.get("destaques", [])]
    glossario = plano.get("glossario", [])
    figuras = plano.get("figuras", [])
    ancoras = []
    for c in est.get("capitulos", []) or []:
        if c.get("ancora"):
            ancoras.append(c["ancora"].strip())
    for cx in caixas_cfg:
        if cx.get("tipo", "nota") not in TIPOS_CAIXA:
            falhar(f"tipo de caixa desconhecido: {cx.get('tipo')} (use {', '.join(sorted(TIPOS_CAIXA))})")
        ancoras.append(cx["inicio"].strip())
        if cx.get("fim"):
            ancoras.append(cx["fim"].strip())
    ancoras += destaques
    ancoras += [g["antes"].strip() for g in glossario]
    ancoras += [f["antes"].strip() for f in figuras]
    ancoras = list(dict.fromkeys(a for a in ancoras if a))

    erros = []
    unidades = aplicar_ancoras(md, env, unidades, ancoras, rf, erros)
    if erros:
        falhar(erros)
    caps = resolver_capitulos(unidades, plano, meta, erros)
    if erros:
        falhar(erros)

    idx_ancora = {}
    for k, u in enumerate(unidades):
        for a in u.get("ancoras", ()):
            idx_ancora.setdefault(a, k)

    def idx(a, onde):
        a = a.strip()
        if a not in idx_ancora:
            falhar(f"{onde}: a âncora {a[:70]!r} não abre nenhum bloco — confira se ela não "
                   "caiu dentro de um corte ou de outra âncora com o mesmo início")
        return idx_ancora[a]

    def fim_do_capitulo(k):
        for c in caps:
            if c["inicio"] <= k < c["fim"]:
                return c["fim"]
        return len(unidades)

    caixas = {}
    for cx in caixas_cfg:
        onde = f"caixa {cx.get('rotulo', '')!r}"
        ini = idx(cx["inicio"], onde)
        lim = fim_do_capitulo(ini)  # sem 'fim', ou 'fim' noutro capítulo: termina no fim do atual
        fim = min(idx(cx["fim"], onde), lim) if cx.get("fim") else lim
        if fim <= ini:
            falhar(f"caixa {cx.get('rotulo', '')!r}: 'fim' vem antes do 'inicio'")
        if ini in caixas:
            falhar(f"duas caixas começam no mesmo ponto: {cx['inicio'][:60]!r}")
        caixas[ini] = (fim, cx.get("tipo", "nota"), cx.get("rotulo", ""))
    ocupado = []
    for ini, (fim, _, _) in sorted(caixas.items()):
        if ocupado and ini < ocupado[-1]:
            falhar(f"caixas sobrepostas perto de {unidades[ini].get('raw', '')[:60]!r}")
        ocupado.append(fim)

    insercoes = {}
    for g in glossario:
        k = idx(g["antes"], f"glossário {g.get('termo', '')!r}")
        insercoes.setdefault(k, []).append(
            f'<aside class="termo"><span class="rot">{esc(g.get("rotulo", "Glossário"))}</span>'
            f'<p><b>{esc(g["termo"])}</b> — {md.renderInline(g["texto"], env)}</p></aside>')
    for f in figuras:
        k = idx(f["antes"], f"figura {f.get('svg') or f.get('imagem')!r}")
        insercoes.setdefault(k, []).append(figura_html(f, base_plano, md, env))
    set_destaques = set(destaques)

    partes = est.get("partes", [])
    tem_partes = bool(partes)
    ac = tema["cores"]["acento"]
    ac_cl = tema["cores"]["acento_claro"]
    stats = dict(caixas=0, destaques=0, figuras=len(figuras), glossario=len(glossario),
                 capitulares=0, intertitulos=0)

    # ---- renderização de uma unidade ----
    def render(k, u, estado, lvl_cap, base_h, em_caixa):
        out = "".join(insercoes.get(k, []))
        if out:
            estado["prev"] = "fig"
        t = u["tipo"]
        if t == "p":
            if not em_caixa and (u["ancoras"] & set_destaques):
                stats["destaques"] += 1
                estado["prev"] = "destaque"
                return out + f'<div class="destaque"><p data-src>{u["inner"]}</p></div>'
            cls = "t" if estado["prev"] == "p" else "t primeira"
            inner = u["inner"]
            if (not em_caixa and tema["capitular"] and not estado["capitular"]):
                estado["capitular"] = True
                m = re.match(r"([^\W\d_])", inner)
                if m and m.group(1).isupper():
                    inner = f'<span class="capitular">{m.group(1)}</span>{inner[1:]}'
                    stats["capitulares"] += 1
            estado["prev"] = "p"
            return out + f'<p class="{cls}" data-src>{inner}</p>'
        estado["prev"] = t
        if t == "h":
            stats["intertitulos"] += 1
            tag, lv = ("h3", lvl_cap + 1) if u["nivel"] <= base_h else ("h4", lvl_cap + 2)
            return out + f'<{tag} class="bm{lv}" data-src>{u["inner"]}</{tag}>'
        if t == "img":
            leg = u["titulo"] or u["alt"]
            cap = f"<figcaption data-editorial>{esc(leg)}</figcaption>" if leg else ""
            return out + f'<figure class="fig-md" data-src>{u["inner"]}{cap}</figure>'
        if t == "hr":
            return out + f'<div class="sep">{ornamento(ac)}</div>'
        if t == "alerta":
            return out + (f'<div class="alerta alerta-{u["alerta"]}"><span class="rot">'
                          f'{ROTULO_ALERTA[u["alerta"]]}</span><div data-src>{u["html"]}</div></div>')
        if t == "codigo":
            lang = f' data-lang="{esc_attr(u["lang"])}"' if u.get("lang") else ""
            return out + f'<div class="md-codigo"{lang} data-src>{u["html"]}</div>'
        corpo = u["html"]
        if t == "lista":
            # caixas de tarefa: o WeasyPrint desenha <input> com glifo próprio;
            # um <span> estilizado fica fiel ao tema (input não carrega texto)
            corpo = re.sub(r'<input[^>]*\bchecked\b[^>]*>', '<span class="tarefa feita"></span>', corpo)
            corpo = re.sub(r'<input[^>]*type="checkbox"[^>]*>', '<span class="tarefa"></span>', corpo)
        return out + f'<div class="md-{t}" data-src>{corpo}</div>'

    # ---- capítulos ----
    corpo_html, toc, parte_atual = [], [], object()
    num_cap, num_ap, n_par_saida = 0, 0, 0
    for c in caps:
        if c["apendice"]:
            num_ap += 1
            cid, label, toc_num = f"apendice{num_ap}", "Apêndice", chr(64 + num_ap)
            grupo = ("ap", "Apêndices" if sum(x["apendice"] for x in caps) > 1 else "Apêndice")
            lvl_cap = 1
        else:
            num_cap += 1
            cid, label, toc_num = f"cap{num_cap:02d}", f"Capítulo {num_cap:02d}", f"{num_cap:02d}"
            grupo = ("parte", c["parte"]) if tem_partes else ("nada", None)
            lvl_cap = 2 if tem_partes else 1

        if grupo != parte_atual:
            parte_atual = grupo
            if grupo[0] == "parte" and grupo[1] is not None:
                p = partes[grupo[1]]
                rom = p.get("id", str(grupo[1] + 1))
                corpo_html.append(
                    f'<section class="parte" data-parte="Parte {esc_attr(rom)} · {esc_attr(p["titulo"])}">'
                    f'<div class="moldura"></div><div class="miolo">'
                    f'<div class="num">Parte {esc(rom)}</div>'
                    f'<h1 data-titulo="Parte {esc_attr(rom)} — {esc_attr(p["titulo"])}">{esc(p["titulo"])}</h1>'
                    f'<div class="orn">{ornamento(ac_cl)}</div>'
                    + (f'<div class="resumo">{esc(p["resumo"])}</div>' if p.get("resumo") else "")
                    + "</div></section>")
                toc.append(f'<div class="toc-parte">Parte {esc(rom)} — {esc(p["titulo"])}</div>')
            elif grupo[0] == "ap":
                toc.append(f'<div class="toc-parte">{grupo[1]}</div>')

        body_units = range(c["corpo_ini"], c["fim"])
        niveis = [unidades[k]["nivel"] for k in body_units if unidades[k]["tipo"] == "h"]
        base_h = min(niveis) if niveis else 9
        estado = dict(prev="inicio", capitular=False)
        partes_cap = []
        k = c["corpo_ini"]
        while k < c["fim"]:
            if k in caixas:
                fim, tipo, rot = caixas[k]
                fim = min(fim, c["fim"])
                antes = insercoes.pop(k, [])  # glossário/figura na âncora de início da caixa: antes dela, não dentro
                if antes:
                    partes_cap.append("".join(antes))
                est_cx = dict(prev="inicio", capitular=True)
                dentro = "".join(render(j, unidades[j], est_cx, lvl_cap, base_h, True) for j in range(k, fim))
                partes_cap.append(f'<div class="caixa caixa-{tipo}">'
                                  + (f'<span class="rot">{esc(rot)}</span>' if rot else "")
                                  + dentro + "</div>")
                stats["caixas"] += 1
                estado["prev"] = "caixa"
                k = fim
                continue
            partes_cap.append(render(k, unidades[k], estado, lvl_cap, base_h, False))
            k += 1
        n_par_saida += sum(1 for j in body_units if unidades[j]["tipo"] == "p")

        data_src = " data-src" if c["fonte"] else ""
        corpo_html.append(
            f'<section class="cap{" apendice" if c["apendice"] else ""}" id="{cid}" '
            f'data-cap="{esc_attr(c["plano"])}"><header class="cap-abre">'
            f'<div class="num">{label}</div>'
            f'<h2 class="bm{lvl_cap}"{data_src}>{c["titulo_html"]}</h2>'
            f'<div class="filete"></div></header>{"".join(partes_cap)}</section>')
        toc.append(f'<a class="toc-item" href="#{cid}"><span class="num">{toc_num}</span>'
                   f'<span class="tit">{esc(c["plano"])}</span></a>')
    if toc and toc[0].startswith('<div class="toc-parte">'):
        toc[0] = toc[0].replace('class="toc-parte"', 'class="toc-parte primeira"', 1)

    # ---- páginas preliminares ----
    titulo = meta.get("titulo") or (titulo_fonte["plano"] if titulo_fonte else md_path.stem)
    subtitulo = meta.get("subtitulo", "")
    tcapa = meta.get("titulo_capa", titulo)
    tam = "t-g" if len(tcapa) <= 20 else ("t-m" if len(tcapa) <= 34 else "t-p")
    tcapa_html = "<br>".join(esc(x) for x in tcapa.split("\n"))
    arte = ""
    if meta.get("capa_imagem"):
        img = (base_plano / meta["capa_imagem"]).resolve()
        if not img.exists():
            falhar(f"capa_imagem não encontrada: {img}")
        arte = f'<div class="arte" style="background-image:url(\'{img.as_uri()}\')"></div><div class="veu"></div>'

    capa = (f'<section class="capa">{arte}<div class="moldura"></div><div class="moldura2"></div>'
            f'<div class="selo">{selo(tema["selo"], ac_cl)}</div><div class="miolo">'
            + (f'<div class="chapeu">{esc(meta["chapeu"])}</div>' if meta.get("chapeu") else "")
            + f'<div class="titulo {tam}">{tcapa_html}</div>'
            + (f'<div class="sub">{esc(subtitulo)}</div>' if subtitulo else "")
            + '<div class="filete-c"></div>'
            + (f'<div class="descricao">{esc(meta["descricao_capa"])}</div>' if meta.get("descricao_capa") else "")
            + "</div>"
            + (f'<div class="rodape">{esc(meta["rodape_capa"])}</div>' if meta.get("rodape_capa") else "")
            + "</section>")

    meia = f'<section class="meia-folha"><div class="nome">{esc(titulo)}</div><div class="orn">{ornamento(ac)}</div></section>'

    if titulo_fonte:
        inner = titulo_fonte["inner"]
        for sep in (" — ", " – ", ": "):
            if sep in inner:
                a, b = inner.split(sep, 1)
                inner = f'{a}<span class="sub">{sep.lstrip() if sep == ": " else sep}{b}</span>'
                if sep == ": ":
                    inner = f'{a}:<span class="sub"> {b}</span>'
                break
        h1_rosto = f"<h1 data-src>{inner}</h1>"
    else:
        h1_rosto = f'<h1>{esc(titulo)}' + (f'<span class="sub">{esc(subtitulo)}</span>' if subtitulo else "") + "</h1>"
    creditos = []
    for linha in meta.get("creditos", []):
        if "|" in linha:
            r, n = linha.split("|", 1)
            creditos.append(f"{esc(r.strip())}<br><strong>{esc(n.strip())}</strong>")
        else:
            creditos.append(esc(linha))
    rosto = ('<section class="rosto">'
             + (f'<div class="chapeu">{esc(meta.get("chapeu_rosto", meta.get("chapeu", "")))}</div>'
                if meta.get("chapeu_rosto") or meta.get("chapeu") else "")
             + h1_rosto + '<div class="filete"></div>'
             + (f'<div class="creditos">{"<br><br>".join(creditos)}</div>' if creditos else "")
             + "</section>")

    refluidos = any(u.get("refluido") for u in unidades)
    editoriais = sum(1 for c in caps if not c["fonte"])
    feitos = []
    if refluidos:
        feitos.append("re-fluir o texto corrido em parágrafos")
    if editoriais:
        if len(caps) == 1:
            quais = "com título de navegação editorial"
        elif editoriais == len(caps):
            quais = "todos com títulos de navegação editoriais"
        else:
            quais = (f"{editoriais} " + pl(editoriais, "deles com título de navegação editorial",
                                           "deles com títulos de navegação editoriais"))
        feitos.append(f"organizá-lo em {len(caps)} {pl(len(caps), 'capítulo', 'capítulos')}, {quais}")
    elif len(caps) > 1:
        feitos.append(f"organizá-lo em {len(caps)} capítulos a partir dos títulos originais")
    if partes:
        feitos.append(f"agrupar os capítulos em {len(partes)} partes")
    if caixas:
        feitos.append(f"destacar {len(caixas)} " + pl(len(caixas), "trecho numa caixa temática",
                                                      "trechos em caixas temáticas"))
    if destaques:
        feitos.append(f"realçar {len(destaques)} " + pl(len(destaques), "parágrafo-chave", "parágrafos-chave"))
    if figuras:
        feitos.append(f"acrescentar {len(figuras)} " + pl(len(figuras), "ilustração identificada como editorial",
                                                         "ilustrações identificadas como editoriais"))
    if glossario:
        feitos.append(f"incluir {len(glossario)} " + pl(len(glossario), "nota de glossário", "notas de glossário"))
    if tipografia:
        feitos.append("aplicar acabamento tipográfico (aspas curvas, travessões e reticências)")
    redacao = plano.get("modo") == "redacao"
    if redacao:
        abertura = ("<b>Nota sobre esta edição.</b> O texto passou por uma revisão leve de redação — fluidez, "
                    "clareza e retirada de repetições acidentais, sem mudar ideias, dados nem a ordem da "
                    "exposição —, aprovada antes da composição e registrada parágrafo a parágrafo no arquivo "
                    "<i>diff-redacao.md</i>. Sobre esse texto aprovado, o trabalho editorial limitou-se a ")
    elif cortes_reg or corr_reg:
        abertura = "<b>Nota sobre esta edição.</b> "
        if cortes_reg:
            motivos = list(dict.fromkeys(r["motivo"] for r in cortes_reg if r["motivo"]))
            n = len(cortes_reg)
            abertura += (f"Para manter o foco, {pl(n, 'foi retirado', 'foram retirados')} {n} "
                         + pl(n, "trecho alheio", "trechos alheios") + " ao conteúdo"
                         + (f" ({esc('; '.join(motivos))})" if motivos else "")
                         + f", {pl(n, 'listado', 'listados')} literalmente no arquivo <i>cortes.md</i> que acompanha a edição. ")
        if corr_reg:
            n_corr = sum(r["vezes"] for r in corr_reg)
            verbo = pl(n_corr, "Foi feita", "Foram feitas") + (" também" if cortes_reg else "")
            abertura += (f"{verbo} {n_corr} " + pl(n_corr, "pequena correção ", "pequenas correções ")
                         + "de ortografia, gramática e erros evidentes, " + pl(n_corr, "registrada", "cada uma registrada") + ", "
                         "com o texto original ao lado, no arquivo <i>correcoes.md</i>. ")
        abertura += ("Fora isso, nenhuma palavra foi removida, resumida, reordenada ou reescrita. "
                     "O trabalho editorial limitou-se a ")
    else:
        abertura = ("<b>Nota sobre esta edição.</b> Nenhuma palavra do texto original foi removida, resumida, "
                    "reordenada ou reescrita. O trabalho editorial limitou-se a ")
    nota = (abertura
            + (", ".join(feitos[:-1]) + " e " + feitos[-1] if len(feitos) > 1 else (feitos[0] if feitos else "diagramá-lo"))
            + ". A integridade é verificada automaticamente a cada geração: o texto do livro é "
              "comparado caractere a caractere com a fonte.")
    # o livro se apresenta como obra própria: a nota editorial (origem, cortes, correções, o que foi
    # feito) vai só para o relatorio.md; o colofão mostra a obra e o que o plano pedir em meta.colofao
    nota_edicao = re.sub(r"</?b>", "**", re.sub(r"</?i>", "*", nota))
    blocos_col = meta.get("colofao") or [
        {"rotulo": "Obra", "texto": titulo + (f" — {subtitulo}" if subtitulo else "")},
    ]
    colofao = ('<section class="colofao">'
               + "".join(f'<div class="bloco"><span class="rot">{esc(b["rotulo"])}</span>'
                         f'{md.renderInline(b["texto"], env)}</div>' for b in blocos_col)
               + "</section>")

    epi = ""
    if meta.get("epigrafe"):
        e = meta["epigrafe"]
        epi = (f'<section class="epigrafe"><p>“{esc(e["texto"])}”</p>'
               + (f'<div class="autor">{esc(e["autor"])}</div>' if e.get("autor") else "") + "</section>")

    # a marca do cabeçalho corrente fica DENTRO do sumário: solta entre duas
    # quebras de página ela gerava uma página em branco
    sumario = (f'<section class="sumario"><h1 class="cab">Sumário</h1>'
               f'<div class="orn-topo">{ornamento(ac)}</div>{"".join(toc)}'
               f'<div class="marca-livro" data-parte="{esc_attr(titulo)}"></div></section>')

    fim_html = ""
    if meta.get("fim"):
        f = meta["fim"]
        fim_html = (f'<section class="fim"><div class="moldura"></div><div class="miolo">'
                    f'<div class="titulo">{esc(f.get("titulo", ""))}</div>'
                    + (f'<div class="sub">{esc(f["subtitulo"])}</div>' if f.get("subtitulo") else "")
                    + f'<div class="orn">{ornamento(ac_cl)}</div></div></section>')

    css = montar_css(tema, plano.get("css_extra", ""))
    agora = datetime.date.today().isoformat()
    titulo_pdf = meta.get("titulo_pdf") or (titulo + (f" — {subtitulo}" if subtitulo else ""))
    doc = f"""<!DOCTYPE html>
<html lang="{esc_attr(meta.get('idioma', 'pt-BR'))}">
<head>
<meta charset="utf-8">
<base href="{base_imagens(md_path).as_uri()}/">
<title>{esc(titulo_pdf)}</title>
<meta name="author" content="{esc_attr(meta.get('autores', ''))}">
<meta name="description" content="{esc_attr(meta.get('descricao', ''))}">
<meta name="keywords" content="{esc_attr(meta.get('palavras_chave', ''))}">
<meta name="dcterms.created" content="{agora}">
<style>
{css}
</style>
</head>
<body>
{capa}
{meia}
{rosto}
{colofao}
{epi}
{sumario}
{"".join(corpo_html)}
{fim_html}
</body>
</html>"""

    wd = pasta_trabalho(md_path)
    wd.mkdir(exist_ok=True)
    (wd / "ebook.html").write_text(doc, encoding="utf-8")
    (wd / "ebook.css").write_text(css, encoding="utf-8")

    ok, n_chars, diag = verificar_integridade(md, fonte, doc)
    n_cortes, n_corr = len(cortes_reg), sum(r["vezes"] for r in corr_reg)
    dif = ([f"menos {n_cortes} {pl(n_cortes, 'corte', 'cortes')}"] if cortes_reg else []) \
        + ([f"com {n_corr} {pl(n_corr, 'correção', 'correções')}"] if corr_reg else [])
    if cortes_reg and corr_reg:
        decl = "declarados"
    elif cortes_reg:
        decl = pl(n_cortes, "declarado", "declarados")
    else:
        decl = pl(n_corr, "declarada", "declaradas")
    alvo = "à fonte " + " e ".join(dif) + " " + decl if dif else "à fonte"
    print(f"[integridade] {'OK — texto idêntico ' + alvo if ok else 'FALHA'} · "
          f"{n_chars:,} caracteres verificados (sem contar espaços)".replace(",", "."))
    if not ok:
        print(diag, file=sys.stderr)
        print(f"HTML de diagnóstico: {wd / 'ebook.html'}", file=sys.stderr)
        sys.exit(3)

    from weasyprint import HTML
    render = HTML(string=doc, base_url=str(base_imagens(md_path))).render()
    render.write_pdf(str(saida_pdf))
    n_pag = len(render.pages)

    return dict(paginas=n_pag, capitulos=num_cap, apendices=num_ap, partes=len(partes),
                paragrafos_fonte=n_par_fonte, paragrafos_saida=n_par_saida, chars=n_chars,
                refluxo=refluidos, editoriais=editoriais, tema=tema, wd=wd, cortes=cortes_reg,
                correcoes=corr_reg, nota_edicao=nota_edicao, **stats)


def cmd_build(args):
    md_path = Path(args.arquivo).expanduser().resolve()
    if not md_path.exists():
        falhar(f"arquivo não encontrado: {md_path}")
    plano_path = Path(args.plano).expanduser().resolve() if args.plano else pasta_trabalho(md_path) / "plano.json"
    if args.saida:
        saida = Path(args.saida).expanduser().resolve()
    else:
        try:
            m = json.loads(plano_path.read_text(encoding="utf-8")).get("meta", {})
        except Exception:
            m = {}
        conv = info_conversao(md_path)
        pasta = Path(conv["original"]).parent if conv.get("original") else md_path.parent
        nome = m.get("titulo") or (Path(conv["original"]).stem if conv.get("original") else md_path.stem)
        if m.get("subtitulo"):
            nome += f" - {m['subtitulo']}"
        saida = pasta / f"{nome_arquivo(nome)}.pdf"  # ex.: "Curso X - Aula 04.pdf"
    conv = info_conversao(md_path)
    original = Path(conv["original"]) if conv.get("original") else None
    if saida.suffix.lower() != ".pdf" or saida == md_path:
        falhar(f"saída inválida: {saida}")
    if original is not None and saida.resolve() == original.resolve():
        saida = saida.with_name(f"{saida.stem} (premium).pdf")
        print(f"[saída] o nome coincidia com o arquivo original — o PDF novo será {saida.name}")

    h_antes = sha256(md_path)
    h_orig = sha256(original) if original is not None and original.exists() else None
    if h_orig and conv.get("sha256") and h_orig != conv["sha256"]:
        print(f"AVISO: {original.name} mudou depois da conversão — rode `gerar converter` de novo "
              "para compor a versão atual.", file=sys.stderr)
    r = construir(md_path, plano_path, saida)
    h_depois = sha256(md_path)
    if h_antes != h_depois:
        falhar("a fonte mudou durante o build — isso nunca deveria acontecer", 4)
    if h_orig and sha256(original) != h_orig:
        falhar("o arquivo original mudou durante o build — isso nunca deveria acontecer", 4)

    a = auditar(saida, silencioso=True)
    linhas = [
        f"# Relatório de composição — {saida.name}",
        "",
        f"- Fonte: `{md_path}` (SHA-256 `{h_antes[:16]}…`, inalterado)",
        f"- Plano: `{plano_path}`",
        f"- PDF: `{saida}` · {r['paginas']} páginas · {saida.stat().st_size / 1024:.0f} KB",
        f"- Tema: {r['tema']['preset']} · formato {r['tema']['L']}×{r['tema']['A']} mm",
        "",
        "## Estrutura",
        f"- Partes: {r['partes']} · Capítulos: {r['capitulos']} · Apêndices: {r['apendices']}",
        f"- Capítulos com título editorial: {r['editoriais']}",
        f"- Parágrafos: {r['paragrafos_fonte']} na fonte → {r['paragrafos_saida']} no livro"
        + (" (texto corrido re-fluído)" if r["refluxo"] else ""),
        f"- Intertítulos da fonte: {r['intertitulos']}",
        "",
        "## Componentes",
        f"- Caixas: {r['caixas']} · Destaques: {r['destaques']} · Capitulares: {r['capitulares']}",
        f"- Figuras editoriais: {r['figuras']} · Notas de glossário: {r['glossario']}",
        "",
        "## Navegação",
        f"- Marcadores (bookmarks): {a['bookmarks']}",
        f"- Páginas com links internos: {a['paginas_com_links']}",
        f"- Metadados: título “{a['meta'].get('Title', '')}”, autor “{a['meta'].get('Author', '')}”",
        "",
        "## Integridade",
        f"- Texto do livro idêntico à fonte{' com os cortes e correções declarados' if r['cortes'] or r['correcoes'] else ''}: "
        f"SIM ({r['chars']:,} caracteres comparados, sem espaços)".replace(",", "."),
        "- Fonte não modificada: SIM (hash conferido antes e depois)"
        + (f"; arquivo original `{original.name}` também inalterado" if h_orig else ""),
    ]
    linhas += ["", "## Nota editorial (não entra no livro)", "", r["nota_edicao"]]
    if r["cortes"]:
        n_pal = sum(c["palavras"] for c in r["cortes"])
        linhas += ["", "## Cortes", f"- {len(r['cortes'])} trechos · {n_pal} palavras · lista literal em `cortes.md`"]
        cm = [f"# Cortes editoriais — {saida.stem}", "",
              f"Fonte: `{md_path.name}` (SHA-256 `{h_antes}`), mantida intacta. "
              f"{len(r['cortes'])} trechos removidos, {n_pal} palavras.", ""]
        for c in r["cortes"]:
            cm += [f"## {c['n']}. {c['motivo'] or 'sem motivo declarado'} · {c['palavras']} palavras", "",
                   f"> {c['texto']}", ""]
        (r["wd"] / "cortes.md").write_text("\n".join(cm), encoding="utf-8")
        print(f"[cortes] {len(r['cortes'])} trechos · {n_pal} palavras removidas · {r['wd']}/cortes.md")
    arq_corr = r["wd"] / "correcoes.md"
    if r["correcoes"]:
        n_corr = sum(c["vezes"] for c in r["correcoes"])
        linhas += ["", "## Correções", f"- {len(r['correcoes'])} declaradas · {n_corr} aplicações · "
                   "original e correção lado a lado em `correcoes.md`"]
        km = [f"# Correções editoriais — {saida.stem}", "",
              f"Fonte: `{md_path.name}` (SHA-256 `{h_antes}`), mantida intacta. "
              f"{len(r['correcoes'])} correções declaradas, {n_corr} aplicações no texto.", ""]
        for c in r["correcoes"]:
            km += [f"## {c['n']}. {c['motivo'] or 'sem motivo declarado'}"
                   + (f" · {c['vezes']}×" if c["vezes"] > 1 else ""), "",
                   f"- **Original:** {c['de']}", f"- **Corrigido:** {c['para'] or '(removido)'}", ""]
        arq_corr.write_text("\n".join(km), encoding="utf-8")
        print(f"[correções] {len(r['correcoes'])} declaradas · {n_corr} aplicações · {arq_corr}")
    elif arq_corr.exists():
        arq_corr.unlink()
    (r["wd"] / "relatorio.md").write_text("\n".join(linhas) + "\n", encoding="utf-8")
    print(f"[pdf] {saida} · {r['paginas']} páginas · {saida.stat().st_size / 1024:.0f} KB")
    print(f"[estrutura] {r['partes']} partes · {r['capitulos']} capítulos · {r['apendices']} apêndices · "
          f"{r['caixas']} caixas · {r['destaques']} destaques · {r['figuras']} figuras · {r['glossario']} glossário")
    print(f"[navegação] {a['bookmarks']} bookmarks · links internos em {a['paginas_com_links']} página(s)")
    print(f"[fonte] {md_path.name} inalterado (sha256 {h_antes[:12]}…)"
          + (f" · original {original.name} inalterado (sha256 {h_orig[:12]}…)" if h_orig else ""))
    print(f"[arquivos] {r['wd']}/ebook.html · ebook.css · relatorio.md")


# ============================================================
# PREVIEW / AUDITORIA
# ============================================================
def auditar(pdf, silencioso=False):
    import ctypes
    import pypdfium2 as pdfium
    import pypdfium2.raw as raw

    d = pdfium.PdfDocument(str(pdf))
    meta = {k: d.get_metadata_value(k) for k in ("Title", "Author", "Subject", "Keywords")}
    marcadores = []
    for b in d.get_toc():
        dest = b.get_dest()
        pg = dest.get_index() + 1 if dest is not None and dest.get_index() is not None else 0
        marcadores.append((b.level, b.get_title(), pg))
    com_links, curtas, aberturas = [], [], []
    for i in range(len(d)):
        pg = d[i]
        pos, link = ctypes.c_int(0), raw.FPDF_LINK()
        n_links = 0
        while raw.FPDFLink_Enumerate(pg, ctypes.byref(pos), ctypes.byref(link)):
            n_links += 1
        if n_links:
            com_links.append(i + 1)
        t = pg.get_textpage().get_text_range()
        # páginas de sumário (muitos links) citam “Apêndice” sem serem abertura;
        # uma nota de rodapé ou link avulso não torna a página um sumário
        if n_links < 3 and re.search(r"C\s*A\s*P\s*[ÍI]\s*T\s*U\s*L\s*O|A\s*P\s*[ÊE]\s*N\s*D\s*I\s*C\s*E", t):
            aberturas.append(i + 1)
        if len(t.strip()) < 260:
            curtas.append((i + 1, len(t.strip())))
    r = dict(paginas=len(d), meta=meta, bookmarks=len(marcadores), marcadores=marcadores,
             paginas_com_links=len(com_links), links=com_links, curtas=curtas, aberturas=aberturas)
    if not silencioso:
        print(f"PDF        {pdf}")
        print(f"PÁGINAS    {r['paginas']}")
        print(f"METADADOS  {meta}")
        print(f"LINKS      páginas com links internos: {com_links}")
        print(f"ABERTURAS  {len(aberturas)} aberturas de capítulo/apêndice: {aberturas}")
        print(f"CURTAS     páginas com pouco texto (capa, partes, fins de capítulo — confira se são intencionais):")
        print("           " + ", ".join(f"{p}({n})" for p, n in curtas))
        print(f"BOOKMARKS  {len(marcadores)}")
        for lv, tt, pg in marcadores:
            print(f"           {'  ' * lv}{tt}  →p.{pg}")
    return r


def paginas_de(spec, total):
    out = []
    for parte in spec.split(","):
        parte = parte.strip()
        if not parte:
            continue
        if "-" in parte:
            a, b = parte.split("-", 1)
            out += list(range(int(a), int(b) + 1))
        else:
            out.append(int(parte))
    return [p for p in out if 1 <= p <= total]


def cmd_preview(args):
    import pypdfium2 as pdfium
    from PIL import Image, ImageDraw

    pdf = Path(args.arquivo).expanduser().resolve()
    if not pdf.exists():
        falhar(f"PDF não encontrado: {pdf}")
    auditar(pdf)
    d = pdfium.PdfDocument(str(pdf))
    total = len(d)
    # dentro do projeto, nunca no temporário do sistema; `gerar limpar` apaga ao final
    tmp_raiz = Path(os.environ.get("GERA_PDF_PREMIUM_TMP") or Path.cwd() / ".gera-pdf-premium" / "tmp")
    saida = Path(args.saida).expanduser() if args.saida else tmp_raiz / "preview" / pdf.stem
    saida.mkdir(parents=True, exist_ok=True)
    for velho in saida.glob("*.png"):
        velho.unlink()

    if args.paginas:
        pags, escala, cols, por_folha, nome = paginas_de(args.paginas, total), 1.6, 3, 6, "detalhe"
    else:
        pags, escala, cols, por_folha, nome = list(range(1, total + 1)), 0.55, 6, 24, "contato"

    folhas = []
    for f0 in range(0, len(pags), por_folha):
        lote = pags[f0:f0 + por_folha]
        ims = [d[p - 1].render(scale=escala).to_pil() for p in lote]
        w, h = ims[0].size
        linhas = (len(ims) + cols - 1) // cols
        gap, rotulo = 10, 18
        g = Image.new("RGB", (cols * w + (cols + 1) * gap, linhas * (h + rotulo) + (linhas + 1) * gap), "#8C8C8C")
        dr = ImageDraw.Draw(g)
        for k, (p, im) in enumerate(zip(lote, ims)):
            x = gap + (k % cols) * (w + gap)
            y = gap + (k // cols) * (h + rotulo + gap)
            dr.text((x, y), f"p.{p}", fill="#FFFFFF")
            g.paste(im, (x, y + rotulo))
        arq = saida / f"{nome}-{len(folhas) + 1:02d}.png"
        g.save(arq)
        folhas.append(arq)
    print(f"\nFOLHAS ({nome})")
    for f in folhas:
        print(f"  {f}")


def cmd_ocorrencias(args):
    """Falhas registradas desde a última revisão, agrupadas — insumo da retrospectiva."""
    if not LOG_OCORRENCIAS.exists():
        print("Nenhuma ocorrência registrada.")
        return
    desde = MARCA_REVISAO.read_text().strip() if MARCA_REVISAO.exists() and not args.todas else ""
    regs = []
    for linha in LOG_OCORRENCIAS.read_text(encoding="utf-8").splitlines():
        try:
            r = json.loads(linha)
        except ValueError:
            continue
        if r.get("data", "") > desde:
            regs.append(r)
    if args.marcar_revisadas:
        import time
        MARCA_REVISAO.write_text(time.strftime("%Y-%m-%dT%H:%M:%S"))
        print(f"{len(regs)} ocorrência(s) marcadas como revisadas.")
        return
    if not regs:
        print(f"Nenhuma ocorrência nova desde {desde or 'o início'}.")
        return
    grupos = {}
    for r in regs:
        for m in r["mensagens"]:
            chave = (r["tipo"], re.sub(r"'[^']*'|\"[^\"]*\"|\d+", "…", m.strip().splitlines()[-1])[:110])
            grupos.setdefault(chave, []).append(r)
    print(f"OCORRÊNCIAS NÃO REVISADAS  {len(regs)} desde {desde or 'o início'}\n")
    for (tipo, chave), rs in sorted(grupos.items(), key=lambda kv: -len(kv[1])):
        print(f"  {len(rs)}×  [{tipo}] {chave}")
        ult = rs[-1]
        print(f"       último: {ult['data']} · {ult.get('cmd')} · {Path(ult.get('arquivo') or '-').name}")
        if tipo == "excecao":
            print("       " + ult["mensagens"][0].strip().replace("\n", "\n       ")[-900:])
    print("\nDepois da retrospectiva: gerar ocorrencias --marcar-revisadas")


# ============================================================
# CLI
# ============================================================
def _registrar_excecao(tipo, valor, tb):
    import traceback
    registrar_ocorrencia("excecao", ["".join(traceback.format_exception(tipo, valor, tb))[-4000:]])
    sys.__excepthook__(tipo, valor, tb)


def main():
    ap = argparse.ArgumentParser(prog="gera-pdf-premium", description="qualquer texto → ebook PDF premium")
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("converter")
    c.add_argument("arquivo")
    c.add_argument("--idioma", help="idiomas do OCR no formato do tesseract (ex.: por+eng)")
    r = sub.add_parser("redigir-diff")
    r.add_argument("fonte")
    r.add_argument("editado")
    a = sub.add_parser("analisar")
    a.add_argument("arquivo")
    b = sub.add_parser("build")
    b.add_argument("arquivo")
    b.add_argument("--plano")
    b.add_argument("--saida")
    p = sub.add_parser("preview")
    p.add_argument("arquivo")
    p.add_argument("--paginas")
    p.add_argument("--saida")
    o = sub.add_parser("ocorrencias")
    o.add_argument("--todas", action="store_true", help="inclui as já revisadas")
    o.add_argument("--marcar-revisadas", action="store_true")
    args = ap.parse_args()
    CONTEXTO.update(cmd=args.cmd, arquivo=getattr(args, "arquivo", None))
    sys.excepthook = _registrar_excecao
    {"converter": cmd_converter, "analisar": cmd_analisar, "redigir-diff": cmd_redigir_diff,
     "build": cmd_build, "preview": cmd_preview, "ocorrencias": cmd_ocorrencias}[args.cmd](args)


if __name__ == "__main__":
    main()
