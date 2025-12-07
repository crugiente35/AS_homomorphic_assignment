import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'

export default function List() {
  const [questionnaires, setQuestionnaires] = useState([])

  useEffect(() => {
    fetch('/api/questionnaires').then(r => r.json()).then(d => setQuestionnaires(d.questionnaires || []))
  }, [])

  return (
    <div>
      <div className="nav-header">
        <Link to="/" className="back-link">← Back to Home</Link>
      </div>
      
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2rem' }}>
        <h1>Questionnaires</h1>
        <Link to="/create">
          <button>+ New Questionnaire</button>
        </Link>
      </div>

      {questionnaires.length === 0 ? (
        <div className="text-center" style={{ padding: '3rem', background: '#f7fafc', borderRadius: '12px' }}>
          <p>No questionnaires found.</p>
          <Link to="/create">Create your first questionnaire</Link>
        </div>
      ) : (
        <div className="questionnaire-list">
          {questionnaires.map(q => (
            <div key={q.id} className="list-item">
              <div className="list-item-content">
                <h3>Questionnaire #{q.id}</h3>
                <div className="meta-info">
                  <span className={`status-badge ${q.is_expired ? 'status-expired' : 'status-active'}`}>
                    {q.is_expired ? 'Expired' : 'Active'}
                  </span>
                  <span>👥 {q.num_responses} responses</span>
                  <span>📅 {new Date(q.deadline).toLocaleDateString()}</span>
                </div>
              </div>
              
              <div style={{ display: 'flex', gap: '10px' }}>
                <button 
                  onClick={() => { navigator.clipboard.writeText(`${window.location.origin}/questionnaire/${q.link}`); alert('Link copied!') }}
                  style={{ background: 'white', color: '#5a67d8', border: '1px solid #e2e8f0' }}
                >
                  🔗 Copy
                </button>
                <Link to={`/questionnaire/${q.link}`}>
                  <button style={{ background: 'white', color: '#5a67d8', border: '1px solid #e2e8f0' }}>View</button>
                </Link>
                <Link to={`/results/${q.link}`}>
                  <button>Results</button>
                </Link>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
