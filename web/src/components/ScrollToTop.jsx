import { useEffect } from 'react'
import { useLocation } from 'react-router-dom'

/**
 * ScrollToTop component that scrolls the window to the top
 * whenever the route/location changes.
 * 
 * This ensures users always start at the top of a new page,
 * regardless of their scroll position on the previous page.
 */
const ScrollToTop = () => {
  const { pathname } = useLocation()

  useEffect(() => {
    // Scroll to top of page when route changes
    window.scrollTo(0, 0)
  }, [pathname])

  return null
}

export default ScrollToTop
