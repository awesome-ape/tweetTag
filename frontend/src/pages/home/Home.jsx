import React from "react";
import { useNavigate } from "react-router-dom";
import Header from "../../components/Header/Header.jsx"; // Adjust this path if needed
import styles from "./Home.module.css";

export default function Home() {
  const navigate = useNavigate();
  const username = localStorage.getItem("username") || "User";

  return (
    <div className={styles.page}>
      {/* ====== HEADER COMPONENT ====== */}
      <Header />

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