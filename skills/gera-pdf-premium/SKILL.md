---
name: gera-pdf-premium
description: Transforma qualquer texto — arquivo .md, .txt, .docx, legenda .srt/.vtt, PDF com texto ou PDF escaneado (OCR) — em um ebook PDF premium, com capa, rosto, sumário clicável, bookmarks, partes e capítulos, capitulares, caixas editoriais, figuras vetoriais, cabeçalhos correntes e fólios. Conduz um questionário fixo (título, autor, subtítulo, tratamento do texto, identidade visual, capa, destino) e oferece quatro modos: íntegra, só correção de língua, correção + limpeza de ruído, ou melhoria leve de redação com aprovação. Verifica automaticamente que o texto chegou intacto, com cada corte e correção declarados. Use quando o usuário pedir para gerar, converter ou diagramar um documento em PDF, ebook, livro digital, apostila ou material com design profissional. Recebe como argumento o caminho do arquivo, ou `update` para atualizar a skill pela versão mais recente do GitHub.
argument-hint: <arquivo.md|.txt|.docx|.pdf|.srt|.vtt> | update
---

# gera-pdf-premium — qualquer texto → ebook PDF premium

Arquivo de entrada: **$ARGUMENTS**
(Se vazio, pergunte ao usuário qual arquivo usar antes de qualquer coisa. Se for `update` ou `atualizar`, não é um arquivo: siga só a seção "Atualizar a skill" abaixo e pare.)

Você vai agir como uma equipe editorial completa — designer premiado, especialista em UX de leitura, diretor de arte, tipógrafo, editor e engenheiro de publicação — e entregar um ebook com cara de produto comercial, não de conversão automática.

## Como chamar o motor

`SKILL_DIR` é a pasta onde está este `SKILL.md` (em geral `~/.claude/skills/gera-pdf-premium` ou, instalada como plugin, a pasta `skills/gera-pdf-premium` do plugin). Todos os comandos passam por um único executável:

- macOS / Linux: `"<SKILL_DIR>/scripts/gerar" <subcomando> …`
- Windows: `"<SKILL_DIR>\scripts\gerar.cmd" <subcomando> …`

Nos exemplos abaixo, `gerar` significa esse caminho completo. Cada chamada de Bash é um shell novo: escreva o caminho completo em todas. **Nunca use `cd`**: passe caminhos absolutos entre aspas (em alguns apps o `cd` muda o diretório da sessão e o comando é recusado).

Esta skill **aprende**: tem memória (`APRENDIZADOS.md`), registra sozinha cada falha do motor (`aprendizados/ocorrencias.jsonl`) e termina toda execução com uma retrospectiva que corrige as próprias instruções, o CSS ou o motor (passo 12). Não pule os passos 0 e 12.

## Atualizar a skill (`update`)

Quando o argumento for `update` ou `atualizar` (ou o usuário pedir para atualizar a skill), rode só isto — sem passo P, sem questionário, sem converter nada:

```bash
gerar atualizar
```

Ele consulta a última release no GitHub, compara com o arquivo `VERSAO` e, se houver versão nova, atualiza conforme a forma de instalação. Não peça confirmação: o usuário já pediu a atualização. Leia a linha `RESULTADO` e responda em poucas linhas:

| `RESULTADO` | O que dizer |
|---|---|
| `ultima-versao` | "Você já está na versão mais recente (`ATUAL`)." |
| `atualizado` (pasta) | Atualizou de `ATUAL` para `ULTIMA`; o link `NOVIDADES` mostra o que mudou; `APRENDIZADOS.md` e `aprendizados/` foram preservados; a versão anterior está em `BACKUP`. Se `APRENDIZADOS.md` registrar correções aplicadas em arquivos da skill, avise que elas estão só no backup e ofereça reaplicá-las. |
| `atualizado` (plugin) | Atualizou de `ATUAL` para `ULTIMA`; é preciso fechar e abrir o Claude Code; link `NOVIDADES`. Os aprendizados de um plugin recomeçam a cada atualização. |
| `disponivel` | Há a versão `ULTIMA`, mas ela não foi instalada: mostre o `AVISO` e os `COMANDO` a rodar (num clone do repositório, é `git pull`). |
| `erro` | Mostre o `ERRO` e diga que nada foi alterado (ou que o backup foi restaurado). |

## Regras absolutas

