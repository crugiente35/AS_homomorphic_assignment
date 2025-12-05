import { Link } from 'react-router-dom'

export default function Home() {
  return (
    <div>
      <h1>🔐 Questionnaire System</h1>
      <p>Privacy guaranteed with BFV Homomorphic Encryption</p>
      <div>
        <Link to="/create">📝 Create Questionnaire</Link>
        {' | '}
        <Link to="/list">📊 View Questionnaires</Link>
      </div>
    </div>
  )
}
