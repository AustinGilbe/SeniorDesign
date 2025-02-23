import React, { useEffect, useState } from 'react';
import './styles.css';
function App()
{
  const [message, setMessage] = useState('');

  useEffect(() =>
  {
    fetch("http://localhost:5000/api/test")
      .then(response => response.json())
      .then(data => setMessage(data.message))
      .catch(error => console.error("Error fetching data:", error));
  }, []);

  return (
    <div>
      <div className="temp">
      <h1>Frontend Connected to Backend</h1>
      <p>Backend Response: {message}</p>
      </div>

      <div className="sidebar">
        <h2>Navigation</h2>
        <ul>
          <li><a href="#">Home</a></li>
          <li><a href="#">About</a></li>
          <li><a href="#">Contact</a></li>
        </ul>
      </div>
    

      <div className="main-content">
        <h2>Main Content</h2>
        <p>This is the main content of the website.</p>
      </div>
      <footer className='temp'>
        <p>&copy; 2023 Our Company</p>
      </footer>
  </div>
  );
}

export default App; 
