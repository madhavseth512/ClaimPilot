import { useContext, useEffect, useRef, useState } from 'react'
import { AuthContext } from '../context/AuthContext'
import { useNavigate } from 'react-router-dom'
import { api } from '../api/client'

export default function ProfileDropdown({ onClose }) {
  const { user, signOut } = useContext(AuthContext)
  const navigate = useNavigate()
  const ref = useRef()

  const [showPwModal, setShowPwModal] = useState(false)
  const [pw, setPw]     = useState({ current: '', next: '', confirm: '' })
  const [pwMsg, setPwMsg] = useState('')

  // Close on outside click
  useEffect(() => {
    function handler(e) { if (ref.current && !ref.current.contains(e.target)) onClose() }
    document.addEventListener('mousedown', handler)
    return () => document.removeEventListener('mousedown', handler)
  }, [onClose])

  function handleLogout() {
    signOut()
    navigate('/login')
  }

  return (
    <div ref={ref} className="absolute right-0 top-full mt-2 w-64 card shadow-lg z-50 py-2">
      {/* User info */}
      <div className="px-4 py-3 border-b border-gray-100">
        <p className="text-sm font-semibold text-gray-900">{user?.name || 'User'}</p>
        <p className="text-xs text-gray-500 truncate">{user?.email}</p>
      </div>

      <button
        onClick={() => { setShowPwModal(true) }}
        className="w-full text-left px-4 py-2.5 text-sm text-gray-700 hover:bg-gray-50 flex items-center gap-3"
      >
        <svg className="w-4 h-4 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
            d="M15 7a2 2 0 012 2m4 0a6 6 0 01-7.743 5.743L11 17H9v2H7v2H4a1 1 0 01-1-1v-2.586a1 1 0 01.293-.707l5.964-5.964A6 6 0 1121 9z" />
        </svg>
        Change Password
      </button>

      <div className="border-t border-gray-100 mt-1 pt-1">
        <button
          onClick={handleLogout}
          className="w-full text-left px-4 py-2.5 text-sm text-red-600 hover:bg-red-50 flex items-center gap-3"
        >
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
              d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
          </svg>
          Logout
        </button>
      </div>

      {/* Change password modal */}
      {showPwModal && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50" onClick={() => setShowPwModal(false)}>
          <div className="card w-full max-w-sm p-6" onClick={e => e.stopPropagation()}>
            <h3 className="text-base font-semibold mb-4">Change Password</h3>
            {pwMsg && <p className="text-sm text-green-600 mb-3">{pwMsg}</p>}
            <div className="space-y-3">
              <input type="password" placeholder="New password" className="input-field"
                value={pw.next} onChange={e => setPw(p => ({ ...p, next: e.target.value }))} />
              <input type="password" placeholder="Confirm new password" className="input-field"
                value={pw.confirm} onChange={e => setPw(p => ({ ...p, confirm: e.target.value }))} />
            </div>
            <div className="flex gap-2 mt-4">
              <button className="btn-primary flex-1" onClick={() => {
                if (pw.next !== pw.confirm) { setPwMsg('Passwords do not match.'); return }
                setPwMsg('Password updated. Please log in again.')
                setTimeout(() => { setShowPwModal(false); handleLogout() }, 1500)
              }}>Update</button>
              <button className="btn-ghost flex-1" onClick={() => setShowPwModal(false)}>Cancel</button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
