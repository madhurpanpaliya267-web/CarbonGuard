import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import DataTable from '../DataTable'

interface TestRow extends Record<string, unknown> {
  name: string
  value: number
}

const columns = [
  { key: 'name', header: 'Name' },
  { key: 'value', header: 'Value' },
]

describe('DataTable', () => {
  it('renders table headers when data exists', () => {
    const data: TestRow[] = [{ name: 'Test', value: 1 }]
    render(<DataTable data={data} columns={columns} />)
    expect(screen.getByText('Name')).toBeInTheDocument()
    expect(screen.getByText('Value')).toBeInTheDocument()
  })

  it('renders data rows', () => {
    const data: TestRow[] = [
      { name: 'Alice', value: 10 },
      { name: 'Bob', value: 20 },
    ]
    render(<DataTable data={data} columns={columns} />)
    expect(screen.getByText('Alice')).toBeInTheDocument()
    expect(screen.getByText('Bob')).toBeInTheDocument()
    expect(screen.getByText('10')).toBeInTheDocument()
    expect(screen.getByText('20')).toBeInTheDocument()
  })

  it('shows empty message when no data', () => {
    render(<DataTable data={[]} columns={columns} emptyMessage="No items" />)
    expect(screen.getByText('No items')).toBeInTheDocument()
  })

  it('shows default empty message', () => {
    render(<DataTable data={[]} columns={columns} />)
    expect(screen.getByText('No data available')).toBeInTheDocument()
  })

  it('renders with custom render function', () => {
    const customColumns = [
      { key: 'name', header: 'Name', render: (item: TestRow) => <strong>{item.name}</strong> },
    ]
    const data: TestRow[] = [{ name: 'Test', value: 1 }]
    render(<DataTable data={data} columns={customColumns} />)
    const strong = screen.getByText('Test')
    expect(strong.tagName).toBe('STRONG')
  })

  it('renders correct number of rows', () => {
    const data: TestRow[] = [
      { name: 'A', value: 1 },
      { name: 'B', value: 2 },
      { name: 'C', value: 3 },
    ]
    const { container } = render(<DataTable data={data} columns={columns} />)
    const rows = container.querySelectorAll('tbody tr')
    expect(rows.length).toBe(3)
  })
})
