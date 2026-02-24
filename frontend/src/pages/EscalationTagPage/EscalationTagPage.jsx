import React, { useEffect, useState, useCallback } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import Header from "../../components/Header/Header.jsx";
import Button from "../../components/Button/Button.jsx";
import ErrorModal from "../../components/ErrorModal/ErrorModal.jsx";
import styles from "./EscalationTagPage.module.css";

const TIMEOUT_MSG =
  "You ran out of time to tag this one. Go back or press X to claim again.";

function toText(content) {
  if (content === null || content === undefined) return "";
  if (typeof content === "string") return content;

  if (typeof content === "object") {
    const maybe =
      content.full_text || content.text || content.content || content.message;
    return maybe ? String(maybe) : JSON.stringify(content, null, 2);
  }

  return String(content);
}

function EscalationTweet({ tweet }) {
  const date = tweet?.created_at ? new Date(tweet.created_at).toLocaleString() : "";
  const raw = tweet?.content;
  const text = toText(raw);

  return (
    <div className={styles.tweetCard}>
      <div className={styles.tweetDate}>{date}</div>
      <div className={styles.tweetScroll}>
        {typeof raw === "object" ? (
          <pre className={styles.tweetText}>{text}</pre>
        ) : (
          <div className={styles.tweetText}>{text}</div>
        )}
      </div>
    </div>
  );
}

