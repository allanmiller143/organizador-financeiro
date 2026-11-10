# Lógica do motor financeiro

## 1. Objetivo e escopo

Este documento descreve como reproduzir o motor de simulação das Caixinhas usado neste projeto. Ele reúne as regras observadas nos dados reais, as decisões de modelagem e as limitações conhecidas.

O motor é uma **simulação aproximada** do comportamento observado nas Caixinhas do Nubank. Ele não é o código interno do Nubank e não deve ser tratado como uma implementação oficial. Algumas regras públicas são conhecidas, enquanto outras foram inferidas por comparação com extratos e tabelas do usuário.

A implementação principal está em:

```text
backend/app/services/yield_engine.py
backend/app/services/tax_engine.py
backend/app/services/deposit_detail_service.py
backend/app/services/calendar_br.py
backend/app/services/cdi_service.py
```

O serviço de relatórios reúne os dados e fornece o fechamento usado pela interface:

```text
backend/app/services/report_service.py
```

## 2. Representação dos lançamentos

Cada lançamento possui, no mínimo:

```text
data
valor positivo
operação: DEPOSIT ou WITHDRAWAL
percentual do CDI
prazo e trava, quando aplicável
sort_order: ordem operacional dentro do dia
reinvestment_order: ordem dos lotes que vencem na mesma data
```

No motor, um aporte é representado por um `Flow` com valor positivo e uma retirada por um `Flow` com valor negativo. Cada aporte cria um `Lot` independente.

Um lote guarda:

```text
start: data de entrada
principal: base atual para imposto
value: valor bruto atual
invested: valor originalmente aportado que ainda está representado no lote
cdi_percent: percentual do CDI
term_months e locked: informações de RDB planejado
sequence: posição operacional do lançamento
source_id: identificação da transação original
reinvestment_order: ordem manual de reaplicação
```

`principal` e `value` não são a mesma coisa. O principal é a base tributária; o valor bruto inclui os rendimentos acumulados.

## 3. Calendário e CDI

O motor usa dias civis para idade de IR e IOF, mas só aplica rendimento nos dias que possuem CDI disponível e que são dias úteis do calendário brasileiro.

A fonte automática atual é a série 12 do SGS do Banco Central do Brasil:

```text
https://api.bcb.gov.br/dados/serie/bcdata.sgs.12/dados
```

O valor diário da série é uma taxa percentual ao dia. O sistema transforma a taxa anual ou diária conforme a função de cálculo e aplica o percentual da caixinha.

Para um lote que rende `p%` do CDI:

```text
fator_do_lote = taxa_diária_do_CDI × p / 100
valor_novo = valor_atual × (1 + fator_do_lote)
```

A fonte pública pode publicar o CDI com atraso em relação ao aplicativo do Nubank. O motor não deve repetir artificialmente a última taxa para fingir atualização. Quando não há taxa para um dia útil, esse dia não recebe rendimento e o fechamento deve indicar a última data de CDI disponível.

## 4. Ordem do ciclo diário

A ordem diária implementada é:

1. Entram os aportes do dia, na ordem operacional.
2. São processadas as retiradas do dia, na ordem operacional.
3. O saldo que permaneceu recebe o rendimento do dia, quando existe CDI.
4. São processados os lotes cujo vencimento ocorre naquele dia.
5. É salvo o retrato mensal, quando necessário.

A consequência importante é:

- o aporte pode render no próprio dia;
- uma retirada do próprio dia pode usar o aporte se ele ocorreu antes dela na ordem operacional;
- uma retirada do próprio dia não recebe o rendimento daquele dia;
- o saldo que não foi retirado recebe o rendimento do dia.

Se uma retirada aparece antes de um aporte na mesma data, ela não pode consumir aquele aporte. Por isso `sequence` é usado para impedir que um lançamento posterior seja usado por uma retirada anterior.

## 5. Retiradas são valores líquidos

O valor informado em uma retirada representa o valor líquido recebido pelo usuário, e não o valor bruto removido do lote.

Para um lote com valor bruto `V`, principal `P` e rendimento `Y = V - P`, o motor estima o custo tributário relativo:

```text
fração_de_rendimento = max(V - P, 0) / V
custo = fração_de_rendimento × [IOF + (1 - IOF) × IR]
```

