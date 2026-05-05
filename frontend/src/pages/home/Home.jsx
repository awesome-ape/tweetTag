import React from "react";
import { useNavigate } from "react-router-dom";
import Header from "../../components/Header/Header.jsx";
import styles from "./Home.module.css";

export default function Home() {
  const navigate = useNavigate();
  const token = localStorage.getItem("token");
  const username = localStorage.getItem("username") || "User";

  React.useEffect(() => {
    if (!token) navigate("/login");
  }, [token, navigate]);

  return (
    <div className={styles.page}>
      <Header />
      <div className={styles.bg} />

      <div className={styles.container}>

        {/* ── Hero ── */}
        <div className={styles.hero}>
          <div className={styles.heroText}>
            <h1 className={styles.heroTitle}>TweetTag #</h1>
            <p className={styles.heroSub}>
              Welcome back, <span className={styles.heroName}>{username}</span>
            </p>
          </div>
          <button className={styles.heroCta} onClick={() => navigate("/tweets")}>
            ⚡ Pull Random Tweet
          </button>
        </div>

        {/* ── My Work ── */}
        <section className={styles.section}>
          <h2 className={styles.sectionLabel}>My Work</h2>
          <div className={styles.grid4}>
            <button className={`${styles.card} ${styles.cardBlue}`} onClick={() => navigate("/tags")}>
              <span className={styles.cardIcon}>🏷️</span>
              <span className={styles.cardLabel}>My Tags</span>
              <span className={styles.cardDesc}>View your tagged tweets</span>
            </button>

            <button className={styles.card} onClick={() => navigate("/user-tagged-tweets")}>
              <span className={styles.cardIcon}>✏️</span>
              <span className={styles.cardLabel}>Edit Tags</span>
              <span className={styles.cardDesc}>Update your decisions</span>
            </button>

            <button className={`${styles.card} ${styles.cardAmber}`} onClick={() => navigate("/escalation")}>
              <span className={styles.cardIcon}>⚠️</span>
              <span className={styles.cardLabel}>Escalations</span>
              <span className={styles.cardDesc}>Tag flagged tweets</span>
            </button>

            <button className={styles.card} onClick={() => navigate("/my-impact")}>
              <span className={styles.cardIcon}>📈</span>
              <span className={styles.cardLabel}>My Impact</span>
              <span className={styles.cardDesc}>Your tagging stats</span>
            </button>
          </div>
        </section>

        {/* ── Analytics ── */}
        <section className={styles.section}>
          <h2 className={styles.sectionLabel}>Analytics</h2>
          <div className={styles.grid5}>
            <button className={styles.card} onClick={() => navigate("/table")}>
              <span className={styles.cardIcon}>🏆</span>
              <span className={styles.cardLabel}>Rankings</span>
              <span className={styles.cardDesc}>User leaderboard</span>
            </button>

            <button className={styles.card} onClick={() => navigate("/admin-daily-stats")}>
              <span className={styles.cardIcon}>📊</span>
              <span className={styles.cardLabel}>Daily Stats</span>
              <span className={styles.cardDesc}>Day-by-day activity</span>
            </button>

            <button className={styles.card} onClick={() => navigate("/admin-tagging-distribution")}>
              <span className={styles.cardIcon}>🗂️</span>
              <span className={styles.cardLabel}>Distribution</span>
              <span className={styles.cardDesc}>Category breakdown</span>
            </button>

            <button className={styles.card} onClick={() => navigate("/admin-user-insights")}>
              <span className={styles.cardIcon}>👥</span>
              <span className={styles.cardLabel}>User Insights</span>
              <span className={styles.cardDesc}>Per-user analytics</span>
            </button>

            <button className={styles.card} onClick={() => navigate("/tagged-tweets")}>
              <span className={styles.cardIcon}>🗄️</span>
              <span className={styles.cardLabel}>Database</span>
              <span className={styles.cardDesc}>All tagged tweets</span>
            </button>
          </div>
        </section>

      </div>
    </div>
  );
}
