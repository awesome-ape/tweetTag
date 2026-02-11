import React, { useState } from "react";
import Input from "../../components/Input/Input.jsx";
import Button from "../../components/Button/Button.jsx";
import ErrorModal from "../../components/ErrorModal/ErrorModal.jsx";
import "./register.css";

export default function RegisterPage() {
  const [formData, setFormData] = useState({
    username: "",
    email: "",
    password: "",
  });

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

  const handleAction = async (type) => {
    const serverUrl = import.meta.env.VITE_SERVER_URL || "http://127.0.0.1:8000";

    const isLogin = type === "Login";
    const url = `${serverUrl}/auth/${type.toLowerCase()}`;

    const options = { method: "POST", headers: {} };

    if (isLogin) {
      // OAuth2PasswordRequestForm expects x-www-form-urlencoded
      const body = new URLSearchParams();
      body.append("username", formData.username);
      body.append("password", formData.password);

      options.headers["Content-Type"] = "application/x-www-form-urlencoded";
      options.body = body;
    } else {
      // Typical register endpoint expects JSON
      options.headers["Content-Type"] = "application/json";
      options.body = JSON.stringify({
        username: formData.username,
        email: formData.email,
        password: formData.password,
      });
    }

    try {
      const response = await fetch(url, options);

      // sometimes errors return non-json
      const text = await response.text();
      let data;
      try {
        data = text ? JSON.parse(text) : {};
      } catch {
        data = { detail: text };
      }

      if (response.ok) {
        console.log("Server Response:", data);
        alert(`${type} Successful! Check console.`);
      } else {
        console.error(`${type} Failed:`, data);
        triggerError(data?.detail || `${type} failed.`);
      }
    } catch (err) {
      console.error("Request Failed", err);
      triggerError(
        `Could not connect to the server (${serverUrl}). Is the FastAPI backend running?`
      );
    }
  };

  return (
    <div className="app-wrapper">
      <div className="login-card">
        <header className="login-header">Register</header>

        <form
          onSubmit={(e) => {
            e.preventDefault();
            handleAction("Register");
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
            className="email-input"
            name="email"
            value={formData.email}
            placeholder="myemail@email.com"
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
            type="submit"
            variant="outline"
          >
            Register
          </Button>

          <Button
            className="btn-sub"
            type="button"
            onClick={() => handleAction("Login")}
            variant="primary"
          >
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
