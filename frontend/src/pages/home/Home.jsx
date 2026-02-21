import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import Header from "../../components/Header/Header.jsx";
import styles from "./Home.module.css";

export default function Home() {
  const navigate = useNavigate();
  const username = localStorage.getItem("username") || "User";

  const [isAdmin, setIsAdmin] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchIsAdmin = async () => {
      const token = localStorage.getItem("token");
      if (!token) {
        navigate("/login");
        return;
      }

      try {
        const serverUrl =
          import.meta.env.VITE_SERVER_URL || "http://127.0.0.1:8000";

        const res = await fetch(`${serverUrl}/get_header_data`, {
          headers: { Authorization: `Bearer ${token}` },
        });

        const data = await res.json();

        if (res.ok) {
          setIsAdmin(Boolean(data.isADMIN));
        } else if (res.status === 401) {
          localStorage.removeItem("token");
          localStorage.removeItem("username");
          navigate("/login");
        } else {
          setIsAdmin(false);
        }
      } catch (err) {
        console.error("Failed to fetch admin status:", err);
        setIsAdmin(false);
      } finally {
        setLoading(false);
      }
    };

    fetchIsAdmin();
  }, [navigate]);

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

          {}
          {!loading && isAdmin && (
            <>
              <button
               className={`${styles.btn} ${styles.btnLight}`}
                onClick={() => navigate("/tagged-tweets")} >
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