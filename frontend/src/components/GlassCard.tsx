import type { HTMLAttributes } from 'react'

export function GlassCard({ className = '', ...props }: HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={`rounded-3xl border border-white/20 bg-white/10 p-6 shadow-xl backdrop-blur-md ${className}`}
      {...props}
    />
  )
}