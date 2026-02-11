import React, { useEffect, useState } from "react";
import "./TweetsPage.css";

export default function TweetsPage() {
  const [tweet, setTweet] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  const serverUrl = import.meta.env.VITE_SERVER_URL || "http://127.0.0.1:8000";

  const fetchSingleTweet = async () => {
    setLoading(true);
    setError("");

    const token = localStorage.getItem("token");
    if (!token) {
      setError("Missing token. Please login again.");
      setLoading(false);
      return;
    }

    try {
      const res = await fetch(`${serverUrl}/claim_tweet`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      const data = await res.json().catch(() => ({}));

      if (!res.ok) {
        throw new Error(data?.detail || "Failed to claim tweet");
      }

      // כאן זה כבר TweetinDB ישירות
      setTweet(data);
    } catch (err) {
      setError(err.message || "Request failed");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSingleTweet();
  }, []);

  if (loading) return <div className="center">Loading...</div>;
  if (error) return <div className="center error">{error}</div>;
  if (!tweet) return <div className="center">No tweet found</div>;

  return (
    <div className="tweets-page">
      <div className="tweet-card">
        <div className="tweet-date">
          {tweet.created_at ? new Date(tweet.created_at).toLocaleString() : ""}
        </div>

        <div className="tweet-content">{tweet.content}</div>

        {/* בונוס קטן: למשוך עוד ציוץ */}
        <button className="btn btn-dark" onClick={fetchSingleTweet}>
          Pull another tweet
        </button>
      </div>
    </div>
  );
}
