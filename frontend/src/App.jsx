import React from "react";
import {BrowserRouter as Router, Routes, Route, Navigate} from 'react-router-dom'
import Login from './pages/login/login'
import Register from './pages/register/register'
import Home from './pages/home/Home'
import TweetsPage from "./pages/tweets/TweetsPage";

import './index.css'


function App(){
  return (
    <Router>
      <div className="app-wraper">
        <Routes>
          <Route path="/" element={<Navigate to="/login"/>}/>
          <Route path="/login" element={<Login />} />          
          <Route path="/Register" element={<Register />} />          
          <Route path="*" element={<Navigate to="/login" />} />
          <Route path="/home" element={<Home />} />
          <Route path="/tweets" element={<TweetsPage />} />
        </Routes>
      </div>
    </Router>
  )
}
export default App;