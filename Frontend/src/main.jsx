import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import Home from './pages/Home'
import Create from './pages/Create'
import List from './pages/List'
import Questionnaire from './pages/Questionnaire'
import Results from './pages/Results'
import './index.css'

ReactDOM.createRoot(document.getElementById('root')).render(
  <BrowserRouter>
    <Routes>
      <Route path="/" element={<Home />} />
      <Route path="/create" element={<Create />} />
      <Route path="/list" element={<List />} />
      <Route path="/questionnaire/:id" element={<Questionnaire />} />
      <Route path="/results/:id" element={<Results />} />
    </Routes>
  </BrowserRouter>
)
