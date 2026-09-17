# Requisitos e escopo da rodada

## Objetivos da primeira rodada

1. Organizar a rastreabilidade do projeto.
2. Auditar as fontes de forma reproduzível.
3. Validar divergências estruturais e semânticas da base principal.
4. Comparar populações candidatas ao modelo sem adotar recorte definitivo.
5. Registrar limitações e pendências antes de qualquer preparação de dados.

## Regras de preservação

- Não alterar, renomear, mover ou excluir qualquer arquivo em `DATATHON`.
- Não combinar bases antigas com a atual sem justificativa documental.
- Não corrigir valores por suposição, nem eliminar registros silenciosamente.
- Não tratar ausências como zeros nem usar junção pela posição da linha.

## Evidência esperada

- Contagem de abas, linhas e colunas por ano.
- Cabeçalhos por posição, inclusive repetidos.
- Tipos e formatos mistos.
- Ausências e textos em campos numéricos.
- Verificação de RA ausentes e duplicados.
- Correspondência entre anos.
- Comparação entre indicadores e regras de fase/defasagem.
- Relato de divergências entre documentação e observação local.

## Entregáveis desta etapa

- `README.md`
- `docs/`
- `src/`
- `reports/relatorio_auditoria_inicial.md`

## Exclusões de versionamento

- `DATATHON/`
- bases derivadas locais
- relatórios com dados sensíveis
- ambientes virtuais e caches
- segredos e arquivos temporários
