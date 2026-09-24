# Plano editorial (`plano.json`)

O plano é onde mora todo o julgamento editorial. O motor não inventa nada: ele lê o plano, localiza cada âncora no texto, compõe e verifica.

## Esqueleto

```json
{
  "modo": "limpeza",
  "meta": { ... },
  "tema": { ... },
  "cortes": [ ... ],
  "correcoes": [ ... ],
  "estrutura": { "partes": [ ... ], "capitulos": [ ... ] },
  "caixas": [ ... ],
  "destaques": [ ... ],
  "glossario": [ ... ],
  "figuras": [ ... ],
  "refluxo": { ... },
  "tipografia": true,
  "muletas": true,
  "css_extra": ""
}
```

Só `meta.titulo` é realmente necessário. Plano mínimo para um Markdown bem estruturado: `exemplos/minimo.plano.json`. Plano completo: `exemplos/neutro/`.

O plano mora em `<nome>-ebook/plano.json`, ao lado de `fonte.md` (criado por `gerar converter`). Todos os literais — âncoras, cortes, correções — são copiados de **`fonte.md`** (ou de `texto-editado.md`, no modo `redacao`), nunca do arquivo original em DOCX/PDF.

## `modo`

O tratamento do texto escolhido no questionário (`respostas.json`). O motor recusa um plano incoerente com ele.

| `modo` | permite | fonte do build |
|---|---|---|
| `integra` | nem `cortes` nem `correcoes` | `fonte.md` |
| `lingua` | só `correcoes` | `fonte.md` |
| `limpeza` | `cortes` e `correcoes`; retira sozinho os vícios de linguagem inequívocos (`"muletas": false` desliga) | `fonte.md` |
| `redacao` | nem `cortes` nem `correcoes` (a revisão já está no texto) | `texto-editado.md`, com `diff-redacao.md` gerado depois da última edição |

Sem `modo`, nada é travado (compatibilidade); sempre declare-o.

`muletas` (só no modo `limpeza`, ligado por padrão): retira "…, né?", "Tá?", "né" solto, hesitações e afins, depois dos cortes e das correções, registrando cada ocorrência em `correcoes.md` (critérios em SKILL.md, "Vícios de linguagem"). As correções do plano citam o texto **com** as muletas, como está no `fonte.md`; as âncoras também, porque o motor aplica a elas a mesma limpeza.

## Âncoras — a regra central

Uma **âncora** é um trecho **literal** do `.md` que marca um ponto do texto. É como capítulos, caixas, destaques, glossário e figuras se prendem ao conteúdo sem alterá-lo.

