import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'

export default function List() {
  const [questionnaires, setQuestionnaires] = useState([])

  useEffect(() => {
    fetch('/api/questionnaires').then(r => r.json()).then(d => setQuestionnaires(d.questionnaires || []))
  }, [])

  return (
    <div>
      <Link to="/">← Home</Link>
      <h1>Questionnaires</h1>
      {questionnaires.length === 0 ? (
        <p>No questionnaires. <Link to="/create">Create one</Link></p>
      ) : (
        <ul>
          {questionnaires.map(q => (
            <li key={q.id}>
              <strong>#{q.id}</strong> - {q.is_expired ? 'Finished' : 'Active'} - {q.num_responses} responses
              {' '}
              <Link to={`/questionnaire/${q.link}`}>View</Link>
              {' '}
              <Link to={`/results/${q.link}`}>Results</Link>
              {' '}
              <button onClick={() => { navigator.clipboard.writeText(`${window.location.origin}/questionnaire/${q.link}`); alert('Copied') }}>Copy Link</button>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
