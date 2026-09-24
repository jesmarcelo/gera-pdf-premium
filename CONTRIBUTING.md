# Como contribuir

Obrigado pelo interesse em melhorar a gera-pdf-premium! Toda ajuda é bem-vinda, de um relato de erro a uma correção no código.

## Encontrou um problema?

Abra uma [issue](https://github.com/jesmarcelo/gera-pdf-premium/issues/new/choose) usando o modelo **Relatar um problema**. O que mais ajuda:

- o sistema operacional (macOS, Windows ou Linux);
- a saída do comando de verificação:
  - macOS/Linux: `<pasta-da-skill>/scripts/gerar verificar`
  - Windows: `<pasta-da-skill>\scripts\gerar.cmd verificar`
- o tipo de arquivo de entrada (`.docx`, PDF escaneado etc.) e o modo escolhido;
- a mensagem de erro completa.

**Não anexe documentos confidenciais.** Se o problema só acontece com um arquivo específico, tente reproduzi-lo com um trecho curto e sem dados sensíveis.

## Tem uma ideia?

Abra uma issue com o modelo **Sugerir uma melhoria** e conte qual problema ela resolve.

## Quer mandar código?

1. Faça um fork e crie um branch a partir do `main`.
2. Faça a mudança dentro de `skills/gera-pdf-premium/`.
3. Teste com o exemplo que acompanha a skill, **numa cópia temporária dentro do repositório** (nunca componha dentro da pasta da skill, nem use `/tmp`):

   ```bash
   cp -R "skills/gera-pdf-premium/exemplos/neutro" teste-neutro
   skills/gera-pdf-premium/scripts/gerar converter "teste-neutro/Pequenos Hábitos.md"
   skills/gera-pdf-premium/scripts/gerar build "teste-neutro/Pequenos Hábitos-ebook/fonte.md" --saida teste-neutro/neutro.pdf
   rm -rf teste-neutro && skills/gera-pdf-premium/scripts/gerar limpar
   ```

   A saída precisa mostrar `[integridade] OK`.
4. Se mudou o `plugin.json` ou o `marketplace.json`, valide com `claude plugin validate . --strict`.
   Ao lançar uma versão nova, o número precisa ser o mesmo em três lugares: `.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json` e `skills/gera-pdf-premium/VERSAO`. É o `VERSAO` que o comando `update` compara com a última release do GitHub.
5. Registre a mudança no [CHANGELOG.md](CHANGELOG.md), na seção da próxima versão.
6. Abra o pull request explicando o que mudou e por quê.

## Regras que não mudam

A skill existe para respeitar o texto do autor. Por isso, contribuições **não podem**:

- alterar ou sobrescrever o arquivo original;
- enfraquecer a verificação de integridade ou as travas contra paráfrase;
- permitir que o texto mude além do modo escolhido pelo usuário.

## Antes de publicar uma contribuição

A skill aprende com o uso e grava anotações em `APRENDIZADOS.md` e em `aprendizados/ocorrencias.jsonl`. Se você usou a skill a partir do seu fork, confira esses arquivos antes do commit para não publicar preferências pessoais ou nomes de documentos.
