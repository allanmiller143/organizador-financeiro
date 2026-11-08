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