1. **O arquivo original é imutável.** Nunca o edite, sobrescreva ou substitua. `gerar converter` cria `fonte.md` na pasta de trabalho; a partir daí `fonte.md` também é imutável. O motor confere o SHA-256 dos dois antes e depois. O PDF nunca é gravado por cima do original (se o nome coincidir, ganha " (premium)").
2. **O modo escolhido pelo usuário manda.** Íntegra = nenhuma palavra muda. Só correção de língua = só `correcoes`. Correção + limpeza = `cortes` + `correcoes`. Melhoria de redação = `texto-editado.md` aprovado pelo usuário. O motor recusa um plano que contrarie o `modo`.
3. **Corrija a língua, nunca o conteúdo.** Proibido resumir, reordenar, parafrasear, acrescentar informação ou "melhorar" opiniões — em todos os modos. Mesmo a melhoria de redação é leve e mantém ideias, dados, ordem e voz do autor.
4. **O build é o juiz.** O motor extrai o texto de todo elemento `data-src` do HTML final e compara com a fonte menos os cortes e com as correções declaradas, caractere a caractere (ignora só espaços e a forma das aspas). Se falhar, o PDF não é gerado. O motor também recusa correções que viram paráfrase (mais de 40 palavras ou muitas palavras novas). Nunca contorne essas verificações.
5. **Tudo o que não é do autor é declarado — fora do livro.** Títulos de navegação, nomes de partes, rótulos de caixas, glossário, figuras e epígrafe são editoriais. A limpeza técnica da conversão está em `conversao.md`; cortes em `cortes.md`; correções em `correcoes.md`; redação em `diff-redacao.md`; o resumo do que foi feito, em `relatorio.md`. No relatório final você diz tudo isso ao usuário com clareza.
6. **O livro se apresenta como obra própria.** O PDF não menciona de onde o texto veio nem como foi feito: nada de arquivo de origem, aula, vídeo, transcrição, palestrante, "texto original", cortes, correções, "editorial" ou o nome desta skill. Todo texto que você escreve para o livro (títulos, rótulos, legendas, glossário, descrição da capa, créditos) fala direto do assunto: "A casa e a sucá: a estrutura permanente e a provisória", nunca "A casa e a sucá, como a aula as descreve". Em `creditos`, só pessoas (autor, organizador, tradutor).
7. **Nada fora do projeto.** Nunca use `/tmp`, `/var`, `/private`, `%TEMP%` nem qualquer diretório fora do projeto (o ambiente pode bloqueá-los). O `gerar` guarda tudo em `.gera-pdf-premium/` no diretório atual: ambiente Python (`venv/`), caches e backups, que ficam, e temporários (`tmp/`), que ele apaga a cada execução. Arquivos seus de rascunho e as folhas do `preview` vão para `.gera-pdf-premium/tmp/`. Ao terminar, rode `gerar limpar` (apaga só o `tmp/`).

## Processo

### P. Pré-requisitos — antes de tudo

```bash
gerar verificar
```

Não depende de Python. Cada linha é `OK`, `FALTA`, `OPCIONAL` ou `PENDENTE`, com o comando de instalação do sistema do usuário depois de `instalar:`. A última linha é `RESULTADO pronto` ou `RESULTADO faltam pré-requisitos`.

- `FALTA python` ou `FALTA uv`: **pergunte com `AskUserQuestion` se pode instalar**, mostrando o comando exato. Opções: "Instalar o uv (Recomendado) — traz um Python próprio, sem mexer no do sistema" (`curl -LsSf https://astral.sh/uv/install.sh | sh`; no Windows `powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"`), "Instalar o Python do sistema" (o comando da linha `FALTA python`), "Não instalar". Só execute com o "sim".
- `FALTA pango`: é obrigatório para gerar o PDF. Pergunte do mesmo jeito, com o comando da linha. No Windows, mostre o passo a passo do `README.md` e deixe o usuário executar.
- `OPCIONAL tesseract`: só pergunte se a entrada for um PDF escaneado (o `converter` avisa).
- Recusou? Explique o que fica impossível (sem Python ou pango não há PDF; sem tesseract não há OCR) e pare — ou siga, se o item recusado não for necessário para esta entrada.
- Depois de instalar, rode `gerar verificar` de novo e só continue com `RESULTADO pronto`. Comandos com `sudo` pedem senha: se o terminal não permitir, peça ao usuário que rode o comando e avise quando terminar.

O ambiente Python da skill é criado sozinho no primeiro uso (`gerar setup`, ~1 min).

### 0. Consultar a memória da skill

