import { useState, useRef, useCallback, useEffect } from 'react';
import { Link } from 'react-router-dom';
import '../styles.css';

// ErrorBoundary component should be in a separate file, but added here for completeness
/*class ErrorBoundary extends React.Component {
  state = { hasError: false };

  static getDerivedStateFromError(error) {
    return { hasError: true };
  }

  componentDidCatch(error, info) {
    console.error('ErrorBoundary caught:', error, info);
  }

  render() {
    if (this.state.hasError) {
      return <div className="error-fallback">Something went wrong. Please refresh.</div>;
    }
    return this.props.children;
  }
}
*/
const debugFetch = async (url, options) => {
  const start = performance.now();
  const requestId = Math.random().toString(36).substring(2, 8);
  
  console.log(`[${requestId}] REQUEST START:`, {
    url,
    method: options?.method,
    size: options?.body?.length
  });

  try {
    const response = await fetch(url, options);
    console.log(`[${requestId}] REQUEST COMPLETE:`, {
      status: response.status,
      time: `${(performance.now() - start).toFixed(2)}ms`
    });
    return response;
  } catch (error) {
    console.error(`[${requestId}] REQUEST FAILED:`, {
      error: error.message,
      time: `${(performance.now() - start).toFixed(2)}ms`
    });
    throw error;
  }
};

