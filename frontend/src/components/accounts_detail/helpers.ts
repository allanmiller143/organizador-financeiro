// Rendimento sobre o que foi aportado, como texto (evita dividir por zero).
export function yieldPercentLabel(invested: string, grossYield: string): string {
  const base = Number(invested)
  const percent = base > 0 ? (Number(grossYield) / base) * 100 : 0
  return `${percent.toFixed(2).replace('.', ',')}%`
}