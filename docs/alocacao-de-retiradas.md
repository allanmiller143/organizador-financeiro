# Calibração do motor de retiradas com o extrato RDB

## Resultado atual

A regressão baseada no extrato permite confirmar com precisão a seleção de lotes no resgate de 28/10 da Turbo Nubank Croma. O motor atual encerra os lotes de R$ 5 e R$ 30, retira R$ 386,67 líquidos do lote de R$ 621 e não consome os lotes de R$ 300 e R$ 500. Esse comportamento coincide com a divisão mostrada no PDF e corrige a divergência que motivou a investigação.

| Lote aplicado em 29/09 | Resgate bruto | IR | IOF | Líquido | Resultado no extrato e no motor |
|---:|---:|---:|---:|---:|---|
| R$ 5,00 | R$ 5,06 | R$ 0,01 | R$ 0,00 | R$ 5,05 | Encerrado |
| R$ 30,00 | R$ 30,37 | R$ 0,08 | R$ 0,01 | R$ 30,28 | Encerrado |
| R$ 621,00 | R$ 387,83 | R$ 1,02 | R$ 0,14 | R$ 386,67 | Parcial |
| R$ 300,00 | — | — | — | — | Sem resgate |
| R$ 500,00 | — | — | — | — | Sem resgate |
| **Total** | **R$ 423,26** | **R$ 1,11** | **R$ 0,15** | **R$ 422,00** | **Coincide** |

## Diferenças que ainda permanecem

O acerto de 28/10 não significa que todos os resgates da caixinha foram reproduzidos ao centavo. Na simulação do motor atual, usando o fixture diário de CDI e o cenário de 120% CDI, o líquido solicitado coincide, mas o extrato ainda mostra diferenças em bruto e retenções:

| Data | Extrato: bruto / IR / IOF / líquido | Motor: bruto / IR / IOF / líquido | Diferença motor − extrato |
|---|---|---|---|
| 03/09 | 302,43 / 0,33 / 0,97 / 301,13 | 302,42 / 0,32 / 0,97 / 301,13 | −0,01 / −0,01 / 0,00 / 0,00 |
| 09/09 | 290,31 / 0,02 / 0,29 / 290,00 | 290,30 / 0,01 / 0,29 / 290,00 | −0,01 / −0,01 / 0,00 / 0,00 |
| 11/09 | 667,35 / 0,09 / 1,26 / 666,00 | 667,33 / 0,08 / 1,25 / 666,00 | −0,02 / −0,01 / −0,01 / 0,00 |
| 20/09 | 1.500,86 / 0,02 / 0,84 / 1.500,00 | 1.500,86 / 0,01 / 0,85 / 1.500,00 | 0,00 / −0,01 / +0,01 / 0,00 |
| 18/10, total do dia | 1.001,63 / 0,06 / 1,57 / 1.000,00 | 1.001,62 / 0,05 / 1,57 / 1.000,00 | −0,01 / −0,01 / 0,00 / 0,00 |
| 28/10 | 423,26 / 1,11 / 0,15 / 422,00 | 423,26 / 1,11 / 0,15 / 422,00 | 0,00 / 0,00 / 0,00 / 0,00 |
| 04/11 | 1.500,00 / 0,00 / 0,00 / 1.500,00 | 1.500,00 / 0,00 / 0,00 / 1.500,00 | 0,00 / 0,00 / 0,00 / 0,00 |

O documento disponível não revela a origem do lote em cada linha, a taxa contratual do produto nem o cálculo subcentavo usado pelo Nubank. Portanto, as diferenças de um ou dois centavos não podem ser atribuídas com certeza a uma única operação matemática.

## Regra implementada e limites da inferência

A orientação enviada pelo usuário, atribuída ao atendimento automatizado do Nubank, descreve para RDB a prioridade pelo menor custo tributário relativo `(IR + IOF) / valor bruto`, continuando em outros depósitos quando necessário. O alocador do NuBox calcula as parcelas por lote, refaz a comparação após cada parcela, respeita a sequência registrada e conserva resíduos subcentavários para simulações posteriores.

Foram testadas alternativas de arredondamento para eliminar as diferenças restantes. Uma delas reproduz os totais diários do Croma sob certas condições, mas pode mudar a seleção dos lotes ou deslocar um centavo no saldo final da referência da Caixinha 2. Como essas opções não preservam simultaneamente as referências independentes, nenhuma foi incorporada como regra universal. A implementação atual preserva a seleção de lotes corroborada em 28/10 e a regressão anterior da Caixinha 2.

Esse resultado é uma calibração empírica do comportamento observado, não uma reprodução do código proprietário do Nubank. Também não prova que produtos diferentes usem a mesma política fiscal ou de arredondamento.

## Testes e validação

A regressão do Croma está em `backend/tests/test_rdb_statement_reference.py`; a referência anterior da Caixinha 2 está em `backend/tests/test_pdf_caixinhas_reference.py`. O motor agregado e o detalhamento por depósito usam a mesma função de alocação, em `backend/app/services/withdrawal_allocator.py`.

Na validação final desta versão, **170 testes de backend passaram**. O build de produção do frontend e o lint também passaram. O build emite somente um aviso de tamanho para o bundle JavaScript principal.

Para executar a suíte do backend:

```bash
cd backend
python -m pytest -q
```

## O que falta para uma calibração universal

Para fechar os centavos nas nove caixinhas são necessários, conforme o caso, o percentual CDI contratual por produto e período, o saldo/lotes existentes antes do início do PDF, a identificação do lote de origem de cada resgate e a ordem/horário confiável das operações do mesmo dia. O relatório `docs/validacao-nove-caixinhas.md` detalha quais desses dados faltam em cada conta.