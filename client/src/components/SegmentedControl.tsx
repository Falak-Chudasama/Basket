import React, { useRef, useEffect, useState } from 'react'
import { playScroll } from '../lib/sound'

export interface SegmentOption<T extends string = string> {
  id: T
  label: string
  count?: number
  icon?: React.ComponentType<{ className?: string }>
}

interface SegmentedControlProps<T extends string = string> {
  options: SegmentOption<T>[]
  value: T
  onChange: (value: T) => void
  ariaLabel?: string
  className?: string
}

/**
 * SegmentedControl — Fruit Family Design System Specification (Section 5.7)
 *
 * Anatomy: Capsule track hosting segmented pills with text and optional count badge.
 * Dimensions: Height ~44px, capsule shape 9999px.
 * Indicator: Sliding pill with shadow-xs and 300ms cubic-bezier(0.2, 0.8, 0.2, 1).
 */
export function SegmentedControl<T extends string>({
  options,
  value,
  onChange,
  ariaLabel = 'Segment options',
  className = '',
}: SegmentedControlProps<T>) {
  const containerRef = useRef<HTMLDivElement>(null)
  const [indicatorStyle, setIndicatorStyle] = useState<{ left: number; width: number }>({
    left: 0,
    width: 0,
  })
  const buttonRefs = useRef<Map<T, HTMLButtonElement>>(new Map())

  useEffect(() => {
    const btn = buttonRefs.current.get(value)
    const container = containerRef.current
    if (btn && container) {
      const btnRect = btn.getBoundingClientRect()
      const containerRect = container.getBoundingClientRect()
      setIndicatorStyle({
        left: btnRect.left - containerRect.left,
        width: btnRect.width,
      })
    }
  }, [value, options])

  const handleSelect = (id: T) => {
    if (id !== value) {
      playScroll()
      onChange(id)
    }
  }

  return (
    <div
      ref={containerRef}
      role="tablist"
      aria-label={ariaLabel}
      className={`glass-capsule relative inline-flex items-center rounded-full p-1 h-[44px] shadow-xs select-none ${className}`}
    >
      {/* Sliding Pill Indicator (300ms cubic-bezier(0.2, 0.8, 0.2, 1)) */}
      {indicatorStyle.width > 0 && (
        <div
          className="absolute top-1 bottom-1 rounded-full bg-stone-900 text-white dark:bg-stone-100 shadow-xs pointer-events-none transition-all duration-300 ease-[cubic-bezier(0.2,0.8,0.2,1)]"
          style={{
            left: `${indicatorStyle.left}px`,
            width: `${indicatorStyle.width}px`,
          }}
        />
      )}

      {/* Segment Buttons (Strict 48dp touch target) */}
      {options.map(opt => {
        const isActive = value === opt.id
        const Icon = opt.icon
        return (
          <button
            key={opt.id}
            ref={el => {
              if (el) buttonRefs.current.set(opt.id, el)
              else buttonRefs.current.delete(opt.id)
            }}
            type="button"
            role="tab"
            aria-selected={isActive}
            onClick={() => handleSelect(opt.id)}
            className={`focus-ring relative z-10 flex items-center justify-center gap-1.5 px-3.5 py-2 min-h-[36px] rounded-full text-xs font-semibold font-sans whitespace-nowrap transition-colors duration-200 ${
              isActive
                ? 'text-white dark:text-stone-900'
                : 'text-stone-600 dark:text-stone-300 hover:text-stone-900 dark:hover:text-white'
            }`}
          >
            {Icon && <Icon className="h-3.5 w-3.5 shrink-0" />}
            <span>{opt.label}</span>
            {opt.count !== undefined && (
              <span
                className={`ml-0.5 rounded-full px-1.5 py-0.2 font-mono text-[10px] font-bold ${
                  isActive
                    ? 'bg-white/20 text-white dark:bg-stone-900/20 dark:text-stone-900'
                    : 'bg-stone-200/80 dark:bg-stone-800 text-stone-600 dark:text-stone-400'
                }`}
              >
                {opt.count}
              </span>
            )}
          </button>
        )
      })}
    </div>
  )
}
