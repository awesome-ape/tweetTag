import React, { useEffect, useState, useCallback, useRef } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import Header from "../../components/Header/Header.jsx";
import Button from "../../components/Button/Button.jsx";
import ErrorModal from "../../components/ErrorModal/ErrorModal.jsx";
import styles from "./UserEditTweetPage.module.css";
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

export default function UserEditTweetPage() {
  const navigate = useNavigate();
  const location = useLocation();

  const passedTweet = location.state?.tweet || null;

  const [errorMsg, setErrorMsg] = useState(null);
  const [tweet, setTweet] = useState(null);
  const [loading, setLoading] = useState(true);

  const [isDangerous, setIsDangerous] = useState(null);
  const [category, setCategory] = useState(null);

  const tweetRef = useRef(null);

  const serverUrl =
    import.meta.env.VITE_SERVER_URL ||
    "https://em5epzymak.eu-west-3.awsapprunner.com";

  const returnToUserTaggedTweets = () => {
    navigate("/user-tagged-tweets");
  };

  const releaseLock = useCallback(
    async (tweetData) => {
      if (!tweetData || !tweetData.locked_at) return;

      const token = localStorage.getItem("token");
      const id = tweetData._id || tweetData.id;

      try {
        await fetch(`${serverUrl}/release_processed_tweet_lock`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`,
          },
          body: JSON.stringify({
            tweet_id: id,
            locked_at: tweetData.locked_at,
          }),
        });
      } catch (e) {
        console.warn("Release lock failed:", e);
      }
    },
    [serverUrl]
  );

  const claimForEdit = useCallback(
    async (id) => {
      setLoading(true);

      const token = localStorage.getItem("token");
      if (!token) {
        navigate("/login");
        return;
      }

      try {
        const res = await fetch(
          `${serverUrl}/get_processed_tweet?tweet_id=${id}`,
          {
            headers: {
              Authorization: `Bearer ${token}`,
            },
          }
        );

        const data = await res.json();

        if (!res.ok) {
          throw new Error(data?.detail || "Failed to claim tweet");
        }

        setTweet(data);
        tweetRef.current = data;
        setIsDangerous(data.is_dangerous);
        setCategory(data.category);
      } catch (err) {
        setErrorMsg(err.message);
      } finally {
        setLoading(false);
      }
    },
    [navigate, serverUrl]
  );

  useEffect(() => {
    const id = passedTweet?._id || passedTweet?.id;

    if (!id) {
      navigate("/user-tagged-tweets");
      return;
    }

    claimForEdit(id);
  }, [passedTweet, claimForEdit, navigate]);

  useEffect(() => {
    return () => {
      if (tweetRef.current) {
        releaseLock(tweetRef.current);
      }
    };
  }, [releaseLock]);

  const handleBack = async () => {
    if (tweet) {
      const dataToRelease = { ...tweet };

      tweetRef.current = null;
      setTweet(null);

      await releaseLock(dataToRelease);
    }

    navigate("/user-tagged-tweets");
  };

  const submitEdit = async () => {
    if (!tweet) return;

    try {
      const response = await fetch(`${serverUrl}/submit_edited_tweet`, {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${localStorage.getItem("token")}`,
        },
        body: JSON.stringify({
          tweet_id: tweet._id || tweet.id,
          locked_at: tweet.locked_at,
          category,
          is_dangerous: isDangerous,
        }),
      });

      const data = await response.json().catch(() => null);

      if (!response.ok) {
        throw new Error(data?.detail || "Update failed");
      }

      tweetRef.current = null;
      setTweet(null);

      navigate("/user-tagged-tweets");
    } catch (err) {
      setErrorMsg(err.message);
    }
  };

  if (loading) {
    return <div className={styles.center}>Loading Lock...</div>;
  }

  const tweetText = toText(tweet?.content);

  return (
    <div className={styles.page}>
      <Header />

      {errorMsg && (
        <ErrorModal
          message={errorMsg}
          onClose={() => {
            setErrorMsg(null);
            returnToUserTaggedTweets();
          }}
        />
      )}

      <div className={styles.mainWrapper}>
        <div className={styles.container}>
          <div className={styles.scrollableContent}>
            <div className={styles.tweetCard}>
              <div className={styles.tweetDate}>
                {tweet?.created_at
                  ? new Date(tweet.created_at).toLocaleString()
                  : ""}
              </div>

              <div className={styles.tweetScroll}>
                <div className={styles.tweetText}>{tweetText}</div>
              </div>
            </div>
          </div>

          <div className={styles.controls}>
            <div className={styles.sectionHeader}>Risk Assessment</div>

            <div className={styles.riskActions}>
              <button
                type="button"
                className={`${styles.riskBtn} ${styles.safe} ${
                  isDangerous === false ? styles.riskActive : ""
                }`}
                onClick={() => setIsDangerous(false)}
              >
                Safe
              </button>

              <button
                type="button"
                className={`${styles.riskBtn} ${styles.danger} ${
                  isDangerous === true ? styles.riskActive : ""
                }`}
                onClick={() => setIsDangerous(true)}
              >
                Danger
              </button>
            </div>

            <div className={styles.sectionHeader}>Category</div>

            <div className={styles.categoryGrid}>
              {["Oil", "Electricity", "Gas", "Unrelated"].map((cat) => (
                <button
                  key={cat}
                  type="button"
                  className={`${styles.catCard} ${
                    category === cat ? styles.active : ""
                  }`}
                  onClick={() => setCategory(cat)}
                >
                  {cat === "Electricity"
                    ? "Electric"
                    : cat === "Unrelated"
                    ? "Other"
                    : cat}
                </button>
              ))}
            </div>

            <div className={styles.navActions}>
              <Button variant="outline" onClick={handleBack}>
                Cancel
              </Button>

              <Button variant="primary" onClick={submitEdit}>
                Save Changes
              </Button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}