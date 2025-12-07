import { Link } from 'react-router-dom'

export default function Home() {
  return (
    <div className="home-container">
      <div className="hero-section">
        <h1>🔐 Secure Questionnaire System</h1>
        <p className="subtitle">Privacy guaranteed with BFV Homomorphic Encryption</p>
        <p className="description">
          Create and answer questionnaires securely. Your responses are encrypted on your device 
          and remain encrypted while being processed. Only the final aggregated results are decrypted.
        </p>
      </div>

      <div className="action-cards">
        <Link to="/create" className="card action-card">
          <div className="icon">📝</div>
          <h2>Create Questionnaire</h2>
          <p>Design a new secure questionnaire with custom questions and options.</p>
          <span className="btn-link">Start Creating &rarr;</span>
        </Link>

        <Link to="/list" className="card action-card">
          <div className="icon">📊</div>
          <h2>View Questionnaires</h2>
          <p>Browse existing questionnaires, participate, or view aggregated results.</p>
          <span className="btn-link">Browse List &rarr;</span>
        </Link>
      </div>
      
      <div className="features-section">
        <h3>How it works</h3>
        <div className="features-grid">
          <div className="feature">
            <span className="feature-icon">🔒</span>
            <h4>Client-Side Encryption</h4>
            <p>Answers are encrypted before leaving your browser.</p>
          </div>
          <div className="feature">
            <span className="feature-icon">☁️</span>
            <h4>Homomorphic Processing</h4>
            <p>Votes are counted without ever decrypting individual answers.</p>
          </div>
          <div className="feature">
            <span className="feature-icon">🛡️</span>
            <h4>Secure Aggregation</h4>
            <p>Only the final totals are revealed, preserving anonymity.</p>
          </div>
        </div>
      </div>
    </div>
  )
}
