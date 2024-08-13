import React, { useState, useRef, useEffect } from 'react';
import './App.css';
import axios from 'axios';
import ChatAvatar from './assets/prachi.png';  // Make sure this path is correct

function App() {
  const [query, setQuery] = useState('');
  const [messages, setMessages] = useState([]);
  const [showChat, setShowChat] = useState(true);  // Chat widget is open by default
  const [showVideo, setShowVideo] = useState(false);
  const [startTime, setStartTime] = useState(0);
  const [isMinimized, setIsMinimized] = useState(false);
  const videoRef = useRef(null);
  const videoPopupRef = useRef(null);  // Ref for video popup
  const chatPopupRef = useRef(null);  // Ref for chat popup

  const searchAndPlay = async (query) => {
    try {
      const response = await axios.post('http://localhost:5000/search', { query });
      const result = response.data;
      console.log('Result:', result);

      if (result.documents && result.documents.length > 0) {
        const startTime = parseFloat(result.start);
        console.log("start time =", startTime);

        if (!isNaN(startTime)) {
          setStartTime(startTime);
          setShowVideo(true);
        } else {
          console.error('Start time is not a valid number.');
        }
      } else {
        console.error('No documents found.');
      }
    } catch (error) {
      console.error(`Error searching for query "${query}":`, error);
    }
  };

  const sendMessage = () => {
    if (!query.trim()) {
      alert('Please enter a query.');
      return;
    }

    setMessages([...messages, { text: query, type: 'user' }]);
    searchAndPlay(query);
    setQuery('');
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter') {
      sendMessage();
    }
  };

  useEffect(() => {
    if (showVideo && videoRef.current) {
      const player = videoRef.current;
      player.currentTime = startTime;
      player.play().catch((error) => {
        console.error('Error playing video:', error);
      });
    }
  }, [showVideo, startTime]);

  const handleOutsideClick = (event) => {
    if (
      videoPopupRef.current &&
      !videoPopupRef.current.contains(event.target) &&
      chatPopupRef.current &&
      !chatPopupRef.current.contains(event.target)
    ) {
      setShowVideo(false);
    }
  };

  useEffect(() => {
    if (showVideo) {
      document.addEventListener('click', handleOutsideClick);
    } else {
      document.removeEventListener('click', handleOutsideClick);
    }
    return () => {
      document.removeEventListener('click', handleOutsideClick);
    };
  }, [showVideo]);

  return (
    <div className="App">
      {showChat && (
        <div className={`chat-popup ${isMinimized ? 'minimized' : ''}`} ref={chatPopupRef} onClick={() => setIsMinimized(false)}>
          {isMinimized ? (
            <>
              <img src={ChatAvatar} alt="Chat Avatar" />
              <div className="text-box">
                <div className="title">ASK PRACHI</div>
                <div className="subtitle">LIVE CHAT</div>
              </div>
            </>
          ) : (
            <>
              <div className="chat-header">
                <img src={ChatAvatar} alt="Prachi" />
                <div className="header-text">
                  <div className="title">Ask Prachi</div>
                  <div className="subtitle">To purchase new policy or service existing ones.</div>
                </div>
                <button onClick={(e) => { e.stopPropagation(); setIsMinimized(true); }} className="close-btn">
                  &minus;
                </button>
              </div>
              <div className="chat-body">
                {messages.map((msg, index) => (
                  <div key={index} className={`message ${msg.type}`}>
                    {msg.text}
                  </div>
                ))}
              </div>
              <div className="chat-footer">
                <input
                  type="text"
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  placeholder="Enter your query..."
                  onKeyPress={handleKeyPress}
                />
                <button onClick={sendMessage}>Send</button>
              </div>
            </>
          )}
        </div>
      )}

      {showVideo && (
        <div className="video-popup" ref={videoPopupRef}>
          <video id="my-video" ref={videoRef} controls preload="auto" width="640" height="360">
            <source src="trump_clip1.mp4" type="video/mp4" />
            Your browser does not support the video tag.
          </video>
        </div>
      )}
    </div>
  );
}

export default App;