export default function EscalationTagPage() {
  const navigate = useNavigate();
  const location = useLocation();

  const passedTweet = location.state?.tweet || null;

  const [errorMsg, setErrorMsg] = useState(null);
  const [tweetId, setTweetId] = useState(null);
  const [tweet, setTweet] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  const [isDangerous, setIsDangerous] = useState(null);
  const [category, setCategory] = useState(null);

  const [receivedAt, setReceivedAt] = useState(null);

  const serverUrl = import.meta.env.VITE_SERVER_URL || "http://127.0.0.1:8000";

  const releaseEscalationLock = useCallback(
    async (id) => {
      if (!id) return;
      try {
        await fetch(`${serverUrl}/release_escalated_tweet_lock`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${localStorage.getItem("token")}`,
          },
          body: JSON.stringify({ tweet_id: id }),
        });
      } catch (e) {
        console.warn("releaseEscalationLock failed:", e);
      }
    },
    [serverUrl]
  );

  const claimEscalated = useCallback(
    async (id) => {
      setLoading(true);
      setError("");
      setErrorMsg(null);

      const token = localStorage.getItem("token");
      if (!token) {
        navigate("/login");
        return;
      }

      // ✅ אם היה ציוץ קודם נעול אצלך (באותו עמוד), תשחררי לפני claim חדש
      if (tweetId && tweetId !== id) {
        await releaseEscalationLock(tweetId);
      }

      try {
        const res = await fetch(
          `${serverUrl}/claim_escalated_tweet?tweet_id=${encodeURIComponent(id)}`,
          {
            headers: { Authorization: `Bearer ${token}` },
          }
        );

        const data = await res.json().catch(() => ({}));
        if (!res.ok) throw new Error(data?.detail || "Failed to claim tweet");

        setTweet(data);
        setTweetId(data._id || data.id);

        setIsDangerous(null);
        setCategory(null);

        setReceivedAt(Date.now());
      } catch (err) {
        setError(err?.message || "Unknown error");
        setTweet(null);
        setTweetId(null);
        setReceivedAt(null);
      } finally {
        setLoading(false);
      }
    },
    [navigate, serverUrl, tweetId, releaseEscalationLock]
  );

  useEffect(() => {
    const id = passedTweet?._id || passedTweet?.id;
    if (!id) {
      navigate("/escalation");
      return;
    }
    claimEscalated(id);
  }, [passedTweet, claimEscalated, navigate]);

  // ✅ release lock on unmount (עוזר כשעוברים route / סוגרים tab)
  useEffect(() => {
    return () => {
      if (tweetId) releaseEscalationLock(tweetId);
    };
  }, [tweetId, releaseEscalationLock]);

  // Timer logic (10 minutes)
  useEffect(() => {
    if (!receivedAt || errorMsg || !tweetId) return;

    const timerInterval = setInterval(async () => {
      const elapsedSeconds = (Date.now() - receivedAt) / 1000;
      if (elapsedSeconds > 600) {
        setReceivedAt(null);

        // ✅ חשוב: לשחרר נעילה כשהזמן נגמר
        await releaseEscalationLock(tweetId);

        setErrorMsg(TIMEOUT_MSG);
        clearInterval(timerInterval);
      }
    }, 2000);

    return () => clearInterval(timerInterval);
  }, [receivedAt, errorMsg, tweetId, releaseEscalationLock]);

  const handleCloseModal = async () => {
    if (errorMsg === TIMEOUT_MSG) {
      const id = passedTweet?._id || passedTweet?.id;
      if (id) claimEscalated(id);
      else navigate("/escalation");
    } else {
      setErrorMsg(null);
    }
  };

  const setDanger = (bool) =>
    setIsDangerous((prev) => (prev === bool ? null : bool));
  const handleCategory = (cat) =>
    setCategory((prev) => (prev === cat ? null : cat));

  const submit = async () => {
    if (!tweet || !tweetId) {
      setErrorMsg("No tweet loaded");
      return false;
    }

    if (isDangerous === null || !category) {
      setErrorMsg("Tag the tweet first");
      return false;
    }

    if (isDangerous === true && category === "Unrelated") {
      setErrorMsg("A tweet can't be tagged as dangerous and Unrelated at the same time");
      return false;
    }

    try {
      const response = await fetch(`${serverUrl}/submit_escalated_tagged_tweet`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${localStorage.getItem("token")}`,
        },
        body: JSON.stringify({
          tweet_id: tweetId,
          locked_at: tweet.locked_at,
          category,
          is_dangerous: isDangerous,
        }),
      });

      const data = await response.json().catch(() => ({}));

      if (!response.ok) {
        setErrorMsg(data?.detail || "Request failed");
        return false;
      }

      // אחרי submit, הציוץ כבר לא אצלך
      setTweet(null);
      setTweetId(null);
      setReceivedAt(null);

      return true;
    } catch (err) {
      setErrorMsg(err?.message || "Request failed");
      return false;
    }
  };

  const submitAndBack = async () => {
    if (await submit()) navigate("/escalation");
  };

  const submitAndHome = async () => {
    if (await submit()) navigate("/home");
  };

  const handleBack = async () => {
    // ✅ שחרור נעילה כשעושים Back בלי submit
    if (tweetId) await releaseEscalationLock(tweetId);
    navigate("/escalation");
  };

  if (loading) return <div className={styles.center}>Loading...</div>;

  return (
    <div className={styles.page}>
      <Header />
      {errorMsg && <ErrorModal message={errorMsg} onClose={handleCloseModal} />}

      <div className={styles.mainWrapper}>
        <div className={styles.container}>
          <div className={styles.scrollableContent}>
            {error ? (
              <div className={styles.error}>{error}</div>
            ) : tweet ? (
              <EscalationTweet tweet={tweet} />
            ) : (
              <p>No tweet</p>
            )}
          </div>

          <div className={styles.controls}>
            <div className={styles.sectionHeader}>Risk Assessment</div>
            <div className={styles.riskActions}>
              <Button
                className={`${styles.riskBtn} ${
                  isDangerous === false ? styles.active : styles.safe
                }`}
                onClick={() => setDanger(false)}
                disabled={!tweet}
              >
                Safe
              </Button>
              <Button
                className={`${styles.riskBtn} ${
                  isDangerous === true ? styles.active : styles.danger
                }`}
                onClick={() => setDanger(true)}
                disabled={!tweet}
              >
                Danger
              </Button>
            </div>

            <div className={styles.sectionHeader}>Category</div>
            <div className={styles.categoryGrid}>
              {["Oil", "Electricity", "Gas", "Unrelated"].map((cat) => (
                <button
                  key={cat}
                  className={`${styles.catCard} ${category === cat ? styles.active : ""}`}
                  onClick={() => handleCategory(cat)}
                  disabled={!tweet}
                  type="button"
                >
                  {cat === "Electricity" ? "Electric" : cat === "Unrelated" ? "Other" : cat}
                </button>
              ))}
            </div>

            <div className={styles.navActions}>
              <Button variant="outline" onClick={handleBack}>
                Back
              </Button>
              <Button variant="primary" onClick={submitAndHome} disabled={!tweet}>
                Submit & Home
              </Button>
              <Button variant="primary" onClick={submitAndBack} disabled={!tweet}>
                Submit & Back
              </Button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}