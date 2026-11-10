# Regras das caixinhas (como o app calcula)

Estas são as regras implementadas em `backend/app/services/tax_engine.py` e validadas em
`backend/app/services/transaction_service.py`.

## Rendimento
- Cada caixinha tem um rendimento padrão (100%, 105%, 120%... do CDI).
- Todo aporte normal rende o padrão da caixinha. O % gravado no aporte só vale se ele for trancado.
- O aporte entra no lote no próprio dia quando há CDI; a retirada é fechada antes do crédito do CDI daquele dia, e somente o saldo que permanece rende. Em fim de semana ou feriado não há rendimento, e o lote participa do próximo dia com CDI.

## Dinheiro trancado
- Só existe em caixinha de **até 100%** do CDI. Acima de 100% a API recusa (`lock_not_allowed`).
- Rende uma taxa maior durante o prazo (104,5% / 6 meses, 105% / 12, 105,5% / 18, 106% / 24).
  Para aportes históricos, o formulário também permite informar manualmente a taxa efetiva do CDI
  usada naquele contrato; ela fica salva no próprio aporte e não altera a taxa atual da caixinha.
- O prazo da trava não passa de 24 meses.
- Enquanto trancado, **não pode ser retirado**. No último dia da trava ele ainda rende a taxa
  travada e já pode ser sacado; depois volta a ser aporte normal (rende o padrão da caixinha).

## IR regressivo e vencimento
- IR sobre o rendimento: 22,5% até 180 dias, 20% até 360, 17,5% até 719 e 15% a partir de 720.
- Todo aporte vence em **2 anos (730 dias)**: o rendimento paga IR e o resto é reaplicado
  automaticamente como aporte novo (padrão da caixinha, sem trava, idade zerada).
- Quando vários aportes vencem no mesmo dia, a reaplicação segue a ordem de criação dos aportes
  por padrão. Essa ordem pode ser reordenada manualmente no histórico da caixinha.

## Valor aplicado
- `invested` / "Valor aplicado" = o que você colocou e ainda está na caixinha.
  Rendimento e reaplicações **nunca** entram nele: aplicou 1.000 e rendeu 200, aos 2 anos
  continua 1.000 aplicados.
- `deposited_total` / "Total depositado" = soma de todos os aportes já feitos.

## Retiradas
- O valor informado em uma retirada é o valor líquido recebido pelo usuário. O motor converte esse valor para o resgate bruto do lote, calcula IOF e IR sobre o rendimento resgatado e reduz o saldo pelo bruto correspondente.
- Quando o valor líquido informado coincide, dentro da precisão de exibição, com o saldo líquido do lote, o lote é encerrado integralmente; não fica um resíduo artificial de centavos.
- Não é FIFO nem LIFO. Sai primeiro do lote com **menor imposto por real sacado, contando IR + IOF**:
  `(rendimento / valor do lote) x (IOF + (1 - IOF) x IR)`, com IOF e IR pela idade do lote no dia.
  O custo é normalizado antes da comparação para que resíduos infinitesimais da precisão do CDI não decidam um quase-empate. Depois, o desempate é determinístico: data mais nova, maior saldo do lote e sequência mais nova. Lotes trancados ficam fora.
- Por que o IOF entra: lotes com menos de 30 dias têm IOF alto sobre o rendimento, então um lote
  mais velho (IOF já baixo) pode sair mais barato mesmo tendo rendido mais. Calibrado com uma
  caixinha real do Nubank (120% do CDI): a 1ª retirada saiu do depósito mais novo, as seguintes
  do mais antigo. Coberto por `tests/test_deposit_details.py`.
- Se só houver dinheiro trancado, a retirada é recusada e o aviso diz quanto está trancado.
- Na aba de depósitos, "Rendimento bruto" é o rendimento total do depósito, **incluindo a parte
  que já saiu em retiradas** (igual ao Nubank). O IR e o IOF mostrados também são totais.
- A projeção (`projection_engine.py`) ordena só por IR e ignora o IOF (aviso na tela de projeção).
