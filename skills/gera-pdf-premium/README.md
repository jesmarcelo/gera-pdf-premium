# gera-pdf-premium

Skill do Claude Code que transforma qualquer texto — `.md`, `.txt`, `.docx`, legendas `.srt`/`.vtt`, PDF com texto ou PDF escaneado — em um ebook PDF com acabamento de livro comercial: capa, rosto, sumário clicável, marcadores, partes e capítulos, capitulares, caixas editoriais, figuras vetoriais, cabeçalhos correntes e fólios.

Antes de compor, a skill pergunta título, autor, subtítulo, **como tratar o texto** (íntegra, só correção de língua, correção + limpeza de ruído, ou melhoria leve de redação com a sua aprovação), identidade visual, capa e onde salvar. Toda alteração no texto é declarada em arquivos que acompanham o PDF, e o motor confere automaticamente, caractere a caractere, que nada além disso mudou.

## Instalação e uso

Instruções completas, para quem vai instalar: <https://github.com/jesmarcelo/gera-pdf-premium#readme>

Para conferir os pré-requisitos a partir desta pasta:

```bash
scripts/gerar verificar        # macOS / Linux
scripts\gerar.cmd verificar    # Windows
```

## Pré-requisitos

| item | para quê | macOS | Linux (Debian/Ubuntu) | Windows |
|---|---|---|---|---|
| **uv** (recomendado) ou **Python 3.10+** | rodar o motor | `curl -LsSf https://astral.sh/uv/install.sh \| sh` | idem | `powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 \| iex"` |
| **Pango** | desenhar o PDF (WeasyPrint) | `brew install pango` | `sudo apt install libpango-1.0-0 libpangoft2-1.0-0` | ver abaixo |
| **Tesseract** (opcional) | ler PDF escaneado | `brew install tesseract tesseract-lang` | `sudo apt install tesseract-ocr tesseract-ocr-por` | `winget install UB-Mannheim.TesseractOCR` |

Com o `uv`, não é preciso instalar Python: ele baixa uma versão própria, sem mexer no Python do sistema. As bibliotecas Python (WeasyPrint, python-docx, pdfplumber…) são instaladas sozinhas num ambiente separado dentro do projeto, em `.gera-pdf-premium/venv`, reaproveitado em toda geração. Na mesma pasta ficam o cache de downloads, os backups do `update` e os temporários (`tmp/`, apagados no final); nada é gravado fora do projeto.

### Pango no Windows

1. `winget install MSYS2.MSYS2`
2. Abra o terminal **MSYS2 UCRT64** e rode `pacman -S mingw-w64-ucrt-x86_64-pango`
3. Acrescente `C:\msys64\ucrt64\bin` ao `PATH` do Windows (Configurações → Sistema → Sobre → Configurações avançadas → Variáveis de ambiente) e abra um terminal novo.

Detalhes: <https://doc.courtbouillon.org/weasyprint/stable/first_steps.html#windows>

## Como funciona

```
arquivo original ──converter──▶ <nome>-ebook/fonte.md ──(questionário, leitura, plano.json)──▶ build ──▶ PDF
   (nunca alterado)               + conversao.md                                             + cortes.md, correcoes.md,
                                                                                              diff-redacao.md, relatorio.md
```

- O arquivo original nunca é alterado nem sobrescrito. O PDF sai ao lado dele, com o nome `<Título> - <Subtítulo>.pdf`.
- A pasta `<nome>-ebook/`, ao lado do original, guarda tudo o que é preciso para refazer ou ajustar o livro.
- As fontes (Source Serif 4, Cormorant Garamond, Inter, JetBrains Mono) vêm embutidas na skill, sob a licença SIL Open Font License (`assets/fontes/LICENSE-*.txt`): o PDF sai igual em qualquer sistema.
- Texto em alfabetos não latinos (hebraico, grego, cirílico) usa as fontes instaladas no sistema como reserva.

## Limitações conhecidas

- `.doc`, `.rtf`, `.odt` e `.pages`: salve como `.docx` antes.
- PDFs com várias colunas, notas laterais ou layout de revista são convertidos em ordem de leitura aproximada; a skill avisa e permite conferir em `conversao.md`.
- O OCR depende da qualidade da digitalização; use o modo "Só correção de língua" para corrigir os erros de reconhecimento.
