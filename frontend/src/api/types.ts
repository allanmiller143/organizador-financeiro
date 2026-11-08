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
}

export type DashboardAccount = {
  account_id: string
  name: string
  institution: string
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
  id: string
  name: string
  institution: string
  cdi_percent: string 
  opened_on: string 
  is_active: boolean
}

export type AccountInput = {
  name: string
  institution: string
  cdi_percent: string
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
}

export type TransactionInput = {
  kind: TransactionKind
  amount: string
  occurred_on: string
  note: string | null
}


export type AccountSummary = {
  account_id: string
  as_of: string
  gross_balance: string
  invested: string
  gross_yield: string
  tax_estimated: string
  net_balance: string
  tax_paid: string
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
}

export type MonthlyYields = {
  account_id: string
  as_of: string
  months: MonthlyYield[]
}

export type AccountUpdate = {
  name?: string
  institution?: string
  is_active?: boolean
}