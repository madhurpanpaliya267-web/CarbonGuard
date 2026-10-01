import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import ChartContainer from '../ChartContainer'

describe('ChartContainer', () => {
  it('renders title', () => {
    render(<ChartContainer title="Threat Activity">Content</ChartContainer>)
    expect(screen.getByText('Threat Activity')).toBeInTheDocument()
  })

  it('renders children', () => {
    render(<ChartContainer title="Chart">Chart body</ChartContainer>)
    expect(screen.getByText('Chart body')).toBeInTheDocument()
  })

  it('applies card class', () => {
    const { container } = render(<ChartContainer title="T">X</ChartContainer>)
    const card = container.querySelector('.card')
    expect(card).toBeInTheDocument()
  })

  it('applies custom className', () => {
    const { container } = render(<ChartContainer title="T" className="custom">X</ChartContainer>)
    expect(container.firstChild).toHaveClass('custom')
  })
})
