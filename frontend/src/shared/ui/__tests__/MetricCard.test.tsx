import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { Shield } from 'lucide-react'
import MetricCard from '../MetricCard'

describe('MetricCard', () => {
  it('renders title and value', () => {
    render(<MetricCard title="Threats" value={42} icon={Shield} />)
    expect(screen.getByText('Threats')).toBeInTheDocument()
    expect(screen.getByText('42')).toBeInTheDocument()
  })

  it('renders subtitle when provided', () => {
    render(<MetricCard title="Score" value="85" icon={Shield} subtitle="Overall" />)
    expect(screen.getByText('Overall')).toBeInTheDocument()
  })

  it('renders trend when provided', () => {
    render(<MetricCard title="Score" value="85" icon={Shield} trend={5.2} />)
    expect(screen.getByText('+5.2%')).toBeInTheDocument()
    expect(screen.getByText('vs yesterday')).toBeInTheDocument()
  })

  it('renders negative trend', () => {
    render(<MetricCard title="Score" value="85" icon={Shield} trend={-3.1} />)
    expect(screen.getByText('-3.1%')).toBeInTheDocument()
  })

  it('renders zero trend', () => {
    render(<MetricCard title="Score" value="85" icon={Shield} trend={0} />)
    expect(screen.getByText('0%')).toBeInTheDocument()
  })

  it('applies compact mode', () => {
    const { container } = render(<MetricCard title="Score" value="85" icon={Shield} compact />)
    const card = container.querySelector('.card')
    expect(card?.className).toContain('p-4')
  })

  it('applies default non-compact mode', () => {
    const { container } = render(<MetricCard title="Score" value="85" icon={Shield} />)
    const card = container.querySelector('.card')
    expect(card?.className).toContain('p-5')
  })

  it('applies color classes correctly', () => {
    const { container } = render(<MetricCard title="Test" value="1" icon={Shield} color="danger" />)
    expect(container.querySelector('.text-danger')).toBeInTheDocument()
  })
})
