import React, { Fragment, useState, useEffect } from 'react'
import { Dialog, Transition } from '@headlessui/react'
import { ExclamationTriangleIcon } from '@heroicons/react/24/outline'
import { useTranslation } from '../hooks/useTranslation'

const DeleteConfirmationDialog = ({ 
  isOpen, 
  onClose, 
  onConfirm, 
  itemName,
  itemType = 'scan'
}) => {
  const { t } = useTranslation()
  const [confirmText, setConfirmText] = useState('')
  const [isDeleting, setIsDeleting] = useState(false)
  
  // Get the translated confirmation word
  const confirmWord = t('myScans.deleteModal.confirmWord')

  useEffect(() => {
    if (isOpen) {
      setConfirmText('')
      setIsDeleting(false)
    }
  }, [isOpen])

  const handleConfirm = async () => {
    if (confirmText.toLowerCase() !== confirmWord.toLowerCase()) {
      return
    }
    
    setIsDeleting(true)
    try {
      await onConfirm()
    } finally {
      setIsDeleting(false)
    }
  }

  const handleClose = () => {
    if (!isDeleting) {
      onClose()
    }
  }

  const isConfirmDisabled = confirmText.toLowerCase() !== confirmWord.toLowerCase() || isDeleting

  return (
    <Transition appear show={isOpen} as={Fragment}>
      <Dialog as="div" className="relative z-50" onClose={handleClose}>
        <Transition.Child
          as={Fragment}
          enter="ease-out duration-300"
          enterFrom="opacity-0"
          enterTo="opacity-100"
          leave="ease-in duration-200"
          leaveFrom="opacity-100"
          leaveTo="opacity-0"
        >
          <div className="fixed inset-0 bg-gray-500 bg-opacity-75 dark:bg-gray-900 dark:bg-opacity-75" />
        </Transition.Child>

        <div className="fixed inset-0 overflow-y-auto">
          <div className="flex min-h-full items-end justify-center p-4 text-center sm:items-center sm:p-0">
            <Transition.Child
              as={Fragment}
              enter="ease-out duration-300"
              enterFrom="opacity-0 translate-y-4 sm:translate-y-0 sm:scale-95"
              enterTo="opacity-100 translate-y-0 sm:scale-100"
              leave="ease-in duration-200"
              leaveFrom="opacity-100 translate-y-0 sm:scale-100"
              leaveTo="opacity-0 translate-y-4 sm:translate-y-0 sm:scale-95"
            >
              <Dialog.Panel className="relative transform overflow-hidden rounded-lg bg-white dark:bg-gray-800 px-4 pb-4 pt-5 text-left shadow-xl transition-all sm:my-8 sm:w-full sm:max-w-lg sm:p-6">
                <div className="sm:flex sm:items-start">
                  <div className="mx-auto flex h-12 w-12 flex-shrink-0 items-center justify-center rounded-full bg-red-100 dark:bg-red-900/20 sm:mx-0 sm:h-10 sm:w-10">
                    <ExclamationTriangleIcon className="h-6 w-6 text-red-600 dark:text-red-400" />
                  </div>
                  <div className="mt-3 text-center sm:ml-4 sm:mt-0 sm:text-left">
                    <Dialog.Title as="h3" className="text-base font-semibold leading-6 text-gray-900 dark:text-white">
                      {t('common.delete')} {itemType}
                    </Dialog.Title>
                    <div className="mt-2">
                      <p className="text-sm text-gray-500 dark:text-gray-400 mb-3">
                        {t('myScans.deleteModal.confirmMessage', { type: itemType })}
                      </p>
                      <div className="bg-red-50 dark:bg-red-900/10 border border-red-200 dark:border-red-800 rounded-lg p-3 mb-3">
                        <p className="text-sm font-medium text-red-800 dark:text-red-300 mb-1">
                          ⚠️ {t('myScans.deleteModal.warning')}
                        </p>
                        <p className="text-xs text-red-700 dark:text-red-400">
                          {itemName}
                        </p>
                      </div>
                      <div className="mt-3">
                        <label htmlFor="confirm-delete" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                          {t('myScans.deleteModal.typeToConfirm')} <span className="font-bold text-red-600 dark:text-red-400">{confirmWord}</span> {t('myScans.deleteModal.toConfirm')}
                        </label>
                        <input
                          id="confirm-delete"
                          type="text"
                          value={confirmText}
                          onChange={(e) => setConfirmText(e.target.value)}
                          disabled={isDeleting}
                          placeholder={confirmWord}
                          className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:ring-red-500 focus:border-red-500 dark:bg-gray-700 dark:text-white disabled:opacity-50 disabled:cursor-not-allowed"
                          autoComplete="off"
                        />
                      </div>
                    </div>
                  </div>
                </div>
                <div className="mt-5 sm:mt-4 sm:flex sm:flex-row-reverse">
                  <button
                    type="button"
                    onClick={handleConfirm}
                    disabled={isConfirmDisabled}
                    className="inline-flex w-full justify-center rounded-md px-3 py-2 text-sm font-semibold text-white shadow-sm sm:ml-3 sm:w-auto transition-colors duration-200 bg-red-600 hover:bg-red-500 focus:ring-red-500 focus:outline-none focus:ring-2 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:bg-red-600"
                  >
                    {isDeleting ? t('myScans.deleteModal.deleting') : t('myScans.deleteModal.deletePermanently')}
                  </button>
                  <button
                    type="button"
                    onClick={handleClose}
                    disabled={isDeleting}
                    className="mt-3 inline-flex w-full justify-center rounded-md bg-white dark:bg-gray-700 px-3 py-2 text-sm font-semibold text-gray-900 dark:text-gray-300 shadow-sm ring-1 ring-inset ring-gray-300 dark:ring-gray-600 hover:bg-gray-50 dark:hover:bg-gray-600 sm:mt-0 sm:w-auto transition-colors duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {t('common.cancel')}
                  </button>
                </div>
              </Dialog.Panel>
            </Transition.Child>
          </div>
        </div>
      </Dialog>
    </Transition>
  )
}

export default DeleteConfirmationDialog