export default function Prompt() {
  const [text, setText] = useState('');
  const [responseText, setResponseText] = useState('');
  const [dragActive, setDragActive] = useState(false);
  const [uploadedFiles, setUploadedFiles] = useState([]);
  const [isProcessing, setIsProcessing] = useState(false);

  const inputRef = useRef(null);
  const fileQueueRef = useRef([]);
  const isProcessingRef = useRef(false);
  const renderCount = useRef(0);
  const refreshDebugRef = useRef(0);

  // Crash detection and prevention
  useEffect(() => {
    const handleUnhandledRejection = (event) => {
      console.error('UNHANDLED PROMISE REJECTION:', event.reason);
      event.preventDefault();
    };

    const handleError = (event) => {
      console.error('UNHANDLED ERROR:', event.error);
      event.preventDefault();
    };

    window.addEventListener('unhandledrejection', handleUnhandledRejection);
    window.addEventListener('error', handleError);

    return () => {
      window.removeEventListener('unhandledrejection', handleUnhandledRejection);
      window.removeEventListener('error', handleError);
    };
  }, []);

  // Render counter with loop detection
  useEffect(() => {
    renderCount.current += 1;
    console.log(`Render #${renderCount.current}`);

    if (renderCount.current > 20) {
      console.error('EXCESSIVE RE-RENDERS DETECTED', {
        text,
        responseTextLength: responseText?.length,
        uploadedFiles: uploadedFiles.length,
        isProcessing
      });
      // Reset problematic state
      setText('');
      setResponseText('');
      setUploadedFiles([]);
      setIsProcessing(false);
      renderCount.current = 0;
    }
  }, [text, responseText, uploadedFiles, isProcessing]);

  // Component lifecycle tracking
  useEffect(() => {
    console.log('Component mounted. Render count:', refreshDebugRef.current + 1);
    refreshDebugRef.current += 1;

    return () => {
      console.log('Component unmounting');
      // Cleanup
      fileQueueRef.current = [];
    };
  }, []);

  // Crash recovery logger
  useEffect(() => {
    const lastCrash = localStorage.getItem('lastCrash');
    if (lastCrash) {
      console.error('PREVIOUS CRASH RECOVERED:', JSON.parse(lastCrash));
    }

    const logCrashData = () => {
      localStorage.setItem('lastCrash', JSON.stringify({
        timestamp: new Date().toISOString(),
        renderCount: renderCount.current,
        lastAction: window.lastDebugAction,
        state: {
          textLength: text.length,
          responseLength: responseText.length,
          fileCount: uploadedFiles.length
        }
      }));
    };

    window.addEventListener('beforeunload', logCrashData);
    return () => window.removeEventListener('beforeunload', logCrashData);
  }, [text, responseText, uploadedFiles]);

  // Safe state updater for responseText
  const safeSetResponseText = useCallback((updater) => {
    setResponseText(prev => {
      const newValue = typeof updater === 'function' ? updater(prev) : updater;
      if (newValue !== prev) {
        console.log('Updating responseText');
        return newValue;
      }
      console.log('Skipping redundant responseText update');
      return prev;
    });
  }, []);

  // File reader with enhanced error handling
  const readFileAsText = useCallback((file) => {
    return new Promise((resolve, reject) => {
      console.log('Starting to read file:', file.name);
      const reader = new FileReader();
      
      reader.onload = (e) => {
        console.log('File read successfully:', file.name);
        resolve(e.target.result);
      };
      
      reader.onerror = (e) => {
        console.error('File read error:', {
          fileName: file.name,
          error: e.target.error
        });
        reject(new Error(`File read error: ${e.target.error}`));
      };
      
      reader.onabort = (e) => {
        console.error('File read aborted:', file.name);
        reject(new Error('File read aborted by user'));
      };
      
      try {
        reader.readAsText(file);
      } catch (error) {
        console.error('Unexpected error in readAsText:', error);
        reject(error);
      }
    });
  }, []);

  // LLM communication with safeguards
  const sendToLLM = useCallback(async (content, filePath = '') => {
    console.group('sendToLLM Debug');
    try {
      // Content size validation
      if (content.length > 10 * 1024 * 1024) {
        throw new Error('Content too large (>10MB)');
      }

      console.log('Starting LLM request with:', {
        contentLength: content.length,
        filePath,
        previousResponseLength: responseText?.length
      });

      const startTime = performance.now();
      const response = await debugFetch('http://localhost:8000/ask_llm', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          file: content, 
          isBase64: true, 
          filePath,
          previousResponse: responseText 
        }),
      });
      
      const duration = performance.now() - startTime;
      console.log(`Request completed in ${duration.toFixed(2)}ms`);

      if (!response.ok) {
        const errorText = await response.text();
        console.error('Server responded with error:', {
          status: response.status,
          errorText
        });
        throw new Error(`Server error: ${errorText}`);
      }

      const data = await response.json();
      console.log('LLM response received:', {
        responseLength: data.response?.length,
        truncatedResponse: data.response?.substring(0, 100) + '...'
      });
      
      safeSetResponseText(prev => 
        prev ? `${prev}\n\n--- New Response ---\n${data.response}` : data.response
      );
    } catch (error) {
      console.error('LLM processing failed:', error);
      safeSetResponseText(prev => 
        prev ? `${prev}\n\n--- Error ---\n${error.message}` : `Error: ${error.message}`
      );
    } finally {
      console.groupEnd();
    }
  }, [responseText, safeSetResponseText]);

  // File processing queue with throttling
  const processQueue = useCallback(async () => {
    const queueId = Math.random().toString(36).substring(2, 6);
    console.group(`[Q:${queueId}] processQueue`);

    try {
      if (isProcessingRef.current || fileQueueRef.current.length === 0) {
        console.log('Queue not ready for processing');
        return;
      }

      // Add slight delay between processing
      await new Promise(resolve => setTimeout(resolve, 100));
      
      isProcessingRef.current = true;
      setIsProcessing(true);

      const file = fileQueueRef.current[0];
      console.log('Processing file:', file.name);

      try {
        const fileContent = await readFileAsText(file);
        console.log('File content read. Length:', fileContent.length);

        const encodedContent = btoa(unescape(encodeURIComponent(fileContent)));
        console.log('Content encoded. Length:', encodedContent.length);

        // Upload to backend
        const formData = new FormData();
        formData.append('file', file);

        console.log('Starting file upload');
        const uploadResponse = await debugFetch('http://localhost:5000/api/upload', {
          method: 'POST',
          body: formData,
        });

        if (!uploadResponse.ok) {
          throw new Error(`Upload failed: ${uploadResponse.status}`);
        }

        const uploadData = await uploadResponse.json();
        console.log('Upload successful. Path:', uploadData.currentPath);

        setUploadedFiles(prev => [
          ...prev,
          { name: file.name, content: fileContent }
        ]);

        await sendToLLM(encodedContent, uploadData.currentPath);
        fileQueueRef.current.shift();
      } catch (error) {
        console.error('File processing error:', error);
        safeSetResponseText(prev =>
          `${prev}\n\n--- Error Processing ${file.name} ---\n${error.message}`
        );
        fileQueueRef.current.shift();
      }
    } catch (error) {
      console.error('Queue processing error:', error);
    } finally {
      isProcessingRef.current = false;
      setIsProcessing(false);
      
      if (fileQueueRef.current.length > 0) {
        console.log('Processing next file in queue');
        setTimeout(processQueue, 100); // Add delay before next processing
      } else {
        console.log('Queue processing complete');
      }
      console.groupEnd();
    }
  }, [readFileAsText, sendToLLM, safeSetResponseText]);

  // File handler with validation
  const handleFile = useCallback((file) => {
    console.log('[ACTION] handleFile');
    window.lastDebugAction = 'handleFile';

    if (!file.name.endsWith('.csv')) {
      console.log('File rejected - not a CSV:', file.name);
      return;
    }

    if (file.size > 5 * 1024 * 1024) {
      console.error('File too large:', file.name, file.size);
      safeSetResponseText(prev =>
        `${prev || ''}\n\n--- Error ---\nFile too large: ${file.name} (${(file.size / 1024 / 1024).toFixed(2)}MB)`
      );
      return;
    }

    console.log('Adding file to queue:', file.name);
    fileQueueRef.current = [...fileQueueRef.current, file];
    
    if (!isProcessingRef.current) {
      console.log('Starting queue processing');
      processQueue();
    }
  }, [processQueue, safeSetResponseText]);

  // Event handlers with proper prevention
  const handleChange = useCallback((e) => {
    console.log('[ACTION] handleChange');
    window.lastDebugAction = 'handleChange';
    
    e.preventDefault();
    e.stopPropagation();
    
    if (!e.target.files?.length) return;
    
    const validFiles = Array.from(e.target.files).filter(file => 
      file.name.endsWith('.csv') && file.size <= 5 * 1024 * 1024
    );

    if (validFiles.length === 0) {
      console.log('No valid files selected');
      return;
    }

    console.log('Processing', validFiles.length, 'valid files');
    validFiles.forEach(handleFile);
    e.target.value = '';
  }, [handleFile]);

  const handleDrop = useCallback((e) => {
    console.log('[ACTION] handleDrop');
    window.lastDebugAction = 'handleDrop';
    
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    
    if (e.dataTransfer.files?.length > 0) {
      console.log('Files dropped:', e.dataTransfer.files.length);
      Array.from(e.dataTransfer.files).forEach(handleFile);
    }
  }, [handleFile]);

  const handleDrag = useCallback((e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(e.type === 'dragenter' || e.type === 'dragover');
  }, []);

  const onButtonClick = useCallback(() => {
    console.log('[ACTION] onButtonClick');
    window.lastDebugAction = 'onButtonClick';
    
    if (!isProcessing && inputRef.current) {
      inputRef.current.click();
    }
  }, [isProcessing]);

  const handleFileButtonClick = (file) => {
    console.log('[ACTION] handleFileButtonClick');
    window.lastDebugAction = 'handleFileButtonClick';
    console.log('File clicked:', file.name);
  };

  const handleKeyDown = async (event) => {
    if (event.key === 'Enter') {
      console.log('[ACTION] handleKeyDown (Enter)');
      window.lastDebugAction = 'handleKeyDown';
      
      event.preventDefault();
      const query = text.trim();
      
      if (!query) {
        console.log('Empty query ignored');
        return;
      }
      
      console.log('Processing query:', query.substring(0, 50));
      setText('');
      
      try {
        const response = await debugFetch('http://localhost:8000/ask_llm', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ query }),
        });

        if (!response.ok) {
          throw new Error(`Request failed: ${response.status}`);
        }
        
        const data = await response.json();
        safeSetResponseText(prev => 
          prev ? `${prev}\n\n--- New Query Response ---\n${data.response}` : data.response
        );
      } catch (error) {
        console.error('Query error:', error);
        safeSetResponseText(prev =>
          prev ? `${prev}\n\n--- Query Error ---\n${error.message}` : `Error: ${error.message}`
        );
      }
    }
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
          <p className="response-box" style={{ whiteSpace: 'pre-wrap' }}>
            {responseText || 'LLM responses will appear here...'}
          </p>
        </div>

        <form
          id="form-file-upload"
          onDragEnter={handleDrag}
          onSubmit={(e) => e.preventDefault()}
        >
          <input 
            ref={inputRef} 
            type="file" 
            id="input-file-upload" 
            multiple 
            onChange={handleChange} 
            accept=".csv"
            disabled={isProcessing}
          />
          <label 
            id="label-file-upload" 
            htmlFor="input-file-upload" 
            className={dragActive ? 'drag-active' : ''}
          >
            <div>
              <p>Drag and drop your file here or</p>
              <button
                type="button"
                className="upload-button"
                onClick={onButtonClick}
                disabled={isProcessing}
              >
                {isProcessing ? 'Processing...' : 'Upload a file'}
              </button>
            </div>
          </label>
          {dragActive && (
            <div 
              id="drag-file-element" 
              onDragEnter={handleDrag} 
              onDragLeave={handleDrag} 
              onDragOver={handleDrag} 
              onDrop={handleDrop}
            />
          )}
        </form>

        <div className="csv-list-wrapper">
          {uploadedFiles.length > 0 ? (
            uploadedFiles.map((file, index) => (
              <div key={`${file.name}-${index}`} className="csv_list_box">
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