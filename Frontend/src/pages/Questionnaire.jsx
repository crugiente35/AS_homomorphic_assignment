import { useState, useEffect } from 'react'
import { useParams, Link } from 'react-router-dom'
import { PublicKey, BatchEncoder, BFVEncryptor } from '../crypto'

export default function Questionnaire() {
  const { id } = useParams()
  const [data, setData] = useState(null)
  const [answers, setAnswers] = useState({})
  const [submitted, setSubmitted] = useState(false)
  const [alreadySubmitted, setAlreadySubmitted] = useState(false)
  const [certInfo, setCertInfo] = useState(null)

  useEffect(() => {
    fetch(`/api/questionnaire/${id}`).then(r => r.json()).then(setData)
    fetch('/api/cert-info').then(r => r.json()).then(setCertInfo)
  }, [id])

  if (!data) return null

  // Backend sends UTC time, compare with current UTC time
  const deadlineUTC = new Date(data.deadline)
  const nowUTC = new Date()
  const isExpired = deadlineUTC <= nowUTC
  
  // Format deadline for display in local time
  const deadlineLocal = deadlineUTC.toLocaleString()

  const submit = async () => {
    const params = { polyDegree: data.params.poly_degree, plainModulus: data.params.plain_modulus, ciphModulus: data.params.ciph_modulus }
    const pk = PublicKey.fromJSON(data.public_key)
    const encoder = new BatchEncoder(params)
    const encryptor = new BFVEncryptor(params, pk)

    const encrypted = data.questions.map((_, i) => {
      const vec = new Array(params.polyDegree).fill(0)
      vec[answers[i]] = 1
      return encryptor.encrypt(encoder.encode(vec)).toJSON()
    })

    const res = await fetch('/api/submit-answers', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ questionnaire_id: id, encrypted_answers: encrypted })
    })

    if (res.status === 409) {
      setAlreadySubmitted(true)
      return
    }

    setSubmitted(true)
  }

  return (
    <div>
      <div className="nav-header">
        <Link to="/" className="back-link">← Back to Home</Link>
      </div>
      
      <div style={{ marginBottom: '2rem' }}>
        <h1>Questionnaire</h1>
        
        <div style={{ background: '#f7fafc', padding: '1rem', borderRadius: '8px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
          {certInfo && (
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.9rem', color: '#4a5568' }}>
              <span>🔑</span>
              <span style={{ fontWeight: 600 }}>{certInfo.cn}</span>
              <span style={{ color: '#a0aec0', fontSize: '0.8rem' }}>({certInfo.fingerprint.slice(0, 8)}...)</span>
            </div>
          )}
          
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.9rem', color: '#4a5568' }}>
            <span>⏰</span>
            <span>Deadline: <strong>{deadlineLocal}</strong></span>
          </div>
        </div>
      </div>

      {isExpired && (
        <div style={{ background: '#fff5f5', color: '#c53030', padding: '1rem', borderRadius: '8px', marginBottom: '2rem', border: '1px solid #feb2b2' }}>
          <strong>⚠️ This questionnaire has expired.</strong> You can no longer submit answers.
        </div>
      )}
      
      {alreadySubmitted && (
        <div style={{ background: '#ebf8ff', color: '#2b6cb0', padding: '1rem', borderRadius: '8px', marginBottom: '2rem', border: '1px solid #bee3f8' }}>
          <strong>ℹ️ You have already submitted a response.</strong> Thank you for participating!
        </div>
      )}

      {submitted ? (
        <div className="text-center" style={{ padding: '4rem 0' }}>
          <div style={{ fontSize: '4rem', marginBottom: '1rem' }}>🎉</div>
          <h2>Thank you!</h2>
          <p>Your answers have been encrypted and submitted successfully.</p>
          <Link to="/">
            <button className="mt-4">Return Home</button>
          </Link>
        </div>
      ) : (
        <>
          {data.questions.map((q, qi) => (
            <div key={qi} className="question-box">
              <h3>{q.text}</h3>
              <div style={{ display: 'grid', gap: '0.5rem' }}>
                {q.options.map((opt, oi) => opt.toUpperCase() !== 'N/A' && (
                  <div key={oi} className="option-row" onClick={() => !submitted && !isExpired && !alreadySubmitted && setAnswers({ ...answers, [qi]: oi })}>
                    <input
                      type="radio"
                      id={`q${qi}-o${oi}`}
                      name={`q${qi}`}
                      checked={answers[qi] === oi}
                      onChange={() => {}}
                      disabled={submitted || isExpired || alreadySubmitted}
                      style={{ cursor: 'pointer' }}
                    />
                    <label htmlFor={`q${qi}-o${oi}`} style={{ cursor: 'pointer' }}>{opt}</label>
                  </div>
                ))}
              </div>
            </div>
          ))}

          <div style={{ marginTop: '2rem', display: 'flex', justifyContent: 'flex-end' }}>
            <button 
              onClick={submit} 
              disabled={submitted || isExpired || alreadySubmitted || Object.keys(answers).length < data.questions.length}
              style={{ padding: '1rem 3rem', fontSize: '1.1rem' }}
            >
              {submitted ? '✓ Submitted' : alreadySubmitted ? 'Already Submitted' : 'Submit Answers'}
            </button>
          </div>
        </>
      )}
    </div>
  )
}
