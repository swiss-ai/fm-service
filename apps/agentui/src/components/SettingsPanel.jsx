import React, { useState, useEffect } from 'react'
import { Card } from './ui/Card'
import { Input } from './ui/Input'
import { useTranslation } from 'react-i18next'

export default function SettingsPanel({ open = false, onClose, settings, onChange, models = [], selectedModel, onModelChange, onLanguageChange, currentLanguage }) {
  const { t } = useTranslation()
  const [isDark, setIsDark] = useState(false)

  const languages = [
    { code: 'en', name: 'English' },
    { code: 'zh', name: '中文' },
    { code: 'de', name: 'Deutsch' },
    { code: 'fr', name: 'Français' }
  ]

  useEffect(() => {
    setIsDark(document.documentElement.classList.contains('dark'))
  }, [])

  const toggleDarkMode = () => {
    document.documentElement.classList.toggle('dark')
    setIsDark(document.documentElement.classList.contains('dark'))
  }

  // Handle escape key press
  useEffect(() => {
    const handleEscape = (e) => {
      if (e.key === 'Escape' && open) {
        onClose()
      }
    }
    window.addEventListener('keydown', handleEscape)
    return () => window.removeEventListener('keydown', handleEscape)
  }, [open, onClose])

  // Prevent body scroll when panel is open
  useEffect(() => {
    if (open) {
      document.body.style.overflow = 'hidden'
    } else {
      document.body.style.overflow = 'unset'
    }
    return () => {
      document.body.style.overflow = 'unset'
    }
  }, [open])

  if (!open) return null

  return (
    <>
      {/* Backdrop */}
      <div 
        className="fixed inset-0 z-30 bg-black/30 transition-opacity md:hidden" 
        onClick={onClose}
        aria-hidden="true"
      />
      
      {/* Panel */}
      <aside 
        className={`fixed top-0 right-0 z-40 h-full w-80 bg-background border-l flex flex-col transition-transform duration-200 ease-in-out ${
          open ? 'translate-x-0' : 'translate-x-full'
        }`}
      >
        <div className="flex items-center justify-between p-3 border-b">
          <span className="font-semibold text-xs tracking-widest text-muted-foreground text-left">{t('settings')}</span>
          <button 
            onClick={onClose} 
            className="p-1.5 hover:bg-accent rounded-md transition-colors"
            aria-label="Close settings"
          >
            <span className="material-icons text-base">close</span>
          </button>
        </div>

        <div className="flex-1 overflow-y-auto p-3">
          <div className="space-y-4 text-left">
            {/* Language Selection */}
            <div className="space-y-1.5">
              <h3 className="text-xs font-medium text-left">{t('changeLanguage')}</h3>
              <select
                value={currentLanguage}
                onChange={(e) => onLanguageChange(e.target.value)}
                className="w-full p-1.5 border rounded-md bg-background text-xs text-left"
              >
                {languages.map(lang => (
                  <option key={lang.code} value={lang.code}>
                    {lang.name}
                  </option>
                ))}
              </select>
            </div>

            {/* Model Selection */}
            <div className="space-y-1.5">
              <h3 className="text-xs font-medium text-left">{t('model')}</h3>
              <select
                value={selectedModel}
                onChange={onModelChange}
                className="w-full p-1.5 border rounded-md bg-background text-xs text-left"
              >
                {models.map(model => (
                  <option key={model} value={model}>
                    {model}
                  </option>
                ))}
              </select>
            </div>

            {/* Temperature */}
            <div className="space-y-1.5">
              <h3 className="text-xs font-medium text-left">{t('temperature')}</h3>
              <input
                type="range"
                min="0"
                max="1"
                step="0.1"
                value={settings.temperature}
                onChange={(e) => onChange({ ...settings, temperature: parseFloat(e.target.value) })}
                className="w-full"
              />
              <div className="text-xs text-muted-foreground text-left">
                {settings.temperature}
              </div>
            </div>

            {/* Max Tokens */}
            <div className="space-y-1.5">
              <h3 className="text-xs font-medium text-left">{t('maxTokens')}</h3>
              <input
                type="number"
                min="1"
                max="4000"
                value={settings.max_tokens}
                onChange={(e) => onChange({ ...settings, max_tokens: parseInt(e.target.value) })}
                className="w-full p-1.5 border rounded-md bg-background text-xs text-left"
              />
            </div>

            {/* Top P */}
            <div className="space-y-1.5">
              <h3 className="text-xs font-medium text-left">{t('topP')}</h3>
              <input
                type="range"
                min="0"
                max="1"
                step="0.1"
                value={settings.top_p}
                onChange={(e) => onChange({ ...settings, top_p: parseFloat(e.target.value) })}
                className="w-full"
              />
              <div className="text-xs text-muted-foreground text-left">
                {settings.top_p}
              </div>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="p-3 border-t flex justify-between items-center">
          <div className="text-xs text-muted-foreground text-left">
            <a href="#" className="hover:underline mr-2">{t('docs')}</a>
            <a href="#" className="hover:underline">{t('github')}</a>
          </div>
          <button 
            onClick={toggleDarkMode} 
            className="p-1.5 hover:bg-accent rounded-md transition-colors"
            aria-label="Toggle dark mode"
          >
            {isDark ? <span>🌙</span> : <span>☀️</span>}
          </button>
        </div>
      </aside>
    </>
  )
} 