1. Leia **[APRENDIZADOS.md](APRENDIZADOS.md)** inteiro: preferências e regras aprendidas valem como parte destas instruções.
2. Rode `gerar ocorrencias`. Se houver falhas não revisadas de execuções anteriores, trate-as na retrospectiva (passo 12) — ou, se forem só do plano de outro livro, marque-as como revisadas.

### 1. Converter

```bash
gerar converter "<arquivo>"
```

Aceita `.md`, `.txt`, `.docx`, `.pdf` (com texto ou escaneado; `--idioma por+eng` escolhe o idioma do OCR) e legendas `.srt`/`.vtt` (tratadas como transcrição). Transcrição colada com carimbos de tempo (`0:14`, `1:02:07`) no `.txt` também é reconhecida: os carimbos saem e os segmentos viram texto corrido. Para `.doc`, `.rtf`, `.odt` ou `.pages`, peça ao usuário que salve como `.docx`. Cria `<pasta-do-original>/<nome>-ebook/` com:

- `fonte.md` — o texto em Markdown normalizado: **a fonte oficial de todo o resto**. `.md` é copiado byte a byte.
- `conversao.md` / `conversao.json` — relatório: tipo de fonte, indícios, limpeza técnica declarada (cabeçalhos e rodapés corridos, fólios, sumário antigo, hifenização, OCR), avisos, metadados, sugestões de título e autor e volumes irmãos da mesma série.
- `figuras/` — imagens extraídas do DOCX/PDF.

Leia `conversao.md`. Se a limpeza técnica levou algo que parece conteúdo (um intertítulo tomado por cabeçalho corrido, por exemplo), avise o usuário antes de seguir. PDF escaneado sem tesseract: volte ao passo P.

**Tipo de fonte** (decide os critérios de corte e correção):

| tipo | o que é |
|---|---|
| `transcricao` | fala transcrita: aula, palestra, entrevista, podcast |
| `documento` | texto escrito: artigo, relatório, ensaio, apostila curta |
| `livro` | livro ou apostila longa com hierarquia de títulos |
| `notas` | notas, listas e tópicos curtos |

A classificação é automática. Se a leitura mostrar outra coisa, prevalece a leitura: diga isso no resumo do questionário.

Se o `converter` listar uma **SÉRIE** (pastas `*-ebook/` irmãs com `plano.json`), abra o plano do volume anterior e use identidade, créditos, grafia de termos e padrão de nome como sugestões recomendadas.

### 2. Analisar

```bash
gerar analisar "<pasta>-ebook/fonte.md"
```

Mostra blocos por tipo, árvore de títulos, parágrafos gigantes, imagens faltando, frases repetidas (que não servem de âncora nem de corte sem `ocorrencia`), **possíveis cortes** (só pistas — os sinais dependem do tipo de fonte), estimativa de páginas e o **modo de capítulos sugerido**:

- **`titulos`** — o texto já tem hierarquia; os títulos viram capítulos.
- **`ancoras`** — texto corrido; você define os capítulos por trechos literais.

### 3. Questionário — sempre igual, sempre nesta ordem

Antes de ler o texto inteiro, conheça o início dele (primeiras ~150 linhas de `fonte.md`) para fazer boas sugestões. Depois faça **exatamente estas perguntas, nesta ordem**, com `AskUserQuestion`. Em cada uma, a melhor sugestão vem primeiro, marcada "(Recomendado)", e o usuário sempre pode escrever outra resposta. (Sem `AskUserQuestion` no ambiente, faça as mesmas perguntas em texto, numeradas, na mesma ordem.)

**Chamada 1 — o livro**

1. **Título da capa** (`Título`): até 3 sugestões, na ordem: série (se houver), metadados, `# título` do texto, título inferido do conteúdo. Se o título ficar melhor em duas linhas na capa, diga isso na descrição da opção.
2. **Autor** (`Autor`): metadados do DOCX/PDF, autor da série, nomes que aparecem no texto como autor ou professor. Uma opção "Sem autor na capa".
3. **Subtítulo e chapéu** (`Subtítulo`): subtítulo = linha sob o título; chapéu = linha pequena acima dele (coleção, volume, evento). Sugira pares como "Subtítulo: Aula 04 · Chapéu: Curso X · Módulo 1" e uma opção "Sem subtítulo nem chapéu".
4. **Tratamento do texto** (`Texto`), com as quatro opções abaixo. A descrição de cada uma diz, **para este documento e este tipo de fonte**, o que vai acontecer (ex.: numa transcrição, "retira boas-vindas, avisos técnicos e despedidas"; num PDF escaneado, "corrige os erros do OCR"). Recomende: `transcricao` → Correção + limpeza; OCR → Só correção de língua; `documento`/`livro` bem escritos → Íntegra.
   - **Íntegra** — nenhuma palavra muda; só diagramação.
   - **Só correção de língua** — ortografia, acentuação, gramática, termos mal grafados; nada é removido.
   - **Correção + limpeza de ruído** — corrige e retira o que não é conteúdo (critérios em "O que cortar").
   - **Melhoria de redação** — revisão leve de fluidez e clareza, mantendo ideias e voz; você aprova um diff antes do PDF.

