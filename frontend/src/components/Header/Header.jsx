import React from "react";
import { useNavigate } from "react-router-dom";
// 1. Change the import to a module import
import styles from "./Header.module.css"; 

export default function Header() {
  const navigate = useNavigate();
  const username = localStorage.getItem("username") || "User";

  const handleLogout = () => {
    localStorage.removeItem("token");
    localStorage.removeItem("username");
    navigate("/login");
  };

  return (
    /* 2. Use styles.className instead of a string */
    <header className={styles.mainHeader}>
      <div 
        className={styles.navLeft} 
        onClick={() => navigate("/")} 
        style={{cursor: 'pointer'}}
      >
        TweetTag #
      </div>

      <div className={styles.navRight}>
        <span className={styles.username}>👤 {username}</span>
        <button className={styles.logoutBtn} onClick={handleLogout}>
          Logout
        </button>
      </div>
    </header>
  );
}