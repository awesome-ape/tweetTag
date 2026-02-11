import React from "react";
import { useNavigate } from "react-router-dom";
import "./Home.css";

export default function Home() {
  const navigate = useNavigate();

  return (
    <div className="home-page">
      {/* רקע הציפור */}
      <div className="home-bg"></div>

      <div className="home-container">
        <div className="card">
          <h2>TweetTag #</h2>
          <p className="welcome">hello Almog Salman!</p>

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
