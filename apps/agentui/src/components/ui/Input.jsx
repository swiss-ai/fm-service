import React from 'react'

export const Input = React.forwardRef(({ className = '', ...props }, ref) => (
  <input
    ref={ref}
    className={`w-full p-2 rounded-md border border-input bg-background focus:outline-none focus:ring-2 focus:ring-primary ${className}`}
    {...props}
  />
))
Input.displayName = 'Input' 