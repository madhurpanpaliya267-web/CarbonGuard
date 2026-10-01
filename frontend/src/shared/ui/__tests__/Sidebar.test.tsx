import { describe, it, expect } from 'vitest'
import { screen, fireEvent } from '@testing-library/react'
import { render } from '@/test/page-test-utils'
import Sidebar from '../Sidebar'

describe('Sidebar', () => {
  it('renders the Carbon Guard title', () => {
    render(<Sidebar />)
    expect(screen.getByText('Carbon Guard')).toBeInTheDocument()
  })

  it('renders all navigation items', () => {
    render(<Sidebar />)
    expect(screen.getByText('Dashboard')).toBeInTheDocument()
    expect(screen.getByText('Security Monitor')).toBeInTheDocument()
    expect(screen.getByText('Attack Simulator')).toBeInTheDocument()
    expect(screen.getByText('Threats')).toBeInTheDocument()
    expect(screen.getByText('Carbon Monitor')).toBeInTheDocument()
    expect(screen.getByText('Energy Monitor')).toBeInTheDocument()
    expect(screen.getByText('Carbon Optimizer')).toBeInTheDocument()
    expect(screen.getByText('Renewable Energy')).toBeInTheDocument()
    expect(screen.getByText('AI Recommendations')).toBeInTheDocument()
    expect(screen.getByText('Analytics')).toBeInTheDocument()
    expect(screen.getByText('Event Logs')).toBeInTheDocument()
    expect(screen.getByText('System Health')).toBeInTheDocument()
    expect(screen.getByText('Settings')).toBeInTheDocument()
  })

  it('renders navigation links with correct paths', () => {
    render(<Sidebar />)
    const links = screen.getAllByRole('link')
    const dashboardLink = links.find(l => l.textContent?.includes('Dashboard'))
    expect(dashboardLink).toHaveAttribute('href', '/')

    const securityLink = links.find(l => l.textContent?.includes('Security Monitor'))
    expect(securityLink).toHaveAttribute('href', '/security')
  })

  it('renders version in footer', () => {
    render(<Sidebar />)
    expect(screen.getByText('v1.0.0 - Demo Mode')).toBeInTheDocument()
  })

  it('collapses when toggle button clicked', () => {
    const { container } = render(<Sidebar />)
    const toggleBtn = container.querySelector('button.hidden.lg\\:flex')
    expect(toggleBtn).toBeInTheDocument()
    fireEvent.click(toggleBtn!)
    expect(screen.queryByText('Carbon Guard')).not.toBeInTheDocument()
  })
})
