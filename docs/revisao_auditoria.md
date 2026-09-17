# Registro de revisão da auditoria

## Problemas encontrados
- O relatório anterior registrava contagens divergentes para 2022 em seções diferentes e não calculava dimensões efetivas para planilhas com cabeçalho não dimensionado.
- A categoria 'sem defasagem' era tratada como D == 0 sem distinguir D < 0, D = 0 e D > 0.
- A comparação por RA entre anos não estava separada por população elegível e por observação do destino.
- O mapa de campos não contemplava todas as colunas e não distinguia cabeçalhos repetidos.
- A documentação exigia diferenciação entre arquivo localizado, texto extraído e revisão efetiva.

## Correções no código
- Ajustada a leitura de cabeçalhos e cálculo de dimensões efetivas.
- Separadas as categorias D < 0, D = 0, D > 0 e D >= 0.
- Implementadas validações por RA para transições 2022→2023 e 2023→2024.
- Expandido o mapa de campos para todas as colunas das três abas.
- Criado registro de documentação revisada e separação entre dados locais e relatórios públicos.

## Resultados anteriores substituídos
- Substituídos relatórios com contagem duplicada para 2022 e dimensões None.
- Atualizada a forma de apresentar populações candidatas e fluxo de transição por RA.

## Pendências restantes
- Validar manualmente campos de IPP, fase 9, texto INCLUIR e divergências cadastrais com documentação e regra de negócio.
- Confirmar imagens e tabelas em PDFs/docx com OCR ou checagem visual quando houver conteúdo em figura.
- Revisar as classificações de fase e defasagem antes de preparar a próxima etapa.