- Copie exatamente como está no arquivo, com a mesma pontuação e acentos. Quebras de linha do arquivo viram um espaço — junte as linhas.
- Precisa estar **dentro de um único parágrafo** e aparecer **uma única vez** no documento. A análise lista frases repetidas; evite-as ou estenda o trecho.
- Não inclua marcação (`**`, `` ` ``, `[`…`](…)`) e não corte no meio dela.
- Se a âncora está no meio de um parágrafo, o motor quebra o parágrafo ali. Isso é só re-fluxo: nenhum caractere muda.
- Prefira começos de frase, 6–15 palavras, que marquem de fato a virada do assunto.
- Respeite maiúsculas e minúsculas exatamente como estão no arquivo.
- Duas âncoras podem começar no mesmo ponto (capítulo e caixa, capítulo e glossário) e uma pode começar dentro de outra — o motor atribui cada uma pela posição. Ainda assim, para uma caixa que abre junto com o capítulo, prefira repetir a âncora inteira do capítulo.

## `meta`

| campo | uso |
|---|---|
| `titulo` | nome do livro (capa, meia-folha, cabeçalhos, nome do PDF) |
| `subtitulo` | linha sob o título na capa |
| `titulo_capa` | título com quebras manuais: `"Pequenos\nHábitos"` |
| `chapeu` | linha pequena acima do título na capa (“Coleção Viver Melhor · Volume 1”) |
| `chapeu_rosto` | linha acima do título no rosto (padrão: `chapeu`) |
| `descricao_capa` | frase em itálico na capa |
| `rodape_capa` | linha no pé da capa (local, editora, ano) |
| `creditos` | linhas do rosto; `"Rótulo\|Nome"` vira rótulo itálico + nome em negrito. Só pessoas (autor, organizador, tradutor); nunca o nome da skill |
| `autores`, `descricao`, `palavras_chave` | metadados do PDF |
| `titulo_pdf` | título nos metadados (padrão: `titulo — subtitulo`) |
| `idioma` | `pt-BR` (padrão) — controla a hifenização |
| `epigrafe` | `{"texto": "...", "autor": "..."}` — **use uma frase literal do texto**; aspas são postas pelo motor |
| `colofao` | lista `[{"rotulo": "...", "texto": "..."}]` (aceita Markdown inline). Sem ele, o colofão mostra só a obra (título e subtítulo). Origem do texto, cortes, correções e integridade não entram no livro: ficam em `relatorio.md` |
| `fim` | página final escura: `{"titulo": "...", "subtitulo": "..."}` |
| `capa_imagem` | PNG/JPG (relativo ao plano, ex.: `figuras/capa.png`) usado como fundo da capa, sob um véu escuro — vem do fluxo `prompt-capa.txt` (SKILL.md, passo 7) |

Se o `.md` começa com `# Título`, esse título é mostrado no rosto como texto da fonte (`"estrutura": {"consumir_titulo": false}` desliga).

## `tema`

```json
"tema": { "preset": "noite-ouro", "selo": "hexagrama", "formato": "152x229",
          "capitular": true, "cores": {}, "fontes": {} }
```

| preset | quando usar |
|---|---|
| `noite-ouro` | espiritualidade, esoterismo, filosofia, luxo |
| `grafite-cobre` | tecnologia, negócios, relatórios executivos |
| `floresta-latao` | saúde, natureza, bem-estar, educação |
| `bordo-creme` | literatura, história, direito, humanidades |
| `oceano-prata` | ciência, dados, engenharia, software |

- `selo`: `hexagrama`, `losango`, `estrela`, `circulo`, `nenhum`.
- `formato`: `152x229` (padrão, proporção de livro, lê bem em tablet), `a5`, `b5`, `a4`, `quadrado` ou `LxA` em mm.
- `cores`: sobrescreve tokens — `escuro`, `escuro2`, `acento`, `acento_claro`, `acento_lavado`, `papel`, `claro`, `texto_caixa`.
- `fontes`: `serif`, `display`, `sans`, `mono` (pilhas CSS). Padrão: fontes livres embutidas na skill, idênticas em qualquer sistema — `"GP Source Serif 4"` (texto), `"GP Cormorant Garamond"` (títulos), `"GP Inter"` (rótulos), `"GP JetBrains Mono"` (código). Elas cobrem o alfabeto latino (português, inglês, espanhol, francês…); para hebraico, grego ou cirílico, acrescente à pilha uma fonte instalada que os cubra. Nas figuras SVG, use os mesmos nomes.

## `estrutura`

### Modo títulos (Markdown estruturado)

Omita `capitulos`: cada título do menor nível presente (depois do título do livro) vira capítulo, e os níveis abaixo viram intertítulos. Conteúdo antes do primeiro título vira o capítulo `titulo_preambulo` (padrão “Abertura”).

### Modo âncoras (texto corrido) ou controle fino

```json
"estrutura": {
  "partes": [
    { "id": "I", "titulo": "O Começo", "resumo": "Frase curta para a página de abertura da parte." }
  ],
  "capitulos": [
    { "parte": 0, "titulo": "Por que hábitos importam", "ancora": null },
    { "parte": 0, "titulo": "O ciclo do hábito", "ancora": "Todo hábito começa com uma deixa" },
    { "titulo_fonte": "MEMÓRIA DA AULA", "apendice": true }
  ]
}
```

- O **primeiro** capítulo tem `"ancora": null` (começa no início do texto).
- `ancora` + `titulo`: capítulo começa naquele trecho, com título de navegação **editorial** (curto, fiel ao assunto, sem prometer o que o trecho não diz).
- `titulo_fonte`: capítulo começa num título que já existe no `.md` (texto exato); o próprio título da fonte é usado.
- `parte`: índice na lista `partes`. Sem `partes`, não há páginas de parte.
- `apendice: true`: vai para o grupo “Apêndice” no sumário, com página própria.
- Capítulos precisam estar na ordem do texto. O que fica entre duas âncoras pertence ao capítulo — nada sobra, nada falta.

## `cortes`

Trechos do `.md` que **não entram no livro**: apresentações, logística, problemas técnicos, conversas paralelas, agradecimentos, despedidas, cabeçalhos técnicos e duplicações da transcrição (critérios em SKILL.md, "O que cortar"). O motor remove em memória antes de tudo; o arquivo não é tocado.

```json
"cortes": [
  { "trecho": "# TEXTO CORRIGIDO DO BLOCO", "motivo": "cabeçalho técnico" },
  { "inicio": "Pronto, bem-vindos oficialmente.", "fim": "A gente vai continuar, claro, a discussão", "motivo": "apresentação" },
  { "trecho": "Carlos, eu vi que você levantou a mão. Usa o chat, tá?", "motivo": "conversas paralelas" },
  { "inicio": "Bom, então, tudo isso pra falar que na prática", "ocorrencia": 2,
    "fim": "Enfim, vamos pensar ou compartilhar", "motivo": "duplicação da transcrição" },
  { "inicio": "Já te ouço, tá, Ana?", "ate_fim_do_paragrafo": true, "motivo": "agradecimentos e despedida" }
]
```

- `trecho` (ou `inicio` sozinho): remove exatamente esse literal e o espaço que o segue.
- `inicio` + `fim`: remove do início até **antes** de `fim` (exclusivo, como nas caixas). `fim` é procurado depois do início.
- `ate_fim_do_paragrafo: true`: do início até o fim do parágrafo.
- `ocorrencia`: qual aparição do `inicio` usar (1, 2…) quando ele se repete — essencial para duplicações.
- Literais como nas âncoras, mas as quebras de linha do arquivo casam com qualquer espaço e marcação é permitida (útil para cabeçalhos).
- O `fonte.md` convertido de `.txt`, `.docx`, `.pdf`, `.srt` ou `.vtt` escapa os caracteres que o Markdown leria como marcação: `[música]` fica `\[música\]`. Cortes e correções usam o literal **como está no arquivo**; no JSON, a barra é dobrada: `{ "trecho": "\\[música\\]" }`. O mesmo vale para `correcoes.de`.
- `motivo`: categoria curta e repetível. Transcrição: "apresentação", "logística", "problemas técnicos", "conversas paralelas", "agradecimentos e despedida", "duplicação da transcrição". Documento/livro: "sumário manual", "marcas de revisão", "duplicação", "aviso de página", "material do original" (capa, créditos ou sumário de um PDF já diagramado), "cabeçalho técnico". As categorias aparecem na nota editorial do `relatorio.md` (fora do livro).
- Cortes não podem se sobrepor. Todas as outras âncoras (capítulos, caixas, destaques, glossário, figuras) são procuradas **no texto já cortado** — um trecho que só existia na parte cortada deixa de ser único/encontrável.
- O build grava `cortes.md` na pasta de trabalho com o texto literal de cada corte e informa `[cortes] N trechos · P palavras`.

## `correcoes`

Pequenas correções de língua (ortografia, gramática, termos mal transcritos, falsos começos, resíduos de limpeza) aplicadas **em memória, depois dos cortes**; o arquivo não é tocado. Critérios em SKILL.md, "O que corrigir".

```json
"correcoes": [
  { "de": "Cá numa coisa que a gente discutiu na aula passada, que a gente não discutiu na aula passada, você",
    "para": "Coisa que a gente não discutiu na aula passada: você", "motivo": "falso começo" },
  { "de": "efeito com posto", "para": "efeito composto", "todas": true, "motivo": "termo mal transcrito" },
  { "de": ", ?", "para": ", né?", "todas": true, "motivo": "resíduo de transcrição" },
  { "de": "Beleza.", "para": "Beleza?", "ocorrencia": 2, "motivo": "pontuação" }
]
```

- `de`: literal do texto **já cortado** (mesmas regras dos cortes: quebras de linha casam com qualquer espaço), com maiúsculas e minúsculas exatas. Precisa ser único, ou use `ocorrencia` (qual aparição) ou `"todas": true` (todas as aparições).
- `para`: o texto corrigido. Pode ser `""` para eliminar um resíduo (ex.: palavra duplicada).
- Use o **menor trecho** que resolva, mas com contexto suficiente para ser único e não pegar ocorrências certas por engano (prefira `"efeito com posto"` a `"com posto"`).
- Travas do motor: `de` com no máximo 40 palavras; `para` com no máximo 3 palavras que não estão em `de` (ou 25% das palavras de `para`, o que for maior). Acima disso é paráfrase e o build falha.
- Correções não podem se sobrepor entre si. Âncoras (capítulos, caixas, destaques, glossário, figuras) e a epígrafe são procuradas no texto **já corrigido** — escreva-as com a grafia corrigida.
- `motivo`: categoria curta ("ortografia", "gramática", "pontuação", "termo mal transcrito", "erro de OCR", "falso começo", "resíduo de transcrição").
- O build grava `correcoes.md` (original e correção lado a lado) e informa `[correções] N declaradas · M aplicações`.

## `caixas`

Um trecho **contíguo** do texto vira um componente visual.

```json
{ "inicio": "Repita comigo: eu escolho começar pequeno",
  "fim": "Pessoal, esse foi o primeiro passo.",
  "tipo": "ritual", "rotulo": "Primeiro passo · O compromisso" }
```

- `fim` é **exclusivo** (o trecho de `fim` fica fora). Sem `fim`, vai até o fim do capítulo; se `fim` cair em outro capítulo, a caixa termina no fim do atual. Para a caixa acabar junto com o capítulo, basta omitir `fim`.
- Diálogos e exemplos quebram entre páginas; os demais tipos ficam inteiros numa página.
- Tipos: `ritual` (fórmulas, orações, juramentos, citações longas faladas), `dialogo` (perguntas da plateia, entrevistas, trocas), `nota`, `alerta` (riscos, avisos), `exemplo` (casos, exercícios), `termos` (listas de vocabulário).
- Caixas não se sobrepõem. O rótulo é editorial — descreva, não interprete.

## `destaques`

Lista de âncoras; o parágrafo que começa em cada uma ganha tratamento de citação em destaque. O destaque começa na âncora (se ela cai no meio de um parágrafo, o motor quebra ali) e vai até o fim desse parágrafo: a próxima quebra do `.md`, a próxima quebra criada pelo re-fluxo ou a próxima âncora de qualquer tipo, o que vier primeiro. Não há `fim`; confira no HTML se o parágrafo destacado não ficou longo demais. Critério: a ideia central de um capítulo, uma frase-tese, algo que o leitor vai querer reencontrar. Poucos — o destaque perde força quando é comum.

## `glossario`

```json
{ "antes": "Agora vamos falar de neuroplasticidade na prática",
  "termo": "Neuroplasticidade",
  "texto": "Capacidade do cérebro de *reorganizar* conexões com a experiência. …" }
```

Nota editorial inserida **antes** do parágrafo da âncora. Aceita Markdown inline. Só para termos centrais que o texto usa sem definir; use conhecimento sólido e consensual, sem opinião.

## `figuras`

```json
{ "antes": "Olha só como as quatro etapas se encadeiam.",
  "svg": "figuras/ciclo.svg",
  "legenda": "O ciclo do hábito: deixa, desejo, resposta e recompensa …",
  "largura_mm": 95, "altura_max_mm": 105 }
```

- `svg` ou `imagem` (PNG/JPG), com caminho relativo ao `plano.json`.
- O motor dimensiona respeitando a proporção do `viewBox`: largura alvo `largura_mm`, limitada por `altura_max_mm`. Numa abertura de capítulo, ~100 mm de altura cabem com o cabeçalho.
- Legenda com Markdown inline: descreve o que a figura mostra, sem citar a origem ("como a aula descreve", "segundo o texto"). `rotulo` é opcional (padrão: nenhum) e aparece em versalete acima da legenda.

## `refluxo`

```json
"refluxo": { "limite": 1000, "alvo": 560, "maximo": 900 }
```

Parágrafos acima de `limite` caracteres são divididos em fim de frase: um parágrafo fecha quando passa de `alvo` e (passou de `maximo` ou já tem 3 frases). Nunca corta antes de minúscula, depois de abreviação, nem dentro de marcação ou aspas.

## `tipografia`

`true` (padrão): aspas curvas, `---` → —, `--` → –, `...` → …. É acabamento tipográfico, verificado pela integridade.

## `css_extra`

CSS acrescentado ao final — ajuste fino por livro, sem mexer na skill. Classes úteis: `.capa`, `.rosto`, `.colofao`, `.epigrafe`, `.sumario`, `.parte`, `.cap`, `.cap-abre`, `.caixa-<tipo>`, `.destaque`, `.termo`, `.fig-editorial`, `.md-tabela`, `.md-codigo`, `.md-lista`, `.md-citacao`, `.alerta`.
