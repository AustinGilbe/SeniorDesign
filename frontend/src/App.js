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
    </div>
  );
}

export default App;
