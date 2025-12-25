// ===============================
// Smart Tile Dashboard (FINAL)
// Optimized for Smooth Performance
// ===============================

let energyChart = null;
const MAX_POINTS = 20;     // Max points on X-axis
const Y_AXIS_MAX = 4000;   // Fixed Y-axis (mJ)

document.addEventListener('DOMContentLoaded', () => {
    initializeChart();
    loadDashboardData();

    document.getElementById('simulateBtn')?.addEventListener('click', simulateFootstep);
    document.getElementById('clearDataBtn')?.addEventListener('click', clearAllData);
    document.getElementById('timeRange')?.addEventListener('change', loadDashboardData);
});

// ===============================
// CHART INITIALIZATION
// ===============================
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
                borderColor: '#667eea',
                backgroundColor: 'rgba(102,126,234,0.15)',
                borderWidth: 2,
                tension: 0.3,
                fill: true,
                pointRadius: 3
            }]
        },
        options: {
            animation: false,
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: true }
            },
            scales: {
                x: {
                    ticks: { maxRotation: 45 }
                },
                y: {
                    min: 0,
                    max: Y_AXIS_MAX,
                    ticks: {
                        stepSize: 500
                    },
                    title: {
                        display: true,
                        text: 'Energy (mJ)'
                    }
                }
            }
        }
    });
}

// ===============================
// SIMULATE FOOTSTEP
// ===============================
async function simulateFootstep() {
    const btn = document.getElementById('simulateBtn');
    const originalText = btn.innerHTML;

    try {
        btn.disabled = true;
        btn.innerText = 'Simulating...';

        const res = await fetch('/simulate-step', { method: 'POST' });
        const result = await res.json();

        if (!result.success) {
            showNotification('error', 'Simulation failed');
            return;
        }

        // Add data to chart
        addChartPoint(`Step ${result.step}`, result.energy_mj);

        // Update stats visually
        incrementStats(result.energy_mj);

        // Add table row
        addTableRow(result);

        showNotification('success', `⚡ ${result.energy_mj} mJ generated`);

    } catch {
        showNotification('error', 'Server error');
    } finally {
        btn.disabled = false;
        btn.innerHTML = originalText;
    }
}

// ===============================
// LOAD DASHBOARD DATA (MANUAL)
// ===============================
async function loadDashboardData() {
    try {
        const range = document.getElementById('timeRange')?.value || 50;
        const limit = range === 'all' ? 1000 : range === '24h' ? 100 : 50;

        const res = await fetch(`/get-energy-data?limit=${limit}`);
        const data = await res.json();

        if (!data.success) return;

        // Update chart (trimmed)
        energyChart.data.labels = data.chart_data.labels.slice(-MAX_POINTS);
        energyChart.data.datasets[0].data = data.chart_data.energy.slice(-MAX_POINTS);
        energyChart.update('none');

        // Stats
        updateStatistics(data.statistics);

        // Table
        updateTable(data.recent_records);

    } catch {
        showNotification('error', 'Failed to load data');
    }
}

// ===============================
// CHART HELPERS
// ===============================
function addChartPoint(label, value) {
    energyChart.data.labels.push(label);
    energyChart.data.datasets[0].data.push(value);

    if (energyChart.data.labels.length > MAX_POINTS) {
        energyChart.data.labels.shift();
        energyChart.data.datasets[0].data.shift();
    }

    energyChart.update('none');
}

// ===============================
// UI HELPERS
// ===============================
function updateStatistics(stats) {
    document.getElementById('totalEnergy').textContent = `${stats.total_energy_mj} mJ`;
    document.getElementById('energyWh').textContent = `${stats.total_energy_wh} Wh`;
    document.getElementById('stepsToday').textContent = stats.total_steps;
    document.getElementById('avgEnergy').textContent = `${stats.avg_energy} mJ`;
    document.getElementById('totalSteps').textContent = `Total: ${stats.total_steps}`;
    document.getElementById('energyValue').textContent = `₹${stats.energy_value_inr}`;
}

function incrementStats(energy) {
    const el = document.getElementById('totalEnergy');
    const current = parseFloat(el.textContent) || 0;
    el.textContent = `${(current + energy).toFixed(2)} mJ`;
}

// ===============================
// TABLE
// ===============================
function updateTable(records) {
    const tbody = document.getElementById('dataTableBody');
    if (!records.length) {
        tbody.innerHTML = `<tr><td colspan="5">No data yet</td></tr>`;
        return;
    }

    tbody.innerHTML = records.slice(0, 10).map(r => `
        <tr>
            <td>${r.step}</td>
            <td>${formatTime(r.time)}</td>
            <td>${r.force}</td>
            <td>${r.displacement}</td>
            <td>${r.energy}</td>
        </tr>
    `).join('');
}

function addTableRow(data) {
    const tbody = document.getElementById('dataTableBody');
    const row = document.createElement('tr');

    row.innerHTML = `
        <td>${data.step}</td>
        <td>Just now</td>
        <td>—</td>
        <td>—</td>
        <td>${data.energy_mj}</td>
    `;

    tbody.prepend(row);
    while (tbody.children.length > 10) tbody.removeChild(tbody.lastChild);
}

// ===============================
// CLEAR DATA
// ===============================
async function clearAllData() {
    if (!confirm('Clear all data?')) return;

    await fetch('/clear-data', { method: 'POST' });

    energyChart.data.labels = [];
    energyChart.data.datasets[0].data = [];
    energyChart.update('none');

    document.getElementById('dataTableBody').innerHTML =
        `<tr><td colspan="5">No data</td></tr>`;

    showNotification('success', 'Data cleared');
}

// ===============================
// UTILITIES
// ===============================
function showNotification(type, msg) {
    const div = document.createElement('div');
    div.className = `notification ${type}`;
    div.textContent = msg;
    document.body.appendChild(div);
    setTimeout(() => div.remove(), 2500);
}

function formatTime(t) {
    return new Date(t).toLocaleTimeString();
}
