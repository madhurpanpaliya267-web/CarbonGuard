import { ButtonHTMLAttributes, ReactNode } from 'react'

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  children: ReactNode
  variant?: 'primary' | 'secondary' | 'danger' | 'success' | 'ghost'
  size?: 'sm' | 'md' | 'lg'
}

const variantClasses = {
  primary: 'bg-accent text-background hover:bg-accent-light font-medium shadow-glow-sm hover:shadow-glow',
  secondary: 'bg-card border border-border text-text-primary hover:bg-card-hover hover:border-border-hover',
  danger: 'bg-danger/15 text-danger border border-danger/20 hover:bg-danger/25',
  success: 'bg-accent/15 text-accent border border-accent/20 hover:bg-accent/25',
  ghost: 'text-muted hover:text-text-primary hover:bg-card',
}

const sizeClasses = {
  sm: 'px-3 py-1.5 text-xs',
  md: 'px-4 py-2 text-sm',
  lg: 'px-6 py-3 text-base',
}

export default function Button({
  children,
  variant = 'primary',
  size = 'md',
  className = '',
  ...props
}: ButtonProps) {
  return (
    <button
      className={`inline-flex items-center justify-center gap-2 font-medium rounded-md transition-all duration-150 disabled:opacity-50 disabled:cursor-not-allowed ${variantClasses[variant]} ${sizeClasses[size]} ${className}`}
      {...props}
    >
      {children}
    </button>
  )
}
