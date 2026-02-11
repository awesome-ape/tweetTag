import "./Tweet.css";

export default function Tweet({ tweet }) {
  const date = tweet?.created_at ? new Date(tweet.created_at).toLocaleString() : "";
  return (
    <div className="tweet-card">
      <div className="tweet-date">{date}</div>
      <div className="tweet-content">{tweet?.content}</div>
    </div>
  );
}
