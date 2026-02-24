import React, { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import Header from "../../components/Header/Header.jsx";
import TaggedTweetCard from "../../components/TaggedTweetCard/TaggedTweetCard.jsx";
import styles from "./TaggedTweetsPage.module.css";

function isTaggedTweet(t) {
  if (!t) return false;

  // לפי הסכמה שלך
  if (t.status === "tagged") return true;
  if (t.tagged_by) return true;

  // fallback אם status לא תמיד מתעדכן
  if (t.is_dangerous === true || t.is_dangerous === false) return true;
  if (t.category) return true;

  return false;
}

export default function TaggedTweetsPage() {
  const navigate = useNavigate();

  // API returns list of tuples: [TweetinDB, username]
  const [rawItems, setRawItems] = useState([]);
  const [page, setPage] = useState(1);

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const serverUrl = import.meta.env.VITE_SERVER_URL || "http://127.0.0.1:8000";

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
          localStorage.removeItem("username");
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
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [page]);

  // Convert tuples -> tweet + inject tagged_by_username
  const taggedTweets = useMemo(() => {
    const tweets = rawItems
      .map((pair) => {
        if (Array.isArray(pair)) {
          const tweet = pair[0];
          const username = pair[1];
          return { ...tweet, tagged_by_username: username };
        }
        return pair;
      })
      .filter(isTaggedTweet);

    return tweets;
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
            {taggedTweets.map((tweet, idx) => (
              <div key={tweet?._id || tweet?.id || idx} className={styles.item}>
                <TaggedTweetCard tweet={tweet} />
              </div>
            ))}
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