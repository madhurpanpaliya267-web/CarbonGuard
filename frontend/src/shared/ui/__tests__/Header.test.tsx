import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import Header from '../Header'

describe('Header', () => {
  it('renders system online indicator', () => {
    render(<Header />)
    expect(screen.getByText('System Online')).toBeInTheDocument()
  })

  it('renders simulation mode badge', () => {
    render(<Header />)
    expect(screen.getByText('SIMULATION MODE')).toBeInTheDocument()
  })

  it('renders search input', () => {
    render(<Header />)
    const input = screen.getByPlaceholderText('Search events, threats...')
    expect(input).toBeInTheDocument()
  })

  it('renders connected status', () => {
    render(<Header />)
    expect(screen.getByText('Connected')).toBeInTheDocument()
  })

  it('renders user avatar with CG initials', () => {
    render(<Header />)
    expect(screen.getByText('CG')).toBeInTheDocument()
  })

  it('renders admin name', () => {
    render(<Header />)
    expect(screen.getByText('Admin')).toBeInTheDocument()
    expect(screen.getByText('Demo User')).toBeInTheDocument()
  })
})
