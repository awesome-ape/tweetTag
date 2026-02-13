import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import Tweet from "../../components/Tweet/Tweet.jsx";
import styles from "./TweetsPage.module.css";

export default function TweetsPage() {
  const navigate = useNavigate();

  const [tweet, setTweet] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  const serverUrl =
    import.meta.env.VITE_SERVER_URL || "http://127.0.0.1:8000";

  const fetchSingleTweet = async () => {
    setLoading(true);
    setError("");

    const token = localStorage.getItem("token");
    if (!token) {
      navigate("/login");
      return;
    }

    try {
      const res = await fetch(`${serverUrl}/claim_tweet`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      const data = await res.json();

      if (!res.ok) {
        throw new Error(data?.detail || "Failed to fetch tweet");
      }

      setTweet(data);
    } catch (err) {
      setError(err?.message || "Unknown error");
      setTweet(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSingleTweet();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  if (loading) return <div className={styles.center}>Loading...</div>;
  if (error)
    return (
      <div className={`${styles.center} ${styles.error}`}>
        Error: {error}
      </div>
    );

  return (
    <div className={styles.page}>
      <div className={styles.container}>
        {tweet ? <Tweet tweet={tweet} /> : <p>No tweet available</p>}

        <div className={styles.actions}>
          <button
            className={`${styles.btn} ${styles.btnPrimary}`}
            onClick={fetchSingleTweet}
          >
            Pull next tweet
          </button>

          <button
            className={`${styles.btn} ${styles.btnSecondary}`}
            onClick={() => navigate("/home")}
          >
            Back to home
          </button>
        </div>
      </div>
    </div>
  );
}
