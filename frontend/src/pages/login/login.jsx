import React, { useState } from "react";
import { useNavigate } from "react-router-dom";

import Input from "../../components/Input/Input.jsx";
import Button from "../../components/Button/Button.jsx";
import ErrorModal from "../../components/ErrorModal/ErrorModal.jsx";

import "./login.css";

export default function Login() {
  const navigate = useNavigate();

  const [formData, setFormData] = useState({ username: "", password: "" });
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

  const handleLogin = async () => {
    const serverUrl =
      import.meta.env.VITE_SERVER_URL || "http://127.0.0.1:8000";
    const url = `${serverUrl}/auth/login`;

    const body = new URLSearchParams();
    body.append("username", formData.username);
    body.append("password", formData.password);

    try {
      const response = await fetch(url, {
        method: "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body,
      });

      const data = await response.json().catch(() => ({}));

      if (response.ok) {
        // שמירת טוקן (אם זה מה שהשרת מחזיר)
        if (data?.access_token) {
          localStorage.setItem("token", data.access_token);
        }

        // מעבר למסך הבית
        navigate("/home");
        return;
      }

      triggerError(data?.detail || "Login failed. Please check your credentials.");
    } catch (err) {
      console.error("Request Failed", err);
      triggerError(
        `Could not connect to the server (${url}). Is the FastAPI backend running?`
      );
    }
  };

  return (
    <div className="app-wrapper">
      <div className="login-card">
        <header className="login-header">Welcome to TweetTag</header>

        <form
          onSubmit={(e) => {
            e.preventDefault();
            handleLogin();
          }}
        >
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
            onClick={() => navigate("/register")}
            variant="outline"
          >
            Register
          </Button>

          <Button className="btn-sub" type="submit" variant="primary">
            Login
          </Button>
        </form>
      </div>

      {showError && (
        <ErrorModal message={errorMessage} onClose={() => setShowError(false)} />
      )}
    </div>
  );
}
