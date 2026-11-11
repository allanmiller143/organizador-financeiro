# TODO NuBox

- [x] **Sincronização diária do CDI:** ao carregar o dashboard, tentar consultar o CDI do BCB no máximo uma vez por dia; permitir atualização manual; mostrar resultado e data disponível sem erro quando não houver novo dado publicado; manter o saldo principal visível e não presumir juros em dias sem taxa.
- [x] **Vencimento e reaplicação independentes do CDI do dia:** um aporte cujo prazo vence deve ser liquidado/reinvestido na data de vencimento mesmo que o BCB ainda não tenha publicado a taxa daquele dia; só o rendimento depende da taxa CDI disponível.
- [x] **Aviso de simulação:** exibir no app um banner curto e visível esclarecendo que o NuBox simula/aproxima as Caixinhas do Nubank e que valores reais podem divergir.
- [x] **Meta de valor por caixinha:** permitir definir e editar uma meta opcional na criação/edição; apresentar no dashboard o progresso e percentual da meta; incluir botão simples com ícone para estimar em quanto tempo o saldo bruto atual alcançaria a meta se o dinheiro apenas rendesse, sem novos aportes ou retiradas, usando o percentual CDI configurado e o histórico CDI recente como hipótese explícita.
- [x] **Migração e compatibilidade:** persistir a meta por caixinha com migration compatível com dados existentes; contas anteriores devem receber meta vazia.
- [x] **Verificações finais:** suíte backend e build/lint do frontend concluídos; pacote atualizado preparado para entrega.
