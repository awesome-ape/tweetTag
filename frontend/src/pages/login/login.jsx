import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import Input from '../../components/Input/Input.jsx';
import Button from '../../components/Button/Button.jsx';
import ErrorModal from '../../components/ErrorModal/ErrorModal.jsx';
import ThemeToggle from "../../components/ThemeToggle/ThemeToggle.jsx";
import styles from './login.module.css'; 

export default function Login() {
  const navigate = useNavigate();
  const [formData, setFormData] = useState({ username: '', password: '' });
  const [showError, setShowError] = useState(false);
  const [errorMessage, setErrorMessage] = useState("");

  const triggerError = (msg) => {
    setErrorMessage(msg);
    setShowError(true);
  };

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  const handleAction = async () => {
    const serverUrl = import.meta.env.VITE_SERVER_URL;
    const url = `${serverUrl}/auth/login`;

    try {
      if(!formData.username){
        triggerError("please fill in you'r username")
        return
      }
      if(!formData.password){
        triggerError("please fill in you'r passowrd")
        return
      }

      const response = await fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: new URLSearchParams(formData)
      });
      
      const data = await response.json();

      if (response.ok) {
        if (data?.access_token) {
          localStorage.setItem("token", data.access_token);
        }
        navigate("/home");
      } else {
        const errorMsg = Array.isArray(data.detail) 
        ? data.detail[0].msg 
        : data.detail || "Login failed.";
        triggerError(errorMsg);
      }
    } catch (err) {
      triggerError(`Could not connect to the server (${url}).`);
    }
  };

  return (
    <div className="app-wrapper">
      {/* Floating Theme Toggle in the top-right corner */}
      <div style={{ position: 'fixed', top: '20px', right: '20px', zIndex: 2000 }}>
        <ThemeToggle />
      </div>

      <div className={styles['login-card']}>
        <header className={styles['login-header']}>Welcome to TweetTag</header>
        
        <form onSubmit={(e) => { e.preventDefault(); handleAction(); }}>
          <Input 
            className={styles['username-input']} 
            name="username" 
            value={formData.username}
            placeholder="Username"
            onChange={handleChange}
          />
          
          <Input 
            className={styles['password-input']} 
            name="password" 
            type="password" 
            value={formData.password} 
            placeholder="Password" 
            onChange={handleChange} 
          />
          
          <div className={styles['reg-container']}>
            <span>Don't have an account?</span>
            <Link to="/register" className={styles['signup-link']}>
              Sign Up
            </Link>
          </div>

          <Button 
            className={styles['btn-sub']} 
            type="submit" 
            variant="primary"
          >
            Login
          </Button>
        </form>
      </div>

      {showError && (
        <ErrorModal 
          message={errorMessage} 
          onClose={() => setShowError(false)} 
        />
      )}
    </div>
  );
}