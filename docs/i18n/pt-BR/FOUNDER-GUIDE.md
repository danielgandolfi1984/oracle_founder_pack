# Guia do founder: do seu repositório a uma decisão informada sobre OCI

**Português · revisão 2026-09-21 · [English completo](../../FOUNDER-GUIDE.md).**
Para founders e desenvolvedores backend que usam Codex, Cursor ou Claude Code.
Você pode começar sem conta OCI. O primeiro resultado é um plano revisado,
não um deploy. Daniel Gandolfi mantém este projeto pessoal independente;
ele trabalha na Oracle, mas o projeto não é um produto Oracle nem oferece SLA.

## 1. Instale primeiro o skill publicado

Tenha Git, Node.js **22.20.0 ou posterior**, `npx` e seu agente escolhido
instalados e autenticados. Abra o repositório do backend que receberá o skill.
Execute **um** dos comandos abaixo nele; substitua o diretório de exemplo:

```bash
cd /absolute/path/to/your-backend

# Codex
npx --yes skills@1.7.0 add \
  'https://github.com/danielgandolfi1984/oracle_founder_pack#v0.1.1' \
  --skill oci-founder -a codex --copy -y

# OU Cursor
npx --yes skills@1.7.0 add \
  'https://github.com/danielgandolfi1984/oracle_founder_pack#v0.1.1' \
  --skill oci-founder -a cursor --copy -y

# OU Claude Code
npx --yes skills@1.7.0 add \
  'https://github.com/danielgandolfi1984/oracle_founder_pack#v0.1.1' \
  --skill oci-founder -a claude-code --copy -y
```

Os comandos copiam arquivos para o projeto; não use `-g`. Não instale três
cópias no mesmo backend. Há downloads de pacotes/código, mas nenhuma credencial
OCI é necessária. Fixar o instalador não fixa todas as dependências transitivas.
Esta é a **prévia pública v0.1.1**, não uma instalação de marketplace.

Confirme usando o mesmo agente; substitua `codex` se necessário:

```bash
npx --yes skills@1.7.0 list -a codex --json
```

O resultado deve listar `oci-founder` no projeto. Os destinos testados pelo
instalador são `.agents/skills/oci-founder` para Codex/Cursor e
`.claude/skills/oci-founder` para Claude Code. Os três layouts passaram nos testes;
a evidência nativa é um teste Codex com ressalvas, não qualificação completa de
Cursor/Claude. Veja [instalação detalhada](../../QUICKSTART.md) e [compatibilidade](../../COMPATIBILITY.md).

## 2. Peça seu primeiro resultado útil

| Agente | Inicie o pedido com | Se o skill não aparecer |
|---|---|---|
| Codex CLI/IDE | `Use $oci-founder.` ou selecione por `/skills` | Confira a lista; reinicie se necessário |
| Cursor | `/oci-founder` | Reabra ou recarregue o workspace do backend |
| Claude Code | `/oci-founder` | Abra uma nova sessão se necessário |

