import React, { useMemo, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import Input from "../../components/Input/Input.jsx";
import Button from "../../components/Button/Button.jsx";
import ErrorModal from "../../components/ErrorModal/ErrorModal.jsx";
import ThemeToggle from "../../components/ThemeToggle/ThemeToggle.jsx";
import styles from "./ResetPasswordPage.module.css";

export default function ResetPasswordPage() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();

  const token = useMemo(() => searchParams.get("token") || "", [searchParams]);

  const [formData, setFormData] = useState({
    new_password: "",
    confirm_password: "",
  });

  const [loading, setLoading] = useState(false);
  const [showError, setShowError] = useState(false);
  const [errorMessage, setErrorMessage] = useState("");
  const [success, setSuccess] = useState(false);

  const triggerError = (msg) => {
    setErrorMessage(msg);
    setShowError(true);
  };

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (loading) return;

    const { new_password, confirm_password } = formData;

    if (!token) return triggerError("Missing token");
    if (!new_password) return triggerError("Enter new password");
    if (new_password.length < 6)
      return triggerError("Password must be at least 6 characters");
    if (new_password !== confirm_password)
      return triggerError("Passwords do not match");

    const serverUrl =
      import.meta.env.VITE_SERVER_URL ||
      "https://em5epzymak.eu-west-3.awsapprunner.com";

    setLoading(true);

    try {
      const response = await fetch(`${serverUrl}/auth/reset-password`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          token,
          new_password,
        }),
      });

      const data = await response.json().catch(() => ({}));

      if (!response.ok) {
        const msg =
          Array.isArray(data?.detail)
            ? data.detail?.[0]?.msg || "Reset failed."
            : data?.detail || "Reset failed.";
        triggerError(msg);
        return;
      }

      setSuccess(true);

      setTimeout(() => {
        navigate("/login");
      }, 1500);
    } catch (err) {
      triggerError("Server error");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="app-wrapper">
      <div style={{ position: "fixed", top: 20, right: 20 }}>
        <ThemeToggle />
      </div>

      <div className={styles.card}>
        <h2 className={styles.title}>Reset Password</h2>

        {success ? (
          <div className={styles.success}>Password updated successfully</div>
        ) : (
          <form onSubmit={handleSubmit} className={styles.form}>
            <Input
              name="new_password"
              type="password"
              placeholder="New password"
              value={formData.new_password}
              onChange={handleChange}
            />

            <Input
              name="confirm_password"
              type="password"
              placeholder="Confirm password"
              value={formData.confirm_password}
              onChange={handleChange}
            />
              <div className={styles.container}>
            <Button type="submit" disabled={loading}>
              {loading ? "Updating..." : "Reset password"}
            </Button>
             <Button className={styles.back} onClick={() => navigate("/login")}>
          Back to login
        </Button>
        </div>
          </form>
        )}

       
      </div>

      {showError && (
        <ErrorModal message={errorMessage} onClose={() => setShowError(false)} />
      )}
    </div>
  );
}