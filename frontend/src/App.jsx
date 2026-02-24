import React from "react";
import { BrowserRouter as Router, Routes, Route, Navigate } from "react-router-dom";
import EscalatedTweetsPage from "./pages/EscalatedTweetsPage/EscalatedTweetsPage";
import Login from "./pages/login/login";
import Register from "./pages/register/register";
import Home from "./pages/home/Home";
import TweetsPage from "./pages/tweets/TweetsPage";
import TaggedTweetsPage from "./pages/TaggedTweetsPage/TaggedTweetsPage"; 
import EscalationTagPage from "./pages/EscalationTagPage/EscalationTagPage";
import TaggingLeaderboardPage from "./pages/TaggingLeaderboardPage/TaggingLeaderboardPage"
import MyTaggedTweetsPage from "./pages/MyTaggedTweetsPage/MyTaggedTweetsPage"
import EditTweetPage from "./pages/EditTweetPage/EditTweetPage";

import "./index.css";

function App() {
  return (
    <Router>
      <div className="app-wraper">
        <Routes>
          <Route path="/" element={<Navigate to="/login" />} />

          <Route path="/login" element={<Login />} />
          <Route path="/Register" element={<Register />} />

          {/* עמוד הבית אחרי לוגין */}
          <Route path="/home" element={<Home />} />

          {/* משיכת ציוץ רנדומלי */}
          <Route path="/tweets" element={<TweetsPage />} />

          {/* ← העמוד של ה-DB (ציוצים מתוייגים) */}
          <Route path="/tagged-tweets" element={<TaggedTweetsPage />} />

          {/* fallback */}
          <Route path="*" element={<Navigate to="/login" />} />
          <Route path="/escalation" element={<EscalatedTweetsPage />} />
          <Route path="/escalation-tag" element={<EscalationTagPage />} />
           <Route path="/table" element={<TaggingLeaderboardPage />} />
            <Route path="/tags" element={<MyTaggedTweetsPage/>} />
            <Route path="/edit-tweet" element={<EditTweetPage />} />
            
    
        </Routes>
      </div>
    </Router>
  );
}

export default App;