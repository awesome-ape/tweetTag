import React from "react";
import { useNavigate } from "react-router-dom";
import styles from "./Home.module.css";

export default function Home() {
  const navigate = useNavigate();
  const username = localStorage.getItem("username") || "User";

  const handleLogout = () => {
    localStorage.removeItem("token");
    localStorage.removeItem("username");
    navigate("/login");
  };

  return (
    <div className={styles.page}>
      {/* ====== NAVBAR ====== */}
      <div className={styles.navbar}>
        <div className={styles.navLeft}>TweetTag #</div>

        <div className={styles.navRight}>
          <span className={styles.username}>👤 {username}</span>
          <button className={styles.logoutBtn} onClick={handleLogout}>
            Logout
          </button>
        </div>
      </div>

      {/* רקע */}
      <div className={styles.bg} />

      <div className={styles.container}>
        <div className={styles.card}>
          <h2 className={styles.title}>TweetTag #</h2>
          <p className={styles.welcome}>hello {username}!</p>

          <button
            className={`${styles.btn} ${styles.btnDark}`}
            onClick={() => navigate("/tweets")}
          >
            pull random tweet
          </button>

          <button
            className={`${styles.btn} ${styles.btnMid}`}
            onClick={() => navigate("/my-tags")}
          >
            view my tags
          </button>

          <button
            className={`${styles.btn} ${styles.btnLight}`}
            onClick={() => navigate("/database")}
          >
            view database
          </button>
        </div>
      </div>
    </div>
  );
}
