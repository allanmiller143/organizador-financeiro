import { useQuery } from '@tanstack/react-query'

type Health = { status: string }

async function fetchHealth(): Promise<Health> {
  const response = await fetch('/api/health')
  if (!response.ok) {
    throw new Error('Falha ao falar com a API')
  }
  return response.json()
}

export default function App() {
  const { data, isPending, isError } = useQuery({
    queryKey: ['health'],
    queryFn: fetchHealth,
  })

  return (
    <main className="grid min-h-screen place-items-center bg-slate-50 text-slate-900">
      <div className="rounded-2xl bg-white p-8 text-center shadow-sm ring-1 ring-slate-200">
        <h1 className="text-2xl font-semibold">Organizador Financeiro</h1>
        <p className="mt-3 text-sm text-slate-600">
          {isPending && 'Conectando à API...'}
          {isError && 'API fora do ar. O backend está rodando?'}
          {data && `API respondeu: ${data.status}`}
        </p>
      </div>
    </main>
  )
}