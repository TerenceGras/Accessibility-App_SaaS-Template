import React, { useState, useEffect } from 'react'
import { 
  ChartBarIcon,
  GlobeAltIcon,
  DocumentTextIcon,
  CalendarIcon
} from '@heroicons/react/24/outline'
import { useTranslation } from '../../hooks/useTranslation'
import logger from '../../utils/logger'

const UsageChart = ({ userId, apiUrl, isDarkMode }) => {
  const { t } = useTranslation()
  const [loading, setLoading] = useState(true)
  const [chartData, setChartData] = useState([])
  const [stats, setStats] = useState(null)
  
  useEffect(() => {
    if (userId) {
      fetchUsageData()
    }
  }, [userId])

  const fetchUsageData = async () => {
    try {
      setLoading(true)
      // Get auth from firebase config
      const { auth } = await import('../../config/firebase')
      const token = await auth.currentUser?.getIdToken()
      
      if (!token) {
        logger.error('No auth token available')
        setChartData([])
        setLoading(false)
        return
      }
      
      // Fetch usage history (daily summaries)
      try {
        const historyResponse = await fetch(`${apiUrl}/usage-history?limit=30`, {
          headers: { 'Authorization': `Bearer ${token}` }
        })
        
        if (historyResponse.ok) {
          const historyData = await historyResponse.json()
          const history = historyData.history || []
          logger.log(`Fetched ${history.length} usage history records`)
          
          // Process data for chart
          processChartData(history)
        } else {
          logger.error('Failed to fetch usage history:', historyResponse.status, historyResponse.statusText)
          setChartData([])
        }
      } catch (historyError) {
        logger.error('Error fetching usage history:', historyError)
        setChartData([])
      }
      
      // Fetch stats
      try {
        const statsResponse = await fetch(`${apiUrl}/usage-stats`, {
          headers: { 'Authorization': `Bearer ${token}` }
        })
        
        if (statsResponse.ok) {
          const statsData = await statsResponse.json()
          logger.log('Fetched usage stats:', statsData.stats)
          setStats(statsData.stats)
        } else {
          logger.error('Failed to fetch usage stats:', statsResponse.status, statsResponse.statusText)
        }
      } catch (statsError) {
        logger.error('Error fetching usage stats:', statsError)
      }
    } catch (error) {
      logger.error('Error in fetchUsageData:', error)
      setChartData([])
    } finally {
      setLoading(false)
    }
  }

  const processChartData = (history) => {
    // Get current month start and end
    const now = new Date()
    const monthStart = new Date(now.getFullYear(), now.getMonth(), 1)
    const monthEnd = new Date(now.getFullYear(), now.getMonth() + 1, 0)
    
    // Create daily buckets for the entire month
    const dailyData = {}
    for (let d = 1; d <= monthEnd.getDate(); d++) {
      const dateKey = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}-${String(d).padStart(2, '0')}`
      dailyData[dateKey] = { webScans: 0, pdfScans: 0, date: d }
    }
    
    // Process daily summary records (new format from credit_usage_daily_summary)
    history.forEach(entry => {
      try {
        // New format: entry has date (YYYY-MM-DD), total_web_credits_used, total_pdf_credits_used
        if (entry.date) {
          const entryDate = new Date(entry.date + 'T00:00:00')
          if (entryDate >= monthStart && entryDate <= monthEnd) {
            const dateKey = entry.date
            
            if (dailyData[dateKey]) {
              dailyData[dateKey].webScans += entry.total_web_credits_used || 0
              dailyData[dateKey].pdfScans += entry.total_pdf_credits_used || 0
            }
          }
        }
        // Legacy format support (action-based per-transaction records)
        else if (entry.action === 'deduction' && entry.created_at) {
          const entryDate = new Date(entry.created_at)
          if (entryDate >= monthStart && entryDate <= monthEnd) {
            const dateKey = `${entryDate.getFullYear()}-${String(entryDate.getMonth() + 1).padStart(2, '0')}-${String(entryDate.getDate()).padStart(2, '0')}`
            
            if (dailyData[dateKey]) {
              if (entry.credit_type === 'web_scan') {
                dailyData[dateKey].webScans += Math.abs(entry.web_amount || 0)
              } else if (entry.credit_type === 'pdf_scan') {
                dailyData[dateKey].pdfScans += Math.abs(entry.pdf_amount || 0)
              }
            }
          }
        }
      } catch (error) {
        logger.error('Error processing entry:', error)
      }
    })
    
    // Convert to array and sort by date
    const chartArray = Object.values(dailyData).sort((a, b) => a.date - b.date)
    setChartData(chartArray)
  }

  const getMaxValue = () => {
    if (chartData.length === 0) return 10
    const maxWeb = Math.max(...chartData.map(d => d.webScans))
    const maxPdf = Math.max(...chartData.map(d => d.pdfScans))
    return Math.max(maxWeb, maxPdf, 10)
  }

  const formatDate = (day) => {
    const now = new Date()
    return new Date(now.getFullYear(), now.getMonth(), day).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric'
    })
  }

  if (loading) {
    return (
      <div className={`${
        isDarkMode ? 'bg-gray-800' : 'bg-white'
      } rounded-lg shadow-lg border ${
        isDarkMode ? 'border-gray-700' : 'border-gray-200'
      } p-6`}>
        <div className="animate-pulse space-y-4">
          <div className={`h-6 ${isDarkMode ? 'bg-gray-700' : 'bg-gray-200'} rounded w-1/3`}></div>
          <div className={`h-64 ${isDarkMode ? 'bg-gray-700' : 'bg-gray-200'} rounded`}></div>
        </div>
      </div>
    )
  }

  const maxValue = getMaxValue()
  const now = new Date()
  const monthName = now.toLocaleDateString('en-US', { month: 'long', year: 'numeric' })

  return (
    <div className={`${
      isDarkMode ? 'bg-gray-800' : 'bg-white'
    } rounded-lg shadow-lg border ${
      isDarkMode ? 'border-gray-700' : 'border-gray-200'
    }`}>
      {/* Header */}
      <div className={`px-6 py-4 border-b ${
        isDarkMode ? 'border-gray-700' : 'border-gray-200'
      }`}>
        <div className="flex items-center justify-between">
          <div className="flex items-center">
            <ChartBarIcon className={`h-6 w-6 mr-2 ${
              isDarkMode ? 'text-gray-400' : 'text-gray-500'
            }`} />
            <h3 className={`text-lg font-semibold ${
              isDarkMode ? 'text-white' : 'text-gray-900'
            }`}>
              Credit Usage - {monthName}
            </h3>
          </div>
          <CalendarIcon className={`h-5 w-5 ${
            isDarkMode ? 'text-gray-400' : 'text-gray-500'
          }`} />
        </div>
      </div>

      {/* Stats Summary */}
      {stats && (
        <div className={`px-6 py-4 border-b ${
          isDarkMode ? 'border-gray-700' : 'border-gray-200'
        } grid grid-cols-2 gap-4`}>
          <div className="flex items-center">
            <div className="w-3 h-3 rounded-full bg-green-500 mr-2"></div>
            <div>
              <p className={`text-xs ${isDarkMode ? 'text-gray-400' : 'text-gray-500'}`}>
                {t('profile.usage.webScansThisMonth')}
              </p>
              <p className={`text-lg font-bold ${isDarkMode ? 'text-white' : 'text-gray-900'}`}>
                {stats.current_month?.web_scans || 0}
              </p>
            </div>
          </div>
          <div className="flex items-center">
            <div className="w-3 h-3 rounded-full bg-blue-500 mr-2"></div>
            <div>
              <p className={`text-xs ${isDarkMode ? 'text-gray-400' : 'text-gray-500'}`}>
                {t('profile.usage.pdfScansThisMonth')}
              </p>
              <p className={`text-lg font-bold ${isDarkMode ? 'text-white' : 'text-gray-900'}`}>
                {stats.current_month?.pdf_scans || 0}
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Chart */}
      <div className="p-6">
        {chartData.length === 0 ? (
          <div className="text-center py-12">
            <ChartBarIcon className={`h-16 w-16 mx-auto mb-3 ${
              isDarkMode ? 'text-gray-600' : 'text-gray-300'
            }`} />
            <p className={`${isDarkMode ? 'text-gray-400' : 'text-gray-500'}`}>
              No usage data for this month yet
            </p>
          </div>
        ) : (
          <div className="relative h-64">
            {/* Y-axis labels */}
            <div className="absolute left-0 top-0 h-full flex flex-col justify-between text-xs"
                 style={{ width: '40px' }}>
              <span className={isDarkMode ? 'text-gray-400' : 'text-gray-500'}>{maxValue}</span>
              <span className={isDarkMode ? 'text-gray-400' : 'text-gray-500'}>{Math.floor(maxValue * 0.75)}</span>
              <span className={isDarkMode ? 'text-gray-400' : 'text-gray-500'}>{Math.floor(maxValue * 0.5)}</span>
              <span className={isDarkMode ? 'text-gray-400' : 'text-gray-500'}>{Math.floor(maxValue * 0.25)}</span>
              <span className={isDarkMode ? 'text-gray-400' : 'text-gray-500'}>0</span>
            </div>

            {/* Chart area */}
            <div className="ml-12 h-full relative">
              {/* Grid lines */}
              <svg className="absolute inset-0 w-full h-full" style={{ zIndex: 0 }}>
                <line x1="0" y1="0%" x2="100%" y2="0%" 
                      stroke={isDarkMode ? '#374151' : '#E5E7EB'} strokeWidth="1" />
                <line x1="0" y1="25%" x2="100%" y2="25%" 
                      stroke={isDarkMode ? '#374151' : '#E5E7EB'} strokeWidth="1" strokeDasharray="2,2" />
                <line x1="0" y1="50%" x2="100%" y2="50%" 
                      stroke={isDarkMode ? '#374151' : '#E5E7EB'} strokeWidth="1" strokeDasharray="2,2" />
                <line x1="0" y1="75%" x2="100%" y2="75%" 
                      stroke={isDarkMode ? '#374151' : '#E5E7EB'} strokeWidth="1" strokeDasharray="2,2" />
                <line x1="0" y1="100%" x2="100%" y2="100%" 
                      stroke={isDarkMode ? '#374151' : '#E5E7EB'} strokeWidth="1" />
              </svg>

              {/* Line chart */}
              <svg className="absolute inset-0 w-full h-full" style={{ zIndex: 1 }}>
                {/* Web scans line (green) */}
                {chartData.length > 1 && maxValue > 0 && (
                  <polyline
                    fill="none"
                    stroke="#10B981"
                    strokeWidth="2"
                    points={chartData.map((d, i) => {
                      const x = ((i / (chartData.length - 1)) * 100).toFixed(2)
                      const y = (100 - ((d.webScans / maxValue) * 100)).toFixed(2)
                      return `${x},${y}`
                    }).join(' ')}
                  />
                )}
                
                {/* PDF scans line (blue) */}
                {chartData.length > 1 && maxValue > 0 && (
                  <polyline
                    fill="none"
                    stroke="#3B82F6"
                    strokeWidth="2"
                    points={chartData.map((d, i) => {
                      const x = ((i / (chartData.length - 1)) * 100).toFixed(2)
                      const y = (100 - ((d.pdfScans / maxValue) * 100)).toFixed(2)
                      return `${x},${y}`
                    }).join(' ')}
                  />
                )}

                {/* Data points for web scans */}
                {chartData.map((d, i) => {
                  if (d.webScans === 0 || maxValue === 0) return null
                  const x = chartData.length > 1 ? ((i / (chartData.length - 1)) * 100).toFixed(2) : 50
                  const y = (100 - ((d.webScans / maxValue) * 100)).toFixed(2)
                  return (
                    <circle
                      key={`web-${i}`}
                      cx={`${x}%`}
                      cy={`${y}%`}
                      r="3"
                      fill="#10B981"
                    >
                      <title>{formatDate(d.date)}: {d.webScans} web scans</title>
                    </circle>
                  )
                })}

                {/* Data points for PDF scans */}
                {chartData.map((d, i) => {
                  if (d.pdfScans === 0 || maxValue === 0) return null
                  const x = chartData.length > 1 ? ((i / (chartData.length - 1)) * 100).toFixed(2) : 50
                  const y = (100 - ((d.pdfScans / maxValue) * 100)).toFixed(2)
                  return (
                    <circle
                      key={`pdf-${i}`}
                      cx={`${x}%`}
                      cy={`${y}%`}
                      r="3"
                      fill="#3B82F6"
                    >
                      <title>{formatDate(d.date)}: {d.pdfScans} PDF scans</title>
                    </circle>
                  )
                })}
              </svg>
            </div>

            {/* X-axis labels (show every 5 days) */}
            <div className="ml-12 mt-2 flex justify-between text-xs">
              {chartData.filter((_, i) => i % 5 === 0).map((d, i) => (
                <span key={i} className={isDarkMode ? 'text-gray-400' : 'text-gray-500'}>
                  {d.date}
                </span>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Legend */}
      <div className={`px-6 py-4 border-t ${
        isDarkMode ? 'border-gray-700' : 'border-gray-200'
      } flex items-center justify-center space-x-6`}>
        <div className="flex items-center">
          <div className="w-3 h-3 rounded-full bg-green-500 mr-2"></div>
          <span className={`text-sm ${isDarkMode ? 'text-gray-300' : 'text-gray-700'}`}>
            {t('profile.usage.webScans')}
          </span>
        </div>
        <div className="flex items-center">
          <div className="w-3 h-3 rounded-full bg-blue-500 mr-2"></div>
          <span className={`text-sm ${isDarkMode ? 'text-gray-300' : 'text-gray-700'}`}>
            {t('profile.usage.pdfScans')}
          </span>
        </div>
      </div>
    </div>
  )
}

export default UsageChart
