import { useContext, useState } from 'react'
import { AuthContext } from '../context/AuthContext'
import { useNavigate } from 'react-router-dom'
import ProfileDropdown from './ProfileDropdown'

export default function Navbar() {
  const { user } = useContext(AuthContext)
  const [showProfile, setShowProfile] = useState(false)

  const initials = user?.name
    ? user.name.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2)
    : user?.email?.[0]?.toUpperCase() || 'U'

  return (
    <header className="h-14 bg-white border-b border-gray-200 flex items-center px-5 justify-between flex-shrink-0 z-10">
      {/* Brand */}
      <div className="flex items-center gap-2">
        <span className="text-xl">🏢</span>
        <span className="font-bold text-gray-900 text-base tracking-tight">ClaimPilot</span>
        <span className="text-xs text-gray-400 ml-1 hidden sm:block">Insurance Claim Assistant</span>
      </div>

      {/* User menu */}
      <div className="relative">
        <button
          onClick={() => setShowProfile(v => !v)}
          className="flex items-center gap-2 btn-ghost text-sm"
        >
          <div className="w-8 h-8 rounded-full bg-brand-600 text-white flex items-center justify-center text-xs font-semibold">
            {initials}
          </div>
          <span className="hidden sm:block text-gray-700 font-medium">
            {user?.name || user?.email || 'Account'}
          </span>
          <svg className="w-4 h-4 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
          </svg>
        </button>

        {showProfile && (
          <ProfileDropdown onClose={() => setShowProfile(false)} />
        )}
      </div>
    </header>
  )
}
