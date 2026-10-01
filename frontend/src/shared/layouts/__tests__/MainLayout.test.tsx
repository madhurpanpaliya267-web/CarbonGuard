import { describe, it, expect } from 'vitest'
import { screen } from '@testing-library/react'
import { render } from '@/test/page-test-utils'
import MainLayout from '../MainLayout'

describe('MainLayout', () => {
  it('renders the sidebar', () => {
    render(<MainLayout />)
    expect(screen.getByText('Carbon Guard')).toBeInTheDocument()
  })

  it('renders the header', () => {
    render(<MainLayout />)
    expect(screen.getByText('System Online')).toBeInTheDocument()
  })

  it('renders an Outlet container', () => {
    const { container } = render(<MainLayout />)
    expect(container.querySelector('main')).toBeInTheDocument()
  })
})
