import { useEffect } from 'react'

/**
 * Checks whether the event target is an editable field where keyboard navigation
 * shortcuts (like Shift+Arrow selection or Ctrl+Arrow word jump) should remain native.
 */
export function isEditableTarget(target: EventTarget | null): boolean {
  if (!(target instanceof HTMLElement)) return false
  if (
    target instanceof HTMLInputElement ||
    target instanceof HTMLTextAreaElement ||
    target instanceof HTMLSelectElement
  ) {
    return true
  }
  return target.isContentEditable
}

/**
 * Cycles an ordered list of values on Shift+ArrowLeft / Shift+ArrowRight
 * (or Shift+ArrowUp / Shift+ArrowDown when axis === 'vertical').
 */
export function useShiftArrowCycle<T>({
  items,
  current,
  onSelect,
  axis = 'horizontal',
  onCycle,
}: {
  items: readonly T[]
  current: T
  onSelect: (next: T) => void
  axis?: 'horizontal' | 'vertical'
  onCycle?: () => void
}): void {
  useEffect(() => {
    if (items.length === 0) return
    const prevKey = axis === 'horizontal' ? 'ArrowLeft' : 'ArrowUp'
    const nextKey = axis === 'horizontal' ? 'ArrowRight' : 'ArrowDown'

    const handleKeyDown = (e: KeyboardEvent) => {
      if (isEditableTarget(e.target)) return
      if (!e.shiftKey || e.ctrlKey || e.metaKey || e.altKey) return

      const isNext = e.key === nextKey || e.code === nextKey
      const isPrev = e.key === prevKey || e.code === prevKey
      if (!isNext && !isPrev) return

      e.preventDefault()
      const idx = items.indexOf(current)
      const nextIdx = idx === -1
        ? 0
        : isNext
          ? (idx + 1) % items.length
          : (idx - 1 + items.length) % items.length
      onCycle?.()
      onSelect(items[nextIdx])
    }

    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [items, current, onSelect, axis, onCycle])
}

