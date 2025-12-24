// Dashboard functionality - Experiment 9: Energy Simulation Module
let energyChart = null;

document.addEventListener('DOMContentLoaded', function() {
    console.log('Smart Tile Dashboard loaded - Experiment 9');
    
    // Initialize dashboard
    initializeChart();
    loadDashboardData();
    
    // Set up event listeners
    const simulateBtn = document.getElementById('simulateBtn');
    const clearDataBtn = document.getElementById('clearDataBtn');
    const timeRange = document.getElementById('timeRange');
    
    if (simulateBtn) {
        simulateBtn.addEventListener('click', simulateFootstep);
    }
    
    if (clearDataBtn) {
        clearDataBtn.addEventListener('click', clearAllData);
    }
    
    if (timeRange) {
        timeRange.addEventListener('change', function() {
            console.log('Time range changed:', this.value);
            loadDashboardData();
        });
    }
    
    // Auto-refresh every 30 seconds
    setInterval(loadDashboardData, 30000);
});

function initializeChart() {
    const ctx = document.getElementById('energyChart');
    if (!ctx) return;
    
    energyChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [{
                label: 'Energy Generated (mJ)',
                data: [],
                borderColor: 'rgb(102, 126, 234)',
                backgroundColor: 'rgba(102, 126, 234, 0.1)',
                borderWidth: 2,
                tension: 0.4,
                fill: true,
                pointRadius: 4,
                pointHoverRadius: 6
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: true,
                    labels: {
                        color: '#f1f5f9',
                        font: {
                            size: 12
                        }
                    }
                },
                tooltip: {
                    mode: 'index',
                    intersect: false,
                    backgroundColor: 'rgba(30, 41, 59, 0.9)',
                    titleColor: '#f1f5f9',
                    bodyColor: '#94a3b8',
                    borderColor: '#334155',
                    borderWidth: 1
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    grid: {
                        color: '#334155'
                    },
                    ticks: {
                        color: '#94a3b8'
                    },
                    title: {
                        display: true,
                        text: 'Energy (mJ)',
                        color: '#f1f5f9'
                    }
                },
                x: {
                    grid: {
                        color: '#334155'
                    },
                    ticks: {
                        color: '#94a3b8',
                        maxRotation: 45,
                        minRotation: 0
                    }
                }
            },
            interaction: {
                mode: 'nearest',
                axis: 'x',
                intersect: false
            }
        }
    });
}

