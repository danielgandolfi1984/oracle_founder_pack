# Comece aqui: seu primeiro caminho em OCI

Guia curto em português do Brasil, revisão **2026-09-19**, alinhado ao
[guia canônico em inglês](../../GETTING-STARTED.md) desta mesma revisão.
É uma porta de entrada mantida, não uma tradução integral da documentação.
Comandos, limites de execução e procedimentos permanecem nos guias canônicos;
revise este resumo sempre que eles mudarem.

O Founder Toolkit for OCI é um projeto pessoal independente de Daniel Gandolfi,
que trabalha na Oracle e publica em caráter pessoal. Não é um produto Oracle,
não representa a empresa e não oferece suporte Oracle ou SLA.

## Qual resultado você precisa agora?

| Sua situação | Comece por | Resultado esperado |
|---|---|---|
| Estou sozinho e quero entender OCI | [Quickstart](../../QUICKSTART.md) | Uma recomendação para seu backend, premissas, custos a investigar e próximo passo |
| Temos uma equipe pequena | [Baseline](../../FOUNDER-BASELINE.md) | Plano com responsáveis por deploy, acesso, custos e incidentes |
| Já uso AWS, GCP ou Azure | [Casos de uso](../../USE-CASES.md) | Mapeamento de serviços e diferenças que precisam de teste antes da migração |
| Preciso atender o primeiro cliente | [Backend de referência](../../REFERENCE-BACKEND.md) | Checklist de segurança, operação, custo e evidências para decidir se pode avançar |

## Faça na ordem que corresponde à sua necessidade

1. **Instale em um repositório e para um agente.** Siga os comandos do
   [quickstart](../../QUICKSTART.md); não precisa de conta OCI para a primeira
   análise. Não copie credenciais para o chat.
2. **Prepare sua conta quando precisar usá-la.** O guia de
   [acesso local](../../ACCOUNT-SETUP.md) mostra onde encontrar OCIDs, como
   escolher a autenticação e como fazer uma consulta somente leitura.
3. **Aprenda VCN, subnet e VM.** Execute pessoalmente o
   [laboratório de VM Linux](../../FIRST-VM.md), revisando rede, SSH, custo e
   recursos exatos antes de criar ou remover qualquer coisa.
4. **Planeje o produto.** Consulte o [backend de referência](../../REFERENCE-BACKEND.md)
   e os [cenários de custo](../../COST-SCENARIOS.md). Use o guia de
   [evidências](../../EVIDENCE.md) para separar o que foi documentado, testado
   localmente ou realmente executado em OCI.

O skill independente **v0.1.1** fica no planejamento sem suas dependências
operacionais verificadas. Instalar o skill não autentica seu terminal, não
concede IAM e não automatiza o laboratório. O backend de referência é um
projeto de arquitetura, não um produto já implantado e validado em produção.

## Conta, pagamento e região: decisões suas

Se sua empresa já tem OCI, peça ao administrador o acesso e o compartment
corretos. Para uma conta nova, consulte a
[FAQ oficial de cadastro](https://www.oracle.com/cloud/free/faq/): condições,
países, meios de pagamento e capacidade podem variar. Este projeto não garante
créditos, elegibilidade, recursos gratuitos disponíveis ou custo zero.

Cadastro e upgrade pago são decisões separadas. Revise os termos e confirme
pessoalmente qualquer adesão ou alteração financeira; não autorize um upgrade
apenas para contornar um erro. Nunca envie cartão, senha, código MFA ou chave
privada ao agente. Mais detalhes no [guia canônico](../../GETTING-STARTED.md).

Escolha a região considerando clientes, latência medida, serviços necessários,
backup e requisitos de localização dos dados. Não presuma que São Paulo serve
para toda a América Latina, nem que uma região garante conformidade legal.
A [home region não pode ser alterada após o provisionamento](https://docs.oracle.com/en-us/iaas/Content/Identity/Tasks/managingregions.htm);
revise essa decisão antes do cadastro. Confirme a disponibilidade atual e os
requisitos com os responsáveis da sua empresa.

## Travou? Encaminhe pelo problema

- **Cadastro, pagamento, login ou MFA:** use as
  [rotas oficiais de recuperação e chat](https://docs.oracle.com/en-us/iaas/Content/GSG/Tasks/signinginIdentityDomain.htm).
- **Skill não encontrado:** siga o diagnóstico do quickstart; se persistir,
  consulte [suporte do projeto](../../../SUPPORT.md).
- **CLI, região ou IAM:** siga o guia de acesso e fale com o administrador;
  não peça permissão administrativa ampla só para fazer o exemplo funcionar.
- **VM, SSH ou rede:** siga o diagnóstico do laboratório e confira os dados da
  instância; não abra SSH para toda a internet como tentativa de correção.

Problemas do serviço OCI seguem as [opções oficiais de suporte](https://docs.oracle.com/en-us/iaas/Content/GSG/Tasks/contactingsupport.htm)
disponíveis para sua conta. Issues deste projeto têm atendimento comunitário
sem SLA e não substituem o suporte contratado. Remova segredos, dados de
clientes e identificadores privados de qualquer relato público. Para falhas
de segurança, siga [SECURITY.md](../../../SECURITY.md).
