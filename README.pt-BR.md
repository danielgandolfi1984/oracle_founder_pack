# Founder Toolkit for OCI

[English](README.md) · [Guia completo em português](docs/i18n/pt-BR/FOUNDER-GUIDE.md)

Planeje seu backend na Oracle Cloud Infrastructure (OCI) com o agente de
desenvolvimento que você já usa: Codex, Cursor ou Claude Code.

Este kit é para founders técnicos e devs que conhecem backend, mas ainda não
conhecem os conceitos e os caminhos da OCI. Ele ajuda a começar um projeto ou
avaliar uma migração sem pressupor que você vai mudar de linguagem, framework
ou banco de dados.

## Escolha a skill

| Quero… | Skill | Resultado esperado |
|---|---|---|
| Entender OCI e avaliar meu backend | [`oci-founder`](skills/oci-founder/SKILL.md) | Tradução de conceitos, avaliação do repositório e próximo passo |
| Começar um projeto | [`oci-founder-start`](skills/oci-founder-start/SKILL.md) | Arquitetura mínima, preparação da conta, rede/VM e primeira validação |
| Migrar um backend existente | [`oci-founder-migrate`](skills/oci-founder-migrate/SKILL.md) | O que preservar ou adaptar, ensaio com dados, custos, cutover e retorno |

As skills começam em **somente leitura e planejamento**. Elas não são
credenciais, não concedem permissões IAM e não autorizam a criação de recursos.
Podem responder em português; suas instruções canônicas são em inglês.

## Instale e faça a primeira pergunta

Pré-requisitos: Git, Node.js `>=22.20.0` com `npx` e o agente escolhido já
instalado e autenticado. Não é necessário ter conta OCI para avaliar um backend.

No repositório do seu projeto, instale a skill principal publicada:

```bash
cd /caminho/absoluto/do/seu-backend
npx --yes skills@1.7.0 add \
  'https://github.com/danielgandolfi1984/oracle_founder_pack#v0.1.1' \
  --skill oci-founder -a codex --copy -y
npx --yes skills@1.7.0 list -a codex --json
```

Troque `codex` por `cursor` ou `claude-code` para o agente escolhido. No Codex:

> Use $oci-founder. Avalie este backend somente em leitura. Conheço AWS, mas
> não OCI. Recomende o menor caminho seguro e uma próxima validação. Não crie
> recursos nem altere arquivos. Responda em português.

No Cursor e no Claude Code, use `/oci-founder` no início do pedido.

As duas skills complementares são previews `0.1.0` no código-fonte de `main`;
não estão nos arquivos da release `v0.1.1`. O
[guia completo](docs/i18n/pt-BR/FOUNDER-GUIDE.md) mostra a instalação a partir
de um checkout revisado, os exemplos de uso, a atualização e a remoção.

## Do agente à sua primeira VM

O [guia em português](docs/i18n/pt-BR/FOUNDER-GUIDE.md) contém:

1. Instalação e exemplos de pedidos para projeto novo e migração.
2. Onde encontrar tenancy, compartment, região e identificadores no Console.
3. Autenticação local, diferença entre chaves e primeira consulta somente leitura.
4. Rede VCN, subnet, acesso SSH restrito, VM Linux, validação e limpeza.
5. Custos, segurança, glossário, exemplos locais e reuso de `oracle/skills`.

Há um [guia equivalente em inglês](docs/FOUNDER-GUIDE.md). Documentos técnicos
de referência e manutenção podem estar somente em inglês; o guia bilíngue cobre
a jornada do usuário sem exigir leitura desses documentos para começar.

## Limites e segurança

[Atualização de segurança — 21/09/2026](docs/i18n/pt-BR/SECURITY-UPDATE-2026-09-21.md):
use o Container API `0.2.0-preview.4`, com os validadores corrigidos. Não use os
pacotes completos antigos `v0.1.0`/`v0.1.1` para validar infraestrutura. As três
skills de planejamento e os comandos de instalação continuam inalterados.

Preview público independente, não qualificado para produção. A evidência de
instalação não prova comportamento nativo em todos os agentes. Os laboratórios
locais usam dados sintéticos; não comprovam deploy, login real ou custos em OCI.
O laboratório de VM depende da sua conta, permissões e aprovação de mudanças.

Nunca cole chaves, tokens, senhas, dados de clientes ou conteúdo interno no chat,
Git ou issues. Budget gera alertas: não é um bloqueio automático de gastos.
Confira [evidências](docs/EVIDENCE.md), [ajuda](SUPPORT.md) e o
[canal privado de segurança](SECURITY.md).

Projeto pessoal de [Daniel Gandolfi](https://github.com/danielgandolfi1984), que
trabalha na Oracle e publica em caráter pessoal. Não é produto oficial nem é
patrocinado, mantido ou suportado pela Oracle. Código e conteúdo público original
sob [UPL-1.0](LICENSE); apresentações com o template interno Oracle ficam fora
da distribuição pública e dessa licença.
