export type User = {
  id: string
  name: string
  email: string
}

export type AuthResponse = {
  user: User
  access_token: string
  refresh_token: string
}

export type ApiFieldError = {
  field: string
  message: string
}

export type ApiErrorBody = {
  error: {
    code: string
    message: string
    details?: ApiFieldError[]
  }
}

export type DashboardTotals = {
  gross_balance: string 
  invested: string 
  gross_yield: string 
  tax_estimated: string 
  net_balance: string 
  tax_paid: string 
  deposited_total: string
  locked_balance: string
}

export type DashboardAccount = {
  account_id: string
  name: string
  institution: string
  goal_amount: string | null
  share_percent: string
  gross_balance: string
  net_balance: string
  gross_yield: string
}

export type Dashboard = {
  as_of: string | null 
  totals: DashboardTotals
  accounts: DashboardAccount[]
}

export type Account = {
  net_balance: string
  gross_balance: string
  account_id: string
  id: string
  name: string
  institution: string
  cdi_percent: string 
  goal_amount: string | null
  opened_on: string 
  is_active: boolean
}

export type AccountInput = {
  name: string
  institution: string
  cdi_percent: string
  goal_amount: string | null
  opened_on: string
}

export type TransactionKind = 'DEPOSIT' | 'WITHDRAWAL' // aporte | retirada

export type Transaction = {
  id: string
  account_id: string
  kind: TransactionKind
  amount: string // texto, ex.: "1000.00"
  occurred_on: string // "AAAA-MM-DD"
  note: string | null
  cdi_percent: string
  term_months: number
  locked: boolean
  sort_order: number | null
}

export type TransactionInput = {
  kind: TransactionKind
  amount: string
  occurred_on: string
  note: string | null
  cdi_percent: string
  term_months: number
  locked: boolean
}

export type TransactionUpdate = Pick<
  TransactionInput,
  'amount' | 'occurred_on' | 'note' | 'cdi_percent' | 'term_months' | 'locked'
>


export type AccountSummary = {
  account_id: string
  as_of: string
  gross_balance: string
  invested: string
  gross_yield: string
  tax_estimated: string
  net_balance: string
  tax_paid: string
  deposited_total: string
  locked_balance: string
  iof_paid: string // parte de tax_paid que foi IOF
  iof_estimated: string // parte de tax_estimated que seria IOF
}

// O que enviamos para simular. Dinheiro como texto, como sempre.
export type SimulationInput = {
  initial_amount: string
  monthly_deposit: string
  monthly_withdrawal: string
  withdrawal_start_month: number
  horizon_months: number
  expected_cdi_annual: string
  cdi_percent: string
}

// Um mês da projeção (um ponto do gráfico).
export type SimulationPoint = {
  month: string // "2027-03"
  gross_balance: string
  net_balance: string
  invested: string
}

export type SimulationSummary = {
  gross_balance: string
  net_balance: string
  invested: string
  gross_yield: string
  tax_estimated: string
  tax_paid: string
  withdrawn: string
}

export type Simulation = {
  summary: SimulationSummary
  depleted_month: number | null // mês em que o dinheiro acabou (null se não acabou)
  months: SimulationPoint[]
}

// O rendimento de um mês (uma barra do gráfico).
export type MonthlyYield = {
  month: string // "2025-01"
  yield_amount: string // "40.60"
  net_yield_amount: string
  gross_balance: string
  net_balance: string
  invested: string // valor aplicado no fim do mês (sem rendimento nem reaplicações)
  reapplications: Reapplication[]
}

export type Reapplication = {
  occurred_on: string
  gross_yield: string
  tax_paid: string
  amount: string
  source_transaction_id: string | null
}

export type MonthlyYields = {
  account_id: string
  as_of: string
  months: MonthlyYield[]
}

// Um resgate que saiu de um depósito (lote), com o imposto cobrado nele.
export type DepositWithdrawal = {
  occurred_on: string
  amount: string
  gross_yield: string
  income_tax: string
  iof: string
  net_amount: string
}

export type DepositDetail = {
  deposited_on: string
  product: string // "RDB Resgate Imediato" ou "RDB Planejado"
  applied_amount: string
  principal_remaining: string
  partial_withdrawals: string
  gross_yield: string
  income_tax: string
  iof: string
  iof_estimated: string
  withdrawals: DepositWithdrawal[]
  gross_balance: string
  net_balance: string
  maturity_on: string
  locked: boolean
  term_months: number
  cdi_percent: string
}

export type DepositDetails = {
  account_id: string
  as_of: string
  deposits: DepositDetail[]
}

export type AccountUpdate = {
  name?: string
  institution?: string
  is_active?: boolean
  goal_amount?: string | null
}

export type GoalForecast = {
  status: 'reached' | 'no_balance' | 'no_growth' | 'projected'
  months: number | null
  balance: string
  goal_amount: string
  projected_date: string | null
  assumption: string
}
