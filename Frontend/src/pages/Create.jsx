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
      <div>
        <h1>✅ Questionnaire Created</h1>
        <p>Link: {window.location.origin}/questionnaire/{result.link}</p>
        <button onClick={() => navigator.clipboard.writeText(`${window.location.origin}/questionnaire/${result.link}`)}>Copy</button>
        <Link to={`/questionnaire/${result.link}`}>View</Link>
        {' | '}
        <Link to="/list">List</Link>
      </div>
    )
  }

  return (
    <div>
      <Link to="/">← Home</Link>
      <h1>Create Questionnaire</h1>
      <form onSubmit={submit}>
        <div>
          <label>Deadline (Local Time): </label>
          <input type="datetime-local" value={deadline} onChange={e => setDeadline(e.target.value)} required />
        </div>
        <div>
          <label>Custom link: </label>
          <input value={customLink} onChange={e => setCustomLink(e.target.value)} placeholder="optional" />
        </div>
        <div>
          <label>Hide results until deadline</label>
          <input type="checkbox" checked={hideResultsUntilDeadline} onChange={e => setHideResultsUntilDeadline(e.target.checked)} />
        </div>
        <hr />
        {questions.map((q, qi) => (
          <div key={q.id} style={{ border: '1px solid #ccc', padding: 10, marginBottom: 10 }}>
            <h3>Question {qi + 1} {questions.length > 1 && <button type="button" onClick={() => removeQuestion(q.id)}>×</button>}</h3>
            <div>
              <label>Question text:</label><br />
              <textarea value={q.text} onChange={e => updateText(q.id, e.target.value)} placeholder="Question text" required style={{ width: '100%' }} />
            </div>
            <div>
              <label>Options (8 required, use N/A for unused):</label>
              {q.options.map((opt, oi) => (
                <div key={oi}>
                  <label>{oi + 1}: </label>
                  <input value={opt} onChange={e => updateOption(q.id, oi, e.target.value)} placeholder={`Option ${oi + 1}`} required />
                </div>
              ))}
            </div>
          </div>
        ))}
        <button type="button" onClick={addQuestion}>+ Add Question</button>
        <br /><br />
        <button type="submit">Create</button>
      </form>
    </div>
  )
}
