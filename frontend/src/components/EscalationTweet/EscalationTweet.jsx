function EscalationTweet({ tweet }) {
  if (!tweet) return null;

  return (
    <div className={styles.tweetCard}>
      <pre className={styles.tweetText}>
        {JSON.stringify(tweet, null, 2)}
      </pre>
    </div>
  );
}