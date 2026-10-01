import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import PageHeader from '../PageHeader'

describe('PageHeader', () => {
  it('renders title', () => {
    render(<PageHeader title="Dashboard" />)
    expect(screen.getByRole('heading', { level: 1 })).toHaveTextContent('Dashboard')
  })

  it('renders subtitle when provided', () => {
    render(<PageHeader title="Dashboard" subtitle="Overview" />)
    expect(screen.getByText('Overview')).toBeInTheDocument()
  })

  it('does not render subtitle when not provided', () => {
    render(<PageHeader title="Dashboard" />)
    expect(screen.queryByText('Overview')).not.toBeInTheDocument()
  })

  it('renders actions when provided', () => {
    render(<PageHeader title="Test" actions={<button>Action</button>} />)
    expect(screen.getByRole('button', { name: 'Action' })).toBeInTheDocument()
  })

  it('renders badge when provided', () => {
    render(<PageHeader title="Test" badge={<span>Badge</span>} />)
    expect(screen.getByText('Badge')).toBeInTheDocument()
  })

  it('renders h1 element for title', () => {
    render(<PageHeader title="Test" />)
    const heading = screen.getByRole('heading', { level: 1 })
    expect(heading).toBeInTheDocument()
  })
})
