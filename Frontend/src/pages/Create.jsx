import { useState } from 'react'
import { Link } from 'react-router-dom'

export default function Create() {
  const [questions, setQuestions] = useState([{ id: 1, text: '', options: ['', '', '', '', 'N/A', 'N/A', 'N/A', 'N/A'] }])
  // Initialize with local time (7 days from now)
  const defaultDate = new Date(Date.now() + 7 * 24 * 60 * 60 * 1000)
  const localDateStr = new Date(defaultDate.getTime() - defaultDate.getTimezoneOffset() * 60000).toISOString().slice(0, 16)
  const [deadline, setDeadline] = useState(localDateStr)
  const [customLink, setCustomLink] = useState('')
  const [hideResultsUntilDeadline, setHideResultsUntilDeadline] = useState(true)
  const [result, setResult] = useState(null)

  const addQuestion = () => setQuestions([...questions, { id: Date.now(), text: '', options: ['', '', '', '', 'N/A', 'N/A', 'N/A', 'N/A'] }])

  const removeQuestion = (id) => setQuestions(questions.filter(q => q.id !== id))

  const updateText = (id, text) => setQuestions(questions.map(q => q.id === id ? { ...q, text } : q))

  const updateOption = (id, idx, val) => setQuestions(questions.map(q => {
    if (q.id !== id) return q
    const options = [...q.options]
    options[idx] = val
    return { ...q, options }
  }))

  const submit = async (e) => {
    e.preventDefault()
    // Convert local time to UTC for backend
    const localDate = new Date(deadline)
    const utcDateStr = localDate.toISOString()

    const res = await fetch('/api/create-questionnaire', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        questions: questions.map(q => ({ text: q.text, options: q.options })),
        deadline_datetime: utcDateStr,
        link: customLink || null,
        hide_results_until_deadline: hideResultsUntilDeadline
      })
    })
    setResult(await res.json())
  }

  if (result) {
    return (
      <div className="text-center" style={{ padding: '4rem 0' }}>
        <div style={{ fontSize: '4rem', marginBottom: '1rem' }}>✅</div>
        <h1>Questionnaire Created!</h1>
        <div style={{ background: '#f7fafc', padding: '2rem', borderRadius: '12px', margin: '2rem 0' }}>
          <p style={{ marginBottom: '0.5rem' }}>Share this link with participants:</p>
          <div style={{ display: 'flex', gap: '10px', justifyContent: 'center', alignItems: 'center' }}>
            <input 
              readOnly 
              value={`${window.location.origin}/questionnaire/${result.link}`} 
              style={{ margin: 0, maxWidth: '400px' }}
            />
            <button onClick={() => { navigator.clipboard.writeText(`${window.location.origin}/questionnaire/${result.link}`); alert('Copied!') }}>
              Copy
            </button>
          </div>
        </div>
        <div style={{ display: 'flex', gap: '1rem', justifyContent: 'center' }}>
          <Link to={`/questionnaire/${result.link}`}>
            <button>View Questionnaire</button>
          </Link>
          <Link to="/list">
            <button style={{ background: 'white', color: '#5a67d8', border: '1px solid #e2e8f0' }}>Back to List</button>
          </Link>
        </div>
      </div>
    )
  }

  return (
    <div>
      <div className="nav-header">
        <Link to="/" className="back-link">← Back to Home</Link>
      </div>
      
      <h1>Create New Questionnaire</h1>
      
      <form onSubmit={submit} style={{ maxWidth: '800px', margin: '0 auto' }}>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '2rem', marginBottom: '2rem' }}>
          <div>
            <label>Deadline (Local Time)</label>
            <input type="datetime-local" value={deadline} onChange={e => setDeadline(e.target.value)} required />
            <p className="text-sm text-gray">Questionnaire will automatically close at this time.</p>
          </div>
          <div>
            <label>Custom Link (Optional)</label>
            <input value={customLink} onChange={e => setCustomLink(e.target.value)} placeholder="e.g., team-survey-2025" />
            <p className="text-sm text-gray">Leave empty for a random secure link.</p>
          </div>
        </div>

        <div style={{ marginBottom: '2rem' }}>
           <label style={{ display: 'flex', alignItems: 'center', gap: '10px', cursor: 'pointer' }}>
            <input 
              type="checkbox" 
              checked={hideResultsUntilDeadline} 
              onChange={e => setHideResultsUntilDeadline(e.target.checked)} 
              style={{ width: 'auto', margin: 0 }}
            />
            Hide results until deadline
          </label>
        </div>

        <hr style={{ border: 'none', borderTop: '1px solid #e2e8f0', margin: '2rem 0' }} />
        
        {questions.map((q, qi) => (
          <div key={q.id} className="question-box">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
              <h3>Question {qi + 1}</h3>
              {questions.length > 1 && (
                <button 
                  type="button" 
                  onClick={() => removeQuestion(q.id)}
                  style={{ background: '#fed7d7', color: '#9b2c2c', padding: '4px 12px', fontSize: '0.875rem' }}
                >
                  Remove
                </button>
              )}
            </div>
            
            <div style={{ marginBottom: '1.5rem' }}>
              <label>Question Text</label>
              <textarea 
                value={q.text} 
                onChange={e => updateText(q.id, e.target.value)} 
                placeholder="What would you like to ask?" 
                required 
              />
            </div>
            
            <div>
              <label>Options (8 slots available)</label>
              <p className="text-sm text-gray" style={{ marginBottom: '1rem' }}>Enter options below. Use "N/A" for unused slots.</p>
              
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                {q.options.map((opt, oi) => (
                  <div key={oi}>
                    <input 
                      value={opt} 
                      onChange={e => updateOption(q.id, oi, e.target.value)} 
                      placeholder={`Option ${oi + 1}`} 
                      required 
                      style={{ marginBottom: 0 }}
                    />
                  </div>
                ))}
              </div>
            </div>
          </div>
        ))}
        
        <div style={{ display: 'flex', gap: '1rem', marginTop: '2rem' }}>
          <button type="button" onClick={addQuestion} style={{ background: 'white', color: '#5a67d8', border: '1px solid #e2e8f0' }}>
            + Add Another Question
          </button>
          <button type="submit" style={{ flexGrow: 1 }}>
            Create Questionnaire
          </button>
        </div>
      </form>
    </div>
  )
}
