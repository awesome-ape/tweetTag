import React, { useState } from 'react';
import Input from '../../components/Input/Input';
import { Link } from 'react-router-dom';
import Button from '../../components/Button/Button';
import ErrorModal from '../../components/ErrorModal/ErrorModal';
import styles from './login.module.css'; 


function App() {
  const [formData, setFormData] = useState({ username: '', password: '' });
  const [showError, setShowError] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');

  const triggerError = (msg) => {
    setErrorMessage(msg);
    setShowError(true);
  };

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  const handleAction = async (type) => {
    const serverUrl = import.meta.env.VITE_SERVER_URL;
    const url = `${serverUrl}/auth/login`;

    try {
      const response = await fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: new URLSearchParams(formData)
      });
      const data = await response.json();
      if (response.ok) alert("Login Successful!");
      else triggerError(data.detail || "Login failed.");
    } catch (err) {
      triggerError("Could not connect to the server.");
    }
  };

  return (
    <div className="app-wrapper">
      <div className={styles['login-card']}>
        <header className={styles['login-header']}>Welcome to TweetTag</header>
        <form onSubmit={(e) => { e.preventDefault(); handleAction('Login'); }}>
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
            Don't have an account? <Link to="/register" className={styles['signup-link']}>Sign Up</Link>
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
      {showError && <ErrorModal message={errorMessage} onClose={() => setShowError(false)} />}
    </div>
  );
}

export default App;