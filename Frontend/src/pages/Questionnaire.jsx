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

  const isExpired = new Date(data.deadline) <= new Date()

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
      <Link to="/">← Home</Link>
      <h1>Questionnaire</h1>
      {certInfo && (
        <p style={{ fontFamily: 'monospace', fontSize: '12px', color: '#666' }}>
          🔑 Certificate: {certInfo.cn} ({certInfo.fingerprint.slice(0, 16)}...)
        </p>
      )}
      {isExpired && <p>⚠️ Expired</p>}
      {alreadySubmitted && <p>⚠️ You have already submitted</p>}

      {data.questions.map((q, qi) => (
        <div key={qi} className="question-box">
          <h3>{q.text}</h3>
          {q.options.map((opt, oi) => opt.toUpperCase() !== 'N/A' && (
            <div key={oi} className="option-row">
              <input
                type="radio"
                id={`q${qi}-o${oi}`}
                name={`q${qi}`}
                checked={answers[qi] === oi}
                onChange={() => setAnswers({ ...answers, [qi]: oi })}
                disabled={submitted || isExpired || alreadySubmitted}
              />
              <label htmlFor={`q${qi}-o${oi}`}>{opt}</label>
            </div>
          ))}
        </div>
      ))}

      <button onClick={submit} disabled={submitted || isExpired || alreadySubmitted}>
        {submitted ? '✓ Submitted' : alreadySubmitted ? 'Already Submitted' : 'Submit'}
      </button>
    </div>
  )
}
