import React from "react";
import { useNavigate } from "react-router-dom";
import "../home/Home.css";

export default function Home() {
  const navigate = useNavigate();

  const username = localStorage.getItem("username") || "User";

  const handleLogout = () => {
    localStorage.removeItem("token");
    localStorage.removeItem("username");
    navigate("/login");
  };

  return (
    <div className="home-page">
      
      {/* ====== NAVBAR ====== */}
      <div className="navbar">
        <div className="nav-left">
          TweetTag #
        </div>

        <div className="nav-right">
          <span className="username">👤 {username}</span>
          <button className="logout-btn" onClick={handleLogout}>
            Logout
          </button>
        </div>
      </div>

      {/* רקע */}
      <div className="home-bg"></div>

      <div className="home-container">
        <div className="card">
          <h2>TweetTag #</h2>
          <p className="welcome">hello {username}!</p>

          <button
            className="btn btn-dark"
            onClick={() => navigate("/tweets")}
          >
            pull random tweet
          </button>

          <button
            className="btn btn-mid"
            onClick={() => navigate("/my-tags")}
          >
            view my tags
          </button>

          <button
            className="btn btn-light"
            onClick={() => navigate("/database")}
          >
            view database
          </button>
        </div>
      </div>
    </div>
  );
}
