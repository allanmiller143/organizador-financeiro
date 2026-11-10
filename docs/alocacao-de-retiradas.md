# Calibração das caixinhas com os dados corrigidos

Este relatório substitui a análise anterior, que propôs uma regra em cascata sem a referência completa. O PDF **Caixinhas Nubank — dados corrigidos** mostra que o código original deve ser preservado como referência: ele reproduz as retiradas da Caixinha 2 e revela um problema bem mais localizado na Caixinha 3.

## Método

Rodei os módulos originais `tax_engine.py` e `deposit_detail_service.py`, extraídos do ZIP enviado, sem a regra em cascata. Usei o CDI diário de `backend/tests/fixtures/cdi_2026_reference.json` e as movimentações do PDF, até 09/11/2026.

Incluí `backend/tests/test_pdf_caixinhas_reference.py` para proteger a alocação da Caixinha 2. Ele verifica os saques de R$ 216,00 no aporte de 03/06 e de R$ 500,00 no aporte de 12/06, além dos lotes que não tiveram saque. Essa regressão passa com o motor original.

## Caixinha 2: o controle que funciona

| Aporte | Saque parcial no PDF | Resultado do motor original |
|---|---:|---:|
| 03/06 · R$ 1.125,00 | R$ 216,00 | R$ 216,00 |
| 12/06 · R$ 825,00 | R$ 500,00 | R$ 500,00 |
| 11/06 · R$ 2.750,00 | R$ 0,00 | R$ 0,00 |
| 02/07 · R$ 1.000,00 | R$ 0,00 | R$ 0,00 |
| 10/07 · R$ 3.000,00 | R$ 0,00 | R$ 0,00 |
| 03/08 · R$ 510,00 | R$ 0,00 | R$ 0,00 |
| 16/08 · R$ 1.354,32 | R$ 0,00 | R$ 0,00 |

Os rendimentos também batem com o PDF. A diferença de IR no aporte de 12/06 é de R$ 0,01: motor R$ 4,85, PDF R$ 4,84. Isso é compatível com arredondamento monetário.

## Caixinha 3: o que bate e o que não bate

| Aporte / saque | PDF corrigido | Motor original com CDI diário | Diferença |
|---|---:|---:|---:|
| 04/09 · dois saques de 09 e 11/09 | R$ 956,00 | R$ 956,00 | R$ 0,00 |
| 14/10 · saque de 18/10 | R$ 999,95 | R$ 1.000,00 | R$ 0,05 |
| 621,00 · saque de 28/10 | R$ 386,67 | R$ 422,00 | R$ 35,33 |
| 300,00 · total de saques | R$ 0,00 | R$ 0,00 | R$ 0,00 |
| 500,00 · total de saques | R$ 0,00 | R$ 0,00 | R$ 0,00 |
| 04/11 · depósito de R$ 2.300 e saque de R$ 1.500 | R$ 1.500,00 | R$ 1.500,00 | R$ 0,00 |

O motor original mantém os depósitos de R$ 300 e R$ 500 intactos, como no PDF; o erro que encontramos antes (e que a regra em cascata alteraria) não era a explicação correta. O que ainda diverge de forma material é a distribuição da retirada de 28/10 entre os cinco aportes de 29/09.

## A hipótese a testar: desempate entre lotes da mesma data

Aos 29 dias, todos os depósitos de 29/09 têm a mesma taxa e, sem arredondamento, o mesmo custo tributário proporcional. O motor original desempata pelo maior saldo, então escolhe o lote de R$ 621 primeiro e atribui a ele os R$ 422 inteiros.

O PDF mostra que o Nubank consumiu por completo os lotes de R$ 5 e R$ 30 e atribuiu R$ 386,67 ao de R$ 621, deixando os lotes de R$ 300 e R$ 500 sem saque. Isso é compatível com uma ordenação estável diferente entre os lotes empatados — por exemplo, prioridade de criação/ordem interna — e não com a regra genérica "fechar todo lote pequeno que cabe". A Caixinha 2 não distingue esses desempates porque os lotes escolhidos ali têm datas/idades diferentes.

A diferença de R$ 35,33 não é arredondamento; é escolha de lotes. Separadamente, a diferença de R$ 0,05 no saque de 18/10 e as diferenças de R$ 0,01–0,02 nos impostos são compatíveis com política de arredondamento/cálculo do Nubank.

## Ordem confirmada e testes de desempate

O usuário confirmou que a lista do PDF está correta e que, quanto mais abaixo, mais antigo. Assim, a ordem de criação do mais antigo para o mais novo é **500 → 621 → 30 → 300 → 5**.

Testei desempatar pelo número de sequência nos dois sentidos, preservando o motor tributário original. Nenhum reproduz o PDF:

- Mais antigo primeiro: o motor usa o lote de R$ 500 para cobrir os R$ 422.
- Mais novo primeiro: encerra os lotes de R$ 5, R$ 300 e R$ 30, depois tira R$ 83,91 do lote de R$ 621.
- Resultado observado: encerra os lotes de R$ 5 e R$ 30, tira R$ 386,67 do lote de R$ 621 e mantém R$ 300 e R$ 500 intactos.

O resumo repassado pelo bot do Nubank confirma a regra que já está no motor: menor `(IR + IOF) / valor bruto`, continuando para o próximo lote quando necessário. Mas ele não define desempate quando os custos são iguais nem a precisão/arredondamento usados nesse índice.

Com o CDI diário de referência, o custo proporcional dos cinco lotes dá **0,003006671362** para cada um na precisão usada pelo motor. Enumerei as **120 ordens possíveis** desses cinco candidatos, mantendo a mesma retirada total de R$ 422,00 e o mesmo cálculo tributário.

**Resultado: sim, sua hipótese se confirma no total da caixinha.** A ordem `5 → 30 → 621 → 300 → 500` reproduz a composição do PDF quase exatamente: os lotes de R$ 5 e R$ 30 são encerrados, o de R$ 621 recebe R$ 386,68 (R$ 0,01 acima do PDF) e os de R$ 300 e R$ 500 ficam intactos. Nessa ordem, o saldo bruto total calculado termina em R$ 7.545,54 e o líquido em R$ 7.527,41. Com o desempate atual do motor (maior lote primeiro), o saque inteiro de R$ 422 sai do lote de R$ 621 — mas os totais também terminam em R$ 7.545,54 bruto e R$ 7.527,41 líquido.

Nas 120 permutações, os impostos pagos variaram menos que `3 × 10⁻²⁶` reais em precisão interna; a soma exibida dos saldos brutos variou R$ 0,01 e a dos líquidos, R$ 0,02, por arredondamento de centavos. Ou seja, escolher outro lote empatado muda a composição por depósito, mas praticamente não muda o saldo agregado final. É plausível que o Nubank use um desempate interno diferente — o PDF e a resposta genérica do bot não permitem identificar qual.

Arredondar IR e IOF de cada lote para centavos antes de calcular o índice daria a ordem `5 → 30 → 300 → 500 → 621`, que consumiria o lote de R$ 300 e não reproduziria o PDF. Portanto, não vou codificar esse desempate especulativo. O motor original permanece intacto; o relatório registra que o saldo agregado fica correto dentro de centavos, embora a atribuição por lote possa divergir.

## Testes

```bash
cd backend
python -m pytest -q
```

Resultado após restaurar a regra original e adicionar o caso de referência do PDF: **157 testes passando**.
