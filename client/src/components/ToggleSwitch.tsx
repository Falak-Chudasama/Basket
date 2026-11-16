import React from 'react'
import { playEnter, playBack } from '../lib/sound'

interface ToggleSwitchProps {
  checked: boolean
  onChange: (checked: boolean) => void
  disabled?: boolean
  label?: string
  description?: string
  id?: string
}

/**
 * ToggleSwitch — Fruit Family Design System Specification (Section 5.2)
 *
 * Anatomy: Pill track with 2px inset circular thumb.
 * Dimensions: Track 50px width x 30px height. Thumb 26px diameter. Travel distance: 22px.
 * Bounding touch box: 48px x 48px minimum touch target.
 * Active color: Basket's derived primaryAccent token (#DF8A2D light / #FACD8F dark).
 */
export const ToggleSwitch: React.FC<ToggleSwitchProps> = ({
  checked,
  onChange,
  disabled = false,
  label,
  description,
  id,
}) => {
  const switchId = id || `switch-${Math.random().toString(36).substring(2, 9)}`

  const handleToggle = () => {
    if (disabled) return
    const next = !checked
    if (next) {
      playEnter()
    } else {
      playBack()
    }
    onChange(next)
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === ' ' || e.key === 'Enter') {
      e.preventDefault()
      handleToggle()
    }
  }

  return (
    <div className="flex items-center justify-between gap-3 select-none">
      {(label || description) && (
        <label
          htmlFor={switchId}
          onClick={handleToggle}
          className={`cursor-pointer ${disabled ? 'opacity-50 cursor-not-allowed' : ''}`}
        >
          {label && (
            <span className="block text-sm font-semibold font-sans text-stone-900 dark:text-stone-100">
              {label}
            </span>
          )}
          {description && (
            <span className="block text-xs font-sans text-stone-500 dark:text-stone-400">
              {description}
            </span>
          )}
        </label>
      )}

      {/* 48px x 48px Minimum Bounding Touch Box (Section 1 & 5.2) */}
      <div
        className="flex items-center justify-center min-w-[48px] min-h-[48px] cursor-pointer"
        onClick={handleToggle}
      >
        <button
          type="button"
          id={switchId}
          role="switch"
          aria-checked={checked}
          disabled={disabled}
          onKeyDown={handleKeyDown}
          className={`focus-ring relative inline-flex h-[30px] w-[50px] shrink-0 items-center rounded-full transition-colors duration-200 ease-out ${
            disabled ? 'opacity-45 cursor-not-allowed' : 'cursor-pointer'
          } ${
            checked
              ? 'bg-basket-DEFAULT dark:bg-basket-200'
              : 'bg-stone-200 dark:bg-stone-800'
          }`}
        >
          {/* Circular 26px Thumb with 22px travel distance */}
          <span
            className={`pointer-events-none inline-block h-[26px] w-[26px] rounded-full shadow-xs transition-transform duration-200 cubic-bezier(0.16, 1, 0.3, 1) ${
              checked
                ? 'translate-x-[22px] bg-white dark:bg-stone-900'
                : 'translate-x-[2px] bg-white dark:bg-[#E0DDD5]'
            }`}
          />
        </button>
      </div>
    </div>
  )
}
