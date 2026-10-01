import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import StatusIndicator from '../StatusIndicator'

describe('StatusIndicator', () => {
  it('renders online status', () => {
    render(<StatusIndicator status="online" label="API" />)
    expect(screen.getByText('API')).toBeInTheDocument()
    expect(screen.getByText('Online')).toBeInTheDocument()
  })

  it('renders offline status', () => {
    render(<StatusIndicator status="offline" label="DB" />)
    expect(screen.getByText('DB')).toBeInTheDocument()
    expect(screen.getByText('Offline')).toBeInTheDocument()
  })

  it('renders degraded status', () => {
    render(<StatusIndicator status="degraded" label="Cache" />)
    expect(screen.getByText('Cache')).toBeInTheDocument()
    expect(screen.getByText('Degraded')).toBeInTheDocument()
  })

  it('applies correct color for online', () => {
    const { container } = render(<StatusIndicator status="online" label="Svc" />)
    const dot = container.querySelector('.bg-success')
    expect(dot).toBeInTheDocument()
  })

  it('applies correct color for offline', () => {
    const { container } = render(<StatusIndicator status="offline" label="Svc" />)
    const dot = container.querySelector('.bg-danger')
    expect(dot).toBeInTheDocument()
  })

  it('applies correct color for degraded', () => {
    const { container } = render(<StatusIndicator status="degraded" label="Svc" />)
    const dot = container.querySelector('.bg-warning')
    expect(dot).toBeInTheDocument()
  })
})
