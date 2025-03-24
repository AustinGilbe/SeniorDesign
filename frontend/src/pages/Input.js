import * as React from 'react';
import { useEffect } from 'react';

import { Link } from 'react-router-dom';
import '../styles.css';

export default function Input() {

  const [dragActive, setDragActive] = React.useState(false);
  // ref
  const inputRef = React.useRef(null);
  
  // handle drag events
  const handleDrag = function(e) {
  
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };
  
  // triggers when file is dropped
  const handleDrop = function(e) {
 
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      console.log('File dropped:', e.dataTransfer.files[0].name);
      // handle the dropped file here
    } else {
      console.log('No file dropped');
    }
  };
  
  // triggers when file is selected with click
  const handleChange = function(e) {

    e.preventDefault();
    if (e.target.files && e.target.files[0]) {
      // handleFiles(e.target.files);
    }
  };
  
// triggers the input when the button is clicked
  const onButtonClick = () => {
    inputRef.current.click();

  };
  








    return (
        <div>

        <div className="main-content">
            <h1>Input Data Below</h1>

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
                <Link to="/Input">
                    <button className='sidebar_buttons' role="button"><span class="text">Input</span></button>
                </Link>
                </ul>
            </div>


            <form id="form-file-upload" onDragEnter={handleDrag} onSubmit={(e) => e.preventDefault()}>
              <input ref={inputRef} type="file" id="input-file-upload" multiple={true} onChange={handleChange} />
              <label id="label-file-upload" htmlFor="input-file-upload" className={dragActive ? "drag-active" : "" }>
                <div>
                  <p>Drag and drop your file here or</p>
                  <button className="upload-button" onClick={onButtonClick}>Upload a file</button>
                </div> 
              </label>
              { dragActive && <div id="drag-file-element" onDragEnter={handleDrag} onDragLeave={handleDrag} onDragOver={handleDrag} onDrop={handleDrop}></div> }
            </form>

            

        </div>
      );
  }