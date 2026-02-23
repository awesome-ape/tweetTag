import React, { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import Header from "../../components/Header/Header.jsx";
import TaggedTweetCard from "../../components/TaggedTweetCard/TaggedTweetCard.jsx";
// Import styles
import styles from "./TaggedTweetsPage.module.css";

function isTaggedTweet(t) {
  if (!t) return false;
  if (t.status === "tagged") return true;
  if (t.tagged_by) return true;
  if (t.is_dangerous === true || t.is_dangerous === false) return true;
  if (t.category) return true;
  return false;
}

export default function TaggedTweetsPage() {
  const navigate = useNavigate();

  const [rawItems, setRawItems] = useState([]);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const serverUrl = import.meta.env.VITE_SERVER_URL || "http://127.0.0.1:8000";

  // ✅ REDIRECT LOGIC
  const handleEditClick = (tweet) => {
    // If the tweet is already being tagged by someone else, don't redirect
    if (tweet.status === "tagging") {
       alert("This tweet is currently being edited by another admin.");
       return;
    }
    // Pass the tweet object to the editor page via state
    navigate("/edit-tweet", { state: { tweet } });
  };

  const fetchPage = async (pageNum) => {
    setLoading(true);
    setError("");

    const token = localStorage.getItem("token");
    if (!token) {
      navigate("/login");
      return;
    }

    try {
      const res = await fetch(
        `${serverUrl}/get_tweets_for_display?page=${pageNum}`,
        { headers: { Authorization: `Bearer ${token}` } }
      );

      const data = await res.json();

      if (!res.ok) {
        const msg = data?.detail || "Failed to fetch tweets";
        setError(msg);
        if (res.status === 401) {
          localStorage.removeItem("token");
          navigate("/login");
        }
        return;
      }

      setRawItems(Array.isArray(data) ? data : []);
    } catch (e) {
      setError("Network error while fetching tweets");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPage(page);
  }, [page]);

  const taggedTweets = useMemo(() => {
    return rawItems
      .map((pair) => {
        if (Array.isArray(pair)) {
          const tweet = pair[0];
          const username = pair[1];
          return { ...tweet, tagged_by_username: username };
        }
        return pair;
      })
      .filter(isTaggedTweet);
  }, [rawItems]);

  return (
    <div className={styles.page}>
      <Header />
      <div className={styles.bg} />

      <div className={styles.container}>
        <div className={styles.headerRow}>
          <h2 className={styles.title}>Tagged Tweets</h2>
          <div className={styles.actions}>
            <button
              className={`${styles.btn} ${styles.btnMid}`}
              onClick={() => navigate("/home")}
            >
              back
            </button>
          </div>
        </div>

        {error && <div className={styles.errorBox}>{error}</div>}

        {loading ? (
          <div className={styles.infoBox}>Loading...</div>
        ) : taggedTweets.length === 0 ? (
          <div className={styles.infoBox}>No tagged tweets found.</div>
        ) : (
          <div className={styles.list}>
            {taggedTweets.map((tweet, idx) => {
              const isLocked = tweet.status === "tagging";
              
              return (
                <div 
                  key={tweet?._id || tweet?.id || idx} 
                  className={`${styles.item} ${isLocked ? styles.lockedItem : ""}`}
                  onClick={() => handleEditClick(tweet)}
                  style={{ 
                    cursor: isLocked ? "not-allowed" : "pointer",
                    position: "relative" 
                  }}
                >
                  <TaggedTweetCard tweet={tweet} />
                  
                  {/* Visual indicator if locked */}
                  {isLocked && (
                    <div className={styles.lockOverlay}>
                      <span>🔒 Being Edited</span>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}

        <div className={styles.pagination}>
          <button
            className={`${styles.btn} ${styles.btnLight}`}
            onClick={() => setPage((p) => Math.max(1, p - 1))}
            disabled={page === 1 || loading}
          >
            prev
          </button>
          <span className={styles.pageLabel}>page {page}</span>
          <button
            className={`${styles.btn} ${styles.btnLight}`}
            onClick={() => setPage((p) => p + 1)}
            disabled={loading || rawItems.length === 0}
          >
            next
          </button>
        </div>
      </div>
    </div>
  );
}