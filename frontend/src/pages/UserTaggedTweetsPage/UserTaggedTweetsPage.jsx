import React, { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import Header from "../../components/Header/Header.jsx";
import TaggedTweetCard from "../../components/TaggedTweetCard/TaggedTweetCard.jsx";
import styles from "./UserTaggedTweetsPage.module.css";

export default function UserTaggedTweetsPage() {
  const navigate = useNavigate();

  const [tweets, setTweets] = useState([]);
  const [search, setSearch] = useState(() => {
    return sessionStorage.getItem("userTaggedTweetsSearch") || "";
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const serverUrl =
    import.meta.env.VITE_SERVER_URL ||
    "https://em5epzymak.eu-west-3.awsapprunner.com";

  useEffect(() => {
    sessionStorage.setItem("userTaggedTweetsSearch", search);
  }, [search]);

  useEffect(() => {
    async function fetchMyTaggedTweets() {
      setLoading(true);
      setError("");

      const token = localStorage.getItem("token");

      if (!token) {
        navigate("/login");
        return;
      }

      try {
        const res = await fetch(`${serverUrl}/my_tagged_tweets?limit=500`, {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        });

        const data = await res.json();

        if (!res.ok) {
          setError(data?.detail || "Failed to fetch your tagged tweets");

          if (res.status === 401) {
            localStorage.removeItem("token");
            navigate("/login");
          }

          return;
        }

        setTweets(Array.isArray(data) ? data : []);
      } catch (err) {
        setError("Network error while fetching tweets");
      } finally {
        setLoading(false);
      }
    }

    fetchMyTaggedTweets();
  }, [navigate, serverUrl]);

  const filteredTweets = useMemo(() => {
    const q = search.trim().toLowerCase();

    if (!q) return tweets;

    return tweets.filter((tweet) => {
      const content = String(tweet.content || "").toLowerCase();
      const category = String(tweet.category || "").toLowerCase();
      const dangerousText =
        tweet.is_dangerous === true
          ? "danger dangerous"
          : tweet.is_dangerous === false
          ? "safe"
          : "";

      return (
        content.includes(q) ||
        category.includes(q) ||
        dangerousText.includes(q)
      );
    });
  }, [tweets, search]);

  const handleEditClick = (tweet) => {
    if (tweet.status === "tagging") {
      alert("This tweet is currently being edited.");
      return;
    }

    navigate("/user-edit-tweet", {
      state: {
        tweet,
      },
    });
  };

  return (
    <div className={styles.page}>
      <Header />
      <div className={styles.bg} />

      <main className={styles.container}>
        <div className={styles.headerRow}>
          <div>
            <h2 className={styles.title}>My Tagged Tweets</h2>
            <p className={styles.subtitle}>
              Search tweets you tagged and choose one to edit
            </p>
          </div>

         <button
  type="button"
  className={`${styles.btn} ${styles.btnMid}`}
  onClick={() => {
    sessionStorage.removeItem("userTaggedTweetsSearch");

    const isAdmin = localStorage.getItem("isADMIN") === "true";
    navigate(isAdmin ? "/home" : "/home-user");
  }}
>
  Back
</button>
        </div>

        <div className={styles.searchBox}>
          <input
            className={styles.searchInput}
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search by word, category, safe, danger..."
          />

          <div className={styles.resultCount}>
            {filteredTweets.length} / {tweets.length}
          </div>
        </div>

        {error && <div className={styles.errorBox}>{error}</div>}

        {loading ? (
          <div className={styles.infoBox}>Loading...</div>
        ) : filteredTweets.length === 0 ? (
          <div className={styles.infoBox}>No tweets found.</div>
        ) : (
          <div className={styles.list}>
            {filteredTweets.map((tweet, idx) => {
              const isLocked = tweet.status === "tagging";

              return (
                <div
                  key={tweet?._id || tweet?.id || idx}
                  className={`${styles.item} ${
                    isLocked ? styles.lockedItem : ""
                  }`}
                  onClick={() => handleEditClick(tweet)}
                >
                  <TaggedTweetCard tweet={tweet} />

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
      </main>
    </div>
  );
}