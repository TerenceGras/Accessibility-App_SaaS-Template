import React, { useState, useEffect, Fragment } from 'react'
import { Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import { Dialog, Transition } from '@headlessui/react'
import useAuthStore from '../stores/authStore'
import { KeyIcon, ClipboardDocumentIcon, TrashIcon, PlusIcon, ExclamationTriangleIcon, LockClosedIcon } from '@heroicons/react/24/outline'
import { CheckIcon } from '@heroicons/react/24/solid'
import toast from 'react-hot-toast'
import PageContainer, { PageCard } from '../components/PageContainer'
import { useTranslation } from '../hooks/useTranslation'
import logger from '../utils/logger'

const API_URL = import.meta.env.VITE_API_URL || ''
const PRICING_API_URL = import.meta.env.VITE_PRICING_API_URL || ''

// Syntax highlighting component for JSON code blocks
const JsonCodeBlock = ({ code }) => {
  const { t } = useTranslation()
  const copyCode = () => {
    navigator.clipboard.writeText(code)
    toast.success(t('api.toasts.codeCopied'))
  }

  const highlightJson = (source) => {
    const tokens = []
    let i = 0
    
    while (i < source.length) {
      // Strings (double quotes)
      if (source[i] === '"') {
        let end = i + 1
        while (end < source.length && source[end] !== '"') {
          if (source[end] === '\\') end++
          end++
        }
        tokens.push({ type: 'string', value: source.slice(i, end + 1) })
        i = end + 1
        continue
      }
      
      // Numbers
      if (/[0-9\-]/.test(source[i]) && (source[i] === '-' ? /[0-9]/.test(source[i + 1]) : true)) {
        let end = i
        if (source[end] === '-') end++
        while (end < source.length && /[0-9.]/.test(source[end])) end++
        const num = source.slice(i, end)
        if (num !== '-' && num !== '.') {
          tokens.push({ type: 'number', value: num })
          i = end
          continue
        }
      }
      
      // Booleans and null
      const keywords = ['true', 'false', 'null']
      let matched = false
      for (const keyword of keywords) {
        if (source.substr(i, keyword.length) === keyword) {
          tokens.push({ type: 'boolean', value: keyword })
          i += keyword.length
          matched = true
          break
        }
      }
      if (matched) continue
      
      // Braces, brackets, colons, commas
      if (/[{}[\]:,]/.test(source[i])) {
        let type = 'text'
        if (source[i] === '{' || source[i] === '}') type = 'brace'
        else if (source[i] === '[' || source[i] === ']') type = 'bracket'
        else if (source[i] === ':') type = 'colon'
        else if (source[i] === ',') type = 'comma'
        tokens.push({ type, value: source[i] })
        i++
        continue
      }
      
      // Everything else (whitespace, etc)
      tokens.push({ type: 'text', value: source[i] })
      i++
    }
    
    // Convert tokens to HTML with light/dark theme support
    return tokens.map(t => {
      const escaped = t.value.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
      switch (t.type) {
        case 'string': return `<span class="json-string">${escaped}</span>`
        case 'number': return `<span class="json-number">${escaped}</span>`
        case 'boolean': return `<span class="json-boolean">${escaped}</span>`
        case 'brace': return `<span class="json-brace">${escaped}</span>`
        case 'bracket': return `<span class="json-bracket">${escaped}</span>`
        case 'colon': return `<span class="json-punctuation">${escaped}</span>`
        case 'comma': return `<span class="json-punctuation">${escaped}</span>`
        default: return escaped
      }
    }).join('')
  }

  return (
    <div className="relative group">
      <button
        onClick={copyCode}
        className="absolute top-2 right-2 p-1.5 bg-gray-700 hover:bg-gray-600 rounded text-gray-300 opacity-0 group-hover:opacity-100 transition-opacity z-10"
        title={t('api.codeBlocks.copyCode')}
      >
        <ClipboardDocumentIcon className="h-4 w-4" />
      </button>
      <pre className="bg-gray-100 dark:bg-gray-900 p-4 rounded-lg text-sm overflow-x-auto border border-gray-300 dark:border-gray-700 font-mono leading-relaxed text-gray-800 dark:text-gray-200">
        <code dangerouslySetInnerHTML={{ __html: highlightJson(code) }} />
        <style>{`
          .json-string { color: #059669; font-weight: 500; }
          .json-number { color: #7c3aed; font-weight: 500; }
          .json-boolean { color: #dc2626; font-weight: 600; }
          .json-brace { color: #1f2937; font-weight: 700; }
          .json-bracket { color: #1f2937; font-weight: 700; }
          .json-punctuation { color: #1f2937; }
          
          .dark .json-string { color: #50fa7b; }
          .dark .json-number { color: #bd93f9; }
          .dark .json-boolean { color: #ff79c6; }
          .dark .json-brace { color: #f8f8f2; }
          .dark .json-bracket { color: #f8f8f2; }
          .dark .json-punctuation { color: #f8f8f2; }
        `}</style>
      </pre>
    </div>
  )
}

// Syntax highlighting component for Python code blocks - uses simple CSS classes
const PythonCodeBlock = ({ code }) => {
  const { t } = useTranslation()
  const copyCode = () => {
    navigator.clipboard.writeText(code)
    toast.success(t('api.toasts.codeCopied'))
  }

  // Simple token-based highlighting that doesn't corrupt itself
  const highlightPython = (source) => {
    const tokens = []
    let i = 0
    
    while (i < source.length) {
      // Comments
      if (source[i] === '#') {
        let end = source.indexOf('\n', i)
        if (end === -1) end = source.length
        tokens.push({ type: 'comment', value: source.slice(i, end) })
        i = end
        continue
      }
      
      // Strings (double quotes)
      if (source[i] === '"') {
        let end = i + 1
        while (end < source.length && source[end] !== '"') {
          if (source[end] === '\\') end++
          end++
        }
        tokens.push({ type: 'string', value: source.slice(i, end + 1) })
        i = end + 1
        continue
      }
      
      // Strings (single quotes)
      if (source[i] === "'") {
        let end = i + 1
        while (end < source.length && source[end] !== "'") {
          if (source[end] === '\\') end++
          end++
        }
        tokens.push({ type: 'string', value: source.slice(i, end + 1) })
        i = end + 1
        continue
      }
      
      // Words (identifiers, keywords)
      if (/[a-zA-Z_]/.test(source[i])) {
        let end = i
        while (end < source.length && /[a-zA-Z0-9_]/.test(source[end])) end++
        const word = source.slice(i, end)
        const keywords = ['import', 'from', 'as', 'if', 'else', 'elif', 'for', 'while', 'try', 'except', 'finally', 'with', 'return', 'def', 'class', 'and', 'or', 'not', 'in', 'is', 'None', 'True', 'False']
        const builtins = ['print', 'len', 'str', 'int', 'float', 'list', 'dict', 'open', 'range', 'type']
        if (keywords.includes(word)) {
          tokens.push({ type: 'keyword', value: word })
        } else if (builtins.includes(word)) {
          tokens.push({ type: 'builtin', value: word })
        } else {
          tokens.push({ type: 'text', value: word })
        }
        i = end
        continue
      }
      
      // Numbers
      if (/[0-9]/.test(source[i])) {
        let end = i
        while (end < source.length && /[0-9.]/.test(source[end])) end++
        tokens.push({ type: 'number', value: source.slice(i, end) })
        i = end
        continue
      }
      
      // Everything else (operators, punctuation, whitespace)
      tokens.push({ type: 'text', value: source[i] })
      i++
    }
    
    // Convert tokens to HTML with light/dark theme support
    return tokens.map(t => {
      const escaped = t.value.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
      switch (t.type) {
        case 'keyword': return `<span class="py-keyword">${escaped}</span>`
        case 'string': return `<span class="py-string">${escaped}</span>`
        case 'number': return `<span class="py-number">${escaped}</span>`
        case 'comment': return `<span class="py-comment">${escaped}</span>`
        case 'builtin': return `<span class="py-builtin">${escaped}</span>`
        default: return escaped
      }
    }).join('')
  }

  return (
    <div className="relative group">
      <button
        onClick={copyCode}
        className="absolute top-2 right-2 p-1.5 bg-gray-700 hover:bg-gray-600 rounded text-gray-300 opacity-0 group-hover:opacity-100 transition-opacity z-10"
        title={t('api.codeBlocks.copyCode')}
      >
        <ClipboardDocumentIcon className="h-4 w-4" />
      </button>
      <pre className="bg-gray-100 dark:bg-gray-900 p-4 rounded-lg text-sm overflow-x-auto border border-gray-300 dark:border-gray-700 font-mono leading-relaxed text-gray-800 dark:text-gray-200">
        <code dangerouslySetInnerHTML={{ __html: highlightPython(code) }} />
        <style>{`
          .py-keyword { color: #d97706; font-weight: 600; }
          .py-string { color: #059669; font-weight: 500; }
          .py-number { color: #7c3aed; font-weight: 500; }
          .py-comment { color: #6b7280; font-style: italic; }
          .py-builtin { color: #0891b2; font-weight: 500; }
          
          .dark .py-keyword { color: #ff79c6; font-weight: 500; }
          .dark .py-string { color: #50fa7b; }
          .dark .py-number { color: #bd93f9; }
          .dark .py-comment { color: #6272a4; font-style: italic; }
          .dark .py-builtin { color: #8be9fd; }
        `}</style>
      </pre>
    </div>
  )
}

// Delete confirmation modal component
const DeleteConfirmModal = ({ isOpen, onClose, onConfirm, keyName }) => {
  const { t } = useTranslation()

  return (
    <Transition appear show={isOpen} as={Fragment}>
      <Dialog as="div" className="relative z-50" onClose={onClose}>
        <Transition.Child
          as={Fragment}
          enter="ease-out duration-300"
          enterFrom="opacity-0"
          enterTo="opacity-100"
          leave="ease-in duration-200"
          leaveFrom="opacity-100"
          leaveTo="opacity-0"
        >
          <div className="fixed inset-0 bg-black bg-opacity-50" />
        </Transition.Child>

        <div className="fixed inset-0 overflow-y-auto">
          <div className="flex min-h-full items-center justify-center p-4 text-center">
            <Transition.Child
              as={Fragment}
              enter="ease-out duration-300"
              enterFrom="opacity-0 scale-95"
              enterTo="opacity-100 scale-100"
              leave="ease-in duration-200"
              leaveFrom="opacity-100 scale-100"
              leaveTo="opacity-0 scale-95"
            >
              <Dialog.Panel className="w-full max-w-md transform overflow-hidden rounded-lg bg-white dark:bg-gray-800 shadow-xl transition-all">
                <div className="p-6">
                  <div className="flex items-center justify-center w-12 h-12 mx-auto bg-red-100 dark:bg-red-900/30 rounded-full mb-4">
                    <ExclamationTriangleIcon className="h-6 w-6 text-red-600 dark:text-red-400" />
                  </div>
                  <Dialog.Title as="h3" className="text-lg font-semibold text-gray-900 dark:text-white text-center mb-2">
                    {t('api.revokeModal.title')}
                  </Dialog.Title>
                  <p className="text-sm text-gray-600 dark:text-gray-400 text-center mb-2">
                    {t('api.revokeModal.description')}
                  </p>
                  <p className="text-sm font-mono bg-gray-100 dark:bg-gray-700 px-3 py-2 rounded text-center text-gray-900 dark:text-white mb-4">
                    {keyName}
                  </p>
                  <p className="text-xs text-red-600 dark:text-red-400 text-center mb-6">
                    {t('api.revokeModal.warning')}
                  </p>
                  <div className="flex space-x-3">
                    <button
                      onClick={onClose}
                      className="flex-1 px-4 py-2 bg-gray-100 hover:bg-gray-200 dark:bg-gray-700 dark:hover:bg-gray-600 text-gray-700 dark:text-gray-300 rounded-md font-medium transition-colors duration-200"
                    >
                      {t('common.cancel')}
                    </button>
                    <button
                      onClick={onConfirm}
                      className="flex-1 px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-md font-medium transition-colors duration-200"
                    >
                      {t('api.revokeModal.confirm')}
                    </button>
                  </div>
                </div>
              </Dialog.Panel>
            </Transition.Child>
          </div>
        </div>
      </Dialog>
    </Transition>
  )
}

// Configuration Options component with styled sections
const ConfigOptionsBlock = ({ platform }) => {
  const platformConfigs = {
    github: {
      baseConfig: [
        { key: 'web_scan_enabled', desc: 'Enable/disable web scan results push' },
        { key: 'pdf_scan_enabled', desc: 'Enable/disable PDF scan results push' },
        { key: 'repository', desc: 'GitHub repository (format: "owner/repo")' },
        { key: 'label', desc: 'Issue label (default: "accessibility")' },
      ]
    },
    notion: {
      baseConfig: [
        { key: 'web_scan_enabled', desc: 'Enable/disable web scan results push' },
        { key: 'pdf_scan_enabled', desc: 'Enable/disable PDF scan results push' },
        { key: 'page_url', desc: 'Notion parent page URL' },
      ]
    },
    slack: {
      baseConfig: [
        { key: 'web_scan_enabled', desc: 'Enable/disable web scan results push' },
        { key: 'pdf_scan_enabled', desc: 'Enable/disable PDF scan results push' },
        { key: 'channel_id', desc: 'Slack channel ID for posting results' },
      ]
    }
  }

  const webScanOptions = [
    { key: 'wcag_enabled', desc: 'Push WCAG/axe-core violations' },
    { key: 'html_enabled', desc: 'Push HTML validation errors' },
    { key: 'links_enabled', desc: 'Push broken link results' },
    { key: 'axtree_enabled', desc: 'Push accessibility tree' },
    { key: 'layout_enabled', desc: 'Push layout testing results' },
    { key: 'wcag_grouping_option', desc: '"per-error-type" or "single-issue"' },
    { key: 'wcag_regroup_violations', desc: 'Group violations by rule type' },
    { key: 'wcag_severity_filter', desc: 'Array of ["High", "Medium", "Low"]' },
    { key: 'html_grouping_option', desc: '"per-error-type" or "single-issue"' },
    { key: 'links_grouping_option', desc: '"per-error-type" or "single-issue"' },
    { key: 'layout_grouping_option', desc: '"per-error-type" or "single-issue"' },
  ]

  const pdfScanOptions = [
    { key: 'pdf_grouping_option', desc: '"per-page" or "single-issue"' },
  ]

  const config = platformConfigs[platform]

  const renderSection = (title, options, colorClass) => (
    <div className="mb-3 last:mb-0">
      <div className={`flex items-center mb-2`}>
        <span className={`w-1.5 h-1.5 ${colorClass} rounded-full mr-2`}></span>
        <span className="text-xs font-semibold text-gray-700 dark:text-gray-300 uppercase tracking-wide">{title}</span>
      </div>
      <div className="ml-3.5 space-y-1">
        {options.map((opt, idx) => (
          <div key={idx} className="flex text-xs">
            <code className="text-purple-600 dark:text-purple-400 font-medium mr-1.5">{opt.key}</code>
            <span className="text-gray-500 dark:text-gray-500">—</span>
            <span className="text-gray-600 dark:text-gray-400 ml-1.5">{opt.desc}</span>
          </div>
        ))}
      </div>
    </div>
  )

  return (
    <div className="bg-gradient-to-br from-gray-50 to-slate-50 dark:from-gray-900 dark:to-slate-900 p-3 rounded-lg text-xs border border-gray-200 dark:border-gray-700">
      {renderSection('Base Config', config.baseConfig, 'bg-blue-500')}
      {renderSection('Web Scan Sections', webScanOptions, 'bg-green-500')}
      {renderSection('PDF Scan Sections', pdfScanOptions, 'bg-orange-500')}
    </div>
  )
}

const APIPage = () => {
  const { t } = useTranslation()
  const { user, getIdToken, loading: authLoading } = useAuthStore()
  const [apiKeys, setApiKeys] = useState([])
  const [loading, setLoading] = useState(true)
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [newKeyName, setNewKeyName] = useState('')
  const [validityPeriod, setValidityPeriod] = useState('1month')
  const [createdKey, setCreatedKey] = useState(null)
  const [copiedKey, setCopiedKey] = useState(false)
  const [deleteModal, setDeleteModal] = useState({ isOpen: false, keyId: null, keyName: '' })
  const [subscription, setSubscription] = useState(null)

  useEffect(() => {
    if (user && !authLoading) {
      loadAPIKeys()
      loadSubscription()
    } else if (!user && !authLoading) {
      // User not logged in, no need to load API keys
      setLoading(false)
    }
  }, [user, authLoading])

  const loadSubscription = async () => {
    try {
      const token = await getIdToken()
      const response = await fetch(`${PRICING_API_URL}/subscription`, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      })
      
      if (response.ok) {
        const data = await response.json()
        setSubscription(data.subscription)
      }
    } catch (error) {
      logger.error('Error fetching subscription:', error)
    }
  }

  // API access is now available to all logged-in users
  const hasApiAccess = true  // Was: subscription && subscription.plan !== 'free' && subscription.status === 'active'

  const loadAPIKeys = async () => {
    try {
      const token = await getIdToken()
      const response = await fetch(`${API_URL}/api-keys/list`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      })

      if (response.ok) {
        const data = await response.json()
        setApiKeys(data.keys)
      } else {
        toast.error(t('api.toasts.loadKeysFailed'))
      }
    } catch (error) {
      logger.error('Error loading API keys:', error)
      toast.error(t('api.toasts.loadKeysFailed'))
    } finally {
      setLoading(false)
    }
  }

  const handleCreateKey = async () => {
    if (!newKeyName.trim()) {
      toast.error(t('api.toasts.enterKeyName'))
      return
    }

    // Validate key name
    if (!/^[a-z0-9_-]+$/.test(newKeyName)) {
      toast.error(t('api.toasts.invalidKeyName'))
      return
    }

    try {
      const token = await getIdToken()
      const response = await fetch(`${API_URL}/api-keys/create`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          key_name: newKeyName,
          validity_period: validityPeriod
        })
      })

      if (response.ok) {
        const data = await response.json()
        setCreatedKey(data)
        setNewKeyName('')
        toast.success(t('api.toasts.keyCreated'))
        loadAPIKeys()
      } else {
        const error = await response.json()
        logger.error('API key creation failed:', error.detail)
        toast.error(t('api.toasts.createFailed'))
      }
    } catch (error) {
      logger.error('Error creating API key:', error)
      toast.error(t('api.toasts.createFailed'))
    }
  }

  const handleRevokeKey = async (keyId, keyName) => {
    setDeleteModal({ isOpen: true, keyId, keyName })
  }

  const confirmRevokeKey = async () => {
    const { keyId } = deleteModal
    setDeleteModal({ isOpen: false, keyId: null, keyName: '' })

    try {
      const token = await getIdToken()
      const response = await fetch(`${API_URL}/api-keys/${keyId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      })

      if (response.ok) {
        toast.success(t('api.toasts.keyRevoked'))
        loadAPIKeys()
      } else {
        toast.error(t('api.toasts.revokeFailed'))
      }
    } catch (error) {
      logger.error('Error revoking API key:', error)
      toast.error(t('api.toasts.revokeFailed'))
    }
  }

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text)
    setCopiedKey(true)
    toast.success(t('api.toasts.keyCopied'))
    setTimeout(() => setCopiedKey(false), 2000)
  }

  const formatDate = (dateString) => {
    if (!dateString) return 'Never'
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    })
  }

  if (authLoading || loading) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex items-center justify-center">
        <div className="text-gray-600 dark:text-gray-400">{t('common.loading')}</div>
      </div>
    )
  }

  // Determine access state: not logged in, free user, or paid user
  const isLoggedIn = !!user
  const canCreateKeys = isLoggedIn && hasApiAccess

  return (
    <PageContainer
      title={t('api.pageTitle')}
      description={t('api.pageDescription')}
    >
      {/* API Keys Section - Locked for non-logged-in or free users */}
      {!canCreateKeys ? (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4 }}
          className="relative mb-8"
        >
          {/* Blurred API Keys section */}
          <div className="filter blur-sm pointer-events-none select-none opacity-60">
            <PageCard>
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-xl font-semibold text-gray-900 dark:text-white">{t('api.yourApiKeys')}</h2>
              </div>
              <div className="text-center py-12">
                <div className="inline-flex items-center justify-center h-16 w-16 rounded-2xl bg-gray-100 dark:bg-gray-700 mb-4">
                  <KeyIcon className="h-8 w-8 text-gray-400" />
                </div>
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white">{t('api.noApiKeysYet')}</h3>
              </div>
            </PageCard>
          </div>
          
          {/* Overlay with lock message - only covers API Keys section */}
          <div className="absolute inset-0 flex items-center justify-center">
            <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-2xl border border-gray-200 dark:border-gray-700 p-8 max-w-md mx-4 text-center">
              <div className="flex justify-center mb-4">
                <div className="p-3 bg-amber-100 dark:bg-amber-900/30 rounded-full">
                  <LockClosedIcon className="h-8 w-8 text-amber-600 dark:text-amber-400" />
                </div>
              </div>
              {!isLoggedIn ? (
                <>
                  <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
                    {t('api.loginRequiredTitle')}
                  </h3>
                  <p className="text-sm text-gray-600 dark:text-gray-400 mb-6">
                    {t('api.loginRequiredDescription')}
                  </p>
                  <Link
                    to="/auth?mode=signin"
                    className="inline-flex items-center px-6 py-3 bg-primary-600 hover:bg-primary-700 text-white rounded-xl font-medium transition-colors shadow-lg hover:shadow-xl"
                  >
                    {t('common.signIn')}
                  </Link>
                </>
              ) : (
                <>
                  <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
                    {t('api.apiAccessRequiresPaidSubscription')}
                  </h3>
                  <p className="text-sm text-gray-600 dark:text-gray-400 mb-6">
                    {t('api.apiAccessDescription')}
                  </p>
                  <Link
                    to="/pricing"
                    className="inline-flex items-center px-6 py-3 bg-primary-600 hover:bg-primary-700 text-white rounded-xl font-medium transition-colors shadow-lg hover:shadow-xl"
                  >
                    {t('api.viewPlansAndUpgrade')}
                  </Link>
                </>
              )}
            </div>
          </div>
        </motion.div>
      ) : (
        <>
          {/* API Keys Section - Visible for paid users */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4 }}
          >
            <PageCard className="mb-8">
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-xl font-semibold text-gray-900 dark:text-white">{t('api.yourApiKeys')}</h2>
                <button
                  onClick={() => setShowCreateModal(true)}
                  className="inline-flex items-center px-4 py-2 bg-primary-500 hover:bg-primary-600 text-white rounded-xl font-medium transition-all duration-200 shadow-sm hover:shadow-md active:scale-[0.98]"
                >
                  <PlusIcon className="h-5 w-5 mr-2" />
                  {t('api.createKey')}
                </button>
              </div>

              {apiKeys.length === 0 ? (
            <div className="text-center py-12">
              <div className="inline-flex items-center justify-center h-16 w-16 rounded-2xl bg-gray-100 dark:bg-gray-700 mb-4">
                <KeyIcon className="h-8 w-8 text-gray-400" />
              </div>
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white">{t('api.noApiKeysYet')}</h3>
              <p className="mt-2 text-gray-500 dark:text-gray-400 max-w-md mx-auto">
                {t('api.clickCreateKeyToGetStarted')}
              </p>
            </div>
          ) : (
            <div className="space-y-3">
              {apiKeys.map((key, index) => (
                <motion.div
                  key={key.key_id}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.3, delay: index * 0.05 }}
                  className="flex items-center justify-between p-4 bg-gray-50 dark:bg-gray-700/50 rounded-xl border border-gray-200 dark:border-gray-600 hover:border-primary-300 dark:hover:border-primary-600 transition-colors"
                >
                  <div className="flex-1">
                    <div className="flex items-center space-x-3">
                      <div className="p-2 bg-primary-100 dark:bg-primary-900/30 rounded-lg">
                        <KeyIcon className="h-5 w-5 text-primary-600 dark:text-primary-400" />
                      </div>
                      <div>
                        <h3 className="text-sm font-medium text-gray-900 dark:text-white">
                          {key.key_name}
                        </h3>
                        <div className="flex items-center space-x-4 mt-1 text-xs text-gray-500 dark:text-gray-400">
                          <span>{t('api.created')}: {formatDate(key.created_at)}</span>
                          {key.expires_at ? (
                            <span>{t('api.expires')}: {formatDate(key.expires_at)}</span>
                            ) : (
                              <span className="text-amber-600 dark:text-amber-400">{t('api.noExpiration')}</span>
                            )}
                            {key.last_used && <span>{t('api.lastUsed')}: {formatDate(key.last_used)}</span>}
                            <span>{t('api.requests')}: {key.request_count}</span>
                          </div>
                        </div>
                      </div>
                    </div>
                    <button
                      onClick={() => handleRevokeKey(key.key_id, key.key_name)}
                      className="ml-4 p-2 text-red-600 hover:bg-red-100 dark:hover:bg-red-900/20 rounded-xl transition-colors duration-200"
                      title={t('api.revokeThisKey')}
                    >
                      <TrashIcon className="h-5 w-5" />
                    </button>
                  </motion.div>
                ))}
              </div>
            )}
        </PageCard>
      </motion.div>
        </>
      )}

      {/* API Documentation Section - Always visible */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4, delay: 0.1 }}
      >
        <PageCard>
          <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-6">{t('api.documentation.title')}</h2>
          
          <div className="space-y-6">
            {/* Base URL */}
            <div className="bg-primary-50 dark:bg-primary-900/20 rounded-xl p-4 border border-primary-100 dark:border-primary-800">
              <h3 className="text-lg font-medium text-primary-900 dark:text-primary-100 mb-2">{t('api.documentation.baseUrl')}</h3>
              <code className="text-sm bg-primary-100 dark:bg-primary-900/40 px-3 py-2 rounded-lg inline-block font-mono">
                https://dev-api.your-domain.com
              </code>
            </div>

            {/* Authentication */}
            <div>
              <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">{t('api.documentation.authentication')}</h3>
              <p className="text-sm text-gray-600 dark:text-gray-400 mb-2">
                {t('api.documentation.authDescription')}
              </p>
              <pre className="bg-gray-100 dark:bg-gray-900 p-3 rounded-xl text-sm overflow-x-auto border border-gray-200 dark:border-gray-700">
                <code className="text-gray-800 dark:text-gray-200">Authorization: Bearer YOUR_API_KEY</code>
              </pre>
              <div className="mt-2 text-xs text-gray-500 dark:text-gray-400">
                <strong>{t('api.documentation.rateLimit')}:</strong> {t('api.documentation.rateLimitDescription')}
              </div>
            </div>

            {/* Credits System */}
            <div className="bg-amber-50 dark:bg-amber-900/20 rounded-xl p-4 border border-amber-100 dark:border-amber-800">
                <h3 className="text-lg font-medium text-amber-900 dark:text-amber-100 mb-2">{t('api.documentation.creditsSystem')}</h3>
                <div className="text-sm text-amber-800 dark:text-amber-200 space-y-1">
                  <p>• <strong>{t('api.documentation.webScans')}:</strong> {t('api.documentation.webScansCredits')}</p>
                  <p>• <strong>{t('api.documentation.pdfScans')}:</strong> {t('api.documentation.pdfScansCredits')}</p>
                  <p className="mt-2 text-xs">{t('api.documentation.creditsDeducted')} <code className="bg-amber-100 dark:bg-amber-900/40 px-1 rounded">/account</code> {t('api.documentation.endpoint')}.</p>
                </div>
              </div>

              {/* Navigation Menu */}
              <div className="bg-gradient-to-r from-blue-50 to-indigo-50 dark:from-blue-900/20 dark:to-indigo-900/20 rounded-lg p-4 border border-blue-100 dark:border-blue-800">
                <div className="flex items-center mb-3">
                  <div className="w-1 h-5 bg-blue-500 rounded-full mr-2"></div>
                  <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300 uppercase tracking-wide">{t('api.documentation.quickNavigation')}</h3>
                </div>
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
                  <a href="#general-routes" className="flex items-center px-3 py-2 bg-white dark:bg-gray-800 rounded-md border border-gray-200 dark:border-gray-700 hover:border-blue-400 dark:hover:border-blue-500 hover:shadow-sm transition-all group">
                    <span className="w-2 h-2 bg-green-500 rounded-full mr-2"></span>
                    <span className="text-sm text-gray-700 dark:text-gray-300 group-hover:text-blue-600 dark:group-hover:text-blue-400">{t('api.documentation.general')}</span>
                  </a>
                  <a href="#web-scan" className="flex items-center px-3 py-2 bg-white dark:bg-gray-800 rounded-md border border-gray-200 dark:border-gray-700 hover:border-blue-400 dark:hover:border-blue-500 hover:shadow-sm transition-all group">
                    <span className="w-2 h-2 bg-blue-500 rounded-full mr-2"></span>
                    <span className="text-sm text-gray-700 dark:text-gray-300 group-hover:text-blue-600 dark:group-hover:text-blue-400">{t('api.documentation.webScan')}</span>
                  </a>
                  <a href="#pdf-scan" className="flex items-center px-3 py-2 bg-white dark:bg-gray-800 rounded-md border border-gray-200 dark:border-gray-700 hover:border-blue-400 dark:hover:border-blue-500 hover:shadow-sm transition-all group">
                    <span className="w-2 h-2 bg-orange-500 rounded-full mr-2"></span>
                    <span className="text-sm text-gray-700 dark:text-gray-300 group-hover:text-blue-600 dark:group-hover:text-blue-400">{t('api.documentation.pdfScan')}</span>
                  </a>
                  <a href="#integrations" className="flex items-center px-3 py-2 bg-white dark:bg-gray-800 rounded-md border border-gray-200 dark:border-gray-700 hover:border-blue-400 dark:hover:border-blue-500 hover:shadow-sm transition-all group">
                    <span className="w-2 h-2 bg-purple-500 rounded-full mr-2"></span>
                    <span className="text-sm text-gray-700 dark:text-gray-300 group-hover:text-blue-600 dark:group-hover:text-blue-400">{t('api.documentation.integrations')}</span>
                  </a>
                </div>
              </div>

              <hr className="border-gray-200 dark:border-gray-700" />

              {/* GENERAL ROUTES */}
              <div id="general-routes">
                <h3 className="text-2xl font-bold text-gray-900 dark:text-white mb-4">{t('api.documentation.generalRoutes')}</h3>
                
                {/* Health Check */}
                <div className="mb-6 border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden">
                  <div className="bg-green-50 dark:bg-green-900/20 px-4 py-3 border-b border-gray-200 dark:border-gray-700">
                    <div className="flex items-center space-x-2">
                      <span className="px-2 py-1 bg-green-600 text-white text-xs font-bold rounded">GET</span>
                      <code className="text-sm font-mono text-gray-900 dark:text-white">/health</code>
                    </div>
                  </div>
                  <div className="p-4 bg-white dark:bg-gray-800">
                    <p className="text-sm text-gray-700 dark:text-gray-300 mb-3">
                      {t('api.documentation.healthDescription')}
                    </p>
                    <div className="space-y-3">
                      <div>
                        <h5 className="text-xs font-semibold text-gray-600 dark:text-gray-400 uppercase mb-1">{t('api.documentation.response')} (200)</h5>
                        <JsonCodeBlock code={`{
  "status": "healthy",
  "message": "API is operational",
  "timestamp": "2025-12-05T12:00:00Z"
}`} />
                      </div>
                      <div>
                        <h5 className="text-xs font-semibold text-gray-600 dark:text-gray-400 uppercase mb-1">{t('api.codeBlocks.pythonExample')}</h5>
                        <PythonCodeBlock code={`import requests

API_KEY = "lum_abc123xyz789"
BASE_URL = "https://api.your-domain.com"

response = requests.get(
    BASE_URL + "/health",
    headers={"Authorization": "Bearer " + API_KEY}
)

data = response.json()
print(data["status"])      # "healthy"
print(data["message"])     # "API is operational"`} />
                      </div>
                    </div>
                  </div>
                </div>

                {/* Validity Check */}
                <div className="mb-6 border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden">
                  <div className="bg-green-50 dark:bg-green-900/20 px-4 py-3 border-b border-gray-200 dark:border-gray-700">
                    <div className="flex items-center space-x-2">
                      <span className="px-2 py-1 bg-green-600 text-white text-xs font-bold rounded">GET</span>
                      <code className="text-sm font-mono text-gray-900 dark:text-white">/validity</code>
                    </div>
                  </div>
                  <div className="p-4 bg-white dark:bg-gray-800">
                    <p className="text-sm text-gray-700 dark:text-gray-300 mb-3">
                      Check remaining validity time for your API key. Shows expiration date and time remaining.
                    </p>
                    <div className="space-y-3">
                      <div>
                        <h5 className="text-xs font-semibold text-gray-600 dark:text-gray-400 uppercase mb-1">Response (200)</h5>
                        <JsonCodeBlock code={`{
  "key_name": "my-api-key",
  "expires_at": "2026-01-05T12:00:00Z",
  "time_remaining": "30 days, 14 hours",
  "is_unlimited": false
}`} />
                      </div>
                      <div>
                        <h5 className="text-xs font-semibold text-gray-600 dark:text-gray-400 uppercase mb-1">{t('api.codeBlocks.pythonExample')}</h5>
                        <PythonCodeBlock code={`import requests

API_KEY = "lum_abc123xyz789"
BASE_URL = "https://api.your-domain.com"

response = requests.get(
    BASE_URL + "/validity",
    headers={"Authorization": "Bearer " + API_KEY}
)

data = response.json()
print(data["expires_at"])      # "2026-01-05T12:00:00Z"
print(data["time_remaining"])  # "30 days, 14 hours"`} />
                      </div>
                    </div>
                  </div>
                </div>

                {/* Account Info */}
                <div className="mb-6 border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden">
                  <div className="bg-green-50 dark:bg-green-900/20 px-4 py-3 border-b border-gray-200 dark:border-gray-700">
                    <div className="flex items-center space-x-2">
                      <span className="px-2 py-1 bg-green-600 text-white text-xs font-bold rounded">GET</span>
                      <code className="text-sm font-mono text-gray-900 dark:text-white">/account</code>
                    </div>
                  </div>
                  <div className="p-4 bg-white dark:bg-gray-800">
                    <p className="text-sm text-gray-700 dark:text-gray-300 mb-3">
                      Get account information including user ID, email, and available credits for both web and PDF scans.
                    </p>
                    <div className="space-y-3">
                      <div>
                        <h5 className="text-xs font-semibold text-gray-600 dark:text-gray-400 uppercase mb-1">Response (200)</h5>
                        <JsonCodeBlock code={`{
  "user_id": "abc123",
  "email": "user@example.com",
  "credits": {
    "web_scan_credits": 100,
    "pdf_scan_credits": 50
  }
}`} />
                      </div>
                      <div>
                        <h5 className="text-xs font-semibold text-gray-600 dark:text-gray-400 uppercase mb-1">{t('api.codeBlocks.pythonExample')}</h5>
                        <PythonCodeBlock code={`import requests

API_KEY = "lum_abc123xyz789"
BASE_URL = "https://api.your-domain.com"

response = requests.get(
    BASE_URL + "/account",
    headers={"Authorization": "Bearer " + API_KEY}
)

data = response.json()
credits = data["credits"]
print(credits["web_scan_credits"])  # 100
print(credits["pdf_scan_credits"])  # 50`} />
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              <hr className="border-gray-200 dark:border-gray-700" />

              {/* WEB SCAN */}
              <div id="web-scan">
                <h3 className="text-2xl font-bold text-gray-900 dark:text-white mb-4">{t('api.documentation.webScan')}</h3>
                
                <div className="mb-6 border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden">
                  <div className="bg-blue-50 dark:bg-blue-900/20 px-4 py-3 border-b border-gray-200 dark:border-gray-700">
                    <div className="flex items-center space-x-2">
                      <span className="px-2 py-1 bg-blue-600 text-white text-xs font-bold rounded">POST</span>
                      <code className="text-sm font-mono text-gray-900 dark:text-white">/web-scan</code>
                    </div>
                  </div>
                  <div className="p-4 bg-white dark:bg-gray-800">
                    <p className="text-sm text-gray-700 dark:text-gray-300 mb-3">
                      {t('api.documentation.webScanDescription')} <strong>{t('api.documentation.webScanSyncNote')}</strong>
                    </p>
                    <div className="mb-3 p-2 bg-amber-50 dark:bg-amber-900/20 rounded text-xs text-amber-700 dark:text-amber-300">
                      <strong>{t('api.documentation.cost')}:</strong> {t('api.documentation.webScanCost')}
                    </div>
                    <div className="mb-3 p-2 bg-blue-50 dark:bg-blue-900/20 rounded text-xs text-blue-700 dark:text-blue-300">
                      <strong>{t('api.documentation.note')}:</strong> {t('api.documentation.webScanIntegrationNote')}
                    </div>
                    <div className="space-y-3">
                      <div>
                        <h5 className="text-xs font-semibold text-gray-600 dark:text-gray-400 uppercase mb-1">{t('api.documentation.requestBody')}</h5>
                        <JsonCodeBlock code={`{
  "url": "https://example.com",
  "modules": ["axe", "nu", "axTree", "galen", "links"]
}`} />
                        <div className="mt-2 p-3 bg-gray-50 dark:bg-gray-900 rounded-lg">
                          <h6 className="text-xs font-semibold text-gray-700 dark:text-gray-300 mb-2">{t('api.documentation.availableModules')}:</h6>
                          <div className="grid grid-cols-1 md:grid-cols-2 gap-2 text-xs">
                            <div className="flex items-start space-x-2">
                              <code className="px-1.5 py-0.5 bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 rounded font-mono">axe</code>
                              <span className="text-gray-600 dark:text-gray-400">{t('api.documentation.axeDescription')}</span>
                            </div>
                            <div className="flex items-start space-x-2">
                              <code className="px-1.5 py-0.5 bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 rounded font-mono">nu</code>
                              <span className="text-gray-600 dark:text-gray-400">{t('api.documentation.nuDescription')}</span>
                            </div>
                            <div className="flex items-start space-x-2">
                              <code className="px-1.5 py-0.5 bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 rounded font-mono">axTree</code>
                              <span className="text-gray-600 dark:text-gray-400">{t('api.documentation.axTreeDescription')}</span>
                            </div>
                            <div className="flex items-start space-x-2">
                              <code className="px-1.5 py-0.5 bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 rounded font-mono">galen</code>
                              <span className="text-gray-600 dark:text-gray-400">{t('api.documentation.galenDescription')}</span>
                            </div>
                            <div className="flex items-start space-x-2">
                              <code className="px-1.5 py-0.5 bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 rounded font-mono">links</code>
                              <span className="text-gray-600 dark:text-gray-400">{t('api.documentation.linksDescription')}</span>
                            </div>
                          </div>
                          <p className="mt-2 text-xs text-gray-500 dark:text-gray-400">
                            If <code className="px-1 bg-gray-200 dark:bg-gray-700 rounded">modules</code> is not specified, all available modules will run by default.
                          </p>
                        </div>
                      </div>
                      <div>
                        <h5 className="text-xs font-semibold text-gray-600 dark:text-gray-400 uppercase mb-1">Response (200 - Success) - v3.0.0 Format</h5>
                        <JsonCodeBlock code={`{
  "scan_id": "api_web_abc123",
  "status": "completed",
  "url": "https://example.com",
  "timestamp": "2025-12-05T12:00:00Z",
  "scan_format_version": "3.0.0",
  "modules_executed": ["axe", "nu", "axTree", "galen", "links"],
  "scan_duration_ms": 5234,
  "credits_used": 5,
  "credits_remaining": 95,
  "summary": {
    "total_violations": 12,
    "total_passes": 45,
    "total_html_errors": 3,
    "total_broken_links": 2
  },
  "unified_results": {
    "axe": { "violations": [], "passes": [] },
    "nu": { "messages": [] },
    "axTree": { "role": "WebArea", "children": [] },
    "galen": { "viewport_results": [] },
    "links": { "links": [], "total_links": 87 },
    "meta": { "viewport": {}, "page_title": "Example" }
  }
}`} />
                      </div>
                      <div>
                        <h5 className="text-xs font-semibold text-gray-600 dark:text-gray-400 uppercase mb-1">Error (402 - Insufficient Credits)</h5>
                        <JsonCodeBlock code={`{
  "error": "insufficient_credits",
  "message": "Insufficient web scan credits. Required: 5 (1 per module), Available: 3",
  "credits_required": 5,
  "credits_available": 3,
  "modules_requested": ["axe", "nu", "axTree", "galen", "links"]
}`} />
                      </div>
                      <div>
                        <h5 className="text-xs font-semibold text-gray-600 dark:text-gray-400 uppercase mb-1">{t('api.codeBlocks.pythonExample')}</h5>
                        <PythonCodeBlock code={`import requests

API_KEY = "lum_abc123xyz789"
BASE_URL = "https://api.your-domain.com"

# Scan with all modules (default - costs 1 credit per module)
response = requests.post(
    BASE_URL + "/web-scan",
    headers={
        "Authorization": "Bearer " + API_KEY,
        "Content-Type": "application/json"
    },
    json={
        "url": "https://example.com"
    }
)

# Or select specific modules (costs 3 credits)
response = requests.post(
    BASE_URL + "/web-scan",
    headers={
        "Authorization": "Bearer " + API_KEY,
        "Content-Type": "application/json"
    },
    json={
        "url": "https://example.com",
        "modules": ["axe", "nu", "links"]
    }
)

data = response.json()
print(data["scan_id"])                       # "web_abc123"
print(data["credits_used"])                  # 3 (for 3 modules)
print(data["summary"]["total_violations"])   # 12
print(data["credits_remaining"])             # 97`} />
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              <hr className="border-gray-200 dark:border-gray-700" />

              {/* PDF SCAN */}
              <div id="pdf-scan">
                <h3 className="text-2xl font-bold text-gray-900 dark:text-white mb-4">{t('api.documentation.pdfScan')}</h3>
                
                <div className="mb-6 border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden">
                  <div className="bg-blue-50 dark:bg-blue-900/20 px-4 py-3 border-b border-gray-200 dark:border-gray-700">
                    <div className="flex items-center space-x-2">
                      <span className="px-2 py-1 bg-blue-600 text-white text-xs font-bold rounded">POST</span>
                      <code className="text-sm font-mono text-gray-900 dark:text-white">/pdf-scan</code>
                    </div>
                  </div>
                  <div className="p-4 bg-white dark:bg-gray-800">
                    <p className="text-sm text-gray-700 dark:text-gray-300 mb-3">
                      {t('api.documentation.pdfScanDescription')} {t('api.documentation.pdfScanMethods')}
                    </p>
                    <div className="mb-3 p-2 bg-amber-50 dark:bg-amber-900/20 rounded text-xs text-amber-700 dark:text-amber-300">
                      <strong>{t('api.documentation.cost')}:</strong> {t('api.documentation.pdfScanCost')}
                    </div>
                    <div className="space-y-3">
                      <div>
                        <h5 className="text-xs font-semibold text-gray-600 dark:text-gray-400 uppercase mb-1">Request (URL Method)</h5>
                        <JsonCodeBlock code={`{
  "pdf_url": "https://example.com/document.pdf"
}`} />
                      </div>
                      <div>
                        <h5 className="text-xs font-semibold text-gray-600 dark:text-gray-400 uppercase mb-1">Response (200 - Success)</h5>
                        <JsonCodeBlock code={`{
  "scan_id": "api_pdf_xyz789",
  "status": "completed",
  "file_name": "document.pdf",
  "timestamp": "2025-12-05T12:00:00Z",
  "pages_analyzed": 5,
  "credits_used": 5,
  "credits_remaining": 45,
  "accessibility_report": "# Page 1 Analysis...",
  "page_results": [
    {"page_number": 1, "accessibility_report": "..."},
    {"page_number": 2, "accessibility_report": "..."}
  ],
  "tool_info": {
    "name": "LumTrails-PDF-AI-Scanner",
    "version": "2.0.0"
  }
}`} />
                      </div>
                      <div>
                        <h5 className="text-xs font-semibold text-gray-600 dark:text-gray-400 uppercase mb-1">Error (402 - Insufficient Credits)</h5>
                        <JsonCodeBlock code={`{
  "error": "insufficient_credits",
  "message": "Insufficient PDF scan credits",
  "credits_required": 5,
  "credits_available": 2
}`} />
                      </div>
                      <div>
                        <h5 className="text-xs font-semibold text-gray-600 dark:text-gray-400 uppercase mb-1">{t('api.codeBlocks.pythonExampleUrl')}</h5>
                        <PythonCodeBlock code={`import requests

API_KEY = "lum_abc123xyz789"
BASE_URL = "https://api.your-domain.com"

# Scan a PDF from URL
response = requests.post(
    BASE_URL + "/pdf-scan",
    headers={"Authorization": "Bearer " + API_KEY},
    data={"pdf_url": "https://example.com/document.pdf"}
)

data = response.json()
print(data["scan_id"])        # "pdf_abc123"
print(data["pages_analyzed"]) # 5
print(data["credits_used"])   # 5`} />
                      </div>
                      <div>
                        <h5 className="text-xs font-semibold text-gray-600 dark:text-gray-400 uppercase mb-1">{t('api.codeBlocks.pythonExampleFile')}</h5>
                        <PythonCodeBlock code={`import requests

API_KEY = "lum_abc123xyz789"
BASE_URL = "https://api.your-domain.com"

# Upload and scan a PDF file
with open("document.pdf", "rb") as pdf_file:
    response = requests.post(
        BASE_URL + "/pdf-scan",
        headers={"Authorization": "Bearer " + API_KEY},
        files={"file": ("document.pdf", pdf_file, "application/pdf")}
    )

data = response.json()
print(data["accessibility_report"])  # "# Page 1 Analysis..."`} />
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              <hr className="border-gray-200 dark:border-gray-700" />

              {/* INTEGRATIONS */}
              <div id="integrations">
                <h3 className="text-2xl font-bold text-gray-900 dark:text-white mb-4">{t('api.documentation.integrationsTitle')}</h3>
                <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
                  {t('api.documentation.integrationsDescription')}
                </p>

                {/* GitHub */}
                <div className="mb-6">
                  <h4 className="text-lg font-semibold text-gray-900 dark:text-white mb-3 flex items-center">
                    <span className="w-2 h-2 bg-purple-500 rounded-full mr-2"></span>
                    {t('api.documentation.githubIntegration')}
                  </h4>

                  {/* GitHub Health */}
                  <div className="mb-4 border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden">
                    <div className="bg-purple-50 dark:bg-purple-900/20 px-4 py-3 border-b border-gray-200 dark:border-gray-700">
                      <div className="flex items-center space-x-2">
                        <span className="px-2 py-1 bg-green-600 text-white text-xs font-bold rounded">GET</span>
                        <code className="text-sm font-mono text-gray-900 dark:text-white">/integrations/github/health</code>
                      </div>
                    </div>
                    <div className="p-4 bg-white dark:bg-gray-800">
                      <p className="text-sm text-gray-700 dark:text-gray-300 mb-3">
                        Check if GitHub integration is connected and retrieve account information.
                      </p>
                      <div className="space-y-3">
                        <div>
                          <h5 className="text-xs font-semibold text-gray-600 dark:text-gray-400 uppercase mb-1">Response (200)</h5>
                          <JsonCodeBlock code={`{
  "connected": true,
  "account": {
    "username": "johndoe",
    "id": 12345678
  },
  "repository": "johndoe/my-repo",
  "web_scan_enabled": true,
  "pdf_scan_enabled": false
}`} />
                        </div>
                        <div>
                          <h5 className="text-xs font-semibold text-gray-600 dark:text-gray-400 uppercase mb-1">{t('api.codeBlocks.pythonExample')}</h5>
                          <PythonCodeBlock code={`import requests

API_KEY = "lum_abc123xyz789"
BASE_URL = "https://api.your-domain.com"

response = requests.get(
    BASE_URL + "/integrations/github/health",
    headers={"Authorization": "Bearer " + API_KEY}
)

data = response.json()
if data["connected"]:
    print(data["account"]["username"])  # "johndoe"
    print(data["repository"])           # "johndoe/my-repo"`} />
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* GitHub Config */}
                  <div className="mb-4 border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden">
                    <div className="bg-purple-50 dark:bg-purple-900/20 px-4 py-3 border-b border-gray-200 dark:border-gray-700">
                      <div className="flex items-center space-x-2">
                        <span className="px-2 py-1 bg-orange-600 text-white text-xs font-bold rounded">PUT</span>
                        <code className="text-sm font-mono text-gray-900 dark:text-white">/integrations/github/config</code>
                      </div>
                    </div>
                    <div className="p-4 bg-white dark:bg-gray-800">
                      <p className="text-sm text-gray-700 dark:text-gray-300 mb-3">
                        Update GitHub integration configuration. All parameters are optional.
                      </p>
                      <div className="space-y-3">
                        <div>
                          <h5 className="text-xs font-semibold text-gray-600 dark:text-gray-400 uppercase mb-1">{t('api.codeBlocks.requestBody')}</h5>
                          <JsonCodeBlock code={`{
  "web_scan_enabled": true,
  "pdf_scan_enabled": true,
  "repository": "username/repo",
  "label": "accessibility",
  "web_scan_sections": {
    "wcag_enabled": true,
    "html_enabled": true,
    "links_enabled": true,
    "axtree_enabled": false,
    "layout_enabled": true,
    "wcag_grouping_option": "per-error-type",
    "wcag_regroup_violations": false,
    "wcag_severity_filter": ["High", "Medium"],
    "html_grouping_option": "per-error-type",
    "links_grouping_option": "per-error-type",
    "layout_grouping_option": "per-error-type"
  },
  "pdf_scan_sections": {
    "pdf_grouping_option": "per-page"
  }
}`} />
                        </div>
                        <div>
                          <h5 className="text-xs font-semibold text-gray-600 dark:text-gray-400 uppercase mb-1">Response (200 - Success)</h5>
                          <JsonCodeBlock code={`{
  "success": true,
  "message": "GitHub integration configuration updated successfully",
  "config": {
    "config": {
      "web_scan_enabled": true,
      "repository": "myorg/accessibility-issues",
      "label": "a11y"
    },
    "web_scan_sections": {...},
    "pdf_scan_sections": {...}
  }
}`} />
                        </div>
                        <div>
                          <h5 className="text-xs font-semibold text-gray-600 dark:text-gray-400 uppercase mb-1">Error (404 - Not Connected)</h5>
                          <JsonCodeBlock code={`{
  "error": "not_found",
  "message": "GitHub integration not connected. Please connect via the web interface."
}`} />
                        </div>
                        <div>
                          <h5 className="text-xs font-semibold text-gray-600 dark:text-gray-400 uppercase mb-1">{t('api.codeBlocks.configurationOptions')}</h5>
                          <ConfigOptionsBlock platform="github" />
                        </div>
                        <div>
                          <h5 className="text-xs font-semibold text-gray-600 dark:text-gray-400 uppercase mb-1">{t('api.codeBlocks.pythonExample')}</h5>
                          <PythonCodeBlock code={`import requests

API_KEY = "lum_abc123xyz789"
BASE_URL = "https://api.your-domain.com"

config = {
    "web_scan_enabled": True,
    "repository": "myorg/accessibility-issues",
    "label": "a11y",
    "web_scan_sections": {
        "wcag_enabled": True,
        "html_enabled": True,
        "wcag_severity_filter": ["High", "Medium"]
    }
}

response = requests.put(
    BASE_URL + "/integrations/github/config",
    headers={
        "Authorization": "Bearer " + API_KEY,
        "Content-Type": "application/json"
    },
    json=config
)

print(response.status_code)  # 200`} />
                        </div>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Notion */}
                <div className="mb-6">
                  <h4 className="text-lg font-semibold text-gray-900 dark:text-white mb-3 flex items-center">
                    <span className="w-2 h-2 bg-purple-500 rounded-full mr-2"></span>
                    {t('api.documentation.notionIntegration')}
                  </h4>

                  {/* Notion Health */}
                  <div className="mb-4 border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden">
                    <div className="bg-purple-50 dark:bg-purple-900/20 px-4 py-3 border-b border-gray-200 dark:border-gray-700">
                      <div className="flex items-center space-x-2">
                        <span className="px-2 py-1 bg-green-600 text-white text-xs font-bold rounded">GET</span>
                        <code className="text-sm font-mono text-gray-900 dark:text-white">/integrations/notion/health</code>
                      </div>
                    </div>
                    <div className="p-4 bg-white dark:bg-gray-800">
                      <p className="text-sm text-gray-700 dark:text-gray-300 mb-3">
                        Check if Notion integration is connected and retrieve workspace information.
                      </p>
                      <div className="space-y-3">
                        <div>
                          <h5 className="text-xs font-semibold text-gray-600 dark:text-gray-400 uppercase mb-1">Response (200)</h5>
                          <JsonCodeBlock code={`{
  "connected": true,
  "workspace": {
    "name": "My Workspace",
    "id": "abc123def456"
  },
  "parent_page_id": "abc123def456...",
  "web_scan_enabled": true,
  "pdf_scan_enabled": false
}`} />
                        </div>
                        <div>
                          <h5 className="text-xs font-semibold text-gray-600 dark:text-gray-400 uppercase mb-1">{t('api.codeBlocks.pythonExample')}</h5>
                          <PythonCodeBlock code={`import requests

API_KEY = "lum_abc123xyz789"
BASE_URL = "https://api.your-domain.com"

response = requests.get(
    BASE_URL + "/integrations/notion/health",
    headers={"Authorization": "Bearer " + API_KEY}
)

data = response.json()
if data["connected"]:
    print(data["workspace"]["name"])  # "My Workspace"
    print(data["parent_page_id"])     # "abc123def456..."`} />
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Notion Config */}
                  <div className="mb-4 border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden">
                    <div className="bg-purple-50 dark:bg-purple-900/20 px-4 py-3 border-b border-gray-200 dark:border-gray-700">
                      <div className="flex items-center space-x-2">
                        <span className="px-2 py-1 bg-orange-600 text-white text-xs font-bold rounded">PUT</span>
                        <code className="text-sm font-mono text-gray-900 dark:text-white">/integrations/notion/config</code>
                      </div>
                    </div>
                    <div className="p-4 bg-white dark:bg-gray-800">
                      <p className="text-sm text-gray-700 dark:text-gray-300 mb-3">
                        Update Notion integration configuration. All parameters are optional.
                      </p>
                      <div className="space-y-3">
                        <div>
                          <h5 className="text-xs font-semibold text-gray-600 dark:text-gray-400 uppercase mb-1">{t('api.codeBlocks.requestBody')}</h5>
                          <JsonCodeBlock code={`{
  "web_scan_enabled": true,
  "pdf_scan_enabled": true,
  "page_url": "https://notion.so/Page-ID",
  "web_scan_sections": {
    "wcag_enabled": true,
    "html_enabled": true,
    "links_enabled": true,
    "axtree_enabled": false,
    "layout_enabled": false,
    "wcag_grouping_option": "per-error-type",
    "wcag_regroup_violations": true,
    "wcag_severity_filter": ["High", "Medium", "Low"],
    "html_grouping_option": "per-error-type",
    "links_grouping_option": "per-error-type",
    "layout_grouping_option": "per-error-type"
  },
  "pdf_scan_sections": {
    "pdf_grouping_option": "single-issue"
  }
}`} />
                        </div>
                        <div>
                          <h5 className="text-xs font-semibold text-gray-600 dark:text-gray-400 uppercase mb-1">Response (200 - Success)</h5>
                          <JsonCodeBlock code={`{
  "success": true,
  "message": "Notion integration configuration updated successfully",
  "config": {
    "config": {
      "web_scan_enabled": true,
      "page_url": "https://notion.so/My-Page-abc123"
    },
    "web_scan_sections": {...},
    "pdf_scan_sections": {...}
  }
}`} />
                        </div>
                        <div>
                          <h5 className="text-xs font-semibold text-gray-600 dark:text-gray-400 uppercase mb-1">Error (404 - Not Connected)</h5>
                          <JsonCodeBlock code={`{
  "error": "not_found",
  "message": "Notion integration not connected. Please connect via the web interface."
}`} />
                        </div>
                        <div>
                          <h5 className="text-xs font-semibold text-gray-600 dark:text-gray-400 uppercase mb-1">{t('api.codeBlocks.configurationOptions')}</h5>
                          <ConfigOptionsBlock platform="notion" />
                        </div>
                        <div>
                          <h5 className="text-xs font-semibold text-gray-600 dark:text-gray-400 uppercase mb-1">{t('api.codeBlocks.pythonExample')}</h5>
                          <PythonCodeBlock code={`import requests

API_KEY = "lum_abc123xyz789"
BASE_URL = "https://api.your-domain.com"

config = {
    "web_scan_enabled": True,
    "page_url": "https://notion.so/My-Page-abc123",
    "web_scan_sections": {
        "wcag_enabled": True,
        "axtree_enabled": True,
        "wcag_regroup_violations": True
    }
}

response = requests.put(
    BASE_URL + "/integrations/notion/config",
    headers={
        "Authorization": "Bearer " + API_KEY,
        "Content-Type": "application/json"
    },
    json=config
)

print(response.status_code)  # 200`} />
                        </div>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Slack */}
                <div className="mb-6">
                  <h4 className="text-lg font-semibold text-gray-900 dark:text-white mb-3 flex items-center">
                    <span className="w-2 h-2 bg-purple-500 rounded-full mr-2"></span>
                    {t('api.documentation.slackIntegration')}
                  </h4>

                  {/* Slack Health */}
                  <div className="mb-4 border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden">
                    <div className="bg-purple-50 dark:bg-purple-900/20 px-4 py-3 border-b border-gray-200 dark:border-gray-700">
                      <div className="flex items-center space-x-2">
                        <span className="px-2 py-1 bg-green-600 text-white text-xs font-bold rounded">GET</span>
                        <code className="text-sm font-mono text-gray-900 dark:text-white">/integrations/slack/health</code>
                      </div>
                    </div>
                    <div className="p-4 bg-white dark:bg-gray-800">
                      <p className="text-sm text-gray-700 dark:text-gray-300 mb-3">
                        Check if Slack integration is connected and retrieve channel information.
                      </p>
                      <div className="space-y-3">
                        <div>
                          <h5 className="text-xs font-semibold text-gray-600 dark:text-gray-400 uppercase mb-1">Response (200)</h5>
                          <JsonCodeBlock code={`{
  "connected": true,
  "team": {
    "name": "My Team Workspace",
    "id": "T12345678"
  },
  "channel_id": "C12345678",
  "web_scan_enabled": true,
  "pdf_scan_enabled": false
}`} />
                        </div>
                        <div>
                          <h5 className="text-xs font-semibold text-gray-600 dark:text-gray-400 uppercase mb-1">{t('api.codeBlocks.pythonExample')}</h5>
                          <PythonCodeBlock code={`import requests

API_KEY = "lum_abc123xyz789"
BASE_URL = "https://api.your-domain.com"

response = requests.get(
    BASE_URL + "/integrations/slack/health",
    headers={"Authorization": "Bearer " + API_KEY}
)

data = response.json()
if data["connected"]:
    print(data["team"]["name"])  # "My Team Workspace"
    print(data["channel_id"])    # "C12345678"`} />
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Slack Config */}
                  <div className="mb-4 border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden">
                    <div className="bg-purple-50 dark:bg-purple-900/20 px-4 py-3 border-b border-gray-200 dark:border-gray-700">
                      <div className="flex items-center space-x-2">
                        <span className="px-2 py-1 bg-orange-600 text-white text-xs font-bold rounded">PUT</span>
                        <code className="text-sm font-mono text-gray-900 dark:text-white">/integrations/slack/config</code>
                      </div>
                    </div>
                    <div className="p-4 bg-white dark:bg-gray-800">
                      <p className="text-sm text-gray-700 dark:text-gray-300 mb-3">
                        Update Slack integration configuration. All parameters are optional.
                      </p>
                      <div className="space-y-3">
                        <div>
                          <h5 className="text-xs font-semibold text-gray-600 dark:text-gray-400 uppercase mb-1">{t('api.codeBlocks.requestBody')}</h5>
                          <JsonCodeBlock code={`{
  "web_scan_enabled": true,
  "pdf_scan_enabled": false,
  "channel_id": "C12345678",
  "web_scan_sections": {
    "wcag_enabled": true,
    "html_enabled": true,
    "links_enabled": true,
    "axtree_enabled": false,
    "layout_enabled": false,
    "wcag_grouping_option": "per-error-type",
    "wcag_regroup_violations": false,
    "wcag_severity_filter": ["High", "Medium", "Low"],
    "html_grouping_option": "per-error-type",
    "links_grouping_option": "per-error-type",
    "layout_grouping_option": "per-error-type"
  },
  "pdf_scan_sections": {
    "pdf_grouping_option": "single-issue"
  }
}`} />
                        </div>
                        <div>
                          <h5 className="text-xs font-semibold text-gray-600 dark:text-gray-400 uppercase mb-1">Response (200 - Success)</h5>
                          <JsonCodeBlock code={`{
  "success": true,
  "message": "Slack integration configuration updated successfully",
  "config": {
    "config": {
      "web_scan_enabled": true,
      "channel_id": "C12345678"
    },
    "web_scan_sections": {...},
    "pdf_scan_sections": {...}
  }
}`} />
                        </div>
                        <div>
                          <h5 className="text-xs font-semibold text-gray-600 dark:text-gray-400 uppercase mb-1">Error (404 - Not Connected)</h5>
                          <JsonCodeBlock code={`{
  "error": "not_found",
  "message": "Slack integration not connected. Please connect via the web interface."
}`} />
                        </div>
                        <div>
                          <h5 className="text-xs font-semibold text-gray-600 dark:text-gray-400 uppercase mb-1">{t('api.codeBlocks.configurationOptions')}</h5>
                          <ConfigOptionsBlock platform="slack" />
                        </div>
                        <div>
                          <h5 className="text-xs font-semibold text-gray-600 dark:text-gray-400 uppercase mb-1">{t('api.codeBlocks.pythonExample')}</h5>
                          <PythonCodeBlock code={`import requests

API_KEY = "lum_abc123xyz789"
BASE_URL = "https://api.your-domain.com"

config = {
    "web_scan_enabled": True,
    "channel_id": "C12345678",
    "web_scan_sections": {
        "wcag_enabled": True,
        "wcag_severity_filter": ["High"]
    }
}

response = requests.put(
    BASE_URL + "/integrations/slack/config",
    headers={
        "Authorization": "Bearer " + API_KEY,
        "Content-Type": "application/json"
    },
    json=config
)

print(response.status_code)  # 200`} />
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              <hr className="border-gray-200 dark:border-gray-700" />

              {/* Error Responses */}
              <div>
                <h3 className="text-2xl font-bold text-gray-900 dark:text-white mb-4">{t('api.documentation.errorsTitle')}</h3>
                <div className="overflow-x-auto">
                  <table className="w-full text-sm border border-gray-200 dark:border-gray-700">
                    <thead className="bg-gray-50 dark:bg-gray-900">
                      <tr>
                        <th className="px-4 py-2 text-left text-xs font-semibold text-gray-700 dark:text-gray-300 border-b border-gray-200 dark:border-gray-700">{t('api.documentation.errors.tableHeaders.code')}</th>
                        <th className="px-4 py-2 text-left text-xs font-semibold text-gray-700 dark:text-gray-300 border-b border-gray-200 dark:border-gray-700">{t('api.documentation.errors.tableHeaders.status')}</th>
                        <th className="px-4 py-2 text-left text-xs font-semibold text-gray-700 dark:text-gray-300 border-b border-gray-200 dark:border-gray-700">{t('api.documentation.errors.tableHeaders.description')}</th>
                      </tr>
                    </thead>
                    <tbody className="bg-white dark:bg-gray-800">
                      <tr>
                        <td className="px-4 py-2 border-b border-gray-200 dark:border-gray-700"><code className="bg-gray-100 dark:bg-gray-900 px-1 rounded">401</code></td>
                        <td className="px-4 py-2 border-b border-gray-200 dark:border-gray-700 text-gray-700 dark:text-gray-300">{t('api.documentation.errors.statusLabels.401')}</td>
                        <td className="px-4 py-2 border-b border-gray-200 dark:border-gray-700 text-gray-700 dark:text-gray-300">{t('api.documentation.errors.401')}</td>
                      </tr>
                      <tr>
                        <td className="px-4 py-2 border-b border-gray-200 dark:border-gray-700"><code className="bg-gray-100 dark:bg-gray-900 px-1 rounded">402</code></td>
                        <td className="px-4 py-2 border-b border-gray-200 dark:border-gray-700 text-gray-700 dark:text-gray-300">{t('api.documentation.errors.statusLabels.402')}</td>
                        <td className="px-4 py-2 border-b border-gray-200 dark:border-gray-700 text-gray-700 dark:text-gray-300">{t('api.documentation.errors.402')}</td>
                      </tr>
                      <tr>
                        <td className="px-4 py-2 border-b border-gray-200 dark:border-gray-700"><code className="bg-gray-100 dark:bg-gray-900 px-1 rounded">400</code></td>
                        <td className="px-4 py-2 border-b border-gray-200 dark:border-gray-700 text-gray-700 dark:text-gray-300">{t('api.documentation.errors.statusLabels.400')}</td>
                        <td className="px-4 py-2 border-b border-gray-200 dark:border-gray-700 text-gray-700 dark:text-gray-300">{t('api.documentation.errors.400')}</td>
                      </tr>
                      <tr>
                        <td className="px-4 py-2 border-b border-gray-200 dark:border-gray-700"><code className="bg-gray-100 dark:bg-gray-900 px-1 rounded">404</code></td>
                        <td className="px-4 py-2 border-b border-gray-200 dark:border-gray-700 text-gray-700 dark:text-gray-300">{t('api.documentation.errors.statusLabels.404')}</td>
                        <td className="px-4 py-2 border-b border-gray-200 dark:border-gray-700 text-gray-700 dark:text-gray-300">{t('api.documentation.errors.404')}</td>
                      </tr>
                      <tr>
                        <td className="px-4 py-2 border-b border-gray-200 dark:border-gray-700"><code className="bg-gray-100 dark:bg-gray-900 px-1 rounded">429</code></td>
                        <td className="px-4 py-2 border-b border-gray-200 dark:border-gray-700 text-gray-700 dark:text-gray-300">{t('api.documentation.errors.statusLabels.429')}</td>
                        <td className="px-4 py-2 border-b border-gray-200 dark:border-gray-700 text-gray-700 dark:text-gray-300">{t('api.documentation.errors.429')}</td>
                      </tr>
                      <tr>
                        <td className="px-4 py-2"><code className="bg-gray-100 dark:bg-gray-900 px-1 rounded">500</code></td>
                        <td className="px-4 py-2 text-gray-700 dark:text-gray-300">{t('api.documentation.errors.statusLabels.500')}</td>
                        <td className="px-4 py-2 text-gray-700 dark:text-gray-300">{t('api.documentation.errors.500')}</td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
        </PageCard>
      </motion.div>

      {/* Delete Confirmation Modal */}
      <DeleteConfirmModal
        isOpen={deleteModal.isOpen}
        onClose={() => setDeleteModal({ isOpen: false, keyId: null, keyName: '' })}
        onConfirm={confirmRevokeKey}
        keyName={deleteModal.keyName}
      />

      {/* Create API Key Modal */}
      <Transition appear show={showCreateModal} as={Fragment}>
        <Dialog as="div" className="relative z-50" onClose={() => {
          if (!createdKey) {
            setShowCreateModal(false)
            setNewKeyName('')
            setValidityPeriod('1month')
          }
        }}>
          <Transition.Child
            as={Fragment}
            enter="ease-out duration-300"
            enterFrom="opacity-0"
            enterTo="opacity-100"
            leave="ease-in duration-200"
            leaveFrom="opacity-100"
            leaveTo="opacity-0"
          >
            <div className="fixed inset-0 bg-black bg-opacity-50" />
          </Transition.Child>

          <div className="fixed inset-0 overflow-y-auto">
            <div className="flex min-h-full items-center justify-center p-4 text-center">
              <Transition.Child
                as={Fragment}
                enter="ease-out duration-300"
                enterFrom="opacity-0 scale-95"
                enterTo="opacity-100 scale-100"
                leave="ease-in duration-200"
                leaveFrom="opacity-100 scale-100"
                leaveTo="opacity-0 scale-95"
              >
                <Dialog.Panel className="w-full max-w-md transform overflow-hidden rounded-lg bg-white dark:bg-gray-800 shadow-xl transition-all">
                  <div className="p-6">
                    <Dialog.Title as="h3" className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                      {t('api.createModal.title')}
                    </Dialog.Title>

                    {!createdKey ? (
                      <>
                        <div className="space-y-4">
                          <div>
                            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                              {t('api.createModal.keyName')} *
                            </label>
                            <input
                              type="text"
                              value={newKeyName}
                              onChange={(e) => setNewKeyName(e.target.value.toLowerCase())}
                              placeholder={t('api.createModal.keyNamePlaceholder')}
                              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                            />
                            <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
                              {t('api.createModal.keyNameHelp')}
                            </p>
                          </div>

                          <div>
                            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                              {t('api.createModal.validityPeriod')} *
                            </label>
                            <select
                              value={validityPeriod}
                              onChange={(e) => setValidityPeriod(e.target.value)}
                              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                            >
                              <option value="1day">{t('api.createModal.validityOptions.1day')}</option>
                              <option value="1week">{t('api.createModal.validityOptions.1week')}</option>
                              <option value="1month">{t('api.createModal.validityOptions.1month')}</option>
                              <option value="6months">{t('api.createModal.validityOptions.6months')}</option>
                              <option value="1year">{t('api.createModal.validityOptions.1year')}</option>
                              <option value="unlimited">{t('api.createModal.validityOptions.unlimited')}</option>
                            </select>
                            {validityPeriod === 'unlimited' && (
                              <div className="mt-2 flex items-start space-x-2 text-amber-600 dark:text-amber-400 bg-amber-50 dark:bg-amber-900/20 rounded-md p-2">
                                <ExclamationTriangleIcon className="h-5 w-5 flex-shrink-0 mt-0.5" />
                                <p className="text-xs">
                                  {t('api.createModal.unlimitedWarning')}
                                </p>
                              </div>
                            )}
                          </div>
                        </div>

                        <div className="flex justify-end space-x-3 mt-6">
                          <button
                            onClick={() => {
                              setShowCreateModal(false)
                              setNewKeyName('')
                              setValidityPeriod('1month')
                            }}
                            className="px-4 py-2 bg-gray-100 hover:bg-gray-200 dark:bg-gray-700 dark:hover:bg-gray-600 text-gray-700 dark:text-gray-300 rounded-md font-medium transition-colors duration-200"
                          >
                            {t('common.cancel')}
                          </button>
                          <button
                            onClick={handleCreateKey}
                            className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-md font-medium transition-colors duration-200"
                          >
                            {t('api.createModal.generate')}
                          </button>
                        </div>
                      </>
                    ) : (
                      <>
                        <div className="bg-green-50 dark:bg-green-900/20 rounded-xl p-4 mb-4 border border-green-100 dark:border-green-800">
                          <h4 className="font-medium text-green-900 dark:text-green-100 mb-2">{t('api.createModal.success.title')}</h4>
                          <p className="text-sm text-green-700 dark:text-green-300 mb-3">
                            {t('api.createModal.success.description')}
                          </p>
                          <div className="flex items-center space-x-2">
                            <code className="flex-1 bg-white dark:bg-gray-800 px-3 py-2 rounded-lg border border-green-200 dark:border-green-800 text-sm font-mono break-all">
                              {createdKey.api_key}
                            </code>
                            <button
                              onClick={() => copyToClipboard(createdKey.api_key)}
                              className="p-2 bg-green-600 hover:bg-green-700 text-white rounded-xl transition-colors duration-200"
                              title={t('common.copy')}
                            >
                              {copiedKey ? (
                                <CheckIcon className="h-5 w-5" />
                              ) : (
                                <ClipboardDocumentIcon className="h-5 w-5" />
                              )}
                            </button>
                          </div>
                        </div>

                        <button
                          onClick={() => {
                            setShowCreateModal(false)
                            setCreatedKey(null)
                            setNewKeyName('')
                            setValidityPeriod('1month')
                          }}
                          className="w-full px-4 py-2 bg-primary-500 hover:bg-primary-600 text-white rounded-xl font-medium transition-colors duration-200"
                        >
                          {t('api.createModal.success.done')}
                        </button>
                      </>
                    )}
                  </div>
                </Dialog.Panel>
              </Transition.Child>
            </div>
          </div>
        </Dialog>
      </Transition>
    </PageContainer>
  )
}

export default APIPage
