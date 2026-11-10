
## Decisão de calibração sem horários

O aplicativo do Nubank não expõe o horário das movimentações. Portanto, o projeto não exige horário para simular uma movimentação: a data civil é a entrada principal.

A regra geral implementada é:

- aportes entram no lote na data informada;
- o saque do dia é processado antes do crédito do CDI desse dia;
- o saldo que permanece rende em dia útil;
- a seleção de lote usa a menor carga tributária relativa `(IR + IOF) / valor bruto`, com desempate determinístico por data e sequência do lançamento;
- depósitos do mesmo dia respeitam a ordem registrada em `sort_order`/`sequence`;
- quando a referência observada não pode ser deduzida só com datas e regras públicas, o motor não inventa horário: o CSV exportado mostra a alocação determinística efetivamente usada.

A ausência de horário não será usada para esconder diferenças. As linhas do documento de referência permanecem como casos de comparação e qualquer diferença residual deve ser exibida na calibração, não compensada por um ajuste arbitrário.

## Rodada de calibração de 10/11/2026

A análise separou duas causas. As diferenças de R$ 0,03–0,04 nos rendimentos dos lotes de 03/06 e 12/06 não são explicadas por trocar 120% do CDI por outra fórmula, inverter a ordem do saque ou abandonar o rateio proporcional. O IOF observado permanece compatível; a diferença fica na base de rendimento/IR e é compatível com precisão e arredondamento operacional do produto.

Foi corrigida uma falha objetiva na seleção de lotes: antes, resíduos infinitesimais da precisão do CDI podiam decidir um quase-empate entre aportes da mesma data. Agora o custo tributário usado na ordenação é normalizado em 12 casas decimais e, depois, o desempate usa data mais nova, maior saldo do lote e sequência mais nova. A mesma chave é usada no motor principal e no detalhamento por depósito.

Essa correção torna o resultado determinístico e evita que casas invisíveis do CDI escolham um lote diferente. Ela não inventa uma distribuição para o saque de 28/10: a referência de R$ 386,67 no lote de R$ 621,00 não é dedutível apenas das datas, valores e regra pública disponíveis, portanto não foi hardcoded.

## Rodada de calibração de 10/11/2026 — saques e ordem

As retiradas reais do documento são tratadas como o valor líquido recebido pelo usuário. O motor agora converte o valor líquido pedido em resgate bruto, calcula IR/IOF sobre a parcela de rendimento e encerra o lote quando o valor líquido coincide com o saldo exibido, evitando resíduos artificiais como o lote de R$ 300,00 que foi sacado integralmente por R$ 301,13.

O Histórico visual, a ordem persistida em `sort_order`, os cálculos e o CSV passaram a usar a mesma ordem operacional: data decrescente na apresentação e ordem crescente dentro do mesmo dia. A reordenação não é mais invertida indevidamente antes de ser salva.

O relatório não afirma estar atualizado até o dia civil atual em um dia útil se o CDI desse dia ainda não foi sincronizado; em finais de semana e feriados ele pode fechar na data civil sem inventar uma taxa.

O documento atualmente anexado não contém uma linha `09/09/2023`; por isso essa correção específica não foi aplicada a nenhum lançamento do projeto. A data equivalente encontrada no documento é `29/09/2023`, além das linhas de junho de 2023. Se houver uma transação extra fora desse anexo, ela precisa ser corrigida no histórico importado.
