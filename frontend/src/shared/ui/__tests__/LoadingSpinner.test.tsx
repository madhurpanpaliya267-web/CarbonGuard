import { describe, it, expect } from 'vitest'
import { render } from '@testing-library/react'
import LoadingSpinner from '../LoadingSpinner'

describe('LoadingSpinner', () => {
  it('renders medium size by default', () => {
    const { container } = render(<LoadingSpinner />)
    const spinner = container.querySelector('.animate-spin')
    expect(spinner).toBeInTheDocument()
    expect(spinner?.className).toContain('w-8')
    expect(spinner?.className).toContain('h-8')
  })

  it('renders small size', () => {
    const { container } = render(<LoadingSpinner size="sm" />)
    const spinner = container.querySelector('.animate-spin')
    expect(spinner?.className).toContain('w-4')
    expect(spinner?.className).toContain('h-4')
  })

  it('renders large size', () => {
    const { container } = render(<LoadingSpinner size="lg" />)
    const spinner = container.querySelector('.animate-spin')
    expect(spinner?.className).toContain('w-12')
    expect(spinner?.className).toContain('h-12')
  })

  it('applies spinning animation', () => {
    const { container } = render(<LoadingSpinner />)
    const spinner = container.querySelector('.animate-spin')
    expect(spinner).toBeInTheDocument()
  })
})
