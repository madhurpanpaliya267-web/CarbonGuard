import { describe, it, expect } from 'vitest'
import { screen } from '@testing-library/react'
import { render } from '@/test/page-test-utils'
import AttackSimulatorPage from '../components/AttackSimulatorPage'

describe('AttackSimulatorPage', () => {
  it('renders page title', () => {
    render(<AttackSimulatorPage />)
    expect(screen.getByText('Attack Simulator')).toBeInTheDocument()
  })

  it('renders simulation only badge', () => {
    render(<AttackSimulatorPage />)
    expect(screen.getByText('SIMULATION ONLY')).toBeInTheDocument()
  })

  it('renders educational purpose notice', () => {
    render(<AttackSimulatorPage />)
    expect(screen.getByText('EDUCATIONAL PURPOSE ONLY')).toBeInTheDocument()
  })

  it('renders all attack type cards', () => {
    render(<AttackSimulatorPage />)
    expect(screen.getByText('DDoS')).toBeInTheDocument()
    expect(screen.getByText('Brute Force')).toBeInTheDocument()
    expect(screen.getByText('Port Scan')).toBeInTheDocument()
    expect(screen.getByText('SQL Injection')).toBeInTheDocument()
    expect(screen.getByText('Malware')).toBeInTheDocument()
    expect(screen.getByText('Suspicious Login')).toBeInTheDocument()
  })

  it('renders simulate buttons for each attack type', () => {
    render(<AttackSimulatorPage />)
    const buttons = screen.getAllByText('Simulate')
    expect(buttons.length).toBe(6)
  })

  it('simulate buttons are not disabled initially', () => {
    render(<AttackSimulatorPage />)
    const buttons = screen.getAllByText('Simulate')
    buttons.forEach((btn) => {
      expect(btn).not.toBeDisabled()
    })
  })
})