O valor bruto necessário para entregar um líquido `L` é aproximado por:

```text
bruto_do_resgate = L / (1 - custo)
```

Depois o lote é reduzido proporcionalmente:

```text
principal_removido = principal × bruto_do_resgate / valor
rendimento_removido = rendimento × bruto_do_resgate / valor
```

O IOF incide sobre a parte de rendimento resgatada. O IR incide sobre o rendimento depois do IOF:

```text
IOF = rendimento_resgatado × alíquota_IOF
IR = (rendimento_resgatado - IOF) × alíquota_IR
```

A retirada líquida registrada é o valor pedido pelo usuário, arredondado para exibição. Essa decisão corrigiu casos em que o Nubank retirava, por exemplo, R$ 301,13 para consumir integralmente um lote iniciado em R$ 300,00, mas o motor deixava centavos artificiais.

## 6. Tabela de IOF e IR

O IOF usa a tabela regressiva oficial de 30 dias sobre o rendimento, começando em 96% no primeiro dia e chegando a 0% no trigésimo dia.

O IR usa as faixas regressivas:

```text
até 180 dias: 22,5%
181 a 360 dias: 20%
361 a 720 dias: 17,5%
acima de 720 dias: 15%
```

A idade é calculada em dias corridos entre a data do aporte ou reaplicação e a data do evento.

## 7. Seleção do lote em uma retirada

A retirada não é FIFO nem LIFO puro. O lote escolhido é o que possui menor custo tributário relativo por real sacado, considerando IR e IOF.

A ordenação usada é:

```text
1. menor custo tributário normalizado;
2. data de início mais recente;
3. maior valor atual do lote;
4. sequência operacional mais recente.
```

O custo é normalizado em alta precisão antes da comparação para evitar que resíduos muito pequenos do CDI decidam um quase-empate.

Lotes travados ficam fora da seleção enquanto a trava estiver ativa.

A mesma lógica precisa existir nos dois lugares abaixo:

```text
backend/app/services/tax_engine.py
backend/app/services/deposit_detail_service.py
```

Se apenas um deles for alterado, o resumo da caixinha e o drawer de detalhes podem apresentar alocações diferentes.

## 8. Vencimento e reaplicação

Cada aporte vence depois de dois anos, representados pelo prazo operacional de 730 dias. No vencimento:

1. calcula-se o rendimento bruto acumulado;
2. calcula-se o IR correspondente;
3. o lote antigo é encerrado;
4. o saldo líquido após o IR é reaplicado como um novo lote;
5. o novo lote volta como RDB imediato, sem trava, com idade tributária zero;
6. o `principal` do novo lote passa a ser o valor reaplicado;
7. o campo `invested` continua representando apenas o valor originalmente aportado, e não o rendimento reaplicado.

A fórmula conceitual é:

```text
rendimento = valor_bruto - principal
IR = rendimento × alíquota correspondente
valor_reaplicado = valor_bruto - IR
```

O valor reaplicado é arredondado para centavos na apresentação e no nascimento do novo lote. Diferenças de um centavo podem surgir quando a instituição usa precisão interna ou uma ordem de arredondamento diferente.

Quando vários aportes vencem no mesmo dia, usa-se `reinvestment_order` se houver uma ordem manual; caso contrário, usa-se a sequência de criação dos aportes.

## 9. Arredondamento e precisão

A regra geral é manter `Decimal` com precisão interna durante o máximo possível e arredondar para centavos apenas na apresentação ou nos pontos em que um valor operacional é criado:

- valores exibidos;
- impostos pagos ou estimados apresentados;
- valor de uma reaplicação que nasce como novo principal;
- valores dos CSVs.

Não se deve arredondar o saldo diariamente sem evidência, porque isso altera o rendimento composto e pode criar diferenças maiores.

Existe uma tolerância para reconhecer que um lote foi integralmente consumido quando a diferença está dentro da faixa de exibição. O lote é zerado, mas o motor não deve registrar a tolerância como dinheiro adicional recebido pelo usuário.

Essa área ainda pode gerar diferenças residuais de centavos em relação ao Nubank. Não é correto aplicar automaticamente `+R$ 0,01` a todas as reaplicações: alguns casos já coincidem e outros podem ficar errados.

