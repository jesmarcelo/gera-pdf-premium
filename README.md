# gera-pdf-premium

**Transforme qualquer texto em um ebook PDF com cara de livro de verdade.**

![Capa e páginas internas de um ebook gerado pela gera-pdf-premium](docs/vitrine.jpg)

Você tem uma apostila em Word, a transcrição de uma aula ou de um vídeo do YouTube, as legendas de um vídeo, um artigo em Markdown ou até um PDF escaneado? Esta skill do [Claude Code](https://claude.com/claude-code) pega esse arquivo e devolve um ebook bonito, pronto para vender, compartilhar ou imprimir, com:

- capa, folha de rosto e página de créditos;
- sumário clicável e marcadores (aqueles que aparecem na lateral do leitor de PDF);
- partes e capítulos bem separados, com letra capitular no início;
- caixas de destaque, figuras, cabeçalhos no topo das páginas e numeração;
- fontes profissionais embutidas: o PDF fica igual em qualquer computador.

E o mais importante: **o seu texto é respeitado.** A skill nunca altera o arquivo original e confere, letra por letra, que o conteúdo chegou inteiro ao PDF. Qualquer correção ou corte que você autorizar fica registrado num arquivo à parte, para você conferir.

O ebook se apresenta como uma obra própria: não menciona de onde o texto veio (aula, vídeo, transcrição) nem o trabalho de edição. Esse histórico fica só nos arquivos de apoio, para você.

---

## O que você precisa antes de começar

1. **Claude Code instalado.** Se ainda não tem, siga o [guia oficial](https://docs.claude.com/pt/docs/claude-code/overview).
2. **Algumas ferramentas no computador.** Não se preocupe: na primeira vez que você usar a skill, ela verifica o que falta e **pergunta antes de instalar qualquer coisa**. Se preferir deixar tudo pronto antes, veja a seção [Pré-requisitos](#pré-requisitos) mais abaixo.

---

## Instalação

Escolha **uma** das duas formas.

### Opção A — Como plugin (recomendado)

É a forma mais simples, e você recebe as atualizações sem precisar baixar nada de novo. Dentro do Claude Code, digite estes dois comandos, um de cada vez:

```text
/plugin marketplace add jesmarcelo/gera-pdf-premium
/plugin install gera-pdf-premium@jesmarcelo
```

Pronto: a skill fica disponível em qualquer pasta. Se pedir, feche e abra o Claude Code de novo.

Para atualizar no futuro, veja [Mantendo a skill atualizada](#mantendo-a-skill-atualizada).

### Opção B — Copiando a pasta

Útil se você quiser modificar a skill ou usá-la só num projeto.

**macOS / Linux** (no Terminal):

```bash
git clone https://github.com/jesmarcelo/gera-pdf-premium.git
mkdir -p ~/.claude/skills
cp -R gera-pdf-premium/skills/gera-pdf-premium ~/.claude/skills/
```

**Windows** (no PowerShell):

```powershell
git clone https://github.com/jesmarcelo/gera-pdf-premium.git
New-Item -ItemType Directory -Force "$env:USERPROFILE\.claude\skills" | Out-Null
Copy-Item -Recurse gera-pdf-premium\skills\gera-pdf-premium "$env:USERPROFILE\.claude\skills\"
```

> Não tem o `git`? Clique no botão verde **Code → Download ZIP** aqui no GitHub, descompacte e copie a pasta `skills/gera-pdf-premium` para `~/.claude/skills/` (no Windows, `C:\Users\<seu-usuário>\.claude\skills\`).
>
> Dica: no macOS, pastas que começam com ponto ficam escondidas. No Finder, aperte `Cmd + Shift + .` para vê-las.

Quer a skill só dentro de um projeto? Copie a pasta para `.claude/skills/` dentro desse projeto. Ela só vai aparecer quando você abrir o Claude Code ali.

### Conferindo se deu certo

Abra o Claude Code e digite `/`. Se `gera-pdf-premium` aparecer na lista, está tudo certo. 🎉

Para conferir também as ferramentas do computador, peça ao Claude Code:

> "Verifique os pré-requisitos da gera-pdf-premium"

Se instalou copiando a pasta, você também pode rodar a verificação direto no terminal:

```bash
~/.claude/skills/gera-pdf-premium/scripts/gerar verificar
```

No Windows:

```powershell
& "$env:USERPROFILE\.claude\skills\gera-pdf-premium\scripts\gerar.cmd" verificar
```

Se a última linha disser `RESULTADO pronto`, pode usar. Se disser `faltam pré-requisitos`, cada item que falta vem com o comando para instalar.

---

## Como usar

Abra o Claude Code e peça do jeito que achar mais natural:

```text
/gera-pdf-premium ~/Documentos/minha-apostila.docx
```

Se instalou como plugin, o comando leva o nome do plugin na frente: `/gera-pdf-premium:gera-pdf-premium`. Não precisa decorar. Você também pode simplesmente pedir:

> "Gere um PDF premium do arquivo ~/Documentos/aula-04.txt"

### O que acontece depois

**1. Algumas perguntas rápidas.** A skill lê o começo do texto e já sugere respostas. Na maioria das vezes, é só confirmar:

| Pergunta | Exemplo |
|---|---|
| Título da capa | *Pequenos Hábitos* |
| Autor | *Maria Silva* ou "sem autor na capa" |
| Subtítulo e chapéu | *Aula 04*, com *Curso de Produtividade* em letras pequenas acima do título |
| Como tratar o texto | veja os quatro modos abaixo |
| Identidade visual | combinações de cores e ornamentos que combinam com o tema |
| Imagem de capa | capa só com tipografia ou um prompt para você gerar a imagem em outra IA |
| Onde salvar | por padrão, na mesma pasta do arquivo original |

No final, ela mostra um resumo e pergunta se pode seguir.

**2. Os quatro modos de tratar o texto:**

| Modo | O que faz | Bom para |
|---|---|---|
| **Íntegra** | Não muda nenhuma palavra, só diagrama. | Livros e textos já revisados |
| **Só correção de língua** | Corrige ortografia, acentos e gramática. Não remove nada. | PDFs escaneados (erros de leitura) |
| **Correção + limpeza** | Corrige e tira o que não é conteúdo, como "bom dia a todos", "estão me ouvindo?" e avisos de intervalo, e os vícios de linguagem da fala, como "né?", "tá?" e "ahn". | Transcrições de aulas, palestras e podcasts |
| **Melhoria de redação** | Uma revisão leve de fluidez, mantendo suas ideias e seu jeito de escrever. **Você aprova as mudanças antes** de o PDF ser gerado. | Rascunhos e textos informais |

**3. O PDF fica pronto.** Ele aparece na pasta que você escolheu, com o nome `Título - Subtítulo.pdf`. Antes de entregar, a skill confere as páginas visualmente para encontrar problemas de diagramação.

### Formatos aceitos

| Aceita | Precisa converter antes |
|---|---|
| `.md`, `.txt`, `.docx`, `.srt`, `.vtt`, PDF com texto, PDF escaneado | `.doc`, `.rtf`, `.odt`, `.pages` → salve como `.docx` no Word, LibreOffice ou Pages |

### O que fica guardado

Ao lado do seu arquivo original, a skill cria uma pasta `<nome>-ebook/` com tudo o que foi feito:

- `correcoes.md`: cada correção feita no texto;
- `cortes.md`: cada trecho retirado e o motivo;
- `diff-redacao.md`: o antes e depois da melhoria de redação, se você escolheu esse modo;
- `relatorio.md`: o resumo final, com a nota do que foi feito na edição (ela não aparece no livro);
- `plano.json`: o "projeto" do livro. Com ele, dá para pedir ajustes e gerar de novo sem começar do zero.

Quer mudar a cor, trocar o subtítulo ou mover um capítulo? É só pedir ao Claude Code e apontar para essa pasta.

A skill não grava nada fora do projeto (nem em `/tmp` ou em outras pastas do sistema). O que ela precisa para funcionar fica numa pasta oculta `.gera-pdf-premium/`, no diretório onde você usa o Claude Code: o ambiente Python, os downloads e os backups das atualizações. Essa pasta é reaproveitada em toda geração e fica fora do git do projeto. Os arquivos temporários ficam em `.gera-pdf-premium/tmp/` e são apagados no final.

---

## Mantendo a skill atualizada

De vez em quando, digite no Claude Code:

```text
/gera-pdf-premium update
```

A skill confere no GitHub se existe uma versão mais nova:

- **Se existir**, ela se atualiza sozinha e mostra o link com as novidades.
- **Se não existir**, avisa que você já está na versão mais recente.

Funciona nas duas formas de instalação:

- **Plugin:** o comando é `/gera-pdf-premium:gera-pdf-premium update`. Depois de atualizar, feche e abra o Claude Code.
- **Pasta copiada:** antes de trocar os arquivos, a skill guarda uma cópia da versão anterior em `.gera-pdf-premium/backups/`, dentro do projeto. O que ela aprendeu com você (`APRENDIZADOS.md`) é mantido.

---

## Pré-requisitos

Se preferir instalar tudo antes do primeiro uso:

| Ferramenta | Para que serve | macOS | Linux (Ubuntu/Debian) | Windows |
|---|---|---|---|---|
| **uv** | Roda a skill (já traz o próprio Python) | `curl -LsSf https://astral.sh/uv/install.sh \| sh` | igual ao macOS | `powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 \| iex"` |
| **Pango** | Desenha o PDF | `brew install pango` | `sudo apt install libpango-1.0-0 libpangoft2-1.0-0` | veja abaixo |
| **Tesseract** *(opcional)* | Lê PDFs escaneados | `brew install tesseract tesseract-lang` | `sudo apt install tesseract-ocr tesseract-ocr-por` | `winget install UB-Mannheim.TesseractOCR` |

No macOS, o `brew` vem do [Homebrew](https://brew.sh).

O **uv** evita mexer no Python do seu computador: ele usa uma versão só dele. As bibliotecas que a skill precisa são instaladas sozinhas no primeiro uso em cada projeto (leva cerca de 1 minuto), na pasta `.gera-pdf-premium/venv` do projeto. Nas próximas vezes, ela é reaproveitada.

### Pango no Windows (passo a passo)

1. Instale o MSYS2: `winget install MSYS2.MSYS2`
2. Abra o programa **MSYS2 UCRT64** e rode: `pacman -S mingw-w64-ucrt-x86_64-pango`
3. Adicione `C:\msys64\ucrt64\bin` ao `PATH` do Windows: **Configurações → Sistema → Sobre → Configurações avançadas do sistema → Variáveis de ambiente**.
4. Feche e abra o terminal de novo.

Mais detalhes na [documentação do WeasyPrint](https://doc.courtbouillon.org/weasyprint/stable/first_steps.html#windows).

---

## Dúvidas comuns

**A skill vai estragar meu arquivo?**
Não. O arquivo original nunca é alterado nem sobrescrito. Se o PDF tiver o mesmo nome de um arquivo existente, ele ganha " (premium)" no final.

**Preciso saber programar?**
Não. Você conversa com o Claude Code em português, e ele cuida do resto.

**A skill gera a imagem da capa?**
Não. Ela pode criar um *prompt*, um texto pronto para você colar no ChatGPT, Gemini ou Midjourney. Depois, é só informar onde salvou a imagem. Se preferir, a capa só com tipografia já fica bem elegante.

**O PDF escaneado saiu com erros.**
O reconhecimento de texto (OCR) depende da qualidade da digitalização. Use o modo **Só correção de língua**, que corrige esses erros.

**Meu PDF tem duas colunas e o texto ficou fora de ordem.**
Layouts de revista, com várias colunas ou notas laterais, são convertidos na ordem de leitura mais provável. A skill avisa quando isso acontece, e você pode conferir o resultado em `conversao.md`, dentro da pasta `<nome>-ebook/`.

**A skill aprende com o uso?**
Sim. No fim de cada execução, ela anota o que deu errado e as suas preferências no arquivo `APRENDIZADOS.md`, dentro da pasta da skill. Na próxima vez, já começa sabendo.

Um detalhe: se você instalou como plugin, cada atualização substitui a pasta da skill e esses aprendizados recomeçam do zero. Se você usa a skill muito e quer guardar o que ela aprendeu, prefira a instalação copiando a pasta (Opção B).

---

## Exemplo

A pasta [`exemplos/neutro`](skills/gera-pdf-premium/exemplos/neutro) tem um texto curto (*Pequenos Hábitos*) e o plano editorial dele. Experimente:

```text
/gera-pdf-premium <caminho-da-skill>/exemplos/neutro/Pequenos Hábitos.md
```

---

## Licença e créditos

O código da skill é livre, sob a [licença MIT](LICENSE): pode usar, modificar e distribuir, inclusive em projetos comerciais.

As fontes Source Serif 4, Cormorant Garamond, Inter e JetBrains Mono são distribuídas sob a [SIL Open Font License](skills/gera-pdf-premium/assets/fontes/). O PDF é gerado com o [WeasyPrint](https://weasyprint.org).

Encontrou um problema ou tem uma ideia? Veja [como contribuir](CONTRIBUTING.md).
