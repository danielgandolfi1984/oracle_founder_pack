# Atualização de segurança — 21 de setembro de 2026

[English](../../SECURITY-UPDATE-2026-09-21.md)

Use o Container API **`0.2.0-preview.4`** ou posterior para os validadores
offline corrigidos. O projeto continua sendo um preview pessoal para sandbox,
não uma auditoria de conta OCI nem uma certificação de produção.

## O que muda para o founder ou dev?

- **Skills de planejamento:** `oci-founder`, `oci-founder-start` e
  `oci-founder-migrate` continuam inalteradas. Instalar uma skill não executa
  o helper afetado nem instala as dependências da fixture de testes.
- **Blueprint Container API:** atualize o checkout/pacote completo revisado,
  incluindo helper e versão, antes de gerar ou revisar novos planos, recibos
  ou auditorias de remoção. Não trate resultados dos validadores antigos como
  comprovação de segurança.
- **Pacotes antigos:** os arquivos completos de `v0.1.0` e `v0.1.1` preservam
  seus bytes e validadores originais, vulneráveis. Não use esses helpers para
  validar infraestrutura. O novo pacote completo tem a identificação
  `container-api-v0.2.0-preview.4` e o nome
  `oci-founder-toolkit-0.1.1-container-api-0.2.0-preview.4.tar.gz`. A versão da
  skill/plugin de planejamento permanece `0.1.1`; não é uma nova versão da skill.
- **Recursos OCI existentes:** atualizar arquivos locais não corrige, altera
  nem apaga recursos na nuvem. Inspecionar uma conta exige escopo autorizado;
  executar correções exige um plano revisado e aprovação separados.

## Problemas corrigidos

| Problema | Impacto e pré-requisito | Correção |
|---|---|---|
| SEC-01, média | Um plano/estado alterado podia incluir rotas extras ignoradas pelo comparador, fazendo uma superfície HTTP inesperada parecer válida | Exigir quantidade exata, caminhos únicos, método GET e contrato completo dos backends; rejeitar entradas inválidas/desconhecidas |
| SEC-02, média | Um plano/estado alterado podia combinar Add=ALL com Drop=ALL e parecer seguro, mesmo restaurando capabilities do container | Rejeitar capabilities adicionadas ou desconhecidas, preservando as representações vazias válidas do provider |
| DEP-01, avisos de dependência | A fixture FastAPI, não implantada, resolvia Starlette 0.47.3, afetado por seis avisos conhecidos; não foi demonstrada exploração nos handlers JSON existentes | Atualizar versões compatíveis, fixar dependências transitivas com hashes de binários revisados e repetir as verificações |

As duas falhas dos validadores foram reproduzidas com planos/estados sintéticos,
sem deploy OCI. Não se demonstrou criação anônima de rotas, escape de container
ou exposição de dados. O comportamento está documentado pela Oracle para
[respostas estáticas do gateway](https://docs.oracle.com/en-us/iaas/Content/APIGateway/Tasks/apigatewayaddingstockresponses.htm)
e [capabilities do container](https://docs.oracle.com/en-us/iaas/Content/container-instances/creating-a-container-instance.htm).

## Verificações contínuas e limites da evidência

A primeira execução do CodeQL também apontou response splitting HTTP e uma
checagem de substring de URL. A revisão confirmou que os IDs de requisição já
tinham uma lista restrita de caracteres ASCII e que a substring rejeitava
exemplos não preenchidos, sem autorizar destinos de rede; nenhuma exploração
foi reproduzida. O pacote final adiciona remoção explícita de CR/LF na escrita
do cabeçalho e identifica placeholders por hostname/domínio de e-mail. Os
testes preservam as restrições reais de HTTPS/repositório e os IDs aceitos.
São proteções adicionais, não duas novas explorações confirmadas.

O workflow de segurança consulta a OSV para os manifests ativos e executa
CodeQL para Python. O Dependabot propõe atualizações, sem merge automático.
Compatibilidade, versões e hashes continuam exigindo revisão. Uma falha de
consulta não deve ser apresentada como ausência de vulnerabilidades.

Os testes de regressão cobrem plano e estado aplicado, defaults válidos do
provider e os bypasses originais. Os testes e scans de privacidade do repo
continuam obrigatórios. Nenhum scan prova ausência de todas as vulnerabilidades.

A fixture agora fixa FastAPI `0.141.1` e Starlette `1.6.0` em um conjunto de
15 pacotes. Passaram a instalação com hashes no macOS arm64, a resolução/download
de wheels Linux x86_64/arm64 e cinco verificações ASGI em processo; nenhum
container Linux foi executado. O [registro do pacote completo final](../../../tests/results/2026-09-21-security-final-full-package-assessment.json)
vincula o hash do arquivo aos novos testes de instalação/remoção/reinstalação
nos layouts Codex, Cursor e Claude Code, não ao comportamento nativo dos modelos.
O [registro do primeiro candidato](../../../tests/results/2026-09-21-security-full-package-assessment.json)
permanece como evidência histórica, anterior às proteções motivadas pelo CodeQL;
seu hash não corresponde ao pacote final publicado.

O [recibo OSV após a correção](../../../tests/results/2026-09-21-security-dependencies.json)
registra 28 versões de pacotes consultadas com sucesso, sem avisos conhecidos
retornados naquele momento. Não cobre camadas de sistema/imagem, binários
Terraform ou dependências ausentes dos manifests ativos.

Checksums de releases, recibos de instalação e respostas históricas dos agentes
permanecem inalterados. O [registro da fixture antiga](../../../tests/results/2026-09-21-fixture-lineage.json)
preserva os hashes originais: atualizar dependências não autoriza reescrever a
evidência de um teste de modelo anterior. Não há nova comparação nativa de
agentes ou teste real em nuvem implícitos nesta correção. Consulte a CI em
[Validate toolkit](https://github.com/danielgandolfi1984/oracle_founder_pack/actions/workflows/validate.yml)
e [Security](https://github.com/danielgandolfi1984/oracle_founder_pack/actions/workflows/security.yml).

Reporte novos problemas pelo [canal privado](../../../SECURITY.md). Nunca
publique credenciais, chaves, dados de clientes ou estado Terraform bruto.
Tokens expostos fora do repositório precisam ser revogados separadamente;
um scan limpo do repo não os revoga.
