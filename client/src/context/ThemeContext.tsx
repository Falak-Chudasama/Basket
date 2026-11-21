import React, { createContext, useContext, useEffect, useState } from 'react'

type Theme = 'light' | 'dark'

interface ThemeContextType {
  theme: Theme
  toggleTheme: () => void
}

/**
 * Time-based theme calculation:
 * Light mode: 6am - 7pm (hour >= 6 && hour < 19)
 * Dark mode:  7pm - 6am (hour >= 19 || hour < 6)
 */
export function getTimeBasedTheme(): Theme {
  const hour = new Date().getHours()
  return hour >= 6 && hour < 19 ? 'light' : 'dark'
}

const ThemeContext = createContext<ThemeContextType>({
  theme: 'light',
  toggleTheme: () => {},
})

export const ThemeProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  // Always initialize from the current time of day on launch or refresh
  const [theme, setTheme] = useState<Theme>(getTimeBasedTheme)

  useEffect(() => {
    try {
      if (theme === 'dark') {
        document.documentElement.classList.add('dark')
      } else {
        document.documentElement.classList.remove('dark')
      }
    } catch {}
  }, [theme])

  const toggleTheme = () => {
    setTheme(prev => (prev === 'light' ? 'dark' : 'light'))
  }

  return (
    <ThemeContext.Provider value={{ theme, toggleTheme }}>
      {children}
    </ThemeContext.Provider>
  )
}

export const useTheme = () => useContext(ThemeContext)