**Chamada 2 — a aparência e a entrega**

5. **Identidade visual** (`Visual`): até 4 combinações de paleta + selo coerentes com o tema do texto (paletas em PLANO.md, `tema`). Ex.: "noite-ouro + hexagrama — espiritualidade, sóbrio e luxuoso". Formato padrão 152×229 mm; se o conteúdo tiver tabelas largas ou for de trabalho (manual, relatório), ofereça A4.
6. **Imagem de capa** (`Capa`): "Capa só tipográfica (Recomendado)" ou "Gerar prompt para criar a imagem em outra IA". Não gere imagens nesta skill.
7. **Nome e pasta do PDF** (`Destino`): padrão `<Título> - <Subtítulo>.pdf` na pasta do arquivo original (mostre o caminho completo), e opções como "Área de Trabalho" ou "pasta de trabalho".

**Chamada 3 — confirmação**

Mostre um resumo em texto (título, autor, subtítulo, chapéu, modo, tipo de fonte, paleta, selo, formato, capa, caminho do PDF) e pergunte `Confirma?` com as opções "Confirmar e seguir" e "Ajustar". Se for "Ajustar", refaça só as perguntas que mudarem.

Grave as respostas em `<pasta>-ebook/respostas.json`:

```json
{ "titulo": "…", "titulo_capa": "…\n…", "autor": "…", "subtitulo": "…", "chapeu": "…",
  "modo": "integra|lingua|limpeza|redacao", "tipo_fonte": "…",
  "tema": { "preset": "…", "selo": "…", "formato": "152x229" },
  "capa": "tipografica|prompt", "saida": "/caminho/completo.pdf" }
```

Se a pasta já tiver um `respostas.json` de uma execução anterior, ofereça as mesmas respostas como "(Recomendado)". Uma nova execução com as mesmas respostas deve dar o mesmo livro.

### 4. Ler o documento inteiro

**Obrigatório.** Leia `fonte.md` do começo ao fim (com `Read`, em partes se for grande). As decisões editoriais — onde começam os capítulos, que parágrafos merecem destaque, o que é fórmula, diálogo ou alerta, que diagrama ajuda, o que é ruído, o que é erro de língua — só podem vir da leitura real. Não amostre.

### 5. Tratamento do texto, conforme o modo

| modo | o que você faz | o que vai no plano |
|---|---|---|
| `integra` | nada no texto | nem `cortes` nem `correcoes` |
| `lingua` | anota os erros de língua ("O que corrigir") | só `correcoes` |
| `limpeza` | anota ruído ("O que cortar") e erros de língua | `cortes` + `correcoes` |
| `redacao` | escreve `texto-editado.md` ("Melhoria de redação") e obtém a aprovação | nem `cortes` nem `correcoes` |

#### O que cortar (modo `limpeza`) — depende do tipo de fonte

**Transcrição** (`transcricao`)
- Apresentação e boas-vindas protocolares; apresentação de convidados e participantes.
- Logística do curso ou evento — gravações, grupos, tarefas, horários, próximos encontros.
- Problemas técnicos e manuseio — áudio, câmera, tela, "deixa eu abrir o chat".
- Falas dirigidas a alguém sem conteúdo — "fulano, usa o chat", "esperando a Maria entrar".
- Conversa paralela sem relação com o tema; piadas internas; vida pessoal que não ilustra o ensinamento.
- Agradecimentos, despedidas e encerramento.
- Duplicações da transcrição automática (a análise aponta em FRASES REPETIDAS): mantenha a primeira ocorrência e corte as outras com `"ocorrencia"`.

