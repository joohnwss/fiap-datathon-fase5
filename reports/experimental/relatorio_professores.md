# Como o modelo se saiu ao prever defasagem no ano seguinte — em linguagem simples

*Análise exploratória, feita depois do resultado oficial já publicado. Não
muda o programa nem a ferramenta usada hoje — é um estudo para ajudar a
decidir se vale a pena ajustar alguma coisa no futuro, com autorização de
quem cuida do projeto.*

## O que a ferramenta faz hoje

Ela olha para sete informações de um(a) estudante no início do ano e
calcula a chance de essa pessoa entrar em defasagem escolar no ano
seguinte. Quando essa chance passa de um certo ponto de corte, o
estudante é sinalizado para acompanhamento.

## O que encontramos quando testamos com dados de um ano seguinte de verdade

No teste com os dados de 2023 prevendo 2024, **84 estudantes realmente
entraram em defasagem**. A ferramenta sinalizou **34 deles com antecedência**
e **não sinalizou 50**. Isso é o "recall" de 40%: de cada 10 estudantes que
realmente iam entrar em defasagem, a ferramenta avisou sobre 4 e não
avisou sobre 6.

Dos 53 estudantes que a ferramenta sinalizou no total, 34 realmente
entraram em defasagem e 19 não entraram — ou seja, quando ela sinaliza,
acerta bem mais da metade das vezes (64%).

## "A acurácia é de 77%, isso não é bom?"

Não é tão simples. Nesse grupo, cerca de 27% dos estudantes realmente
entraram em defasagem. Se alguém simplesmente dissesse "ninguém vai entrar
em defasagem" para todo mundo, sem olhar dado nenhum, essa pessoa já
acertaria 73% das vezes — só porque a maioria não entra em defasagem
mesmo. A ferramenta chega a 78%, só 5 pontos acima desse "chute ingênuo".
Por isso a acurácia sozinha não é o número certo para julgar se a
ferramenta ajuda: o que importa é quantos casos reais ela consegue
encontrar (isso é o recall) e se ela erra pouco ao sinalizar alguém
(isso é a precisão).

## Dá para encontrar mais estudantes em risco sem trocar de modelo?

Sim, ajustando só o "ponto de corte" (a partir de que chance a ferramenta
sinaliza). Testamos várias opções usando apenas dados de anos já
conhecidos (nunca espiamos o ano de teste na hora de escolher o corte) e
depois aplicamos cada opção, uma única vez, no ano de teste real:

| Se ajustarmos o corte para... | Estudantes observados | Casos reais encontrados | Casos reais ainda perdidos |
|---|---|---|---|
| **Como está hoje** | 53 | 34 | 50 |
| Um corte mais sensível (opção A) | 83 | 47 | 37 |
| Um corte ainda mais sensível (opção B) | 87 | 49 | 35 |

A opção B encontra 15 estudantes a mais do que hoje, mas exige observar
mais 34 estudantes no total — nem todos vão de fato estar em risco (mais
falsos alarmes). Não é gratuito: é uma troca. Quanto mais sensível o
corte, mais estudantes entram na lista de observação, e mais desses
alarmes vão ser "falsos" (o estudante estava bem, mesmo assim foi
observado). Isso não é necessariamente ruim — pode ser só uma checagem
pedagógica a mais — mas a equipe precisa poder dar conta dessa lista
maior.

## Um ponto de atenção sobre equidade

Quando olhamos por gênero, hoje a ferramenta encontra 48% dos meninos em
risco e só 33% das meninas em risco — uma diferença real. As duas opções
mais sensíveis de corte, testadas acima, **diminuem** essa diferença, não
aumentam.

Já entre 11 e 13 anos, a ferramenta encontra só 1 em cada 9 estudantes que
realmente entraram em defasagem — e isso **não melhora** mesmo com o corte
mais sensível que testamos. Isso sugere que o problema, nessa faixa
etária, não é o ponto de corte: é algo mais estrutural, que merece
investigação própria, fora desta análise.

## O que fizemos para deixar as probabilidades mais "honestas"

Testamos técnicas de recalibração (ajustar a escala das probabilidades
sem mudar a ordem dos estudantes). Uma delas (chamada Platt) melhorou a
qualidade das probabilidades sem mudar quais estudantes seriam
encontrados. A outra (isotônica) piorou — provavelmente porque temos
poucos casos para ajustá-la com segurança. Recalibrar não faz a ferramenta
"enxergar" ninguém que ela já não enxergava antes; só deixa o número de
chance mais fiel à realidade.

## O que recomendamos

- **Manter o corte atual por enquanto** — ele já é, segundo um critério
  técnico independente (Youden J), um bom ponto de equilíbrio entre
  encontrar casos e não gerar alarmes demais.
- **Considerar, como decisão de gestão (não técnica)**, se vale a pena
  adotar um corte mais sensível — isso depende de quantos estudantes a
  equipe pedagógica consegue efetivamente acompanhar a mais, não só do
  número estatístico.
- **Investigar separadamente** por que a faixa de 11 a 13 anos é
  sistematicamente mal atendida pela ferramenta, já que baixar o corte não
  resolveu isso.
- Nenhuma dessas opções é implementada agora — ficam registradas para
  quando o time responsável quiser decidir com calma.
