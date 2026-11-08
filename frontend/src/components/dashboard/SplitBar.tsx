import { clampPercent } from './helpers'

type Segment = {
  percent: number
  className: string // a cor do pedaço, ex.: "bg-teal-500"
  title?: string
}

type SplitBarProps = {
  segments: Segment[]
  className?: string // para margens, ex.: "mt-5"
}

export function SplitBar({ segments, className = '' }: SplitBarProps) {
  return (
    <div className={`flex h-3 gap-0.5 overflow-hidden rounded-full bg-slate-100 ${className}`}>
      {segments.map((segment, index) => (
        <div
          key={index}
          className={segment.className}
          style={{ width: `${clampPercent(segment.percent)}%` }}
          title={segment.title}
        />
      ))}
    </div>
  )
}