const REFRESH_KEY = 'organizador.refresh_token'

let accessToken: string | null = null

export const tokens = {
  getAccess: () => accessToken,
  setAccess: (token: string | null) => {
    accessToken = token
  },
  getRefresh: () => localStorage.getItem(REFRESH_KEY),
  setRefresh: (token: string) => localStorage.setItem(REFRESH_KEY, token),
  clear: () => {
    accessToken = null
    localStorage.removeItem(REFRESH_KEY)
  },
}