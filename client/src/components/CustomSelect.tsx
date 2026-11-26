import React, { useState, useRef, useEffect, type ReactNode } from 'react'
import { ChevronDown, Check } from 'lucide-react'
import { playEnter, playScroll } from '../lib/sound'

export interface SelectOption {
  value: string
  label: string
  icon?: ReactNode
}

interface CustomSelectProps {
  value: string
  onChange: (value: string) => void
  options: SelectOption[]
  placeholder?: string
  disabled?: boolean
  ariaLabel?: string
  className?: string
  buttonClassName?: string
  menuClassName?: string
}

/**
 * CustomSelect — Fruit Family Design System Specification (Quiet Utility Glass Dropdown)
 */
export const CustomSelect: React.FC<CustomSelectProps> = ({
  value,
  onChange,
  options,
  placeholder = 'Select...',
  disabled = false,
  ariaLabel,
  className = '',
  buttonClassName = '',
  menuClassName = '',
}) => {
  const [isOpen, setIsOpen] = useState(false)
  const containerRef = useRef<HTMLDivElement>(null)

  const selectedOption = options.find(opt => opt.value === value)

  useEffect(() => {
    if (!isOpen) return

    const handleClickOutside = (e: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setIsOpen(false)
      }
    }

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        setIsOpen(false)
      }
    }

    document.addEventListener('mousedown', handleClickOutside)
    document.addEventListener('keydown', handleKeyDown)
    return () => {
      document.removeEventListener('mousedown', handleClickOutside)
      document.removeEventListener('keydown', handleKeyDown)
    }
  }, [isOpen])

  const handleToggle = () => {
    if (disabled) return
    playEnter()
    setIsOpen(prev => !prev)
  }

  const handleSelect = (val: string) => {
    if (val !== value) {
      playScroll()
      onChange(val)
    }
    setIsOpen(false)
  }

  return (
    <div ref={containerRef} className={`relative text-left ${className}`}>
      <button
        type="button"
        disabled={disabled}
        onClick={handleToggle}
        aria-haspopup="listbox"
        aria-expanded={isOpen}
        aria-label={ariaLabel}
        className={`focus-ring btn-interactive flex items-center justify-between gap-2 rounded-xl bg-stone-100/90 dark:bg-stone-800/80 hover:bg-stone-200/70 dark:hover:bg-stone-800 border border-black/[0.06] dark:border-white/[0.08] px-3 py-1.5 min-h-[36px] text-caption font-semibold font-sans text-stone-900 dark:text-stone-100 shadow-xs transition disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer whitespace-nowrap ${buttonClassName}`}
      >
        <div className="flex items-center gap-2 min-w-0 truncate">
          {selectedOption?.icon && <span className="shrink-0 flex items-center">{selectedOption.icon}</span>}
          <span className="truncate">{selectedOption ? selectedOption.label : placeholder}</span>
        </div>
        <ChevronDown
          className={`h-3.5 w-3.5 shrink-0 text-stone-400 dark:text-stone-500 transition-transform duration-200 ${
            isOpen ? 'rotate-180 text-stone-700 dark:text-stone-200' : ''
          }`}
        />
      </button>

      {isOpen && (
        <div
          role="listbox"
          tabIndex={-1}
          className={`absolute left-0 z-50 mt-1.5 min-w-full w-max max-w-[90vw] max-h-64 overflow-y-auto rounded-xl bg-white/95 dark:bg-stone-900/95 backdrop-blur-xl border border-black/[0.08] dark:border-white/[0.10] p-1 shadow-floating animate-scale-in ${menuClassName}`}
        >
          {options.map(opt => {
            const isSelected = opt.value === value
            return (
              <button
                key={opt.value}
                type="button"
                role="option"
                aria-selected={isSelected}
                onClick={() => handleSelect(opt.value)}
                className={`flex w-full items-center justify-between gap-2.5 rounded-lg px-2.5 py-1.5 text-caption font-sans transition text-left cursor-pointer whitespace-nowrap ${
                  isSelected
                    ? 'bg-stone-900 text-white dark:bg-stone-100 dark:text-stone-900 font-semibold'
                    : 'text-stone-700 dark:text-stone-300 hover:bg-stone-200/60 dark:hover:bg-stone-800/80'
                }`}
              >
                <div className="flex items-center gap-2 min-w-0 flex-1">
                  {opt.icon && <span className="shrink-0 flex items-center">{opt.icon}</span>}
                  <span className="truncate">{opt.label}</span>
                </div>
                {isSelected && <Check className="h-3.5 w-3.5 shrink-0" />}
              </button>
            )
          })}
        </div>
      )}
    </div>
  )
}
