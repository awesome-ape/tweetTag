function EscalationTweet({ tweet }) {
  if (!tweet) return null;

  return (
    <div className={styles.tweetCard}>
      <pre className={styles.tweetText} dir="auto">
        {tweet?.content}
      </pre>
    </div>
  );
}