Referências dos agentes: [Codex](https://learn.chatgpt.com/docs/build-skills),
[Cursor](https://cursor.com/docs/skills), [Claude Code](https://code.claude.com/docs/en/skills).
Em outra interface, selecione o skill pelo nome no seletor disponível.

```text
Use o skill oci-founder. Inspecione este backend somente para leitura. Conheço
AWS/GCP/Azure, mas sou novo em OCI. Recomende o menor caminho seguro para
[objetivo do produto]. Separe fatos do repositório e premissas; explique termos
novos, fatores de custo, testes pendentes e um próximo passo. Não instale nada,
abra arquivos de credenciais, execute comandos cloud nem altere recursos.
```

Use o prefixo explícito do seu agente acima. Espere uma recomendação, seus
motivos, o que a faria mudar e uma próxima ação. Uma lista de serviços ou um
preço fixo não verificado não substitui análise. Peça `founder-plan.md` quando
quiser um plano completo; uma pergunta pontual não deve exigir esse artefato.

## 3. Entenda o que você instalou

| Componente | Sua função | O que ele não concede |
|---|---|---|
| Skill do founder | Organizar decisões, traduzir conceitos e revisar riscos | Acesso cloud ou autorização para executar |
| `oracle/skills` | Procedimentos reutilizáveis dos serviços Oracle | Disponibilidade automática ou origem verificada na sua máquina |
| CLI/SDK/conector | Executar uma chamada autorizada | Permissões IAM só porque a ferramenta existe |
| Perfil e credencial | Autenticar quem faz a chamada | Acesso a tudo ou autorização para alterar agora |
| Política IAM | Autorizar operações em um escopo | Sua aprovação de uma mudança específica |

Reutilize o upstream, sem reescrever seus manuais de serviço. O uso operacional
exige lock/verificador do toolkit completo e uma cópia instalada do upstream
verificada; sem isso, fique no planejamento. Siga o
[guia de verificação antes da instalação](../../../skills/oci-founder/references/upstream-oracle-skills.md).

As jornadas opcionais disponíveis no código-fonte são `oci-founder-start`, para
projeto novo, e `oci-founder-migrate`, para workload existente. Elas **não estão
na v0.1.1** e não herdam a evidência da release ou dos agentes. Para avaliar uma,
clone `main` em um diretório novo, revise o conteúdo e registre o commit:

```bash
git clone --branch main --single-branch \
  https://github.com/danielgandolfi1984/oracle_founder_pack.git \
  /absolute/path/to/oci-founder-toolkit
git -C /absolute/path/to/oci-founder-toolkit rev-parse HEAD

cd /absolute/path/to/your-backend
npx --yes skills@1.7.0 add /absolute/path/to/oci-founder-toolkit \
  --skill oci-founder-start -a codex --copy -y
```

Escolha `oci-founder-migrate` se essa for sua necessidade; selecione exatamente
um agente (`codex`, `cursor` ou `claude-code`) e não instale globalmente. Confira
o nome escolhido com o comando de listagem. `main` muda: é o commit local
revisado, não o nome da branch, que identifica o código avaliado. Instalar do
código-fonte não autoriza instalar dependências, acessar a conta ou fazer deploy.

O [teste do código público](../../../tests/results/2026-09-21-public-source-assessment.json)
confirmou as três skills no commit `2baedb0` e a instalação conjunta no layout
de um projeto Codex. Remover uma preservou as outras duas. Isso verifica
arquivos e comportamento do instalador, não respostas nativas do agente nem
acesso OCI. Escolha a skill da sua tarefa; não é obrigatório instalar o conjunto.

## 4. Escolha: produto novo ou workload existente

**Começando:** descreva a primeira ação do cliente, dados, usuários, tráfego
esperado, orçamento e recuperação. Preserve banco e provedor de identidade
conhecidos, salvo evidência para mudar. Uma VM ensina infraestrutura; uma API
em contêiner persistente ou um handler de eventos pode indicar outro runtime.
Não comece com Kubernetes apenas porque pretende crescer.

> Use o skill oci-founder-start. Planeje um MVP para [ação do cliente], usando
> [linguagem/banco]. Explique uma escolha de runtime, base mínima, fatores de
> custo e testes de aceitação. Só planejamento; sem credenciais ou mudanças cloud.

**Migrando:** inventarie runtime, extensões do banco, identidade, storage, filas,
tarefas em segundo plano, rede, DNS e observabilidade. Classifique os mapeamentos
como próximos, aproximados ou sem equivalente direto. Compare o mesmo workload
e objetivo de recuperação; inclua coexistência, egress e esforço operacional.

> Use o skill oci-founder-migrate. Avalie este backend em [cloud] somente para
> leitura. Preserve as escolhas de dados e login. Identifique incompatibilidades,
> um experimento com dados sintéticos, critérios de rollback e motivos para não
> migrar ainda. Não copie dados de clientes, altere DNS/tráfego nem faça deploy.

Antes do ensaio, defina indisponibilidade aceitável, tempo de recuperação (RTO),
janela de perda de dados (RPO) e critérios funcionais/de desempenho. Use dados
sintéticos ou sanitizados com aprovação própria; teste restauração e
reconciliação, sem tratar um arquivo de backup como prova de recuperação.

No cutover, identifique operador, sincronização final, fonte autorizada de
escritas, consumidores em segundo plano e condições de parada. Congele ou
sincronize escritas por um método revisado. Preserve a origem pela janela de
recuperação combinada. Reverter DNS não desfaz escritas aceitas na OCI: o plano
de rollback precisa definir reconciliação ou recuperação para frente antes de
mudar o tráfego. Cada execução e a futura retirada da origem exigem aprovação
própria dos alvos exatos.

Se os skills opcionais não estiverem instalados, use `oci-founder` com o mesmo
pedido. Defina critérios de aprovação antes de testar. Não presuma que OCI é
sempre mais barata ou rápida; use o [guia de decisão](../../WHY-OCI.md).

## 5. Prepare sua conta e região de forma consciente

Na empresa, peça ao administrador tenancy, identity domain, compartment do
projeto e permissões delimitadas. Para conta pessoal, conclua você mesmo o
[cadastro oficial](https://www.oracle.com/cloud/free/faq/).
Adesão ou upgrade pago é uma decisão separada; não há promessa de capacidade
gratuita, créditos ou conta zerada. Não envie cartão, senha ou MFA ao chat.

Escolha a região por latência dos usuários, serviços, localização dos dados e
recuperação. Confira a [disponibilidade atual](https://www.oracle.com/cloud/distributed-cloud/service-availability/)
e a capacidade efetiva na conta. A [home region não pode mudar após o provisionamento](https://docs.oracle.com/en-us/iaas/Content/Identity/Tasks/managingregions.htm);
ela não é necessariamente a região da aplicação. Não existe uma única região
ideal para toda a América Latina.

## 6. Encontre os valores no Console sem expô-los

Entre no [Console](https://cloud.oracle.com/) pessoalmente. Os rótulos podem mudar.
Guarde os valores em notas locais privadas fora do Git; use placeholders em
exemplos públicos e compartilhe só o escopo necessário com um executor confiável.

| Valor necessário | Onde procurar | Para quê |
|---|---|---|
| OCID da tenancy | Profile → Tenancy → Tenancy Information → Copy | Confirmar a conta |
| OCID do usuário | Profile → User settings → User Information | Identidade para API signing, se escolher esse método |
| Identificador da região | Seletor superior; confira a lista oficial de regiões | Direcionar recursos regionais |
| OCID do compartment | Identity & Security → Compartments → compartment escolhido | Delimitar operações do projeto |
| OCID do recurso | Detalhes da VM, VCN, subnet ou outro recurso específico | Identificar o objeto exato |

OCID é identificador, não senha nem permissão. Não forneça dump completo de
configuração/credenciais. Fontes: [como localizar IDs](https://docs.oracle.com/en-us/iaas/Content/GSG/Tasks/contactingsupport_topic-Locating_Oracle_Cloud_Infrastructure_IDs.htm),
[usuário e API key](https://docs.oracle.com/en-us/iaas/Content/API/Concepts/apisigningkey.htm).
Use compartment próprio, fora do root, sem reutilizar produção ou a raiz da tenancy.

## 7. Conecte o CLI local e teste acesso somente leitura

Login no Console não autentica o terminal do agente. Confira `oci --version`;
se faltar, siga a [instalação oficial](https://docs.oracle.com/en-us/iaas/Content/API/SDKDocs/cliinstall.htm)
após aprovar essa mudança local. Os exemplos usam Bash/Zsh; no PowerShell,
coloque cada comando OCI em uma linha. Execute-os pessoalmente primeiro.

```bash
oci session authenticate --profile-name FOUNDER
oci session validate --profile FOUNDER --auth security_token

oci network vcn list \
  --compartment-id '<compartment-ocid>' --region '<region-id>' \
  --profile FOUNDER --auth security_token --all
```

Escolha outro nome se o perfil `FOUNDER` existir e use-o em todos os comandos.
Conclua seleção de região, login e MFA; depois valide. Substitua os dois
placeholders antes da listagem. Uma lista vazia pode estar correta; confira o
escopo. Sessão válida comprova autenticação, não permissão de criação. Arquivos
de token e chave ficam locais. Fontes: [sessões CLI](https://docs.oracle.com/en-us/iaas/Content/API/SDKDocs/clitoken.htm),
[`vcn list`](https://docs.oracle.com/en-us/iaas/tools/oci-cli/latest/oci_cli_docs/cmdref/network/vcn/list.html).

Informe ao agente apenas executor, nome do perfil, método de autenticação,
região, compartment necessário e consulta pretendida. Revise permissões do
agente antes de liberar uso de credenciais. Um runner remoto precisa de outra
configuração; não copie uma sessão humana para ele. O [guia de conta](../../ACCOUNT-SETUP.md)
explica API signing como alternativa. Chaves da API OCI, SSH e tokens de usuários
da aplicação são coisas diferentes.

**Alternativa com API signing:** nos detalhes do usuário correto no Console,
abra Tokens and keys → API keys (layout antigo: Resources → API Keys). Registre
somente a chave pública de assinatura; proteja a privada localmente. Use
Configuration File Preview para preparar um perfil local separado com `user`,
`tenancy`, `region`, `fingerprint` e `key_file`; preserve os perfis existentes e
restrinja as permissões dos arquivos. Revise os valores localmente; nunca cole
configuração ou chave no chat/Git. Na consulta somente leitura acima, selecione
esse perfil e `--auth api_key`, não `security_token`.
[Procedimento oficial de API key](https://docs.oracle.com/en-us/iaas/Content/API/Concepts/apisigningkey.htm).

## 8. Planeje a primeira VCN e VM antes de criar qualquer recurso

Use um laboratório descartável executado por uma pessoa, não um ambiente de
clientes. Combine responsável, horário de encerramento, custos atuais e acesso
para criar e limpar. Registre região, compartment, IDs e decisões de manter ou
excluir em um comprovante privado do laboratório. Se rede pública for proibida,
pare e combine acesso privado com o administrador; não contorne a política.

| Elemento do laboratório | Exemplo para revisar, não padrão obrigatório | Confira |
|---|---|---|
| VCN | `founder-lab-vcn`, `10.20.0.0/16` | Sem sobreposição com escritório/VPN/outras redes |
| Subnet pública regional | `lab-public`, `10.20.10.0/24` | Dentro da VCN; route table e security lists corretas |
| Internet gateway e rota | `lab-igw`; `0.0.0.0/0` → gateway | Rota é caminho, não autorização de entrada |
| NSG | `lab-ssh-nsg`; TCP stateful com destino `22` | Origem é seu IPv4 público real com `/32` |
| VM | `lab-vm`; imagem, shape, CPU/RAM e boot volume revisados | Compatibilidade de imagem/CPU, capacidade e custo do disco |

Acesso público depende de IP público, rota, gateway e regras aplicáveis.
Permissões de NSG e security list se somam: NSG restrita não anula SSH amplo.
Inspecione ambos e o firewall do SO; neste lab nunca libere SSH de `0.0.0.0/0`.
[Regras oficiais de rede](https://docs.oracle.com/en-us/iaas/Content/Network/Concepts/securityrules.htm).

## 9. Crie, valide e limpe com aprovações separadas

Use o [laboratório detalhado de VM](../../FIRST-VM.md) junto desta sequência.
Antes de cada alteração em OCI ou IAM, revise alvo/plano exatos e aprove
explicitamente a execução. Permissão IAM não é aprovação para agir agora.

1. Em Networking → Virtual cloud networks, crie manualmente a VCN revisada;
   habilite hostnames DNS do lab. Crie a subnet pública regional e registre IDs.
   [Procedimento de VCN](https://docs.oracle.com/en-us/iaas/Content/Network/Tasks/create_vcn.htm) / [subnet](https://docs.oracle.com/en-us/iaas/Content/Network/Tasks/create_subnet.htm).
2. Crie/habilite o internet gateway e ajuste a route table da subnet para ele.
   Crie a NSG de SSH, restrinja regras SSH mais amplas nas security lists deste
   lab e preserve deliberadamente as demais regras necessárias.
3. Em Compute → Instances, revise imagem/shape, VCN/subnet existentes, IPv4
   público, associação da NSG e boot volume. Salve a nova chave SSH privada
   com segurança antes de continuar ou forneça apenas uma chave pública aprovada.
   Aprove a criação revisada e registre IDs da VM/VNIC/disco quando estiver Running.
4. Conecte com `ssh -i /absolute/private/key opc@PUBLIC_IP` para Oracle Linux,
   ou `ubuntu@PUBLIC_IP` para Ubuntu. Restrinja permissões locais da chave e
   confira o fingerprint do servidor por canal confiável. Inspecione `uname -m`
   e `cat /etc/os-release`, depois `exit`. [Instruções oficiais de SSH](https://docs.oracle.com/en-us/iaas/Content/Compute/Tasks/connect-to-linux-instance.htm).
5. Registre sucesso/falha, escopo real, telemetria e verificações pendentes.
   SSH funcionando não prova aplicação segura, disponível ou pronta para produção.
6. Antes de excluir, revise comprovante/state e lista exata de manter/excluir;
   aprove ações destrutivas separadamente. Termine a VM escolhendo explicitamente
   a retenção dos discos, depois remova só rede/dependências exclusivas do lab.
   Pare se houver recursos inesperados. [Comportamento de Terminate](https://docs.oracle.com/en-us/iaas/Content/Compute/Tasks/terminatinginstance.htm).

Confirme cada recurso removido ou retido e reveja a cobrança quando o consumo
aparecer. **Stop não é limpeza**: storage e cobranças dependentes do shape podem
continuar. [Cobrança de instâncias paradas](https://docs.oracle.com/en-us/iaas/Content/Compute/Tasks/resource-billing-stopped-instances.htm).
Nunca apague um compartment inteiro para corrigir falha na limpeza.

## 10. Mantenha segurança e custos visíveis

Use privilégio mínimo, responsáveis definidos, separação de desenvolvimento e
produção, state/comprovantes privados. Não exponha chaves, tokens, dados de
clientes ou Terraform state em prompts/issues. Diagnóstico é somente leitura;
aplicar uma correção exige aprovação própria. Plano gerado não autoriza `terraform apply`.

Calcule runtime, banco, storage, rede, logs, backup, entrega, suporte e trabalho
operacional na mesma moeda/período. Registre região, quantidades, preços datados
e validade. Os [cenários de custo](../../COST-SCENARIOS.md) são **premissas sem cotação**,
não faturas ou capacidade comprovada. Desconhecido não é zero. [Budgets alertam,
mas não bloqueiam gastos](https://docs.oracle.com/en-us/iaas/Content/Billing/Concepts/budgetsoverview.htm);
revise quotas suportadas e limites de arquitetura separadamente com o responsável.

## 11. Um glossário curto para ler seu plano

| Termo | Significado nesta jornada |
|---|---|
| Tenancy / compartment | Limite da conta / escopo lógico do projeto; não substituem controles de rede |
| OCID / IAM | Identificador exato do recurso / regras de autorização delimitadas |
| Region / AD / FD | Região geográfica / availability domain / fault domain dentro de uma AD |
| VCN / subnet / CIDR | Rede cloud / faixa contida de endereços / notação da faixa |
| VNIC / NSG / security list | Interface de rede / regras para interfaces selecionadas / regras associadas à subnet |
| Image / shape / boot volume | Base do sistema operacional / alocação computacional / disco persistente do SO |
| OCPU | Unidade de CPU OCI; normalize pelo processador escolhido antes de comparar vCPUs |
| Profile / session / SSH key | Seleção de identidade local / credencial temporária da API / credencial de login na VM |
| Budget / quota | Alerta de custo / restrição de alocação suportada, não teto monetário |
| Rollback / restore / teardown | Reverter mudança / recuperar dados / remover recursos exatos aprovados |

Conceitos entre clouds são aproximados, não serviços equivalentes. Consulte o
[glossário completo](../../GLOSSARY.md) e peça ao skill para explicar um termo do plano.

## 12. Escolha um exemplo sem exagerar a evidência

- O skill publicado planeja/encaminha; instalá-lo não instala blueprints completos.
- A [prévia Container API](../../../blueprints/container-api/README.md) é um sandbox
  separado, com uma instância e endpoints de teste anônimos, não um SaaS completo.
- O [backend local](../../../examples/local-backend/README.md) testa regras sintéticas;
  HTTP assinado opcional fica no loopback. Não é hospedagem pública.
- O [preflight de identidade](../../../examples/local-backend/IDENTITY-INTEGRATION.md)
  verifica configuração existente offline. `--diagnostics` adiciona rótulos seguros,
  não login real, conexão ao provedor, validação de token real ou refresh automático.
- O [backend de referência](../../REFERENCE-BACKEND.md) continua sendo o projeto maior.
  Testes locais verdes não são validação em OCI nem aprovação de produção.

## 13. Busque ajuda e saia com um próximo passo

### Atualize ou remova uma cópia do projeto

Antes de atualizar, revise a nova tag/commit e eventuais edições locais da skill.
Remova a cópia antiga do projeto e instale a versão revisada conforme a seção 1
ou 3. Não adicione uma duplicata global. No mesmo diretório do backend:

```bash
npx --yes skills@1.7.0 remove oci-founder -y
npx --yes skills@1.7.0 list -a codex --json
```

Para uma complementar, substitua `oci-founder` pelo nome exato; escolha seu
agente no comando de listagem. A remoção testada omite `-a`: em `skills@1.7.0`,
filtrar a remoção por agente pode deixar a cópia compartilhada em `.agents`.
Revise primeiro o escopo do projeto; outros agentes que usam essa cópia serão
afetados. Confirme a ausência da skill escolhida. Remover uma skill **não** exclui
recursos OCI. Confira o [ciclo testado](../../QUICKSTART.md) antes de mudar o escopo.

### Resolva dúvidas e peça ajuda

Skill ausente? Confira projeto, agente escolhido, listagem e reinício da sessão.
Em erro de CLI, confira perfil, expiração, região e compartment naquele executor;
peça ao administrador as operações IAM exatas, nunca acesso administrativo amplo.
Em SSH, separe conectividade de erro de chave/usuário; não amplie o acesso de rede.

Para problemas do toolkit, siga [SUPPORT.md](../../../SUPPORT.md) informando versão,
agente, SO, reprodução e saída sanitizada. Vulnerabilidades seguem [SECURITY.md](../../../SECURITY.md).
Incidentes de conta, cobrança ou serviço seguem seu suporte oficial OCI;
issues do projeto não concedem acesso, capacidade ou compromisso de suporte Oracle.

Antes do próximo passo, declare: **meu alvo; minha evidência; o que falta saber;
custo/responsável; aprovação necessária; e como reverter ou encerrar o experimento.**
Confira [EVIDENCE.md](../../EVIDENCE.md): revisão de fontes, teste local, sandbox real
e produção são evidências diferentes. Esta jornada de usuário é mantida em EN/PT;
nem todos os registros de engenharia ou aprofundamentos ligados estão traduzidos.
