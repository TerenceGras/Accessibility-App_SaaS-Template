import React, { useState, useEffect } from 'react'
import { 
  ChartBarIcon,
  CalendarIcon
} from '@heroicons/react/24/outline'
import { useTranslation } from '../../hooks/useTranslation'
import logger from '../../utils/logger'

const UsageSeparateCharts = ({ userId, apiUrl, isDarkMode }) => {
  const { t } = useTranslation()
  const [loading, setLoading] = useState(true)
  const [webChartData, setWebChartData] = useState([])
  const [pdfChartData, setPdfChartData] = useState([])
  const [stats, setStats] = useState(null)
  
  useEffect(() => {
    if (userId) {
      fetchUsageData()
    }
  }, [userId])

  const fetchUsageData = async () => {
    try {
      setLoading(true)
      const { auth } = await import('../../config/firebase')
      const token = await auth.currentUser?.getIdToken()
      
      if (!token) {
        logger.error('No auth token available')
        setWebChartData([])
        setPdfChartData([])
        setLoading(false)
        return
      }
      
      try {
        // Fetch daily usage summaries (new aggregated format)
        const historyResponse = await fetch(`${apiUrl}/usage-history?limit=30`, {
          headers: { 'Authorization': `Bearer ${token}` }
        })
        
        if (historyResponse.ok) {
          const historyData = await historyResponse.json()
          const history = historyData.history || []
          processChartData(history)
        } else {
          logger.error('Failed to fetch usage history')
          setWebChartData([])
          setPdfChartData([])
        }
      } catch (historyError) {
        logger.error('Error fetching usage history:', historyError)
        setWebChartData([])
        setPdfChartData([])
      }
      
      try {
        const statsResponse = await fetch(`${apiUrl}/usage-stats`, {
          headers: { 'Authorization': `Bearer ${token}` }
        })
        
        if (statsResponse.ok) {
          const statsData = await statsResponse.json()
          setStats(statsData.stats)
        }
      } catch (statsError) {
        logger.error('Error fetching usage stats:', statsError)
      }
    } catch (error) {
      logger.error('Error in fetchUsageData:', error)
      setWebChartData([])
      setPdfChartData([])
    } finally {
      setLoading(false)
    }
  }

  const processChartData = (history) => {
    const now = new Date()
    const monthStart = new Date(now.getFullYear(), now.getMonth(), 1)
    const monthEnd = new Date(now.getFullYear(), now.getMonth() + 1, 0)
    
    const webDaily = {}
    const pdfDaily = {}
    
    // Initialize all days of the current month
    for (let d = 1; d <= monthEnd.getDate(); d++) {
      const dateKey = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}-${String(d).padStart(2, '0')}`
      webDaily[dateKey] = { scans: 0, date: d }
      pdfDaily[dateKey] = { scans: 0, date: d }
    }
    
    // Process daily summary records (new format from credit_usage_daily_summary)
    history.forEach(entry => {
      try {
        // New format: entry has date (YYYY-MM-DD), total_web_credits_used, total_pdf_credits_used
        if (entry.date) {
          const entryDate = new Date(entry.date + 'T00:00:00')
          if (entryDate >= monthStart && entryDate <= monthEnd) {
            const dateKey = entry.date
            
            if (webDaily[dateKey]) {
              webDaily[dateKey].scans += entry.total_web_credits_used || 0
            }
            if (pdfDaily[dateKey]) {
              pdfDaily[dateKey].scans += entry.total_pdf_credits_used || 0
            }
          }
        }
        // Legacy format support (action-based per-transaction records)
        else if (entry.action === 'deduction' && entry.created_at) {
          const entryDate = new Date(entry.created_at)
          if (entryDate >= monthStart && entryDate <= monthEnd) {
            const dateKey = `${entryDate.getFullYear()}-${String(entryDate.getMonth() + 1).padStart(2, '0')}-${String(entryDate.getDate()).padStart(2, '0')}`
            
            if (entry.credit_type === 'web_scan' && webDaily[dateKey]) {
              webDaily[dateKey].scans += Math.abs(entry.web_amount || 0)
            } else if (entry.credit_type === 'pdf_scan' && pdfDaily[dateKey]) {
              pdfDaily[dateKey].scans += Math.abs(entry.pdf_amount || 0)
            }
          }
        }
      } catch (error) {
        logger.error('Error processing entry:', error)
      }
    })
    
    setWebChartData(Object.values(webDaily).sort((a, b) => a.date - b.date))
    setPdfChartData(Object.values(pdfDaily).sort((a, b) => a.date - b.date))
  }

  // Generate smooth curve path using bezier curves
  const generateSmoothPath = (data, maxValue, width, height, padding) => {
    if (!data || data.length < 2 || maxValue === 0) return ''
    
    const bottomY = height - padding
    const topY = padding
    
    const points = data.map((d, i) => ({
      x: padding + (i / (data.length - 1)) * (width - 2 * padding),
      y: height - padding - ((d.scans / maxValue) * (height - 2 * padding))
    }))
    
    if (points.length < 2) return ''
    
    // Start path
    let path = `M ${points[0].x},${points[0].y}`
    
    // Use cubic bezier curves with reduced tension to prevent overshooting
    for (let i = 0; i < points.length - 1; i++) {
      const p0 = points[i === 0 ? i : i - 1]
      const p1 = points[i]
      const p2 = points[i + 1]
      const p3 = points[i + 2 < points.length ? i + 2 : i + 1]
      
      // Calculate control points with reduced tension
      const tension = 0.15
      let cp1x = p1.x + (p2.x - p0.x) * tension
      let cp1y = p1.y + (p2.y - p0.y) * tension
      let cp2x = p2.x - (p3.x - p1.x) * tension
      let cp2y = p2.y - (p3.y - p1.y) * tension
      
      // Clamp control points to prevent going outside chart bounds
      cp1y = Math.max(topY, Math.min(bottomY, cp1y))
      cp2y = Math.max(topY, Math.min(bottomY, cp2y))
      
      path += ` C ${cp1x},${cp1y} ${cp2x},${cp2y} ${p2.x},${p2.y}`
    }
    
    return path
  }

  // Generate area fill path
  const generateAreaPath = (data, maxValue, width, height, padding) => {
    if (!data || data.length < 2 || maxValue === 0) return ''
    
    const linePath = generateSmoothPath(data, maxValue, width, height, padding)
    if (!linePath) return ''
    
    const lastX = padding + (width - 2 * padding)
    const firstX = padding
    const bottomY = height - padding
    
    return `${linePath} L ${lastX},${bottomY} L ${firstX},${bottomY} Z`
  }

  const renderChart = (data, color, title, maxValue) => {
    const now = new Date()
    const monthName = now.toLocaleDateString('en-US', { month: 'long', year: 'numeric' })
    const hasData = data.some(d => d.scans > 0)
    
    const width = 400
    const height = 200
    const padding = 30

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
              <div 
                className="w-3 h-3 rounded-full mr-3"
                style={{ backgroundColor: color }}
              />
              <h3 className={`text-lg font-semibold ${
                isDarkMode ? 'text-white' : 'text-gray-900'
              }`}>
                {title}
              </h3>
            </div>
            <span className={`text-sm ${isDarkMode ? 'text-gray-400' : 'text-gray-500'}`}>
              {monthName}
            </span>
          </div>
        </div>

        {/* Chart */}
        <div className="p-6">
          {!hasData ? (
            <div className="text-center py-12">
              <ChartBarIcon className={`h-16 w-16 mx-auto mb-3 ${
                isDarkMode ? 'text-gray-600' : 'text-gray-300'
              }`} />
              <p className={`${isDarkMode ? 'text-gray-400' : 'text-gray-500'}`}>
                No usage data for this month yet
              </p>
            </div>
          ) : (
            <div className="relative">
              {/* SVG Chart */}
              <svg 
                viewBox={`0 0 ${width} ${height}`} 
                className="w-full h-48"
                preserveAspectRatio="none"
              >
                {/* Gradient definition */}
                <defs>
                  <linearGradient id={`gradient-${title.replace(/\s/g, '')}`} x1="0%" y1="0%" x2="0%" y2="100%">
                    <stop offset="0%" stopColor={color} stopOpacity="0.3" />
                    <stop offset="100%" stopColor={color} stopOpacity="0.05" />
                  </linearGradient>
                </defs>

                {/* Grid lines */}
                {[0, 0.25, 0.5, 0.75, 1].map((ratio, i) => (
                  <line
                    key={i}
                    x1={padding}
                    y1={height - padding - ratio * (height - 2 * padding)}
                    x2={width - padding}
                    y2={height - padding - ratio * (height - 2 * padding)}
                    stroke={isDarkMode ? '#374151' : '#E5E7EB'}
                    strokeWidth="1"
                    strokeDasharray={i === 0 || i === 4 ? "0" : "4,4"}
                  />
                ))}

                {/* Area fill */}
                <path
                  d={generateAreaPath(data, maxValue, width, height, padding)}
                  fill={`url(#gradient-${title.replace(/\s/g, '')})`}
                />

                {/* Smooth line */}
                <path
                  d={generateSmoothPath(data, maxValue, width, height, padding)}
                  fill="none"
                  stroke={color}
                  strokeWidth="2.5"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                />

                {/* Data points - only show for non-zero values */}
                {data.map((d, i) => {
                  if (d.scans === 0) return null
                  const x = padding + (i / (data.length - 1)) * (width - 2 * padding)
                  const y = height - padding - ((d.scans / maxValue) * (height - 2 * padding))
                  return (
                    <g key={i}>
                      {/* Outer glow */}
                      <circle
                        cx={x}
                        cy={y}
                        r="6"
                        fill={color}
                        fillOpacity="0.2"
                      />
                      {/* Inner point */}
                      <circle
                        cx={x}
                        cy={y}
                        r="3"
                        fill={color}
                        stroke={isDarkMode ? '#1f2937' : 'white'}
                        strokeWidth="2"
                      />
                      <title>
                        {new Date(now.getFullYear(), now.getMonth(), d.date).toLocaleDateString('en-US', {
                          month: 'short',
                          day: 'numeric'
                        })}: {d.scans} scans
                      </title>
                    </g>
                  )
                })}
              </svg>

              {/* Y-axis labels */}
              <div className="absolute left-0 top-0 h-48 flex flex-col justify-between py-2 text-xs">
                <span className={isDarkMode ? 'text-gray-400' : 'text-gray-500'}>{maxValue}</span>
                <span className={isDarkMode ? 'text-gray-400' : 'text-gray-500'}>{Math.floor(maxValue / 2)}</span>
                <span className={isDarkMode ? 'text-gray-400' : 'text-gray-500'}>0</span>
              </div>

              {/* X-axis labels */}
              <div className="flex justify-between mt-2 text-xs px-6">
                {[1, Math.ceil(data.length / 4), Math.ceil(data.length / 2), Math.ceil(3 * data.length / 4), data.length].map((dayIndex, i) => (
                  <span key={i} className={isDarkMode ? 'text-gray-400' : 'text-gray-500'}>
                    {data[dayIndex - 1]?.date || ''}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    )
  }

  if (loading) {
    return (
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {[1, 2].map(i => (
          <div key={i} className={`${
            isDarkMode ? 'bg-gray-800' : 'bg-white'
          } rounded-lg shadow-lg border ${
            isDarkMode ? 'border-gray-700' : 'border-gray-200'
          } p-6`}>
            <div className="animate-pulse space-y-4">
              <div className={`h-6 ${isDarkMode ? 'bg-gray-700' : 'bg-gray-200'} rounded w-1/3`}></div>
              <div className={`h-48 ${isDarkMode ? 'bg-gray-700' : 'bg-gray-200'} rounded`}></div>
            </div>
          </div>
        ))}
      </div>
    )
  }

  const webMaxValue = Math.max(...webChartData.map(d => d.scans), 5)
  const pdfMaxValue = Math.max(...pdfChartData.map(d => d.scans), 5)

  return (
    <div className="space-y-6">
      {/* Stats Summary */}
      {stats && (
        <div className={`${
          isDarkMode ? 'bg-gray-800' : 'bg-white'
        } rounded-lg shadow-lg border ${
          isDarkMode ? 'border-gray-700' : 'border-gray-200'
        } p-6 grid grid-cols-2 gap-4`}>
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

      {/* Charts - Side by side on desktop, stacked on mobile */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {renderChart(webChartData, '#10B981', t('profile.usage.webScanCredits'), webMaxValue)}
        {renderChart(pdfChartData, '#3B82F6', t('profile.usage.pdfScanCredits'), pdfMaxValue)}
      </div>
    </div>
  )
}

export default UsageSeparateCharts
