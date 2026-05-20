import { useState, useEffect } from 'react';
import api from './api';
import './App.css'; 

function App() {
  // --- Auth State ---
  const [currentUser, setCurrentUser] = useState(null); // null means not logged in
  const [loginEmail, setLoginEmail] = useState("");
  const [loginPassword, setLoginPassword] = useState("");

  // --- Dashboard State ---
  const [events, setEvents] = useState([]);
  const [categories, setCategories] = useState([]);
  const [recommendations, setRecommendations] = useState([]);
  const [message, setMessage] = useState("");
  
  const [newEvent, setNewEvent] = useState({
    title: "", description: "Join us for this amazing campus event!",
    date: "", venue: "", capacity: 50, category_id: 1
  });

  // Fetch data only after user logs in
  useEffect(() => {
    if (currentUser) {
      fetchEvents();
      fetchCategories();
      fetchRecommendations(currentUser.user_id);
    }
  }, [currentUser]);

  const handleLogin = async (e) => {
    e.preventDefault();
    try {
      const response = await api.post('/login/', {
        email: loginEmail,
        password: loginPassword
      });
      // Save user info (including ID and Role) from the token response
      setCurrentUser(response.data);
      setMessage("Logged in successfully!");
      setTimeout(() => setMessage(""), 3000);
    } catch (error) {
      alert("Invalid credentials. Try again.");
    }
  };

  const fetchEvents = async () => {
    const response = await api.get('/events/');
    setEvents(response.data);
  };

  const fetchCategories = async () => {
    const response = await api.get('/categories/');
    setCategories(response.data);
  };

  const fetchRecommendations = async (userId) => {
    try {
      const response = await api.get(`/recommendations/${userId}`);
      setRecommendations(response.data);
    } catch (error) {
      console.log("No recommendations available.");
    }
  };

  const handleRegister = async (eventId) => {
    try {
      const response = await api.post('/register/', {
        user_id: currentUser.user_id, // Use dynamic ID!
        event_id: eventId
      });
      setMessage(`Success! You are ${response.data.status}.`);
      setTimeout(() => setMessage(""), 3000);
      fetchRecommendations(currentUser.user_id); 
    } catch (error) {
      setMessage(error.response?.data?.detail || "Registration failed.");
      setTimeout(() => setMessage(""), 3000);
    }
  };

  const handleCreateEvent = async (e) => {
    e.preventDefault();
    try {
      await api.post(`/events/?organizer_id=${currentUser.user_id}`, newEvent);
      setMessage("Event created!");
      setTimeout(() => setMessage(""), 3000);
      fetchEvents();
      setNewEvent({ ...newEvent, title: "", date: "", venue: "" });
    } catch (error) {
      setMessage("Failed to create event.");
    }
  };

  // --- VIEW: LOGIN SCREEN ---
  if (!currentUser) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh', backgroundColor: '#f0f2f5' }}>
        <form onSubmit={handleLogin} style={{ padding: '2rem', backgroundColor: 'white', borderRadius: '8px', boxShadow: '0 4px 12px rgba(0,0,0,0.1)', width: '300px' }}>
          <h2 style={{ textAlign: 'center', marginBottom: '1.5rem' }}>Campus Portal</h2>
          <input type="email" placeholder="Email" required style={fullInputStyle} value={loginEmail} onChange={e => setLoginEmail(e.target.value)} />
          <input type="password" placeholder="Password" required style={fullInputStyle} value={loginPassword} onChange={e => setLoginPassword(e.target.value)} />
          <button type="submit" style={btnStyle}>Login</button>
        </form>
      </div>
    );
  }

  // --- VIEW: DASHBOARD (Only visible if logged in) ---
  return (
    <div style={{ padding: '2rem', fontFamily: 'system-ui, sans-serif' }}>
      <header style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '2px solid #eee', marginBottom: '2rem', paddingBottom: '1rem' }}>
        <div>
          <h1>Vardhaman Event Portal</h1>
          <p>Logged in as User ID: {currentUser.user_id} | Role: {currentUser.role}</p>
        </div>
        <button onClick={() => setCurrentUser(null)} style={{ ...btnStyle, width: '100px', backgroundColor: '#dc3545' }}>Logout</button>
      </header>

      {message && <div style={alertStyle}>{message}</div>}

      {/* Organizer Panel - Only show if role is organizer or admin */}
      {(currentUser.role === 'organizer' || currentUser.role === 'admin') && (
        <section style={{ marginBottom: '3rem', padding: '1.5rem', backgroundColor: '#f8f9fa', borderRadius: '8px' }}>
          <h2>🛠️ Create Event</h2>
          <form onSubmit={handleCreateEvent} style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap', alignItems: 'flex-end' }}>
            <div>
              <label style={labelStyle}>Event Title</label>
              <input type="text" required style={inputStyle} value={newEvent.title} onChange={e => setNewEvent({...newEvent, title: e.target.value})} />
            </div>
            <div>
              <label style={labelStyle}>Category</label>
              <select style={inputStyle} value={newEvent.category_id} onChange={e => setNewEvent({...newEvent, category_id: parseInt(e.target.value)})}>
                {categories.map(cat => <option key={cat.id} value={cat.id}>{cat.name}</option>)}
              </select>
            </div>
             <div>
              <label style={labelStyle}>Date</label>
              <input type="datetime-local" required style={inputStyle} value={newEvent.date} onChange={e => setNewEvent({...newEvent, date: e.target.value})} />
            </div>
            <div>
              <label style={labelStyle}>Venue</label>
              <input type="text" required style={inputStyle} value={newEvent.venue} onChange={e => setNewEvent({...newEvent, venue: e.target.value})} />
            </div>
            <div>
              <label style={labelStyle}>Capacity</label>
              <input type="number" required style={inputStyle} value={newEvent.capacity} onChange={e => setNewEvent({...newEvent, capacity: parseInt(e.target.value)})} />
            </div>
            <button type="submit" style={{ ...btnStyle, marginTop: 0, backgroundColor: '#28a745', width: 'auto' }}>+ Create Event</button>
          </form>
        </section>
      )}

      {/* Recommendations & Events lists remain the same... */}
      <section style={{ marginBottom: '3rem' }}>
        <h2>✨ AI Recommended For You</h2>
        <div style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap' }}>
          {recommendations.length > 0 ? (
            recommendations.map(event => (
              <div key={event.id} style={cardStyle(true)}>
                <h3>{event.title}</h3>
                <p>📍 {event.venue}</p>
                <button onClick={() => handleRegister(event.id)} style={btnStyle}>Register Now</button>
              </div>
            ))
          ) : (<p style={{ color: '#666' }}>Register for events to get recommendations!</p>)}
        </div>
      </section>

      <section>
        <h2>All Campus Events</h2>
        <div style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap' }}>
          {events.length > 0 ? (
            events.map(event => (
              <div key={event.id} style={cardStyle(false)}>
                <h3>{event.title}</h3>
                <p>📍 {event.venue}</p>
                <p>👥 Capacity: {event.capacity}</p>
                <button onClick={() => handleRegister(event.id)} style={btnStyle}>Register Now</button>
              </div>
            ))
          ) : (<p>No events found.</p>)}
        </div>
      </section>
    </div>
  );
}

// Styles
const fullInputStyle = { width: '100%', padding: '0.75rem', marginBottom: '1rem', border: '1px solid #ccc', borderRadius: '4px', boxSizing: 'border-box' };
const inputStyle = { display: 'block', padding: '0.5rem', borderRadius: '4px', border: '1px solid #ccc', marginTop: '0.25rem' };
const labelStyle = { fontSize: '0.875rem', fontWeight: 'bold', color: '#333' };
const alertStyle = { padding: '1rem', backgroundColor: '#d4edda', color: '#155724', borderRadius: '4px', marginBottom: '1rem' };
const cardStyle = (isRecommended) => ({ border: isRecommended ? '2px solid #007bff' : '1px solid #ccc', borderRadius: '8px', padding: '1.5rem', width: '250px', backgroundColor: isRecommended ? '#f8fbff' : 'white' });
const btnStyle = { backgroundColor: '#007bff', color: 'white', border: 'none', padding: '0.75rem', borderRadius: '4px', cursor: 'pointer', width: '100%', fontWeight: 'bold' };

export default App;