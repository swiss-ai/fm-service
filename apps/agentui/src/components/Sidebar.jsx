import React, { useRef, useState, useEffect } from 'react'
import { Button } from './ui/button'
import { useTranslation } from 'react-i18next'

export default function Sidebar({ 
  open = false, 
  onClose, 
  conversations = [], 
  currentConversationId,
  onNewConversation, 
  onSelectConversation,
  onExport, 
  onImport,
  onSettingsClick,
  onDeleteConversation,
  onClearAllConversations,
  onLogout,
  user
}) {
  const { t } = useTranslation()
  const fileInputRef = useRef(null)
  const [isDrawerOpen, setIsDrawerOpen] = useState(false)

  const handleImportClick = () => {
    fileInputRef.current?.click()
  }

  return (
    <>
      {/* Mobile Drawer Overlay */}
      <div className={`fixed inset-0 z-40 bg-black/40 transition-opacity md:hidden ${open ? 'block' : 'hidden'}`} onClick={onClose} />
      {/* Sidebar Drawer */}
      <aside
        className={`fixed top-0 left-0 z-50 h-full w-full max-w-xs bg-background border-r flex flex-col transition-transform duration-300 ease-in-out
          ${open ? 'translate-x-0' : '-translate-x-full'}
          md:static md:translate-x-0 md:w-64 md:max-w-none md:z-40`}
        style={{ boxShadow: open ? '0 0 24px rgba(0,0,0,0.12)' : undefined }}
      >
        {/* App Logo and Name */}
        <div className="flex items-center gap-3 px-4 py-5 border-b border-b-muted-foreground/10">
          <span className="bg-muted rounded-full p-2"><span className="material-icons text-2xl">hub</span></span>
          <span className="font-semibold text-lg tracking-wide">SwissAI Chat</span>
        </div>
        {/* Recent Conversations */}
        <div className="flex-1 overflow-y-auto p-3 flex flex-col gap-3">
          <div className="text-xs text-muted-foreground mb-1">{t('recents')}</div>
          <Button 
            size="sm" 
            variant="outline" 
            onClick={onNewConversation} 
            className="w-full mb-2 py-3 text-base"
            style={{ backgroundColor: '#215CAF', color: 'white', borderColor: '#215CAF' }}
          >
            {t('new')}
          </Button>
          {conversations.length === 0 ? (
            <div className="text-muted-foreground text-xs">{t('noRecents')}</div>
          ) : (
            <ul className="flex flex-col gap-2">
              {conversations.map((conv) => (
                <li 
                  key={conv.id}
                  className={`group flex items-center justify-between hover:bg-accent rounded p-3 text-sm ${
                    conv.id === currentConversationId ? 'bg-accent' : ''
                  }`}
                  onClick={() => onSelectConversation(conv.id)}
                >
                  <div 
                    className="truncate cursor-pointer flex-1 pr-2"
                  >
                    {conv.title.replace(/<think>.*?<\/think>/g, '').replace(/\s+/g, ' ').trim()}
                  </div>
                  <button
                    onClick={(e) => {
                      e.stopPropagation()
                      onDeleteConversation(conv.id)
                    }}
                    className="opacity-70 group-hover:opacity-100 p-2 hover:bg-destructive/10 rounded-md transition"
                    aria-label="Delete conversation"
                  >
                    <span className="material-icons text-base text-destructive">delete</span>
                  </button>
                </li>
              ))}
            </ul>
          )}
        </div>
        {/* Spacer */}
        <div className="flex-1" />
        {/* User Profile Section */}
        <div className="p-4 border-t border-t-muted-foreground/10">
          <UserProfileDropdown user={user} onLogout={onLogout} onExport={onExport} onImport={onImport} onClearAllConversations={onClearAllConversations} />
        </div>
      </aside>
    </>
  )
}

// SidebarNavItem component
function SidebarNavItem({ icon, label }) {
  return (
    <div className="flex items-center gap-3 px-4 py-2 rounded-lg hover:bg-accent cursor-pointer">
      <span className="material-icons text-xl text-muted-foreground">{icon}</span>
      <span className="text-base">{label}</span>
    </div>
  )
}

// UserProfileDropdown component
function UserProfileDropdown({ user, onLogout, onExport, onImport, onClearAllConversations }) {
  const [open, setOpen] = useState(false)
  const dropdownRef = useRef(null)
  const fileInputRef = useRef(null)

  // Close dropdown on click outside
  useEffect(() => {
    function handleClickOutside(event) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setOpen(false)
      }
    }
    if (open) document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [open])

  const handleImportClick = () => {
    fileInputRef.current?.click()
    setOpen(false)
  }

  return (
    <div className="relative" ref={dropdownRef}>
      <button
        className="flex items-center gap-3 w-full p-2 rounded-lg hover:bg-accent focus:outline-none"
        onClick={() => setOpen((v) => !v)}
      >
        <img
          src={user?.picture || 'https://ui-avatars.com/api/?name=User'}
          alt={user?.name || 'User'}
          className="w-10 h-10 rounded-full object-cover border"
        />
        <div className="flex flex-col items-start flex-1 min-w-0">
          <span className="font-medium truncate text-base">{user?.name || 'User'}</span>
          <span className="text-muted-foreground text-sm truncate">{user?.email || ''}</span>
        </div>
        {/* <span className="material-icons text-base ml-2">expand_more</span> */}
      </button>
      {open && (
        <div className="absolute left-0 bottom-14 w-full bg-background border rounded-lg shadow-lg z-50 overflow-hidden animate-fade-in">
          <button className="flex items-center gap-3 w-full px-4 py-3 hover:bg-accent text-base" onClick={onExport}>
            <span className="material-icons text-lg">download</span> Export
          </button>
          <label className="flex items-center gap-3 w-full px-4 py-3 hover:bg-accent text-base cursor-pointer">
            <span className="material-icons text-lg">upload</span> Import
            <input
              type="file"
              ref={fileInputRef}
              onChange={onImport}
              accept=".json"
              className="hidden"
            />
          </label>
          <button className="flex items-center gap-3 w-full px-4 py-3 hover:bg-accent text-base" onClick={onClearAllConversations}>
            <span className="material-icons text-lg">delete_sweep</span> Clear all
          </button>
          <button className="flex items-center gap-3 w-full px-4 py-3 hover:bg-accent text-base text-destructive" onClick={onLogout}>
            <span className="material-icons text-lg">logout</span> Sign out
          </button>
        </div>
      )}
    </div>
  )
} 