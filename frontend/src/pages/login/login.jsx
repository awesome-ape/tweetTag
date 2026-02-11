import React, { useState } from 'react';
import Input from '../../components/Input/Input';
import Button from '../../components/Button/Button';
import ErrorModal from '../../components/ErrorModal/ErrorModal';
import './login.css';
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
    setFormData((prev) => ({
      ...prev,
      [name]: value
    }));
  };

  const handleAction = async (type) => {
    const serverUrl = import.meta.env.VITE_SERVER_URL;
    const isLogin = type === 'Login';
    const url = `${serverUrl}/auth/${type.toLowerCase()}`;

    // --- REGISTRATION REDIRECT PLACEHOLDER ---
    if (type === 'Register') {
      console.log("Redirecting to Registration Page...");
      alert("Registration page coming soon! For now, use the Login button.");
      return; 
    }

    let options = {
      method: 'POST',
    };

    if (isLogin) {
      // OAuth2PasswordRequestForm expects x-www-form-urlencoded
      const formDataBody = new URLSearchParams();
      formDataBody.append('username', formData.username);
      formDataBody.append('password', formData.password);

      options.headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
      };
      options.body = formDataBody;
    }

    try {
      const response = await fetch(url, options);
      const data = await response.json();

      if (response.ok) {
        console.log("Server Response:", data);
        alert("Login Successful! Check console for token.");
      } else {
        console.error("Login Failed:", data.detail);
        triggerError(data.detail || "Login failed. Please check your credentials.");
      }
    } catch (err) {
      console.error("Request Failed", err);
      triggerError("Could not connect to the server. Is the FastAPI backend running?");
    }
  };

  return (
    <div className="app-wrapper">
      <div className="login-card">
        <header className="login-header">Welcome to TweetTag</header>
        <form onSubmit={(e) => { e.preventDefault(); handleAction('Login'); }}>
          <Input 
            className="username-input" 
            name="username" 
            value={formData.username}
            placeholder="Username" 
            onChange={handleChange} 
          />
          <Input 
            className="password-input" 
            name="password" 
            type="password" 
            value={formData.password} 
            placeholder="Password" 
            onChange={handleChange} 
          />
          
          <Button 
            className="btn-reg" 
            type="button" 
            onClick={() => handleAction('Register')} 
            variant="outline"
          >
            Register
          </Button>
          
          <Button 
            className="btn-sub" 
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

export default App;