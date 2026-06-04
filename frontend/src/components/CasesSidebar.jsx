const INTENT_LABELS = {
  motor_claim:      'Motor Claim',
  health_claim:     'Health Claim',
  life_insurance:   'Life Insurance',
  travel_insurance: 'Travel Insurance',
  home_property:    'Home & Property',
  personal_accident:'Personal Accident',
}

const INTENT_ICONS = {
  motor_claim:      '🚗',
  health_claim:     '🏥',
  life_insurance:   '❤️',
  travel_insurance: '✈️',
  home_property:    '🏠',
  personal_accident:'🩹',
}

export default function CasesSidebar({ cases, activeCaseId, onSelectCase, onNewCase }) {
  return (
    <aside className="w-64 bg-white border-r border-gray-200 flex flex-col flex-shrink-0">
      {/* Header */}
      <div className="px-4 py-4 border-b border-gray-100">
        <button
          onClick={onNewCase}
          className="w-full flex items-center justify-center gap-2 btn-primary text-sm py-2"
        >
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
          </svg>
          New Case
        </button>
      </div>

      {/* Cases list */}
      <div className="flex-1 overflow-y-auto py-2">
        {cases.length === 0 ? (
          <div className="px-4 py-8 text-center">
            <p className="text-xs text-gray-400">No cases yet.</p>
            <p className="text-xs text-gray-400 mt-1">Start a new case above.</p>
          </div>
        ) : (
          cases.map(c => (
            <button
              key={c.case_id}
              onClick={() => onSelectCase(c.case_id)}
              className={`w-full text-left px-4 py-3 border-b border-gray-50 hover:bg-gray-50 transition-colors
                ${activeCaseId === c.case_id ? 'bg-brand-50 border-l-2 border-l-brand-600' : ''}`}
            >
              <div className="flex items-center justify-between mb-1">
                <span className="text-sm font-medium text-gray-800 flex items-center gap-1.5">
                  <span>{INTENT_ICONS[c.intent] || '📋'}</span>
                  {INTENT_LABELS[c.intent] || c.intent || 'New Case'}
                </span>
                <span className={`text-[10px] font-semibold px-1.5 py-0.5 rounded-full
                  ${c.case_status === 'complete'
                    ? 'bg-green-100 text-green-700'
                    : 'bg-orange-100 text-orange-700'}`}>
                  {c.case_status === 'complete' ? 'Done' : 'Active'}
                </span>
              </div>
              {c.case_status !== 'complete' && c.pending_docs?.length > 0 && (
                <p className="text-xs text-gray-400">
                  {c.pending_docs.length} doc{c.pending_docs.length > 1 ? 's' : ''} pending
                </p>
              )}
              {c.created_at && (
                <p className="text-[10px] text-gray-300 mt-0.5">
                  {new Date(c.created_at).toLocaleDateString('en-IN', { day: 'numeric', month: 'short' })}
                </p>
              )}
            </button>
          ))
        )}
      </div>
    </aside>
  )
}
