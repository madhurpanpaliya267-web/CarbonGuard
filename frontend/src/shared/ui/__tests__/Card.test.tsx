import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { Card, CardHeader, CardTitle, CardContent } from '../Card'

describe('Card', () => {
  it('renders children correctly', () => {
    render(<Card>Card content</Card>)
    expect(screen.getByText('Card content')).toBeInTheDocument()
  })

  it('applies default card classes', () => {
    render(<Card>Test</Card>)
    const card = screen.getByText('Test')
    expect(card.className).toContain('card')
    expect(card.className).toContain('p-6')
  })

  it('applies custom className', () => {
    render(<Card className="custom-class">Test</Card>)
    const card = screen.getByText('Test')
    expect(card.className).toContain('custom-class')
  })
})

describe('CardHeader', () => {
  it('renders children correctly', () => {
    render(<CardHeader>Header content</CardHeader>)
    expect(screen.getByText('Header content')).toBeInTheDocument()
  })

  it('applies default margin classes', () => {
    render(<CardHeader>Test</CardHeader>)
    const header = screen.getByText('Test')
    expect(header.className).toContain('mb-4')
  })
})

describe('CardTitle', () => {
  it('renders children correctly', () => {
    render(<CardTitle>Title</CardTitle>)
    expect(screen.getByText('Title')).toBeInTheDocument()
  })

  it('renders as h3 element', () => {
    render(<CardTitle>Title</CardTitle>)
    const title = screen.getByRole('heading', { level: 3 })
    expect(title).toBeInTheDocument()
    expect(title).toHaveTextContent('Title')
  })

  it('applies correct styling classes', () => {
    render(<CardTitle>Title</CardTitle>)
    const title = screen.getByRole('heading', { level: 3 })
    expect(title.className).toContain('text-lg')
    expect(title.className).toContain('font-semibold')
  })
})

describe('CardContent', () => {
  it('renders children correctly', () => {
    render(<CardContent>Content here</CardContent>)
    expect(screen.getByText('Content here')).toBeInTheDocument()
  })
})
