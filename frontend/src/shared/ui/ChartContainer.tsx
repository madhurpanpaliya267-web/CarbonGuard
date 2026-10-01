import { ReactNode } from 'react'

interface ChartContainerProps {
  title: string
  children: ReactNode
  className?: string
}

export default function ChartContainer({ title, children, className = '' }: ChartContainerProps) {
  return (
    <div className={`card p-6 ${className}`}>
      <h3 className="text-sm font-semibold text-text-primary mb-4">{title}</h3>
      {children}
    </div>
  )
}
