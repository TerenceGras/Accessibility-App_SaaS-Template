import React from 'react'

const LoadingSpinner = ({ className = "h-32 w-32" }) => {
  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex items-center justify-center">
      <div className={`animate-spin rounded-full border-b-2 border-blue-600 ${className}`}></div>
    </div>
  )
}

export default LoadingSpinner
