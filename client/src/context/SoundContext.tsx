import React, { createContext, useContext, useState, useEffect, useCallback } from 'react'
import {
  isSoundEnabled,
  setSoundEnabled,
  playEnter,
  playBack,
  playNotification,
  playFailed,
  playScroll,
} from '../lib/sound'

interface SoundContextType {
  soundEnabled: boolean
  toggleSound: () => void
  setSound: (enabled: boolean) => void
  playEnter: () => void
  playBack: () => void
  playNotification: () => void
  playFailed: () => void
  playScroll: () => void
}

const SoundContext = createContext<SoundContextType>({
  soundEnabled: true,
  toggleSound: () => {},
  setSound: () => {},
  playEnter: () => {},
  playBack: () => {},
  playNotification: () => {},
  playFailed: () => {},
  playScroll: () => {},
})

export const SoundProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const soundEnabled = true

  const setSound = useCallback((_enabled: boolean) => {
    // Sound permanently enabled
  }, [])

  const toggleSound = useCallback(() => {
    // Sound permanently enabled
  }, [])

  return (
    <SoundContext.Provider
      value={{
        soundEnabled,
        toggleSound,
        setSound,
        playEnter,
        playBack,
        playNotification,
        playFailed,
        playScroll,
      }}
    >
      {children}
    </SoundContext.Provider>
  )
}

export const useSound = () => useContext(SoundContext)
