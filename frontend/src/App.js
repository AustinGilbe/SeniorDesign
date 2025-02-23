import React, { useEffect, useState } from 'react';

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
      <h1>Frontend Connected to Backend</h1>
      <p>Backend Response: {message}</p>
    
    
    <header>
      <nav>
        <ul>
          <li><a href="#">Home</a></li>
          <li><a href="#">About</a></li>
          <li><a href="#">Contact</a></li>
        </ul>
      </nav>
    </header>
    <main>
      <h1>Welcome to our website!</h1>
      <p>This is a sample website.</p>
    </main>
    <footer>
      <p>&copy; 2023 Our Company</p>
    </footer>
  </div>
  );
}

export default App; 
