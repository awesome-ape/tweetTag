import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import Header from "../../components/Header/Header.jsx";
import styles from "./Home.module.css";

export default function Home() {
  const navigate = useNavigate();

  const token = localStorage.getItem("token");
  const username = localStorage.getItem("username") || "User";

  // ✅ show instantly from localStorage (set on login)
  const [isAdmin, setIsAdmin] = useState(
    localStorage.getItem("isADMIN") === "true"
  );

  // ✅ no loading screen; we can still "refresh" silently in background
  useEffect(() => {
    if (!token) {
      navigate("/login");
      return;
    }

    const serverUrl = import.meta.env.VITE_SERVER_URL || "http://127.0.0.1:8000";

    // optional: silent refresh so localStorage stays correct
    const refreshAdmin = async () => {
      try {
        const res = await fetch(`${serverUrl}/get_header_data`, {
          headers: { Authorization: `Bearer ${token}` },
        });

        const data = await res.json().catch(() => ({}));

        if (res.ok) {
          const admin = Boolean(data.isADMIN);
          setIsAdmin(admin);
          localStorage.setItem("isADMIN", String(admin));
        } else if (res.status === 401) {
          localStorage.removeItem("token");
          localStorage.removeItem("username");
          localStorage.removeItem("isADMIN");
          navigate("/login");
        }
      } catch (err) {
        // don't block UI on network errors
        console.error("Failed to refresh admin status:", err);
      }
    };

    refreshAdmin();
  }, [navigate, token]);

  return (
    <div className={styles.page}>
      <Header />
      <div className={styles.bg} />

      <div className={styles.container}>
        <div className={styles.card}>
          <h2 className={styles.title}>TweetTag #</h2>
          <p className={styles.welcome}>hello {username}!</p>

          <button
            className={`${styles.btn} ${styles.btnDark}`}
            onClick={() => navigate("/tweets")}
          >
            pull random tweet
          </button>

          <button
            className={`${styles.btn} ${styles.btnMid}`}
            onClick={() => navigate("/tags")}
          >
            view my tags
          </button>

          {isAdmin && (
            <>
              <button
                className={`${styles.btn} ${styles.btnLight}`}
                onClick={() => navigate("/tagged-tweets")}
              >
                view database
              </button>

              <button
                className={`${styles.btn} ${styles.btnLight}`}
                onClick={() => navigate("/escalation")}
              >
                tag escalated tweets
              </button>

              <button
                className={`${styles.btn} ${styles.btnLight}`}
                onClick={() => navigate("/table")}
              >
                Tagging Rankings
              </button>
            </>
          )}
        </div>
      </div>
    </div>
  );
}