async function simulateFootstep() {
    const btn = document.getElementById('simulateBtn');
    const originalHTML = btn.innerHTML;
    
    try {
        // Disable button and show loading
        btn.disabled = true;
        btn.innerHTML = `
            <svg class="spinner" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <circle cx="12" cy="12" r="10"/>
            </svg>
            Generating...
        `;
        
        const response = await fetch('/simulate-step', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        const result = await response.json();
        
        if (result.success) {
            // Update statistics
            updateStatistics(result.data);
            
            // Reload chart data
            await loadDashboardData();
            
            // Show success animation
            showNotification('success', `⚡ Step ${result.data.step_number}: ${result.data.energy} mJ generated!`);
            
            // Add row to table
            addTableRow(result.data);
            
        } else {
            showNotification('error', 'Simulation failed: ' + result.error);
        }
        
    } catch (error) {
        console.error('Simulation error:', error);
        showNotification('error', 'Failed to simulate footstep');
    } finally {
        // Re-enable button
        btn.disabled = false;
        btn.innerHTML = originalHTML;
    }
}

async function loadDashboardData() {
    try {
        // Get the selected time range
        const timeRange = document.getElementById('timeRange');
        const limit = timeRange ? (timeRange.value === 'all' ? 1000 : (timeRange.value === '24h' ? 100 : 50)) : 50;
        
        const response = await fetch(`/get-energy-data?limit=${limit}`);
        const result = await response.json();
        
        if (result.success) {
            // Update statistics
            updateStatisticsFromData(result.statistics);
            
            // Update chart with proper data
            if (energyChart && result.chart_data) {
                // If we have data, display it
                if (result.chart_data.labels.length > 0) {
                    energyChart.data.labels = result.chart_data.labels;
                    energyChart.data.datasets[0].data = result.chart_data.energy;
                } else {
                    // No data yet - show empty chart
                    energyChart.data.labels = [];
                    energyChart.data.datasets[0].data = [];
                }
                energyChart.update('none');
            }
            
            // Update table
            updateTable(result.recent_records);
            
            // Update record count
            const recordCount = document.getElementById('recordCount');
            if (recordCount) {
                recordCount.textContent = `${result.statistics.total_steps} records`;
            }
        }
    } catch (error) {
        console.error('Load dashboard data error:', error);
    }
}

function updateStatistics(data) {
    // Update total energy
    const totalEnergyEl = document.getElementById('totalEnergy');
    if (totalEnergyEl) {
        totalEnergyEl.textContent = `${data.total_energy} mJ`;
        animateValue(totalEnergyEl);
    }
    
    // Update total steps
    const totalStepsEl = document.getElementById('totalSteps');
    if (totalStepsEl) {
        totalStepsEl.textContent = `Total: ${data.total_steps} steps`;
    }
    
    // Update average energy
    const avgEnergyEl = document.getElementById('avgEnergy');
    if (avgEnergyEl) {
        avgEnergyEl.textContent = `${data.avg_energy} mJ`;
        animateValue(avgEnergyEl);
    }
}

function updateStatisticsFromData(stats) {
    // Total Energy
    const totalEnergyEl = document.getElementById('totalEnergy');
    if (totalEnergyEl) {
        totalEnergyEl.textContent = `${stats.total_energy_mj} mJ`;
    }
    
    const energyWhEl = document.getElementById('energyWh');
    if (energyWhEl) {
        energyWhEl.textContent = `${stats.total_energy_wh} Wh`;
    }
    
    // Total Steps
    const stepsTodayEl = document.getElementById('stepsToday');
    if (stepsTodayEl) {
        stepsTodayEl.textContent = stats.total_steps;
    }
    
    const totalStepsEl = document.getElementById('totalSteps');
    if (totalStepsEl) {
        totalStepsEl.textContent = `Total: ${stats.total_steps} steps`;
    }
    
    // Average Energy
    const avgEnergyEl = document.getElementById('avgEnergy');
    if (avgEnergyEl) {
        avgEnergyEl.textContent = `${stats.avg_energy} mJ`;
    }
    
    // Energy Value
    const energyValueEl = document.getElementById('energyValue');
    if (energyValueEl) {
        energyValueEl.textContent = `₹${stats.energy_value_inr}`;
    }
    
    // Update step change message
    const stepChangeEl = document.getElementById('stepChange');
    if (stepChangeEl && stats.total_steps > 0) {
        stepChangeEl.textContent = `${stats.total_steps} total steps`;
        stepChangeEl.classList.add('positive');
    }
}

function updateTable(records) {
    const tbody = document.getElementById('dataTableBody');
    if (!tbody) return;
    
    if (records.length === 0) {
        tbody.innerHTML = '<tr class="no-data"><td colspan="5">No data yet. Click "Simulate Footstep" to start!</td></tr>';
        return;
    }
    
    tbody.innerHTML = records.map(record => `
        <tr class="fade-in">
            <td>${record.step}</td>
            <td>${formatTime(record.time)}</td>
            <td>${record.force} N</td>
            <td>${record.displacement} mm</td>
            <td class="energy-cell">${record.energy} mJ</td>
        </tr>
    `).join('');
}

function addTableRow(data) {
    const tbody = document.getElementById('dataTableBody');
    if (!tbody) return;
    
    // Remove "no data" message if present
    const noData = tbody.querySelector('.no-data');
    if (noData) {
        noData.remove();
    }
    
    // Add new row at the top
    const newRow = document.createElement('tr');
    newRow.className = 'fade-in new-row';
    newRow.innerHTML = `
        <td>${data.step_number}</td>
        <td>Just now</td>
        <td>${data.force} N</td>
        <td>${data.displacement} mm</td>
        <td class="energy-cell">${data.energy} mJ</td>
    `;
    
    tbody.insertBefore(newRow, tbody.firstChild);
    
    // Remove highlight after animation
    setTimeout(() => {
        newRow.classList.remove('new-row');
    }, 2000);
    
    // Limit to 10 visible rows
    while (tbody.children.length > 10) {
        tbody.removeChild(tbody.lastChild);
    }
}

async function clearAllData() {
    if (!confirm('Are you sure you want to clear all simulation data? This action cannot be undone.')) {
        return;
    }
    
    const btn = document.getElementById('clearDataBtn');
    const originalHTML = btn.innerHTML;
    
    try {
        btn.disabled = true;
        btn.innerHTML = `
            <svg class="spinner" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <circle cx="12" cy="12" r="10"/>
            </svg>
            Clearing...
        `;
        
        const response = await fetch('/clear-data', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        const result = await response.json();
        
        if (result.success) {
            showNotification('success', `🗑️ Cleared ${result.records_deleted} records`);
            
            // Reset UI
            resetDashboard();
            
        } else {
            showNotification('error', 'Failed to clear data: ' + result.error);
        }
        
    } catch (error) {
        console.error('Clear data error:', error);
        showNotification('error', 'Failed to clear data');
    } finally {
        btn.disabled = false;
        btn.innerHTML = originalHTML;
    }
}

function resetDashboard() {
    // Reset statistics
    document.getElementById('totalEnergy').textContent = '0.00 mJ';
    document.getElementById('energyWh').textContent = '0.0000 Wh';
    document.getElementById('stepsToday').textContent = '0';
    document.getElementById('stepChange').textContent = 'Start stepping!';
    document.getElementById('avgEnergy').textContent = '0.00 mJ';
    document.getElementById('totalSteps').textContent = 'Total: 0 steps';
    document.getElementById('energyValue').textContent = '₹0.00';
    document.getElementById('recordCount').textContent = '0 records';
    
    // Reset chart
    if (energyChart) {
        energyChart.data.labels = [];
        energyChart.data.datasets[0].data = [];
        energyChart.update();
    }
    
    // Reset table
    const tbody = document.getElementById('dataTableBody');
    if (tbody) {
        tbody.innerHTML = '<tr class="no-data"><td colspan="5">No data yet. Click "Simulate Footstep" to start!</td></tr>';
    }
}

function showNotification(type, message) {
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.textContent = message;
    
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.classList.add('show');
    }, 100);
    
    setTimeout(() => {
        notification.classList.remove('show');
        setTimeout(() => {
            notification.remove();
        }, 300);
    }, 3000);
}

function animateValue(element) {
    element.classList.add('pulse');
    setTimeout(() => {
        element.classList.remove('pulse');
    }, 600);
}

function formatTime(timestamp) {
    const date = new Date(timestamp);
    const now = new Date();
    const diff = Math.floor((now - date) / 1000); // seconds
    
    if (diff < 60) return 'Just now';
    if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
    if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
    
    return date.toLocaleTimeString('en-US', { 
        hour: '2-digit', 
        minute: '2-digit' 
    });
}

// Session check
function checkSession() {
    setInterval(() => {
        fetch('/dashboard', {
            method: 'HEAD',
            credentials: 'same-origin'
        }).catch(err => {
            console.log('Session check failed:', err);
            window.location.href = '/login';
        });
    }, 300000); // Check every 5 minutes
}

checkSession();