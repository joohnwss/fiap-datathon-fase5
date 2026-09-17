# Status do projeto

Atualização: 17/09/2026. Integrantes: Victor, Jonatas, Izadora, Laura e Lucas.

## Objetivo e marco atual

O Tech Challenge Fase 5 analisa o desenvolvimento educacional dos alunos da
Associação Passos Mágicos entre 2022 e 2024, responde às 11 perguntas de negócio
e prevê a entrada em defasagem para apoiar a avaliação pedagógica.

A etapa de auditoria, preparação, rastreabilidade e saneamento está concluída,
com preservação dos valores originais e sinalização das inconsistências, sem
correções por suposição. O primeiro marco versionado da preparação é `5e00ebb`
(`chore: consolida auditoria e preparação dos dados`).

Resultados confirmados nesse marco: **3.030 registros anuais**, **142.592 células
conferidas**, **28/28 referências reproduzidas**, **24 testes aprovados** e
**13 fontes intactas**. Registros anuais não correspondem a alunos únicos.
A evidência da execução mais recente, incluindo a quantidade atual de testes,
está em [verificação final](../reports/verificacao_final.md).

O [contrato metodológico](contrato_metodologico.md) está aprovado. A modelagem
ainda não foi iniciada e nenhum modelo foi treinado até este marco.

## Metodologia aprovada

O objetivo será prever entrada em defasagem em t+1 entre alunos sem defasagem
em t, com fase de origem de 0 a 7. O desenvolvimento utilizará 2022→2023
(189 observações e 60 eventos); o teste temporal reservado utilizará 2023→2024
(311 observações e 84 eventos). Ausência de desfecho futuro permanecerá
desconhecida. RA servirá somente à correspondência e à auditoria local.

A regressão logística regularizada será o modelo principal interpretável,
comparada a uma referência de prevalência e a modelos de árvores com
complexidade limitada. Validação interna, transformações, seleção e limiar
serão definidos exclusivamente no desenvolvimento. Average Precision será a
métrica principal; o limiar buscará aproximadamente 80% de recall. O contrato
detalha variáveis, ausências, incerteza, equidade e análises das 11 perguntas.

## Obtenção privada dos materiais

Os arquivos de `DATATHON/` não acompanham o repositório. Cada integrante deverá
obter acesso pelo ambiente restrito da disciplina ou pelo canal privado do
grupo com um integrante que já possua os originais autorizados. O enunciado
disponibiliza a referência à base e ao dicionário. Não incluir links privados,
credenciais ou cópias individuais em issues, relatórios ou documentação pública.

Disponibilizar os 13 arquivos originais em `DATATHON/`, na raiz do projeto,
preservando nomes e subpastas conforme o [inventário](inventario_fontes.md).
Conferir os hashes SHA-256 antes da reprodução. A base analítica utiliza apenas
`DATATHON/BASE DE DADOS PEDE 2024 - DATATHON.xlsx`; materiais históricos são
inventariados, sem incorporação à base principal. Divergências de arquivos ou
hashes devem ser esclarecidas com o grupo, sem modificar os originais.

## Ambiente e reprodução

Usar Python 3.12. Executar os comandos abaixo a partir da raiz do repositório,
após disponibilizar os materiais privados:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m unittest discover -s tests -p "test_*.py" -v
.\.venv\Scripts\python.exe src\auditoria_inicial.py
.\.venv\Scripts\python.exe src\preparacao_longitudinal.py
.\.venv\Scripts\python.exe src\verificar_entrega.py
```

No Linux/macOS, usar `.venv/bin/python` e separadores `/` nos caminhos dos
scripts. A ordem acima permite ao verificador comparar as saídas de auditoria
e preparação. As dependências atuais reproduzem a preparação; dependências de
modelagem e aplicação serão definidas em suas respectivas etapas.

As bases JSONL e CSV e os detalhes individuais serão regenerados em
`local_data/`. Os relatórios públicos contêm agregados. As execuções atualizam
metadados e hashes e preservam cópias datadas das saídas em `local_recovery/`.
Antes de editar código, testes ou documentos manuais, preservar também uma
cópia recuperável desses arquivos: a recuperação automática cobre apenas as
saídas regeneradas. Não restaurar versões antigas sobre trabalho atual.

## Trabalho compartilhado e proteção dos dados

Cada integrante deverá trabalhar em branch própria, criada a partir da versão
compartilhada vigente. Verificar o estado local antes de iniciar:

```powershell
git status --short
git log -1 --oneline
git switch -c trabalho/nome-integrante-etapa
```

Substituir o nome da branch por uma identificação própria e revisar as
diferenças antes de integrar o trabalho ao grupo. Integrações na branch principal, tags e publicações devem ocorrer somente após revisão do grupo.

Não versionar `DATATHON/`, `local_data/`, `local_recovery/` ou `.venv/`.
Não publicar nomes, RAs, amostras individuais ou outros dados identificáveis.
Os originais não devem ser alterados. Ausências e lacunas não serão preenchidas
com dados fictícios. Os documentos manuais serão preservados pelas execuções;
relatórios identificados como regeneráveis devem ser alterados em seu gerador.

## Próximas entregas

1. Preparar as coortes de modelagem conforme o contrato, conferindo elegibilidade,
   perdas, alvo desconhecido, alunos repetidos e as contagens esperadas.
2. Realizar as análises das 11 perguntas, com cobertura e limites observacionais.
3. Construir o notebook reproduzível, com engenharia de atributos e divisão temporal.
4. Treinar e selecionar no desenvolvimento; congelar escolhas e realizar a avaliação
   temporal única, com incerteza, sensibilidade e equidade.
5. Implementar a aplicação Streamlit e o modelo final, distinguindo o retreinamento
   das métricas oficiais de avaliação temporal.
6. Realizar o deploy no Streamlit Community Cloud após revisão dos artefatos públicos.
7. Preparar a apresentação gerencial em PPT/PDF com resultados e limitações.
8. Produzir o vídeo de até cinco minutos, com ao menos uma pessoa do grupo.
9. Concluir a revisão final de requisitos, reprodutibilidade, privacidade e entregas.

O ponto imediato de continuidade é a preparação das coortes, ainda pendente.
Consultar o [registro de decisões](registro_decisoes.md), as
[evidências documentais](evidencias_documentais.md) e o
[relatório de preparação](../reports/relatorio_preparacao_inicial.md) antes de
implementar regras novas. Equivalência curricular, fase 9, INCLUIR, faixas das
pedras e inconsistências cadastrais continuam sujeitos às limitações já registradas.
