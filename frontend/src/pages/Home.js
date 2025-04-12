import * as React from 'react';
import { Link } from 'react-router-dom';
import '../styles.css';

export default function Home() {
    return (
        <div>
        <div className="main-content">
            <h1>Welcome to the LLM-Powered Threat Intelligence System for DER Networks</h1>
            <p>This application is a prototype of a LLM-powered threat intelligence system for DER networks. That can be used to moniter and detect DER specific electrical threats. </p>
            <h1>Our Functionality</h1>
            <p>This application has the following features:  A Moniter area where the user can view incoming data, A prompt area where the user can prompt the model based on the trainned LLM's information and the users own data, and a Input area where the user can input there own data into the model.</p>
            <h1>Our Members</h1>
            <p>
            Henry Hodge,
            Grant Alderson,
            Jacob Howard,
            Patrick Handren,
            Austin Gilbert,
            </p>
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
      );;
  }