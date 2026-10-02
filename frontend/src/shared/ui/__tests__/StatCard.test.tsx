import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { Shield } from 'lucide-react'
import StatCard from '../StatCard'

describe('StatCard', () => {
  it('renders title and value', () => {
    render(<StatCard title="Total Threats" value={120} icon={Shield} />)
    expect(screen.getByText('Total Threats')).toBeInTheDocument()
    expect(screen.getByText('120')).toBeInTheDocument()
  })

  it('renders subtitle when provided', () => {
    render(<StatCard title="Score" value="90" icon={Shield} subtitle="Current" />)
    expect(screen.getByText('Current')).toBeInTheDocument()
  })

  it('renders positive trend', () => {
    render(<StatCard title="Score" value="90" icon={Shield} trend={{ value: 12, isPositive: true }} />)
    expect(screen.getByText('+12%')).toBeInTheDocument()
    expect(screen.getByText('vs last period')).toBeInTheDocument()
  })

  it('renders negative trend', () => {
    render(<StatCard title="Score" value="90" icon={Shield} trend={{ value: 5, isPositive: false }} />)
    expect(screen.getByText('5%')).toBeInTheDocument()
    expect(screen.getByText('vs last period')).toBeInTheDocument()
  })

  it('applies color classes', () => {
    render(<StatCard title="Test" value="1" icon={Shield} color="danger" />)
    expect(screen.getByText('1')).toHaveClass('text-danger')
  })

  it('defaults to primary color', () => {
    render(<StatCard title="Test" value="1" icon={Shield} />)
    expect(screen.getByText('1')).toHaveClass('text-accent')
  })
})
