import { describe, it, expect } from 'vitest'
import { screen } from '@testing-library/react'
import { render } from '@/test/page-test-utils'
import App from '../App'

describe('App routing', () => {
  it('renders the dashboard page on root route', () => {
    render(<App />)
    expect(screen.getByText('Dashboard')).toBeInTheDocument()
  })

  it('renders sidebar navigation', () => {
    render(<App />)
    expect(screen.getByText('Carbon Guard')).toBeInTheDocument()
    expect(screen.getByText('Security Monitor')).toBeInTheDocument()
    expect(screen.getByText('Settings')).toBeInTheDocument()
  })

  it('renders header', () => {
    render(<App />)
    expect(screen.getByText('System Online')).toBeInTheDocument()
  })
})
