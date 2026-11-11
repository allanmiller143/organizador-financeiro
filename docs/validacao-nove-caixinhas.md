# Validação do NuBox contra as nove caixinhas do PDF

## Conclusão

O PDF não sustenta a afirmação de que o motor reproduz com precisão todas as nove caixinhas. Para algumas faltam saldo/lotes anteriores; outras não têm retiradas capazes de testar o motor; e o documento não informa a taxa CDI contratual de cada produto. A referência mais informativa é a Turbo Nubank Croma: o motor atual reproduz a seleção de lotes em 28/10 e os valores líquidos solicitados, mas ainda difere do extrato em bruto, IR e/ou IOF por R$ 0,01–0,02 em cinco das sete datas de resgate. O cenário de 120% CDI usado na simulação é hipótese de teste, não taxa confirmada pelo PDF.

A mensagem do bot do Nubank enviada pelo usuário descreve para RDB uma prioridade pelo menor custo tributário relativo `(IR + IOF) / valor bruto`, com o resgate dividido entre lotes quando necessário. Isso é compatível com a evidência de 28/10, mas não basta para afirmar que uma única regra de arredondamento explica todas as contas. A afirmação separada sobre FIFO para o Fundo Nu Reserva não foi aplicada: as páginas de rendimento examinadas identificam os registros como “Caixinha RDB”, e não fornecem dados que confirmem um fundo nessa conta.

## Resultado por caixinha

| Nº | Caixinha | O que os dados permitem afirmar | Situação da validação |
|---:|---|---|---|
| 01 | Cartão | O recorte lista 52 aplicações e 67 resgates, mas não inclui saldo/lotes suficientes antes do primeiro evento simulado. | **Não conciliável ainda.** A simulação para em 14/06 por falta de R$ 247,86; isso não prova divergência do motor. |
| 02 | cartão mês que vem | O recorte contém 16 aplicações e 21 resgates. Há resgate em 01/06 antes da primeira aplicação listada, em 03/06. | **Não conciliável ainda.** Falta histórico de abertura; taxa do produto também não foi confirmada. |
| 03 | Focar na carreira | Há três aplicações e um resgate líquido/bruto de R$ 3,00 em 09/11, sem IR/IOF observado. | **Correspondência nominal apenas.** O evento não testa rendimento tributável nem desempate entre lotes. |
| 04 | PGE | Há somente uma aplicação de R$ 0,01 e nenhum resgate. | **Teste de aporte apenas.** Não valida rendimento ou regra de saque. |
| 05 | presente se vó | Há cinco aplicações e quatro resgates em três datas. No cenário hipotético de 100% CDI, as diferenças agregadas registradas são: bruto −R$ 0,03, IR −R$ 0,02, IOF −R$ 0,01 e líquido −R$ 0,01 (motor menos extrato). | **Parcial e inconclusiva.** Duas retiradas de 28/07 têm ordem/origem de lote ambígua no PDF e no JSON. |
| 06 | reserva de emergência | O recorte contém quatro aplicações e quatro resgates, mas o estado/lotes anteriores não são suficientes para executar uma conciliação completa. Os registros examinados aparecem como RDB. | **Não conciliável ainda.** O teste interrompe por saldo insuficiente em 04/11; não há pareamento seguro dos lotes. |
| 07 | Turbo Nubank Croma | Há 15 aplicações e sete resgates em sete datas. Em 28/10, os lotes de R$ 5 e R$ 30 encerram, o de R$ 621 entrega R$ 386,67 líquidos e os de R$ 300 e R$ 500 ficam intactos. | **Seleção de lotes confirmada em 28/10; conciliação tributária parcial no restante.** O líquido pedido coincide nas sete datas, mas cinco dias têm diferenças de 1–2 centavos no bruto e/ou nas retenções. Ver quadro seguinte. |
| 08 | Turbo NuCel | Há sete aplicações e três resgates, sem concorrência de aporte e resgate na mesma data no recorte. A taxa efetiva não aparece no PDF. | **Condicional, não confirmada.** A simulação anterior a 100% CDI não reproduz integralmente bruto/IR/IOF; esse cenário não comprova nem refuta a regra real sem taxa contratual. |
| 09 | Viagem | O PDF e o JSON não apresentam transações. | **Sem comparação elegível.** Não há eventos para testar aporte, rendimento ou saque. |

“Correspondência nominal” e “condicional” não significam que o produto tenha sido integralmente validado. Uma igualdade obtida sob uma taxa assumida só é válida para aquele cenário matemático.

## Comparação detalhada da Turbo Nubank Croma

A tabela agrega todas as linhas de resgate de cada data. Para 18/10 e 28/10, o PDF contém mais de uma linha. A coluna “diferença” é o motor atual menos o extrato, em reais. Os aportes e a ordem confirmada pelo usuário foram usados na regressão `backend/tests/test_rdb_statement_reference.py`, com o fixture `backend/tests/fixtures/cdi_2026_reference.json` e 120% CDI como cenário de simulação.

