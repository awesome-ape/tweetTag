import React, { useState } from 'react';
import { Link } from 'react-router-dom.jsx';
import Input from '../../components/Input/Input.jsx';
import Button from '../../components/Button/Button.jsx';
import ErrorModal from '../../components/ErrorModal/ErrorModal.jsx';
import styles from './register.module.css';
export default function RegisterPage() {
function App() {
  const [formData, setFormData] = useState({ username: '', email: '', password: '' });
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
    const url = `${serverUrl}/auth/register`;

    try {
      const response = await fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData)
      });
      const data = await response.json();

      if (response.ok) {
        alert("Registration Successful!");
      } else {
        triggerError(data.detail || "Registration failed.");
      }
    } catch (err) {
      triggerError("Could not connect to the server.");
    }
  };

  return (
    <div className="app-wrapper">
      <div className={styles['register-card']}>
        <header className={styles['login-header']}>Register</header>
        <form onSubmit={(e) => { e.preventDefault(); handleAction(); }}>
          <Input 
            className={styles['username-input']} 
            name="username" 
            value={formData.username}
            placeholder="Username"
            onChange={handleChange}
          />

          <Input
            className={styles['email-input']}
            name="email"
            value={formData.email}
            placeholder="Email@email.com"
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
          
          <Button 
            className={styles['btn-reg']} 
            type="submit" 
            variant="primary"
          >
            Register
          </Button>

          <div className={styles['footer-text']}>
            Already have an account? <div><Link to="/login" className={styles['signin-link']}>Sign in</Link>
          </div>
          </div>
        </form>
      </div>
      {showError && <ErrorModal message={errorMessage} onClose={() => setShowError(false)} />}
    </div>
  );
  }
}
