import { useState, useEffect, useRef } from 'react'
import { useTranslation } from 'react-i18next'
import { Auth0Provider } from '@auth0/auth0-react'
import { AuthProvider, useAuth } from './contexts/AuthContext'
import './i18n'
import Sidebar from './components/Sidebar'
import ChatWindow from './components/ChatWindow'
import SettingsPanel from './components/SettingsPanel'
import OpenAI from 'openai'
import './App.css'

function AppContent() {
  const { t, i18n } = useTranslation()
  const { isAuthenticated, isLoading: authLoading, swissAIToken, login, logout, user } = useAuth()
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [models, setModels] = useState([])
  const [selectedModel, setSelectedModel] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [isRequestInProgress, setIsRequestInProgress] = useState(false)
  const [conversations, setConversations] = useState(() => {
    const savedConversations = localStorage.getItem('conversations')
    if (savedConversations) {
      const parsed = JSON.parse(savedConversations)
      // Add id to any conversations that don't have one and clean titles
      return parsed.map(conv => ({
        ...conv,
        id: conv.id || Date.now().toString() + Math.random().toString(36).substr(2, 9),
        title: conv.title.replace(/<think>.*?<\/think>/g, '').replace(/\s+/g, ' ').trim()
      }))
    }
    return []
  })
  const [currentConversationId, setCurrentConversationId] = useState(() => {
    const savedId = localStorage.getItem('currentConversationId')
    return savedId || null
  })
  const [settings, setSettings] = useState(() => {
    const savedSettings = localStorage.getItem('settings')
    return savedSettings ? JSON.parse(savedSettings) : {
      temperature: 0.7,
      top_p: 1,
      max_tokens: 2048
    }
  })
  const [isAgentMode, setIsAgentMode] = useState(false)
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const [settingsOpen, setSettingsOpen] = useState(false)
  const abortControllerRef = useRef(null)

  // Load messages when current conversation changes
  useEffect(() => {
    if (!isLoading && !streamingMessage) {
      if (currentConversationId) {
        const conversation = conversations.find(c => c.id === currentConversationId)
        if (conversation) {
          setMessages(conversation.messages || [])
        }
      } else {
        setMessages([])
      }
    }
  }, [currentConversationId, conversations, isLoading, streamingMessage])

  // Save conversations to localStorage whenever they change
  useEffect(() => {
    localStorage.setItem('conversations', JSON.stringify(conversations))
  }, [conversations])

  // Save current conversation ID to localStorage whenever it changes
  useEffect(() => {
    if (currentConversationId) {
      localStorage.setItem('currentConversationId', currentConversationId)
    } else {
      localStorage.removeItem('currentConversationId')
    }
  }, [currentConversationId])

  // Save settings to localStorage whenever they change
  useEffect(() => {
    localStorage.setItem('settings', JSON.stringify(settings))
  }, [settings])

  // Save language preference to localStorage
  useEffect(() => {
    localStorage.setItem('language', i18n.language)
  }, [i18n.language])

  // Load language preference on startup
  useEffect(() => {
    const savedLanguage = localStorage.getItem('language')
    if (savedLanguage) {
      i18n.changeLanguage(savedLanguage)
    }
  }, [])

  useEffect(() => {
    if (!authLoading && swissAIToken) {
      console.log('Initializing OpenAI client with SwissAI token...');
      // Initialize OpenAI client with SwissAI token
      const openai = new OpenAI({
        apiKey: swissAIToken,
        baseURL: "https://api.swissai.cscs.ch/v1",
        dangerouslyAllowBrowser: true
      })

      // Fetch available models
      const fetchModels = async () => {
        try {
          console.log('Fetching models...');
          const response = await openai.models.list()
          console.log('Models response:', response);
          const availableModels = response.data
            .map(model => model.id)
          console.log('Available models:', availableModels);
          setModels(availableModels)
          if (availableModels.length > 0) {
            setSelectedModel(availableModels[0])
          }
        } catch (error) {
          console.error('Error fetching models:', error)
        }
      }

      fetchModels()
    } else {
      console.log('Not fetching models:', { authLoading, hasToken: !!swissAIToken });
    }
  }, [authLoading, swissAIToken])

  // Add new function to handle agent mode requests
  const handleAgentRequest = async (input, convId) => {
    const userMessage = { role: 'user', content: input }
    const newMessages = [...messages, userMessage]
    setMessages(newMessages)
    setInput('')
    setIsLoading(true)
    setIsRequestInProgress(true)

    // Update conversation with empty streaming message and set streaming state
    setConversations(prev => prev.map(conv => 
      conv.id === convId 
        ? { 
            ...conv, 
            streamingMessage: '',
            isStreaming: true,
            lastMessageId: Date.now().toString()
          }
        : conv
    ))

    try {
      console.log('Starting agent request...');
      abortControllerRef.current = new AbortController()
      const response = await fetch('http://localhost:8001/v1/responses', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json',
        },
        body: JSON.stringify({
          id: `agent_request_${Date.now()}`,
          module: "vagents.contrib.modules.chat:AgentChat",
          input: input,
          stream: true,
          additional: { round_limit: 2 }
        }),
        signal: abortControllerRef.current.signal
      })
      
      if (!response.ok) {
        const errorText = await response.text();
        console.error('Agent request failed:', response.status, errorText);
        throw new Error(`Agent request failed: ${response.status} ${errorText}`);
      }
      
      if (!response.body) throw new Error('No response body')
      const reader = response.body.getReader()
      let currentChunk = ''
      let updatedMessages = [...newMessages]
      let toolCalls = [] // Array to collect tool calls
      let finalMessage = '' // Store the final message
      let lastToolCall = null // Track the last tool call
      let done = false
      while (!done) {
        const { value, done: doneReading } = await reader.read()
        done = doneReading
        if (value) {
          const chunk = new TextDecoder().decode(value)
          console.log('Raw chunk received:', chunk)
          currentChunk += chunk
          
          // Format the raw chunk for display
          let formattedChunk = ''
          try {
            const parsedChunk = JSON.parse(chunk)
            if (parsedChunk.type === 'tool_call') {
              lastToolCall = parsedChunk.name
              formattedChunk = `🛠️ Calling: ${parsedChunk.name}\n⏳ Waiting for result...`
            } else if (parsedChunk.type === 'tool_result') {
              const result = parsedChunk.result
              // Truncate long results
              const truncatedResult = result.length > 200 ? result.substring(0, 200) + '...' : result
              formattedChunk = `✅ Result from ${parsedChunk.name}:\n${truncatedResult}`
              lastToolCall = null
            } else if (parsedChunk.type === 'data') {
              formattedChunk = parsedChunk.content
            } else {
              formattedChunk = JSON.stringify(parsedChunk, null, 2)
            }
          } catch (e) {
            formattedChunk = chunk
          }
          
          // Update streaming message with formatted chunk
          setConversations(prev => prev.map(conv => 
            conv.id === convId 
              ? { 
                  ...conv, 
                  streamingMessage: formattedChunk,
                  waitingForTool: lastToolCall // Add flag to indicate waiting state
                }
              : conv
          ))
          
          // Check if we have a complete chunk (ends with newline)
          if (currentChunk.includes('\n')) {
            const chunks = currentChunk.split('\n')
            // Process all complete chunks except the last one (which might be incomplete)
            for (let i = 0; i < chunks.length - 1; i++) {
              const chunkText = chunks[i].trim()
              if (chunkText) {
                try {
                  const parsedChunk = JSON.parse(chunkText)
                  if (parsedChunk.type === 'tool_call' || parsedChunk.type === 'tool_result') {
                    toolCalls.push(parsedChunk)
                  } else if (parsedChunk.type === 'data') {
                    finalMessage = parsedChunk.content
                  }
                } catch (e) {
                  console.error('Error parsing chunk:', e)
                }
              }
            }
            // Keep the last (potentially incomplete) chunk for next iteration
            currentChunk = chunks[chunks.length - 1]
          }
        }
      }
      
      // Handle any remaining text
      if (currentChunk.trim()) {
        try {
          const parsedChunk = JSON.parse(currentChunk.trim())
          if (parsedChunk.type === 'tool_call' || parsedChunk.type === 'tool_result') {
            toolCalls.push(parsedChunk)
          } else if (parsedChunk.type === 'data') {
            finalMessage = parsedChunk.content
          }
        } catch (e) {
          console.error('Error parsing final chunk:', e)
        }
      }

      // Add tool calls as a single message if there are any
      if (toolCalls.length > 0) {
        const toolCallsText = toolCalls.map(call => {
          if (call.type === 'tool_call') {
            return `🛠️ Calling: ${call.name}`
          } else {
            const result = call.result
            const truncatedResult = result.length > 200 ? result.substring(0, 200) + '...' : result
            return `✅ Result from ${call.name}:\n${truncatedResult}`
          }
        }).join('\n\n')
        
        updatedMessages = [...updatedMessages, { 
          role: 'assistant', 
          content: toolCallsText,
          isToolCall: true,
          isCollapsed: true // Add flag to indicate this message can be collapsed
        }]
        setMessages(updatedMessages)
      }

      // Add final message if there is one
      if (finalMessage) {
        updatedMessages = [...updatedMessages, { 
          role: 'assistant', 
          content: finalMessage,
          isFinalMessage: true // Add flag to identify the final message
        }]
        setMessages(updatedMessages)
      }

      console.log('Agent request finished');
      setConversations(prev => prev.map(conv => 
        conv.id === convId 
          ? { 
              ...conv, 
              messages: updatedMessages,
              streamingMessage: '',
              isStreaming: false,
              lastMessageId: null,
              waitingForTool: null
            } 
          : conv
      ))
    } catch (error) {
      if (error.name !== 'AbortError') {
        console.error('Error in agent request:', error)
      }
      setConversations(prev => prev.map(conv => 
        conv.id === convId 
          ? { 
              ...conv, 
              streamingMessage: '',
              isStreaming: false,
              lastMessageId: null,
              waitingForTool: null
            } 
          : conv
      ))
    } finally {
      setIsLoading(false)
      setIsRequestInProgress(false)
    }
  }

  const handleSend = async (e) => {
    e.preventDefault()
    if (isRequestInProgress) return
    
    // capture current or new conversation ID to avoid stale closure
    if (!input.trim()) {
      console.log('Cannot send message: No input');
      return;
    }

    // Create new conversation if this is the first message
    if (messages.length === 0) {
      const newId = Date.now().toString()
      setCurrentConversationId(newId)
      // update local convId to new ID
      convId = newId
      setConversations(prev => [
        { 
          id: newId,
          title: t('new'),
          messages: [],
          streamingMessage: '',
          isStreaming: false,
          lastMessageId: null
        },
        ...prev
      ])
    }

    // Handle agent mode differently
    if (isAgentMode) {
      await handleAgentRequest(input, convId)
      return
    }
    
    // Regular chat mode handling
    if (!selectedModel || !swissAIToken) {
      return;
    }
    
    console.log('Sending message with:', { 
      model: selectedModel, 
      hasToken: !!swissAIToken,
      messageCount: messages.length 
    });
    
    const userMessage = { role: 'user', content: input }
    const newMessages = [...messages, userMessage]
    setMessages(newMessages)
    setInput('')
    setIsLoading(true)
    setIsRequestInProgress(true)

    // Update conversation with empty streaming message and set streaming state
    setConversations(prev => prev.map(conv => 
      conv.id === convId 
        ? { 
            ...conv, 
            streamingMessage: '',
            isStreaming: true,
            lastMessageId: Date.now().toString()
          }
        : conv
    ))

    try {
      console.log('Starting chat completion...');
      abortControllerRef.current = new AbortController()

      // If this is the first message, generate a title first
      let title = ''
      if (messages.length === 0) {
        const titleResponse = await fetch('https://api.swissai.cscs.ch/v1/chat/completions', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${swissAIToken}`
          },
          body: JSON.stringify({
            model: selectedModel,
            messages: [
              {
                role: 'system',
                content: 'Generate a short, concise title (max 5 words) for this conversation based on the user\'s first message. The title should capture the main topic or purpose of the conversation. Respond with ONLY the title, no additional text.'
              },
              userMessage
            ],
            temperature: 0.7,
            max_tokens: 50
          })
        })

        if (titleResponse.ok) {
          const titleData = await titleResponse.json()
          title = titleData.choices[0].message.content.trim()
          // Update the conversation title
          setConversations(prev => prev.map(conv => 
            conv.id === convId 
              ? { ...conv, title }
              : conv
          ))
        }
      }

      const response = await fetch('https://api.swissai.cscs.ch/v1/chat/completions', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${swissAIToken}`
        },
        body: JSON.stringify({
          model: selectedModel,
          messages: newMessages,
          stream: true,
          temperature: settings.temperature ?? 0.7,
          top_p: settings.top_p ?? 1,
          max_tokens: settings.max_tokens || 2048
        }),
        signal: abortControllerRef.current.signal
      })
      
      if (!response.ok) {
        const errorText = await response.text();
        console.error('Chat completion failed:', response.status, errorText);
        throw new Error(`Chat completion failed: ${response.status} ${errorText}`);
      }
      
      if (!response.body) throw new Error('No response body')
      const reader = response.body.getReader()
      let fullText = ''
      let done = false
      while (!done) {
        const { value, done: doneReading } = await reader.read()
        done = doneReading
        if (value) {
          const chunk = new TextDecoder().decode(value)
          chunk.split('\n').forEach(line => {
            if (line.startsWith('data: ')) {
              const data = line.replace('data: ', '').trim()
              if (data && data !== '[DONE]') {
                try {
                  const parsed = JSON.parse(data)
                  const delta = parsed.choices?.[0]?.delta?.content || ''
                  fullText += delta
                  
                  // Only update the conversation's streaming message
                  setConversations(prev => prev.map(conv => 
                    conv.id === convId 
                      ? { ...conv, streamingMessage: fullText.replace(/<title>.*?<\/title>/, '') }
                      : conv
                  ))
                } catch (error) {
                  console.error('Error parsing streaming data:', error, data);
                }
              }
            }
          })
        }
      }
      console.log('Chat completion finished');
      const assistantMessage = { role: 'assistant', content: fullText.replace(/<title>.*?<\/title>/, '') }
      const updatedMessages = [...newMessages, assistantMessage]
      setMessages(updatedMessages)
      setStreamingMessage('')

      // Update conversation with new messages
      setConversations(prev => prev.map(conv => 
        conv.id === currentConversationId 
          ? { 
              ...conv, 
              messages: updatedMessages
            }
          : conv
      ))
    } catch (error) {
      if (error.name !== 'AbortError') {
        console.error('Error sending message:', error)
      }
    } finally {
      setIsLoading(false)
      setIsRequestInProgress(false)
    }
  }

  const handleNewConversation = () => {
    const newId = Date.now().toString()
    setMessages([])
    setInput('')
    setCurrentConversationId(newId)
    setConversations(prev => [
      { 
        id: newId,
        title: t('new'),
        messages: []
      },
      ...prev
    ])
  }

  const handleSelectConversation = (conversationId) => {
    setCurrentConversationId(conversationId)
  }

  // Modify the resumeStreaming function to prevent concurrent requests
  const resumeStreaming = async (conversationId) => {
    if (isRequestInProgress) return
    
    const conversation = conversations.find(c => c.id === conversationId)
    if (!conversation || !conversation.isStreaming || !conversation.lastMessageId) return

    setIsLoading(true)
    setIsRequestInProgress(true)
    try {
      console.log('Resuming chat completion...');
      abortControllerRef.current = new AbortController()
      const response = await fetch('https://api.swissai.cscs.ch/v1/chat/completions', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${swissAIToken}`
        },
        body: JSON.stringify({
          model: selectedModel,
          messages: conversation.messages,
          stream: true,
          temperature: settings.temperature ?? 0.7,
          top_p: settings.top_p ?? 1,
          max_tokens: settings.max_tokens || 2048
        }),
        signal: abortControllerRef.current.signal
      })
      
      if (!response.ok) {
        const errorText = await response.text();
        console.error('Chat completion failed:', response.status, errorText);
        throw new Error(`Chat completion failed: ${response.status} ${errorText}`);
      }
      
      if (!response.body) throw new Error('No response body')
      const reader = response.body.getReader()
      let fullText = ''
      let done = false
      while (!done) {
        const { value, done: doneReading } = await reader.read()
        done = doneReading
        if (value) {
          const chunk = new TextDecoder().decode(value)
          chunk.split('\n').forEach(line => {
            if (line.startsWith('data: ')) {
              const data = line.replace('data: ', '').trim()
              if (data && data !== '[DONE]') {
                try {
                  const parsed = JSON.parse(data)
                  const delta = parsed.choices?.[0]?.delta?.content || ''
                  fullText += delta
                  setConversations(prev => prev.map(conv => 
                    conv.id === conversationId 
                      ? { ...conv, streamingMessage: fullText }
                      : conv
                  ))
                } catch (error) {
                  console.error('Error parsing streaming data:', error, data);
                }
              }
            }
          })
        }
      }
      console.log('Chat completion finished');
      const assistantMessage = { role: 'assistant', content: fullText }
      const updatedMessages = [...conversation.messages, assistantMessage]
      setMessages(updatedMessages)

      setConversations(prev => prev.map(conv => 
        conv.id === conversationId 
          ? { 
              ...conv, 
              messages: updatedMessages,
              streamingMessage: '',
              isStreaming: false,
              lastMessageId: null
            } 
          : conv
      ))
    } catch (error) {
      if (error.name !== 'AbortError') {
        console.error('Error resuming message:', error)
      }
      setConversations(prev => prev.map(conv => 
        conv.id === conversationId 
          ? { 
              ...conv, 
              streamingMessage: '',
              isStreaming: false,
              lastMessageId: null
            } 
          : conv
      ))
    } finally {
      setIsLoading(false)
      setIsRequestInProgress(false)
    }
  }

  // Modify the effect to prevent concurrent requests
  useEffect(() => {
    if (currentConversationId && !isRequestInProgress) {
      const conversation = conversations.find(c => c.id === currentConversationId)
      if (conversation?.isStreaming) {
        resumeStreaming(currentConversationId)
      }
    }
  }, [currentConversationId, isRequestInProgress])

  const handleExportConversations = () => {
    const data = {
      conversations: conversations.map(conv => ({
        ...conv,
        title: conv.title.replace(/<think>.*?<\/think>/g, '').replace(/\s+/g, ' ').trim()
      })),
      settings,
      exportDate: new Date().toISOString()
    }
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `chat-export-${new Date().toISOString().split('T')[0]}.json`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  }

  const handleImportConversations = (event) => {
    const file = event.target.files[0]
    if (file) {
      const reader = new FileReader()
      reader.onload = (e) => {
        try {
          const data = JSON.parse(e.target.result)
          if (data.conversations) {
            // Clean titles when importing
            const cleanedConversations = data.conversations.map(conv => ({
              ...conv,
              title: conv.title.replace(/<think>.*?<\/think>/g, '').replace(/\s+/g, ' ').trim()
            }))
            setConversations(cleanedConversations)
            // If there are conversations, select the first one
            if (cleanedConversations.length > 0) {
              setCurrentConversationId(cleanedConversations[0].id)
            }
          }
          if (data.settings) setSettings(data.settings)
        } catch (error) {
          console.error('Error importing conversations:', error)
          alert('Error importing conversations. Please check the file format.')
        }
      }
      reader.readAsText(file)
    }
  }

  const handleDeleteConversation = (conversationId) => {
    if (window.confirm(t('deleteConversationConfirm'))) {
      setConversations(prev => prev.filter(conv => conv.id !== conversationId))
      if (currentConversationId === conversationId) {
        setCurrentConversationId(null)
        setMessages([])
      }
    }
  }

  const handleClearAllConversations = () => {
    if (window.confirm(t('clearAllConversationsConfirm'))) {
      setConversations([])
      setCurrentConversationId(null)
      setMessages([])
    }
  }

  const handleLanguageChange = (language) => {
    i18n.changeLanguage(language)
  }

  // Header for mobile
  const Header = () => (
    <div className="md:hidden fixed top-0 left-0 right-0 flex items-center justify-between p-4 border-b bg-background z-50 shadow-sm">
      <button 
        onClick={() => setSidebarOpen(true)} 
        className="p-2 hover:bg-muted rounded-full transition-colors"
        aria-label="Open menu"
      >
        <span className="material-icons">menu</span>
      </button>
      <div className="flex flex-col items-center">
        <span className="font-semibold text-lg">SwissAI Chat</span>
        {selectedModel && (
          <span className="text-xs text-muted-foreground">{selectedModel}</span>
        )}
      </div>
      <button 
        onClick={() => setSettingsOpen(true)} 
        className="p-2 hover:bg-muted rounded-full transition-colors"
        aria-label="Open settings"
      >
        <span className="material-icons">settings</span>
      </button>
    </div>
  )

  if (authLoading) {
    return (
      <div className="flex h-screen w-screen items-center justify-center bg-background">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto mb-4"></div>
          <p className="text-muted-foreground">{t('loading')}</p>
        </div>
      </div>
    )
  }

  if (!isAuthenticated) {
    return (
      <div className="flex h-screen w-screen items-center justify-center bg-background">
        <div className="text-center">
          <h1 className="text-2xl font-bold mb-4">{t('welcome')}</h1>
          <p className="text-muted-foreground mb-8">{t('loginPrompt')}</p>
          <button
            onClick={login}
            className="px-6 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 transition-colors"
          >
            {t('login')}
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="flex h-screen w-screen bg-background overflow-hidden">
      <Header />
      <Sidebar
        open={sidebarOpen}
        onClose={() => setSidebarOpen(false)}
        conversations={conversations}
        currentConversationId={currentConversationId}
        onNewConversation={handleNewConversation}
        onSelectConversation={handleSelectConversation}
        onExport={handleExportConversations}
        onImport={handleImportConversations}
        onDeleteConversation={handleDeleteConversation}
        onClearAllConversations={handleClearAllConversations}
        onLogout={logout}
        user={user}
      />
      <div className="flex-1 flex flex-col min-h-0 transition-all duration-200 md:mt-0 mt-16">
        <ChatWindow
          messages={messages}
          input={input}
          onInputChange={(e) => setInput(e.target.value)}
          onSend={handleSend}
          isLoading={isLoading}
          streamingMessage={streamingMessage}
          username={user?.name || 'You'}
          modelName={selectedModel || 'Assistant'}
        />
      </div>
      <div className="hidden md:block">
        <SettingsPanel
          open={true}
          onClose={() => setSettingsOpen(false)}
          settings={settings}
          onChange={setSettings}
          models={models}
          selectedModel={selectedModel}
          onModelChange={(e) => setSelectedModel(e.target.value)}
          onLanguageChange={handleLanguageChange}
          currentLanguage={i18n.language}
          isAgentMode={isAgentMode}
          onModeChange={setIsAgentMode}
        />
      </div>
      <div className="md:hidden">
        <SettingsPanel
          open={settingsOpen}
          onClose={() => setSettingsOpen(false)}
          settings={settings}
          onChange={setSettings}
          models={models}
          selectedModel={selectedModel}
          onModelChange={(e) => setSelectedModel(e.target.value)}
          onLanguageChange={handleLanguageChange}
          currentLanguage={i18n.language}
          isAgentMode={isAgentMode}
          onModeChange={setIsAgentMode}
        />
      </div>
    </div>
  )
}

function App() {
  return (
    <Auth0Provider
      domain={import.meta.env.VITE_AUTH0_DOMAIN}
      clientId={import.meta.env.VITE_AUTH0_CLIENT_ID}
      authorizationParams={{
        redirect_uri: window.location.origin
      }}
      cacheLocation="localstorage"
      useRefreshTokens={true}
    >
      <AuthProvider>
        <AppContent />
      </AuthProvider>
    </Auth0Provider>
  )
}

export default App