**Documento, livro e notas**
- Sumário, índice ou lista de figuras escritos à mão dentro do texto (o ebook gera os seus).
- Marcas de revisão e de rascunho — "TODO", "[revisar]", "xxx", comentários de revisor, versões e datas de controle.
- Blocos duplicados por colagem ou exportação.
- Avisos de página ("página deixada em branco", "continua na próxima página"), cabeçalhos técnicos de exportação.
- Cabeçalho, rodapé ou assinatura de e-mail colados junto com o texto, quando não fazem parte da obra.

**Em qualquer tipo, nunca cortar:** conteúdo, argumentos, exemplos, histórias, perguntas e respostas sobre o tema, retomadas e repetições didáticas, muletas dentro da explicação, notas, referências e bibliografia. **Trecho misto:** corte só a parte que é ruído. Na dúvida, mantenha. Depois do build, **leia `cortes.md` inteiro**.

#### O que corrigir (modos `lingua` e `limpeza`)

Declare em `correcoes` (esquema em PLANO.md), sempre com o menor trecho que resolva:

- **Ortografia e acentuação**; **gramática pontual** — concordância, regência, crase, pronome, tempo verbal trocado.
- **Termos mal grafados, transcritos ou reconhecidos pelo OCR**, quando o termo certo é inequívoco pelo contexto. Padronize a grafia de nomes e termos no livro todo.
- **Falsos começos e tropeços** (transcrição) que deixam a frase sem sentido — fique com a versão que o autor quis dizer, usando as palavras dele.
- **Resíduos de limpeza ou de OCR** — marcas órfãs (", ?", "? ?"), letras trocadas ("rn" → "m"), palavras coladas. Para um padrão repetido e sempre igual, `"todas": true`.
- **Pontuação** que muda o sentido ou quebra a frase.

**Nunca corrigir:** o registro do autor (numa transcrição, "a gente", "pra", "tá" ficam); repetições didáticas; conteúdo, opinião ou doutrina, mesmo que pareçam imprecisos; lacunas da gravação ou do original (nunca complete — sinalize com nota de glossário, se ajudar); palavra duvidosa; frases que só funcionariam reescritas. Depois do build, **leia `correcoes.md` inteiro** e confira que cada "Corrigido" diz o mesmo que o "Original".

#### Melhoria de redação (modo `redacao`)

1. Escreva `<pasta>-ebook/texto-editado.md` a partir de `fonte.md`, parágrafo a parágrafo, **mantendo a mesma sequência de parágrafos e todos os títulos idênticos**:
   - pode: dar fluidez, desfazer frases truncadas, tirar muletas, repetições acidentais e redundâncias, corrigir língua, ajustar pontuação, trocar uma palavra imprecisa pela precisa;
   - não pode: resumir, cortar ideias, reordenar, fundir ou criar parágrafos, mudar números, nomes, datas, citações literais ou termos técnicos, acrescentar exemplos, opiniões ou explicações;
   - numa transcrição, a fala vira texto limpo, mas continua sendo a voz do autor (primeira pessoa, exemplos dele); num texto escrito, a intervenção é ainda menor.
2. Rode `gerar redigir-diff "<pasta>/fonte.md" "<pasta>/texto-editado.md"`. Ele grava `diff-redacao.md` e `diff-redacao.html` (supressões em vermelho, inserções em verde) e lista **alertas**: parágrafo novo ou removido, números diferentes, título alterado, mudança grande, texto encolhido mais de 15%. **Resolva todos os alertas** antes de mostrar ao usuário (ou justifique cada um).
3. **Pause e peça aprovação** com `AskUserQuestion`: mostre o resumo (palavras antes → depois, % alterado, parágrafos editados), 2–3 exemplos "antes → depois" e o caminho de `diff-redacao.html` para abrir no navegador. Opções: "Aprovar", "Ajustar (diga o quê)", "Voltar para Só correção de língua". Sem aprovação, não componha.
4. Aprovado: o plano leva `"modo": "redacao"` e o build usa `texto-editado.md` como fonte. Se editar o texto de novo, rode o diff de novo — o motor recusa compor um `texto-editado.md` mais novo que o `diff-redacao.md`.

### 6. Planejamento editorial → `plano.json`

Escreva `<pasta>-ebook/plano.json`. O esquema completo, com exemplos e critérios, está em **[PLANO.md](PLANO.md)** — leia-o antes. Exemplo completo: `exemplos/neutro/Pequenos Hábitos-ebook/plano.json` (com a fonte `exemplos/neutro/Pequenos Hábitos.md`).

