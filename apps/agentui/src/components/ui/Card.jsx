import React from 'react'

export function Card({ className = '', children, ...props }) {
  return (
    <div className={`bg-white dark:bg-card rounded-lg p-4 ${className}`} {...props}>
      {children}
    </div>
  )
} 