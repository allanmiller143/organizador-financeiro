import { Plus } from 'lucide-react'

import { InsightCard } from '../dashboard/InsightCard'
import { TransactionForm } from '../TransactionForm'

type NewTransactionCardProps = {
  accountId: string
  openedOn: string
}

export function NewTransactionCard({ accountId, openedOn }: NewTransactionCardProps) {
  return (
    <InsightCard
      icon={Plus}
      title="Novo lançamento"
      subtitle="Registre um aporte ou uma retirada"
    >
      <div className="mt-5">
        <TransactionForm accountId={accountId} openedOn={openedOn} />
      </div>
    </InsightCard>
  )
}