- **`modo`** e **`meta`/`tema`** vêm do `respostas.json` (título, `titulo_capa`, subtítulo, chapéu, autor → `autores` e `creditos`, paleta, selo, formato).
- **Cortes e correções** conforme o modo. Ordem de aplicação: cortes → correções → âncoras. Âncoras de capítulos, caixas, destaques, glossário e figuras, e também a epígrafe, usam o texto **já cortado e corrigido**.
- **Arquitetura:** partes (3–7 costumam funcionar) e capítulos de 3–6 páginas; num texto corrido, corte onde o assunto muda de fato. Num texto com boa hierarquia, respeite a do autor.
- **Componentes:** caixas para fórmulas, diálogos, alertas e exemplos; poucos destaques (5–8 num livro de 100 páginas); glossário só para termos que o texto usa sem explicar.
- **Figuras:** diagramas que o texto descreve (ver "Imagens").
- **Metadados:** título, autores, descrição, palavras-chave.
- **Saltos:** transcrições e OCR às vezes perdem trechos — a frase quebra no meio e o assunto muda. Não complete nada: sinalize com uma nota de glossário ("Salto no original — …") no ponto de retomada e, se o assunto muda ali, comece o capítulo nesse ponto.

Ao escrever `de` (correções), `trecho`/`inicio` (cortes) e âncoras, **copie do arquivo**, respeitando maiúsculas e minúsculas — no meio de frase o texto costuma ter "é como…", não "É como…".

### 7. Imagem de capa (só se o usuário escolheu "prompt")

1. Escreva `<pasta>-ebook/prompt-capa.txt` com o prompt em **português e em inglês**. O prompt deve ter:
   - formato vertical 2:3, alta resolução;
   - **nenhum texto, letra, número ou logotipo na imagem** (o título é composto pela skill por cima);
   - estilo e motivos derivados do tema real do livro — metáforas visuais do conteúdo, nunca clichês genéricos;
   - paleta da identidade escolhida, com as cores do preset em hexadecimal;
   - área calma e escura no terço central-superior, onde o título vai ficar, porque a capa aplica um véu escuro;
   - o que evitar: texto, marcas d'água, molduras, rostos de pessoas reais.
2. **Pause** e pergunte com `AskUserQuestion`: "Já gerei o prompt em `prompt-capa.txt`. Cole-o no seu gerador de imagens (ChatGPT, Gemini, Midjourney…) e me diga o caminho da imagem." Opções: "Informar o caminho da imagem", "Seguir sem imagem (capa tipográfica)".
3. Com a imagem: confira que o arquivo existe, **olhe-a com `Read`**, copie-a para `figuras/` e use em `meta.capa_imagem`. Se tiver texto ou não combinar com a paleta, diga isso ao usuário e ofereça seguir sem ela.

### 8. Compor

```bash
gerar build "<pasta>-ebook/fonte.md" --saida "<caminho de respostas.saida>"
```

(No modo `redacao`: `gerar build "<pasta>-ebook/texto-editado.md" --saida …`.)

Se der erro, o motor lista **todos** os problemas de uma vez — âncora não encontrada, ambígua, dentro de marcação, capítulos fora de ordem, plano incompatível com o modo. Corrija o plano e rode de novo. Se a integridade falhar (código 3), ele mostra a primeira divergência e deixa o HTML de diagnóstico: o problema está no plano ou no motor, **nunca** se resolve mexendo em `fonte.md`.

### 9. Revisão visual — não pule

```bash
gerar preview "<arquivo.pdf>"
```

Imprime a auditoria (páginas, metadados, bookmarks, links, aberturas de capítulo, páginas quase vazias) e gera folhas de contato com todas as páginas em `.gera-pdf-premium/tmp/preview/` (o caminho sai na saída do comando). **Abra cada folha com `Read`** e procure problemas. Nas miniaturas o texto parece mais pesado do que é: para julgar tipografia, veja de perto:

```bash
gerar preview "<arquivo.pdf>" --paginas "1-8,52-55"
```

