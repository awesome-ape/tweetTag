import React from "react";
import { useNavigate } from "react-router-dom";
import Header from "../../components/Header/Header.jsx";
import styles from "./HomeUser.module.css";

export default function HomeUser() {
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
        <div className={styles.card}>

          {/* Gradient banner */}
          <div className={styles.banner}>
            <p className={styles.bannerGreeting}>Welcome back</p>
            <h2 className={styles.bannerName}>{username}</h2>
          </div>

          {/* Action grid */}
          <div className={styles.grid}>
            <button
              className={`${styles.actionCard} ${styles.actionPrimary}`}
              onClick={() => navigate("/tweets")}
            >
              <span className={styles.actionIcon}>⚡</span>
              <span className={styles.actionLabel}>Pull Random Tweet</span>
            </button>

            <button className={styles.actionCard} onClick={() => navigate("/tags")}>
              <span className={styles.actionIcon}>🏷️</span>
              <span className={styles.actionLabel}>My Tags</span>
            </button>

            <button className={styles.actionCard} onClick={() => navigate("/user-tagged-tweets")}>
              <span className={styles.actionIcon}>✏️</span>
              <span className={styles.actionLabel}>Edit Tags</span>
            </button>

            <button className={styles.actionCard} onClick={() => navigate("/my-impact")}>
              <span className={styles.actionIcon}>📈</span>
              <span className={styles.actionLabel}>My Impact</span>
            </button>
          </div>

        </div>
      </div>
    </div>
  );
}