| Data | Extrato: bruto / IR / IOF / líquido | Motor atual: bruto / IR / IOF / líquido | Diferença: bruto / IR / IOF / líquido |
|---|---|---|---|
| 03/09 | 302,43 / 0,33 / 0,97 / 301,13 | 302,42 / 0,32 / 0,97 / 301,13 | −0,01 / −0,01 / 0,00 / 0,00 |
| 09/09 | 290,31 / 0,02 / 0,29 / 290,00 | 290,30 / 0,01 / 0,29 / 290,00 | −0,01 / −0,01 / 0,00 / 0,00 |
| 11/09 | 667,35 / 0,09 / 1,26 / 666,00 | 667,33 / 0,08 / 1,25 / 666,00 | −0,02 / −0,01 / −0,01 / 0,00 |
| 20/09 | 1.500,86 / 0,02 / 0,84 / 1.500,00 | 1.500,86 / 0,01 / 0,85 / 1.500,00 | 0,00 / −0,01 / +0,01 / 0,00 |
| 18/10, total | 1.001,63 / 0,06 / 1,57 / 1.000,00 | 1.001,62 / 0,05 / 1,57 / 1.000,00 | −0,01 / −0,01 / 0,00 / 0,00 |
| 28/10, total | 423,26 / 1,11 / 0,15 / 422,00 | 423,26 / 1,11 / 0,15 / 422,00 | 0,00 / 0,00 / 0,00 / 0,00 |
| 04/11 | 1.500,00 / 0,00 / 0,00 / 1.500,00 | 1.500,00 / 0,00 / 0,00 / 1.500,00 | 0,00 / 0,00 / 0,00 / 0,00 |

Em 28/10, a divisão do extrato e do motor coincide lote a lote:

| Aporte de 29/09 | Bruto | IR | IOF | Líquido | Estado após o saque |
|---:|---:|---:|---:|---:|---|
| R$ 5,00 | R$ 5,06 | R$ 0,01 | R$ 0,00 | R$ 5,05 | Encerrado |
| R$ 30,00 | R$ 30,37 | R$ 0,08 | R$ 0,01 | R$ 30,28 | Encerrado |
| R$ 621,00 | R$ 387,83 | R$ 1,02 | R$ 0,14 | R$ 386,67 | Parcial |
| R$ 300,00 | — | — | — | — | Sem resgate |
| R$ 500,00 | — | — | — | — | Sem resgate |

Isso sustenta a seleção por custo efetivo do lote, mas não resolve por si só a política de centavos nas outras datas. Foram avaliadas políticas alternativas que arredondam o rendimento tributável e o principal de maneiras diferentes. Algumas fecham os totais diários do Croma, mas podem mudar quais lotes são escolhidos ou deslocar um centavo na referência histórica da Caixinha 2. Por esse motivo, nenhuma variante foi promovida a regra universal sem evidência equivalente nas outras caixinhas.

## O que falta para fechar a calibração

O PDF não apresenta o percentual CDI efetivamente contratado por caixinha/período. Também não traz saldo e lotes de abertura para todos os recortes, identificação inequívoca da aplicação originária de cada saque, nem horário confiável para operações do mesmo dia. Esses dados são especialmente importantes para Cartão, cartão mês que vem e reserva de emergência. Para NuCel e presente se vó, a taxa efetiva e/ou o pareamento dos resgates ainda limitam a comparação.

O suporte automatizado descreve regras de RDB e de Fundo Nu Reserva em termos gerais. Como os documentos examinados não classificam de forma suficiente todas as aplicações em cada modalidade, essa mensagem foi tratada como hipótese de trabalho, não como prova de taxa ou de política fiscal aplicada a todas as nove caixinhas.

## Validação do projeto

As correções de produto já presentes no projeto incluem o nome NuBox, recuperação de senha por e-mail HTTPS via Brevo, alteração autenticada de senha na página de Perfil, roteamento compatível com F5 no Render, inclusão de aportes do dia atual no saldo e correções visuais solicitadas para Perfil e Projeção.

Na verificação final desta versão, a suíte completa do backend passou (**170 testes**), `npm run build` concluiu e `npm run lint` concluiu. O build mostrou apenas o aviso de que o bundle principal ultrapassa 500 kB; não é erro de compilação.

## Arquivos relacionados

- `docs/alocacao-de-retiradas.md`: regra atual do alocador e divergências de centavos do Croma.
- `backend/tests/test_rdb_statement_reference.py`: regressão com os eventos da Turbo Nubank Croma.
- `backend/tests/test_pdf_caixinhas_reference.py`: controle histórico da Caixinha 2, que não deve ser regredido.
- `backend/tests/fixtures/cdi_2026_reference.json`: série de CDI diária usada nas simulações condicionais.
- `ilovepdf_merged.pdf`: documento recebido do usuário; a fonte não é copiada para o ZIP do projeto.