| Sintoma | Correção |
|---|---|
| Colofão ou epígrafe transbordando para uma página extra | `css_extra`: reduzir `padding-top` de `.colofao` / `.epigrafe` |
| Abertura de capítulo quase vazia e a figura na página seguinte | reduzir `altura_max_mm` da figura (≈95–105 cabem com o cabeçalho) |
| Hifenização feia em título, epígrafe ou caixa | `css_extra`: `hyphens: none` no seletor |
| Página com 2–5 linhas no fim de capítulo | aceitável em livro; se incomodar, mover a âncora do capítulo seguinte |
| Caixa enorme ocupando página inteira | normal para diálogos longos; se quebrar mal, dividir em duas caixas |
| Tabela larga espremida | `css_extra` com fonte menor para `.md-tabela table` ou formato A4 |
| Abertura de capítulo vazia porque uma caixa longa pulou inteira | diálogos e exemplos já quebram; para outro tipo, `css_extra` com `break-inside: auto` em `.caixa-<tipo>` |
| Quadradinhos (▯) no lugar de letras | caractere fora do latim (hebraico, grego, cirílico…) sem fonte no sistema: `tema.fontes` com uma fonte instalada que o cubra (ex.: `"serif": "\"GP Source Serif 4\", \"Noto Serif Hebrew\", serif"`) |
| Livro convertido de PDF com restos de capa, créditos ou sumário do original | modo `limpeza`: cortar esses trechos declarando o motivo "material do original" |

Cada sintoma novo que você resolver entra nesta tabela no passo 12.

Corrija, recompile, reveja. Repita até que toda página pareça desenhada de propósito.

### 10. Validação final

Responda com evidência (saída do build e do preview), não por impressão:

1. O texto mantido está presente e inalterado? → linha `[integridade] OK` + fonte e original inalterados (hash)
2. Os cortes são só ruído? → `cortes.md` relido por inteiro. As correções são só de língua? → `correcoes.md` relido. A redação foi aprovada? → aprovação registrada e `diff-redacao.md` atual
3. A conversão não levou conteúdo? → `conversao.md` relido
4. Todas as imagens aparecem? → análise (✓) + folhas de contato
5. Todos os capítulos aparecem? → contagem de aberturas no preview
6. O índice está correto? → sumário com números de página reais
7. A navegação funciona? → bookmarks e páginas com links > 0
8. As respostas do questionário estão no livro? → capa, rosto, créditos, nome e pasta do PDF
9. O livro fala como obra própria? → nenhum título, rótulo, legenda, nota ou crédito cita a origem (aula, vídeo, transcrição, "texto original"), o trabalho editorial ou esta skill (regra 6)
10. A aparência é profissional e a leitura confortável, como num ebook comercial? → sua revisão das folhas

Qualquer "não": corrija antes de entregar.

### 11. Entrega

1. Rode `gerar limpar` para apagar `.gera-pdf-premium/tmp/` (folhas do preview e rascunhos; o ambiente fica). Depois informe o caminho completo do PDF (e anexe o arquivo, se o ambiente tiver ferramenta para isso).
2. Informe os arquivos da pasta de trabalho: `fonte.md`, `conversao.md`, `respostas.json`, `plano.json`, `ebook.html`, `ebook.css`, `figuras/`, `relatorio.md` e, conforme o caso, `cortes.md`, `correcoes.md`, `texto-editado.md`, `diff-redacao.md`/`.html` e `prompt-capa.txt`.
3. Relatório curto:
   - **Origem** — formato, tipo de fonte e o que a conversão limpou (com contagens);
   - **Estrutura criada** — partes, capítulos, apêndices, componentes;
   - **Melhorias visuais aplicadas** — identidade, tipografia, grade, componentes, navegação;
   - **Tratamento do texto** — o modo; cortes (quantos, por categoria, e o que ficou de propósito); correções (quantas, por tipo, 2–3 exemplos "antes → depois"); ou a redação (% alterado e exemplos);
   - **Preservação do conteúdo** — resultado da verificação (caracteres comparados, hashes) **e** a lista honesta do que é acréscimo editorial;
   - **O que a skill aprendeu** — as mudanças do passo 12 (uma linha cada), ou "nenhuma".

### 12. Retrospectiva e autoaperfeiçoamento — obrigatório

Faça isto antes do relatório final (e de novo sempre que o usuário der um retorno sobre o PDF entregue).

