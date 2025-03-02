import * as React from 'react';
import { Link } from 'react-router-dom';
import '../styles.css';

export default function Home() {
    return (
        <div>
        <div className="main-content">
            <h1>Main Content</h1>
            <p>This is the main content area.</p>
        </div>



            <div className="sidebar">
                <h2>Sidebar</h2>
                    <ul>
                    <Link to="/">
                        <button className='sidebar_buttons'>Go to Home</button>
                    </Link>
                    <Link to="/Moniter">
                        <button className='sidebar_buttons'>Go Moniter</button>
                    </Link>
                    <Link to="/Prompt">
                        <button className='sidebar_buttons'>Go to Prompt</button>
                    </Link>
                    </ul>
                </div>
        </div>
      );;
  }