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
    if (!token) {
      navigate("/login");
      return;
    }

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

  useEffect(() => {
    fetchSingleTweet();
  }, []);

  const handleTag = (type) => {
    console.log(`Tagged as: ${type}`);
  };

  if (loading) return <div className={styles.center}>Loading...</div>;

  return (
    <div className={styles.page}>
      <Header />
      
      <div className={styles.mainWrapper}>
        <div className={styles.container}>
          {error ? (
            <div className={styles.error}>Error: {error}</div>
          ) : tweet ? (
            <Tweet tweet={tweet} />
          ) : (
            <p>No tweet available</p>
          )}

          {/* RISK LEVEL SECTION */}
          <div className={styles.riskHeaderContainer}>
            <h3 className={styles.riskTitle}>Risk Level:</h3>
          </div>

          <div className={styles.riskActions}>
            <Button className={styles.safe} onClick={() => handleTag("safe")}>Safe</Button>
            <Button className={styles.danger} onClick={() => handleTag("danger")}>Danger</Button>
            <Button className={styles.escalate} onClick={() => handleTag("escalate")}>Escalate</Button>
          </div>

          {/* CATEGORY SECTION - NOW CIRCULAR BUTTONS */}
          <div className={styles.categoryHeaderContainer}>
            <h3 className={styles.categoryTitle}>Category:</h3>
          </div>

          <div className={styles.categoryActions}>
            <Button className={styles.oilCircle} onClick={() => handleTag("oil")}>Oil</Button>
            <Button className={styles.elecCircle} onClick={() => handleTag("electricity")}>Electricity</Button>
            <Button className={styles.gasCircle} onClick={() => handleTag("gas")}>Gas</Button>
            <Button className={styles.otherCircle} onClick={() => handleTag("unrelated")}>Other</Button>
          </div>

          <div className={styles.navActions}>
            <Button variant="outline" onClick={() => navigate("/home")}>Back to home</Button>
             <Button variant="primary" onClick={submitAndHome}>Submit & Back to Home</Button>
             <Button variant="primary" onClick={submitAndNext}>Submit & Pull next tweet</Button>
          </div>
        </div>
      </div>
    </div>
  );
}


function submitAndHome(){

}

function submitAndNext(){}