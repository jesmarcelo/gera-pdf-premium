# Histórico de versões

Todas as mudanças importantes da skill ficam registradas aqui.
O formato segue o [Keep a Changelog](https://keepachangelog.com/pt-BR/1.1.0/), e as versões seguem o [Versionamento Semântico](https://semver.org/lang/pt-BR/).

## [1.0.0] — 2026-09-24

Primeira versão pública.

### Adicionado

- Conversão de `.md`, `.txt`, `.docx`, PDF com texto e PDF escaneado (OCR com Tesseract).
- Legendas `.srt` e `.vtt` e transcrições coladas com carimbos de tempo (`0:14`, `1:02:07`, como as do YouTube), convertidas em texto corrido com a limpeza registrada.
- Questionário fixo: título, autor, subtítulo e chapéu, tratamento do texto, identidade visual, capa e destino.
- Quatro modos de tratamento: íntegra, só correção de língua, correção + limpeza de ruído e melhoria de redação com aprovação.
- Verificação de integridade caractere a caractere, com cortes e correções declarados em arquivos à parte.
- O livro se apresenta como obra própria: não menciona a origem do texto nem o trabalho de edição, que ficam registrados em `relatorio.md`, `cortes.md` e `correcoes.md`.
- Composição com capa, rosto, créditos, sumário clicável, marcadores, partes, capítulos, capitulares, caixas editoriais, figuras, cabeçalhos correntes e fólios.
- Fontes livres embutidas: Source Serif 4, Cormorant Garamond, Inter e JetBrains Mono.
- Revisão visual com folhas de contato e memória de aprendizados entre execuções.
- Nada é gravado fora do projeto: ambiente Python, caches, backups e temporários ficam em `.gera-pdf-premium/`, no diretório atual. O ambiente é reaproveitado em toda geração, e os temporários (`tmp/`) são apagados com `gerar limpar`.
- Instalação como plugin do Claude Code ou como pasta de skill.
- Comando `/gera-pdf-premium update`, que confere a última versão no GitHub e atualiza a skill, com backup da versão anterior e preservação dos aprendizados.

[1.0.0]: https://github.com/jesmarcelo/gera-pdf-premium/releases/tag/v1.0.0
