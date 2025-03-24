import React, { useEffect, useState } from 'react';
import './styles.css';
import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import Home from "./pages/Home";
import Moniter from "./pages/Moniter";
import Prompt from "./pages/Prompt";
import Input from "./pages/Input";
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
    <Router>
    <div className="App">
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/Moniter" element={<Moniter />} />
          <Route path="/Prompt" element={<Prompt />} />
          <Route path="/Input" element={<Input />} />
        </Routes>
    </div>
    </Router>

  );
}

export default App; 
