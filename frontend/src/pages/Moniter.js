import React, { useState, useEffect, useRef } from 'react';
import { Link } from 'react-router-dom';
import '../styles.css';
import Papa from 'papaparse';
import { 
  LineChart, Line, AreaChart, Area, BarChart, Bar, 
  XAxis, YAxis, Tooltip, CartesianGrid, Legend, 
  ResponsiveContainer, ComposedChart 
} from 'recharts';

export default function Monitor() {
    const [allData, setAllData] = useState([]);
    const [visibleData, setVisibleData] = useState([]);
    const [loading, setLoading] = useState(true);
    const indexRef = useRef(0);
    const initialDisplayCount = 5;
    const intervalMs = 15000;

    useEffect(() => {
        // First load saved data if it exists
        const savedProgress = localStorage.getItem('monitorProgress');
        let savedState = null;
        
        if (savedProgress) {
            try {
                savedState = JSON.parse(savedProgress);
                if (savedState.savedData && savedState.savedIndex) {
                    setVisibleData(savedState.savedData);
                    indexRef.current = savedState.savedIndex;
                }
            } catch (e) {
                console.error("Error parsing saved progress:", e);
            }
        }

        // Then fetch and parse the CSV
        const csvFilePath = `${process.env.PUBLIC_URL}/uploads/current/current.csv`;
        
        fetch(csvFilePath)
            .then(res => res.text())
            .then(csvText => {
                Papa.parse(csvText, {
                    header: true,
                    skipEmptyLines: true,
                    complete: (result) => {
                        const cleanedData = result.data.map(row => ({
                            Timestamp: row.Timestamp,
                            Solar_Generation_kW: parseFloat(row.Solar_Generation_kW) || 0,
                            Home_Load_kW: parseFloat(row.Home_Load_kW) || 0,
                            Tesla_Charger_kW: parseFloat(row.Tesla_Charger_kW) || 0,
                            Battery_Charge_kWh: parseFloat(row.Battery_Charge_kWh) || 0,
                            Battery_Discharge_kW: parseFloat(row.Battery_Discharge_kW) || 0,
                            Grid_Import_kW: parseFloat(row.Grid_Import_kW) || 0,
                            Grid_Export_kW: parseFloat(row.Grid_Export_kW) || 0,
                        }));
                        
                        setAllData(cleanedData);
                        
                        // Only initialize with fresh data if no saved progress exists
                        if (!savedState) {
                            setVisibleData(cleanedData.slice(0, initialDisplayCount));
                            indexRef.current = initialDisplayCount;
                        } else {
                            // Make sure our saved data matches the full dataset
                            if (savedState.savedData.length > cleanedData.length) {
                                // If saved data is longer (shouldn't happen), truncate it
                                const correctedData = savedState.savedData.slice(0, cleanedData.length);
                                setVisibleData(correctedData);
                                indexRef.current = Math.min(savedState.savedIndex, cleanedData.length);
                                localStorage.setItem('monitorProgress', JSON.stringify({
                                    savedIndex: indexRef.current,
                                    savedData: correctedData
                                }));
                            }
                        }
                        
                        setLoading(false);
                    },
                    error: (error) => {
                        console.error("CSV parsing error:", error);
                        setLoading(false);
                    }
                });
            })
            .catch(err => {
                console.error("Fetch error:", err);
                setLoading(false);
            });
    }, []);

    useEffect(() => {
        const interval = setInterval(() => {
            if (indexRef.current < allData.length) {
                const newDataPoint = allData[indexRef.current];
                setVisibleData(prev => {
                    const updatedData = [...prev, newDataPoint];
                    
                    // Save progress to localStorage
                    localStorage.setItem('monitorProgress', JSON.stringify({
                        savedIndex: indexRef.current + 1,
                        savedData: updatedData
                    }));
                    
                    return updatedData;
                });
                indexRef.current += 1;
            } else {
                clearInterval(interval);
            }
        }, intervalMs);
        
        return () => clearInterval(interval);
    }, [allData]);

    const formatHour = (timestamp) => {
        return timestamp.length > 10 ? timestamp.substring(11, 16) : timestamp;
    };

    const resetProgress = () => {
        localStorage.removeItem('monitorProgress');
        setVisibleData(allData.slice(0, initialDisplayCount));
        indexRef.current = initialDisplayCount;
    };

    if (loading) return <div>Loading data...</div>;
    if (visibleData.length === 0) return <div>No data available</div>;

    return (
        <div>
            <div className="main-content">
                <h1>Monitor</h1>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <p>Displaying {visibleData.length} of {allData.length} data points</p>
                    <button onClick={resetProgress} style={{ 
                        padding: '5px 10px', 
                        backgroundColor: '#f94144', 
                        color: 'white', 
                        border: 'none', 
                        borderRadius: '4px',
                        cursor: 'pointer'
                    }}>
                        Reset Progress
                    </button>
                </div>
                
                {/* Rest of your 4-chart grid remains the same */}
                <div style={{ 
                    display: 'grid', 
                    gridTemplateColumns: 'repeat(2, 1fr)',
                    gap: '20px',
                    marginBottom: '20px'
                }}>
                    {/* Chart 1: Energy Flow Overview */}
                    <div style={{ backgroundColor: '#fff', padding: '15px', borderRadius: '8px', boxShadow: '0 2px 4px rgba(0,0,0,0.1)' }}>
                        <h3>Energy Flow (kW)</h3>
                        <ResponsiveContainer width="100%" height={300}>
                            <AreaChart data={visibleData}>
                                <CartesianGrid strokeDasharray="3 3" />
                                <XAxis dataKey="Timestamp" tickFormatter={formatHour}/>
                                <YAxis/>
                                <Tooltip/>
                                <Legend/>
                                <Area type="monotone" dataKey="Solar_Generation_kW" stackId="1" stroke="#FFD166" fill="#FFD166" name="Solar" />
                                <Area type="monotone" dataKey="Battery_Discharge_kW" stackId="1" stroke="#EF476F" fill="#EF476F" name="Battery" />
                                <Area type="monotone" dataKey="Grid_Import_kW" stackId="1" stroke="#118AB2" fill="#118AB2" name="Grid Import" />
                            </AreaChart>
                        </ResponsiveContainer>
                    </div>

                    {/* Chart 2: Battery Status */}
                    <div style={{ backgroundColor: '#fff', padding: '15px', borderRadius: '8px', boxShadow: '0 2px 4px rgba(0,0,0,0.1)' }}>
                        <h3>Battery Status</h3>
                        <ResponsiveContainer width="100%" height={300}>
                            <ComposedChart data={visibleData}>
                                <CartesianGrid strokeDasharray="3 3" />
                                <XAxis dataKey="Timestamp" tickFormatter={formatHour}/>
                                <YAxis yAxisId="left" orientation="left" label={{ value: 'kW', angle: -90 }} />
                                <YAxis yAxisId="right" orientation="right" label={{ value: 'kWh', angle: 90 }} />
                                <Tooltip/>
                                <Legend/>
                                <Bar yAxisId="left" dataKey="Battery_Discharge_kW" fill="#EF476F" name="Discharge (kW)"/>
                                <Line yAxisId="right" type="monotone" dataKey="Battery_Charge_kWh" stroke="#06D6A0" name="Charge (kWh)"/>
                            </ComposedChart>
                        </ResponsiveContainer>
                    </div>

                    {/* Chart 3: Solar vs Consumption */}
                    <div style={{ backgroundColor: '#fff', padding: '15px', borderRadius: '8px', boxShadow: '0 2px 4px rgba(0,0,0,0.1)' }}>
                        <h3>Solar vs Consumption</h3>
                        <ResponsiveContainer width="100%" height={300}>
                            <LineChart data={visibleData}>
                                <CartesianGrid strokeDasharray="3 3" />
                                <XAxis dataKey="Timestamp" tickFormatter={formatHour}/>
                                <YAxis yAxisId="left" label={{ value: 'kW', angle: -90 }}/>
                                <Tooltip/>
                                <Legend/>
                                <Line yAxisId="left" dataKey="Solar_Generation_kW" stroke="#FFD166" name="Solar Gen"/>
                                <Line yAxisId="left" dataKey="Home_Load_kW" stroke="#118AB2" name="Home Load"/>
                                <Line yAxisId="left" dataKey="Tesla_Charger_kW" stroke="#5E548E" name="Tesla Charger"/>
                            </LineChart>
                        </ResponsiveContainer>
                    </div>

                    {/* Chart 4: Grid Interaction */}
                    <div style={{ backgroundColor: '#fff', padding: '15px', borderRadius: '8px', boxShadow: '0 2px 4px rgba(0,0,0,0.1)' }}>
                        <h3>Grid Interaction</h3>
                        <ResponsiveContainer width="100%" height={300}>
                            <BarChart data={visibleData}>
                                <CartesianGrid strokeDasharray="3 3" />
                                <XAxis dataKey="Timestamp" tickFormatter={formatHour}/>
                                <YAxis/>
                                <Tooltip/>
                                <Legend/>
                                <Bar dataKey="Grid_Import_kW" fill="#073B4C" name="Grid Import"/>
                                <Bar dataKey="Grid_Export_kW" fill="#06D6A0" name="Grid Export"/>
                            </BarChart>
                        </ResponsiveContainer>
                    </div>
                </div>
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
        </div>
    );
}