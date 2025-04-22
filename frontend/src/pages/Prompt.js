import * as React from 'react';
import { useState, useRef } from 'react';
import { Link } from 'react-router-dom';
import '../styles.css';

export default function Prompt() {
  const [text, setText] = useState('');
  const [responseText, setResponseText] = useState('');
  const [dragActive, setDragActive] = useState(false);
  const [uploadedFiles, setUploadedFiles] = useState([]);

  const inputRef = useRef(null);
  console.log('TESTING--------------------------------------');

  // Handle key down event for text input
  const handleKeyDown = async (event) => {
    if (event.key === 'Enter') {
      event.preventDefault();
      event.target.value = '';
      try {
        const response = await fetch('http://localhost:8000/ask_llm', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ query: text }),
        });

        if (!response.ok) {
          throw new Error('Network response was not ok');
        }

        const data = await response.json();
        console.log('Response from backend:', data);
        setResponseText(data.response);
      } catch (error) {
        console.error('Error sending message:', error);
        setResponseText(`Error: ${error.message}`);
      }

      setText('');
    }
  };

  // Send file to backend
  const sendFile = async (file) => {
    const reader = new FileReader();
  
    reader.onload = async (event) => {
      const fileContent = event.target.result;
      
      // Convert content to base64 for reliable transmission
      const encodedContent = btoa(unescape(encodeURIComponent(fileContent)));
  
      // Upload to backend
      const formData = new FormData();
      formData.append('file', file);
  
      try {
        const backendResponse = await fetch('http://localhost:5000/api/upload', {
          method: 'POST',
          body: formData,
        });
        const backendData = await backendResponse.json();
        console.log('✅ Backend upload response:', backendData);
  
        // Save file name + content in state (skip duplicates)
        setUploadedFiles((prev) => {
          if (!prev.some((f) => f.name === file.name)) {
            return [...prev, { name: file.name, content: fileContent }];
          }
          return prev;
        });
  
        // Send to LLM with encoded content
        await sendToLLM(encodedContent, backendData.filePath);
      } catch (error) {
        console.error('❌ Upload error:', error);
        setResponseText(`Error: ${error.message}`);
      }
    };
  
    reader.readAsText(file);
  };

  const sendToLLM = async (content, filePath = '') => {
    try {
      console.log("Sending request to LLM API...");
      const llmResponse = await fetch('http://localhost:8000/ask_llm', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ file: content, isBase64: true }),
      });
      console.log("Received response from LLM API:", llmResponse);
  
      if (!llmResponse.ok) {
        const errorText = await llmResponse.text();
        console.error("Error response text:", errorText);
        throw new Error(`Server error (${llmResponse.status}): ${errorText}`);
      }
  
      const llmData = await llmResponse.json();
      console.log("Parsed response data:", llmData);
      
      if (llmData && llmData.response) {
        console.log("Setting response text:", llmData.response);
        setResponseText(llmData.response);
      } else {
        console.error("Unexpected response format:", llmData);
        setResponseText('Error: Received unexpected response format from server');
      }
    } catch (error) {
      console.error("LLM API error:", error);
      setResponseText(`Error: ${error.message}`);
    }
  };
  

  // Handle file selection through input or drag and drop
  const handleChange = (e) => {
    e.preventDefault();
    if (e.target.files && e.target.files.length > 0) {
      const files = Array.from(e.target.files);
      files.forEach((file) => {
        if (file.name.endsWith('.csv')) {
          sendFile(file);
          setUploadedFiles((prev) => [...prev, file]);
        }
      });
    }
  };
  
  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      const files = Array.from(e.dataTransfer.files);
      files.forEach((file) => {
        if (file.name.endsWith('.csv')) {
          sendFile(file);
          setUploadedFiles((prev) => [...prev, file]);
        }
      });
    }
  };

  // Handle drag events to manage active dragging
  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };


  const onButtonClick = () => {
    inputRef.current.click();
  };

  return (
    <div>
      <div className="main-content">
        <h1>Prompt the LLM below</h1>
      </div>

      <div className="sidebar">
        <h2>Sidebar</h2>
        <ul>
          <Link to="/">
            <button className="sidebar_buttons" role="button">
              <span className="text">Home</span>
            </button>
          </Link>
          <Link to="/Moniter">
            <button className="sidebar_buttons" role="button">
              <span className="text">Moniter</span>
            </button>
          </Link>
          <Link to="/Prompt">
            <button className="sidebar_buttons" role="button">
              <span className="text">Prompt</span>
            </button>
          </Link>
        </ul>
      </div>

      <div>
        <p className="response-box">{responseText}</p>
      </div>

      <form id="form-file-upload" onDragEnter={handleDrag} onSubmit={(e) => e.preventDefault()}>
        <input ref={inputRef} type="file" id="input-file-upload" multiple={true} onChange={handleChange} />
        <label id="label-file-upload" htmlFor="input-file-upload" className={dragActive ? 'drag-active' : ''}>
          <div>
            <p>Drag and drop your file here or</p>
            <button className="upload-button" onClick={onButtonClick}>
              Upload a file
            </button>
          </div>
        </label>
        {dragActive && (
          <div id="drag-file-element" onDragEnter={handleDrag} onDragLeave={handleDrag} onDragOver={handleDrag} onDrop={handleDrop}></div>
        )}
      </form>
      <div className="csv-list-wrapper">
        {uploadedFiles.length > 0 ? (
          uploadedFiles.map((file) => (
            <div key={file.name} className="csv_list_box">
              <button onClick={() => handleFileButtonClick(file)}>
                {file.name}
              </button>
            </div>
          ))
        ) : (
          <p>No CSV files uploaded yet.</p>
        )}
      </div>
    </div>
  );
}

