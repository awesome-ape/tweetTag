import React, { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import Input from "../../components/Input/Input.jsx";
import Button from "../../components/Button/Button.jsx";
import ErrorModal from "../../components/ErrorModal/ErrorModal.jsx";
import styles from "./login.module.css";

export default function Login() {
  const navigate = useNavigate();

  const [formData, setFormData] = useState({ username: "", password: "" });
  const [showError, setShowError] = useState(false);
  const [errorMessage, setErrorMessage] = useState("");
  const [loading, setLoading] = useState(false);

  const triggerError = (msg) => {
    setErrorMessage(msg);
    setShowError(true);
  };

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  const handleAction = async () => {
    const username = (formData.username || "").trim();
    const password = formData.password || "";

    // ✅ validate BEFORE fetch
    if (!username) {
      triggerError("Please fill in your username");
      return;
    }
    if (!password) {
      triggerError("Please fill in your password");
      return;
    }

    const serverUrl =
      import.meta.env.VITE_SERVER_URL || "http://127.0.0.1:8000";
    const url = `${serverUrl}/auth/login`;

    setLoading(true);

    try {
      const response = await fetch(url, {
        method: "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body: new URLSearchParams({ username, password }),
      });

      const data = await response.json().catch(() => ({}));

      if (response.ok) {
        // ✅ Save token
        if (data?.access_token) {
          localStorage.setItem("token", data.access_token);
        }

        // ✅ Save username (immediate UI on Home)
        localStorage.setItem("username", data?.username || username);

        // ✅ Save admin flag (immediate UI on Home)
        // supports possible names: isADMIN / is_admin / admin
        const adminFlag =
          data?.isADMIN ?? data?.is_admin ?? data?.admin ?? false;
        localStorage.setItem("isADMIN", String(Boolean(adminFlag)));

        navigate("/home");
      } else {
        const errorMsg = Array.isArray(data?.detail)
          ? data.detail?.[0]?.msg || "Login failed."
          : data?.detail || "Login failed.";
        triggerError(errorMsg);
      }
    } catch (err) {
      triggerError(`Could not connect to the server (${url}).`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="app-wrapper">
      <div className={styles["login-card"]}>
        <header className={styles["login-header"]}>Welcome to TweetTag</header>

        <form
          onSubmit={(e) => {
            e.preventDefault();
            if (!loading) handleAction();
          }}
        >
          <Input
            className={styles["username-input"]}
            name="username"
            value={formData.username}
            placeholder="Username"
            onChange={handleChange}
            autoComplete="username"
          />

          <Input
            className={styles["password-input"]}
            name="password"
            type="password"
            value={formData.password}
            placeholder="Password"
            onChange={handleChange}
            autoComplete="current-password"
          />

          <div className={styles["reg-container"]}>
            <span>Don't have an account?</span>
            <Link to="/register" className={styles["signup-link"]}>
              Sign Up
            </Link>
          </div>

          <Button
            className={styles["btn-sub"]}
            type="submit"
            variant="primary"
            disabled={loading}
          >
            {loading ? "Logging in..." : "Login"}
          </Button>
        </form>
      </div>

      {showError && (
        <ErrorModal message={errorMessage} onClose={() => setShowError(false)} />
      )}
    </div>
  );
}