import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import Input from "../../components/Input/Input.jsx";
import Button from "../../components/Button/Button.jsx";
import ErrorModal from "../../components/ErrorModal/ErrorModal.jsx";
import ThemeToggle from "../../components/ThemeToggle/ThemeToggle.jsx";
import styles from "./ForgotPasswordPage.module.css";

export default function ForgotPasswordPage() {
  const navigate = useNavigate();

  const [email, setEmail] = useState("");
  const [loading, setLoading] = useState(false);
  const [showError, setShowError] = useState(false);
  const [errorMessage, setErrorMessage] = useState("");

  const triggerError = (msg) => {
    setErrorMessage(msg);
    setShowError(true);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (loading) return;

    const trimmedEmail = email.trim();
    if (!trimmedEmail) return triggerError("Please enter your email");

    const serverUrl =
      import.meta.env.VITE_SERVER_URL ||
      "https://em5epzymak.eu-west-3.awsapprunner.com";

    setLoading(true);

    try {
      const response = await fetch(`${serverUrl}/auth/forgot-password`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ email: trimmedEmail }),
      });

      const data = await response.json().catch(() => ({}));

      if (!response.ok) {
        const msg =
          Array.isArray(data?.detail)
            ? data.detail?.[0]?.msg || "Request failed."
            : data?.detail || "Request failed.";
        triggerError(msg);
        return;
      }

      // 🔥 פה הקסם — לוקחים את הטוקן מהשרת ומעבירים לעמוד הבא
      if (data?.reset_token_for_testing) {
        navigate(
          `/reset-password?token=${encodeURIComponent(
            data.reset_token_for_testing
          )}`
        );
        return;
      }

      // fallback (אם אין טוקן)
      triggerError("Something went wrong. No reset token received.");
    } catch (err) {
      triggerError("Could not connect to the server.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="app-wrapper">
      <div style={{ position: "fixed", top: 20, right: 20, zIndex: 2000 }}>
        <ThemeToggle />
      </div>

      <div className={styles.card}>
        <h2 className={styles.title}>Forgot Password</h2>

        <form onSubmit={handleSubmit} className={styles.form}>
          <Input
            name="email"
            type="email"
            value={email}
            placeholder="Enter your email"
            onChange={(e) => setEmail(e.target.value)}
          />

          <Button type="submit" disabled={loading}>
            {loading ? "Sending..." : "Send reset link"}
          </Button>
        </form>

        <button
          className={styles.back}
          onClick={() => navigate("/login")}
        >
          Back to login
        </button>
      </div>

      {showError && (
        <ErrorModal message={errorMessage} onClose={() => setShowError(false)} />
      )}
    </div>
  );
}