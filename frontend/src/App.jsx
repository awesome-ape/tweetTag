import React from "react";
import {BrowserRouter as Router, Routes, Route, Navigate} from 'react-router-dom'
import Login from './pages/login/login'
import './index.css'


function App(){
  return (
    <Router>
      <div className="app-wraper">
        <Routes>
          <Route path="/" element={<Navigate to="/login"/>}/>
          <Route path="/login" element={<Login />} />
          <Route path="*" element={<Navigate to="/login" />} />
        </Routes>
      </div>
    </Router>
  )
}
export default App;