import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import ThreatLevel from '../ThreatLevel'

describe('ThreatLevel', () => {
  it('renders CRITICAL level', () => {
    render(<ThreatLevel level="CRITICAL" />)
    expect(screen.getByText('CRITICAL')).toBeInTheDocument()
  })

  it('renders HIGH level', () => {
    render(<ThreatLevel level="HIGH" />)
    expect(screen.getByText('HIGH')).toBeInTheDocument()
  })

  it('renders MEDIUM level', () => {
    render(<ThreatLevel level="MEDIUM" />)
    expect(screen.getByText('MEDIUM')).toBeInTheDocument()
  })

  it('renders LOW level', () => {
    render(<ThreatLevel level="LOW" />)
    expect(screen.getByText('LOW')).toBeInTheDocument()
  })

  it('hides label when showLabel is false', () => {
    render(<ThreatLevel level="CRITICAL" showLabel={false} />)
    expect(screen.queryByText('CRITICAL')).not.toBeInTheDocument()
  })

  it('applies small size classes', () => {
    const { container } = render(<ThreatLevel level="HIGH" size="sm" />)
    expect(container.querySelector('.text-\\[10px\\]')).toBeInTheDocument()
  })

  it('applies large size classes', () => {
    const { container } = render(<ThreatLevel level="LOW" size="lg" />)
    expect(container.querySelector('.text-sm')).toBeInTheDocument()
  })

  it('renders animated dot', () => {
    const { container } = render(<ThreatLevel level="MEDIUM" />)
    expect(container.querySelector('.animate-pulse')).toBeInTheDocument()
  })
})