1. **Levante tudo o que deu errado ou custou retrabalho** nesta execução: cada erro do build ou da conversão, cada exceção, cada recompilação por problema visual, cada instrução que você teve de adivinhar, cada correção pedida pelo usuário. Rode `gerar ocorrencias` para ver as falhas registradas.
2. **Classifique e corrija na fonte certa** — a correção vai para a skill, não só para o plano deste livro:

   | Tipo | Onde corrigir |
   |---|---|
   | Instrução ambígua, faltando ou que induziu ao erro | `SKILL.md` ou `PLANO.md` (regra curta + exemplo real) |
   | Bug, traceback, mensagem obscura, comportamento diferente do documentado | `scripts/motor.py` ou `scripts/conversores.py` (correção mínima; erro legível em vez de traceback) |
   | Artefato de extração não limpo, ou conteúdo limpo por engano | `scripts/conversores.py` (regra geral, nunca específica de um arquivo) |
   | Ajuste visual que se repetiria em outros livros | `assets/ebook.css` ou a tabela de sintomas do passo 9 |
   | Preferência do usuário (estilo, nomes, identidade, o que cortar) | seção "Preferências do usuário" de `APRENDIZADOS.md` |
   | Específico deste livro | só o `plano.json` — não generalize |

3. **Limites — o autoaperfeiçoamento nunca pode:** enfraquecer as Regras absolutas, afrouxar a verificação de integridade, as travas de paráfrase, as travas de modo ou a imutabilidade do original e de `fonte.md`; mudar o questionário (perguntas, ordem); apagar aprendizados anteriores sem motivo; mudar o comportamento por um caso isolado quando a regra atual está certa.
4. **Teste de regressão** a cada mudança no motor, nos conversores ou no CSS: recompile o livro atual **e** o exemplo neutro numa cópia temporária — copie `<SKILL_DIR>/exemplos/neutro/` para uma pasta temporária, rode `gerar converter "<tmp>/Pequenos Hábitos.md"` e `gerar build "<tmp>/Pequenos Hábitos-ebook/fonte.md" --saida "<tmp>/neutro.pdf"` — e confirme `[integridade] OK` (nunca componha dentro da pasta da skill). Se quebrar, desfaça ou conserte antes de seguir.
5. **Registre** cada mudança em `APRENDIZADOS.md` (data, sintoma, causa, correção aplicada e onde) e depois rode `gerar ocorrencias --marcar-revisadas`.
6. Conte ao usuário, no relatório, o que a skill aprendeu.

## Imagens

- **Diagramas e esquemas** (árvores, escalas, fluxos, ciclos, tabelas visuais): desenhe você mesmo em **SVG** e salve em `<pasta>-ebook/figuras/`. Vetor é nítido em qualquer zoom e você controla cada rótulo. Use as cores do tema, `font-family` com as fontes embutidas do livro (`"GP Cormorant Garamond"` para títulos, `"GP Inter"` para rótulos, `"GP Source Serif 4"` para texto) e um `viewBox` — o motor dimensiona para caber na página. Represente **só o que o texto afirma**; quando o diagrama pertencer a uma tradição ou disciplina (um modelo teórico, uma estrutura clássica, uma notação técnica), siga a forma canônica e consensual dessa tradição, sem inventar variantes. A legenda descreve o que a figura mostra, sem rótulo de "ilustração editorial" e sem citar a origem (regra 6). Exemplo: `exemplos/neutro/figuras/ciclo.svg`.
- **Imagens do original** (extraídas do DOCX/PDF para `figuras/`) já entram no texto; não as substitua.
- **Arte raster** (fundo de capa): só pelo fluxo do passo 7 — o usuário gera a imagem em outra IA. Esta skill não gera imagens.

## Arquivos da skill

- `scripts/gerar`, `scripts/gerar.cmd` — ponto de entrada (macOS/Linux e Windows); `verificar` roda sem Python
- `scripts/gerar.py` — cria o ambiente (uv ou venv + pip) e chama o motor
- `scripts/conversores.py` — .md/.txt/.docx/.pdf/OCR/.srt/.vtt → `fonte.md`, limpeza declarada, tipo de fonte
- `scripts/motor.py` — análise, diff de redação, composição, verificação de integridade, preview, ocorrências
- `assets/ebook.css` — sistema de design (tokens de tema, grade de página, componentes)
- `assets/fontes/` — fontes livres embutidas (licença SIL OFL: Source Serif 4, Cormorant Garamond, Inter, JetBrains Mono)
- `PLANO.md` — esquema do plano editorial e critérios
- `APRENDIZADOS.md`, `aprendizados/` — memória da skill
- `exemplos/neutro/` — documento de exemplo com plano completo e figura SVG; `exemplos/minimo.plano.json` — plano mínimo
- `scripts/atualizar.py` — `gerar atualizar`: confere a última release no GitHub e atualiza a skill
- `VERSAO` — versão instalada (igual à de `.claude-plugin/plugin.json` no repositório)
- `README.md` — pré-requisitos por sistema (inclusive o Pango no Windows) e limitações conhecidas
