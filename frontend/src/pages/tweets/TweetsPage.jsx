import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import Tweet from "../../components/Tweet/Tweet.jsx";
import Header from "../../components/Header/Header.jsx";
import Button from "../../components/Button/Button.jsx"; 
import styles from "./TweetsPage.module.css";

export default function TweetsPage() {
  const navigate = useNavigate();
  const [tweet, setTweet] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  const serverUrl = import.meta.env.VITE_SERVER_URL || "http://127.0.0.1:8000";

  const fetchSingleTweet = async () => {
    setLoading(true);
    setError("");
    const token = localStorage.getItem("token");
    if (!token) { navigate("/login"); return; }

    try {
      const res = await fetch(`${serverUrl}/claim_tweet`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data?.detail || "Failed to fetch tweet");
      setTweet(data);
    } catch (err) {
      setError(err?.message || "Unknown error");
      setTweet(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchSingleTweet(); }, []);

  const handleTag = (type) => console.log(`Tagged as: ${type}`);
  const submitAndHome = () => navigate("/home");
  const submitAndNext = () => fetchSingleTweet();

  if (loading) return <div className={styles.center}>Loading...</div>;

  return (
    <div className={styles.page}>
      <Header />
      
      <div className={styles.mainWrapper}>
        <div className={styles.container}>
          
          {/* ONLY THIS AREA SCROLLS */}
          <div className={styles.scrollableContent}>
            {error ? (
              <div className={styles.error}>Error: {error}</div>
            ) : tweet ? (
              <Tweet tweet={tweet} />
            ) : (
              <p>No tweet available</p>
            )}
          </div>

          <div className={styles.controls}>
            <div className={styles.sectionHeader}>Risk Assessment</div>
            <div className={styles.riskActions}>
              <Button className={`${styles.riskBtn} ${styles.safe}`} onClick={() => handleTag("safe")}>Safe</Button>
              <Button className={`${styles.riskBtn} ${styles.danger}`} onClick={() => handleTag("danger")}>Danger</Button>
              <Button className={`${styles.riskBtn} ${styles.escalate}`} onClick={() => handleTag("escalate")}>Escalate</Button>
            </div>

            <div className={styles.sectionHeader}>Category</div>
            <div className={styles.categoryGrid}>
              <button className={`${styles.catCard} ${styles.oil}`} onClick={() => handleTag("oil")}>Oil</button>
              <button className={`${styles.catCard} ${styles.elec}`} onClick={() => handleTag("electricity")}>Electric</button>
              <button className={`${styles.catCard} ${styles.gas}`} onClick={() => handleTag("gas")}>Gas</button>
              <button className={`${styles.catCard} ${styles.other}`} onClick={() => handleTag("unrelated")}>Other</button>
            </div>

            <div className={styles.navActions}>
              <Button variant="outline" onClick={() => navigate("/home")}>Back</Button>
              <Button variant="primary" onClick={submitAndHome}>Submit & Home</Button>
              <Button variant="primary" onClick={submitAndNext}>Submit & Next</Button>
            </div>
          </div>
          
        </div>
      </div>
    </div>
  );
}