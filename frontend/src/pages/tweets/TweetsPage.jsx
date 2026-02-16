import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import Tweet from "../../components/Tweet/Tweet.jsx";
import Header from "../../components/Header/Header.jsx";
import Button from "../../components/Button/Button.jsx"; 
import ErrorModal from "../../components/ErrorModal/ErrorModal.jsx";
import styles from "./TweetsPage.module.css";

// Define the message constant to ensure strict comparison
const TIMEOUT_MSG = "You ran out of time to tag this one. Go back home or press X to tag a new one.";

export default function TweetsPage() {
  const navigate = useNavigate();
  const [errorMsg, setErrorMsg] = useState(null);
  const [tweetid, setTweetid] = useState(null);
  const [tweet, setTweet] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  
  // Local state for tagging
  const [isDangerous, setIsDangerous] = useState(null);
  const [category, setCategory] = useState(null);

  // New state to anchor the 10-minute timer to the browser's "now" upon receipt
  const [receivedAt, setReceivedAt] = useState(null);

  const serverUrl = import.meta.env.VITE_SERVER_URL || "http://127.0.0.1:8000";

  const fetchSingleTweet = async () => {
    setLoading(true);
    setError("");
    setErrorMsg(null); 
    const token = localStorage.getItem("token");
    if (!token) { navigate("/login"); return; }

    try {
      const res = await fetch(`${serverUrl}/claim_tweet`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data?.detail || "Failed to fetch tweet");
      
      setTweet(data);
      setTweetid(data._id); 
      setReceivedAt(Date.now()); // Capture the exact moment the data arrived
      setIsDangerous(null);
      setCategory(null);
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

  // Timer logic using the local anchor to prevent "Immediate Timeout" caused by clock skew
  useEffect(() => {
    if (!receivedAt || errorMsg) return;

    const timerInterval = setInterval(() => {
      const currentTime = Date.now();
      const elapsedSeconds = (currentTime - receivedAt) / 1000;

      if (elapsedSeconds > 600) { 
        setErrorMsg(TIMEOUT_MSG);
        clearInterval(timerInterval);
      }
    }, 2000);

    return () => clearInterval(timerInterval);
  }, [receivedAt, errorMsg]);

  // Logic to handle "X" button behavior based on the type of error
  const handleCloseModal = () => {
    if (errorMsg === TIMEOUT_MSG) {
      fetchSingleTweet(); // Fetch new tweet if timed out
    } else {
      setErrorMsg(null); // Just close for validation errors (like "Tag the tweet first")
    }
  };

  const setDanger = (bool) => {
    setIsDangerous(prev => (prev === bool ? null : bool));
  };

  const handleCategory = (cat) => {
    setCategory(prev => (prev === cat ? null : cat));
  };

  const submit = async () => {
    if (isDangerous === null || !category) {
      setErrorMsg("Tag the tweet first");
      return false;
    }
    
    if (isDangerous === true && category === "Unrelated") {
      setErrorMsg("A tweet can't be tagged as dangerous and Unrelated at the same time");
      return false;
    }

    const payload = {
      tweet_id: tweetid,
      locked_at: tweet.locked_at, // Send original server timestamp back for DB verification
      category: category,
      is_dangerous: isDangerous,
    };

    try {
      const response = await fetch(`${serverUrl}/submit_tagged_tweet`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${localStorage.getItem("token")}`
        },
        body: JSON.stringify(payload)
      });

      if (!response.ok) {
        const errorData = await response.json();
        setErrorMsg(errorData.detail || "Request failed");
        return false;
      }
      return true;
    } catch (err) {
      setErrorMsg(err.message);
      return false;
    }
  };

  const submitAndHome = async () => {
    if (await submit()) navigate("/home");
  };

  const submitAndNext = async () => {
    if (await submit()) fetchSingleTweet();
  };

  const escalate = async () => {
    if (!tweet || !tweetid) return;
    try {
      const response = await fetch(`${serverUrl}/escalate_tweet`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${localStorage.getItem("token")}`
        },
        body: JSON.stringify({ tweet_id: tweetid, locked_at: tweet.locked_at })
      });
      if (response.ok) {
        fetchSingleTweet();
      } else {
        const data = await response.json();
        setErrorMsg(data.detail || "Escalation failed");
      }
    } catch (err) {
      setErrorMsg(err.message);
    }
  };

  if (loading) return <div className={styles.center}>Loading...</div>;

  return (
    <div className={styles.page}>
      <Header />
      {/* Use the new handleCloseModal function here */}
      {errorMsg && <ErrorModal message={errorMsg} onClose={handleCloseModal} />}

      <div className={styles.mainWrapper}>
        <div className={styles.container}>
          <div className={styles.scrollableContent}>
            {error ? <div className={styles.error}>{error}</div> : tweet ? <Tweet tweet={tweet} /> : <p>No tweet</p>}
          </div>

          <div className={styles.controls}>
            <div className={styles.sectionHeader}>Risk Assessment</div>
            <div className={styles.riskActions}>
              <Button 
                className={`${styles.riskBtn} ${isDangerous === false ? styles.active : styles.safe}`} 
                onClick={() => setDanger(false)}
              >Safe</Button>
              <Button 
                className={`${styles.riskBtn} ${isDangerous === true ? styles.active : styles.danger}`} 
                onClick={() => setDanger(true)}
              >Danger</Button>
              <Button className={`${styles.riskBtn} ${styles.escalate}`} onClick={escalate}>Escalate</Button>
            </div>

            <div className={styles.sectionHeader}>Category</div>
            <div className={styles.categoryGrid}>
              {["Oil", "Electricity", "Gas", "Unrelated"].map((cat) => (
                <button 
                  key={cat}
                  className={`${styles.catCard} ${category === cat ? styles.active : ""}`} 
                  onClick={() => handleCategory(cat)}
                >
                  {cat === "Electricity" ? "Electric" : cat === "Unrelated" ? "Other" : cat}
                </button>
              ))}
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