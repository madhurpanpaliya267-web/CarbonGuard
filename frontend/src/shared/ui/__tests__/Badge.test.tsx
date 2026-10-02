import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import Badge, { SeverityBadge, StatusBadge } from '../Badge'

describe('Badge', () => {
  it('renders children correctly', () => {
    render(<Badge>Test Badge</Badge>)
    expect(screen.getByText('Test Badge')).toBeInTheDocument()
  })

  it('applies muted variant by default', () => {
    render(<Badge>Default</Badge>)
    const badge = screen.getByText('Default')
    expect(badge.className).toContain('bg-muted/15')
  })

  it('applies correct variant classes', () => {
    render(<Badge variant="danger">Danger</Badge>)
    const badge = screen.getByText('Danger')
    expect(badge.className).toContain('bg-danger/15')
  })

  it('applies small size by default', () => {
    render(<Badge>Small</Badge>)
    const badge = screen.getByText('Small')
    expect(badge.className).toContain('text-[10px]')
  })

  it('applies medium size when specified', () => {
    render(<Badge size="md">Medium</Badge>)
    const badge = screen.getByText('Medium')
    expect(badge.className).toContain('text-xs')
  })
})

describe('SeverityBadge', () => {
  it('renders CRITICAL severity with danger variant', () => {
    render(<SeverityBadge severity="CRITICAL" />)
    const badge = screen.getByText('CRITICAL')
    expect(badge.className).toContain('bg-danger/15')
  })

  it('renders HIGH severity with danger variant', () => {
    render(<SeverityBadge severity="HIGH" />)
    const badge = screen.getByText('HIGH')
    expect(badge.className).toContain('bg-danger/15')
  })

  it('renders MEDIUM severity with warning variant', () => {
    render(<SeverityBadge severity="MEDIUM" />)
    const badge = screen.getByText('MEDIUM')
    expect(badge.className).toContain('bg-warning/15')
  })

  it('renders LOW severity with success variant', () => {
    render(<SeverityBadge severity="LOW" />)
    const badge = screen.getByText('LOW')
    expect(badge.className).toContain('bg-accent/15')
  })

  it('renders unknown severity with muted variant', () => {
    render(<SeverityBadge severity="UNKNOWN" />)
    const badge = screen.getByText('UNKNOWN')
    expect(badge.className).toContain('bg-muted/15')
  })
})

describe('StatusBadge', () => {
  it('renders detected status with warning variant', () => {
    render(<StatusBadge status="detected" />)
    const badge = screen.getByText('detected')
    expect(badge.className).toContain('bg-warning/15')
  })

  it('renders blocked status with success variant', () => {
    render(<StatusBadge status="blocked" />)
    const badge = screen.getByText('blocked')
    expect(badge.className).toContain('bg-accent/15')
  })

  it('renders active status with danger variant', () => {
    render(<StatusBadge status="active" />)
    const badge = screen.getByText('active')
    expect(badge.className).toContain('bg-danger/15')
  })

  it('renders unknown status with muted variant', () => {
    render(<StatusBadge status="unknown" />)
    const badge = screen.getByText('unknown')
    expect(badge.className).toContain('bg-muted/15')
  })
})
