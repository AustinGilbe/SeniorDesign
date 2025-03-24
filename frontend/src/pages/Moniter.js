import * as React from 'react';
import { Link } from 'react-router-dom';
import '../styles.css';

export default function Moniter() {
    return (
        <div>
        <div className="main-content">
            <h1>Moniter</h1>
            <p>This is the main content area.</p>
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
        </div>
      );
  }