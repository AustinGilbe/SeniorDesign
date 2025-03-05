import * as React from 'react';
import { useEffect } from 'react';

import { Link } from 'react-router-dom';
import '../styles.css';

export default function Prompt() {
    //handles input from user towards the LLM
    const [text, setText] = React.useState('');

    const handleKeyDown = async (event) => {
      if (event.key === 'Enter') {
        event.preventDefault(); 
        alert(event.target.value);
        
        try {
          const response = await fetch('http://127.0.0.1:8000/ask_llm', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json'
            },
            body: JSON.stringify({ query: text })
          });
  
          if (!response.ok) {
            throw new Error('Network response was not ok');
          }
  
          const data = await response.json();
          console.log('Response from backend:', data);
          
  
        } catch (error) {
          console.error('Error sending message:', error);
        }
  
        setText(''); 
      }
    };

    //-----------------------------------------------------------------


    //handles LLM response
    const [responseText, setResponseText] = React.useState('');

    function handleServerResponse(response) {
      setResponseText(response.data); 
    }
    //-----------------------------------------------------------------


    return (
        <div>

        <div className="main-content">
            <h1>Prompt the LLM below</h1>

        </div>



          <div className="sidebar">
            <h2>Sidebar</h2>
                <ul>
                <Link to="/">
                    <button className='sidebar_buttons' role="button"><span class="text">Home</span></button>
                </Link>
                <Link to="/Moniter">
                    <button className='sidebar_buttons' role="button"><span class="text">Moniter</span></button>
                </Link>
                <Link to="/Prompt">
                    <button className='sidebar_buttons' role="button"><span class="text">Prompt</span></button>
                </Link>
                </ul>
            </div>


            <div>
                <p className="response-box">{responseText}</p>
            </div>

            

            
            <input
              type="text"
              value={text}
              className="prompt-box"
              onChange={(e) => setText(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Type your message and press Enter"
            />
            
            

        </div>
      );
  }

