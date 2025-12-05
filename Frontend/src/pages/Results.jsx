import { useState, useEffect } from 'react'
import { useParams, Link } from 'react-router-dom'
import { Chart as ChartJS, ArcElement, Tooltip, Legend } from 'chart.js'
import { Pie } from 'react-chartjs-2'

ChartJS.register(ArcElement, Tooltip, Legend)

const COLORS = ['#667eea', '#764ba2', '#f093fb', '#4facfe', '#43e97b', '#fa709a', '#fee140', '#30cfd0']

export default function Results() {
  const { id } = useParams()
  const [data, setData] = useState(null)
  const [error, setError] = useState(null)

  useEffect(() => {
    fetch(`/api/questionnaire/${id}/results`)
      .then(r => r.json())
      .then(d => {
        if (d.error) setError(d.error)
        else setData(d)
      })
      .catch(e => setError(e.message))
  }, [id])

  if (error) return <div><Link to="/list">← Back</Link><p>Error: {error}</p></div>
  if (!data) return <div>Loading...</div>
  if (!data.results) return <div><Link to="/list">← Back</Link><p>No results available</p></div>

  const getChartData = (q) => ({
    labels: q.results.map(r => r.option),
    datasets: [{
      data: q.results.map(r => r.votes),
      backgroundColor: COLORS.slice(0, q.results.length)
    }]
  })

  return (
    <div>
      <Link to="/list">← Back</Link>
      <h1>Results</h1>
      <p>Responses: {data.num_responses}</p>

      {data.results.map((q, i) => (
        <div key={i}>
          <h3>Question {i + 1}: {q.question}</h3>
          <div style={{ height: 300 }}>
            <Pie data={getChartData(q)} />
          </div>
        </div>
      ))}
    </div>
  )
}