## 10. Ordem dos lançamentos

A ordem padrão dos novos lançamentos no mesmo dia é a ordem de cadastro mais recente primeiro na interface e na sequência operacional. A ordem é persistida em `sort_order`.

A ordem manual feita por arrastar os cards deve ser enviada ao backend e usada por:

- Histórico visual;
- CSV simples;
- motor de cálculo;
- alocação de saques;
- reaplicações quando aplicável.

A migração de normalização dos dados antigos é:

```text
backend/migrations/versions/c7d8e9f01234_backfill_transaction_order.py
```

Para dados antigos que não possuíam `sort_order`, a migração cria uma ordem inicial estável. Como a ordem histórica original não pode ser recuperada se nunca foi armazenada, esses casos devem ser conferidos manualmente e podem ser corrigidos arrastando os cards.

## 11. Detalhes por depósito

O serviço `deposit_detail_service.py` repete a simulação por lote para mostrar apenas os lotes ainda ativos.

O detalhe de cada lote pode conter:

```text
valor aplicado
principal restante
retiradas parciais
rendimento bruto total
IR pago e estimado
IOF efetivamente pago
IOF estimado do saldo restante
saldo bruto
saldo líquido estimado
vencimento
produto e percentual do CDI
```

O rendimento bruto do lote inclui também o rendimento que já saiu em retiradas parciais, conforme a forma de visualização usada no Nubank.

## 12. Exportações

Existem duas exportações diferentes:

### Histórico simples

Fica no componente Histórico e contém somente:

```text
dia;operacao;valor
```

Inclui aportes, retiradas e reaplicações realmente geradas pelo motor.

### Detalhes dos depósitos

Fica no drawer de detalhes dos depósitos e contém os lotes ativos, seus rendimentos, tributos e retiradas alocadas.

Esses relatórios devem continuar usando exatamente a mesma ordem e as mesmas funções do motor que alimentam a tela.

## 13. Como replicar o motor

Uma implementação independente pode seguir este roteiro:

1. Carregar todos os lançamentos ordenados por data e posição operacional.
2. Transformar cada aporte em um lote com principal e valor bruto iguais ao aporte.
3. Percorrer cada data civil até a data final.
4. Inserir aportes do dia.
5. Processar retiradas do dia em ordem, ignorando lotes travados e lotes posteriores na mesma data.
6. Para cada retirada, ordenar lotes pelo custo tributário relativo.
7. Converter o valor líquido solicitado em valor bruto e reduzir principal, investido e valor proporcionalmente.
8. Aplicar o CDI somente ao saldo restante em dias com taxa disponível.
9. Fechar lotes vencidos, pagar IR e criar lotes de reaplicação.
10. Arredondar somente nos pontos operacionais e na apresentação.
11. Gerar o resumo e, separadamente, o detalhamento por lote.
12. Comparar os dois resultados para garantir que resumo, drawer e CSV não divergem.

## 14. O que ainda precisa de ajuste

O motor está muito próximo dos dados comparados, mas continua sendo uma simulação. As limitações conhecidas são:

- o Nubank não expõe publicamente todos os horários e regras internas de corte;
- a série pública do CDI pode ficar atrasada em relação ao aplicativo;
- a B3 pode publicar dados de DI em uma janela diferente da API usada;
- a instituição pode manter precisão interna e uma ordem de arredondamento que não é pública;
- alguns saques parciais podem apresentar diferenças de centavos na alocação entre lotes;
- quando lotes possuem datas e custos muito próximos, a regra interna de desempate do Nubank não pode ser deduzida apenas dos dados disponíveis;
- reaplicações que foram totalmente consumidas deixam de aparecer no aplicativo, dificultando validar a origem de diferenças antigas;
- a ordem original de lançamentos antigos sem `sort_order` não pode ser reconstruída com certeza.

Portanto, qualquer alteração futura deve ser validada em três níveis:

1. saldo bruto;
2. saldo líquido e impostos;
3. alocação de cada saque e reaplicação.

Uma correção que melhora apenas o saldo final, mas muda a distribuição dos saques, não deve ser considerada comprovadamente correta.
