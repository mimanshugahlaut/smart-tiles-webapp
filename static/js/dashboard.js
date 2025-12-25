// ==================================================
// Smart Tile Dashboard (FINAL – VISUALLY LOCKED)
// Chart.js v4 – No expansion, no upscaling
// ==================================================

let energyChart = null;

const MAX_POINTS = 20;
const Y_AXIS_MAX = 4000;

// --------------------------------------------------
// PLUGIN: HARD LOCK Y-AXIS (CRITICAL FIX)
// --------------------------------------------------
const lockYAxisPlugin = {
    id: 'lockYAxis',
    afterBuildTicks(chart) {
        const y = chart.scales.y;
        if (!y) return;

        y.min = 0;
        y.max = Y_AXIS_MAX;
    }
};

// --------------------------------------------------
// INIT
// --------------------------------------------------
document.addEventListener('DOMContentLoaded', () => {
    initChart();
    loadDashboardData();

    document.getElementById('simulateBtn')?.addEventListener('click', simulateFootstep);
    document.getElementById('clearDataBtn')?.addEventListener('click', clearAllData);
    document.getElementById('timeRange')?.addEventListener('change', loadDashboardData);
});

// --------------------------------------------------
// CHART INITIALIZATION (LOCKED SCALE)
// --------------------------------------------------
function initChart() {
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
            responsive: true,
            animation: false,
            maintainAspectRatio: false,
            parsing: false,

            scales: {
                x: {
                    ticks: {
                        maxRotation: 45,
                        autoSkip: true
                    }
                },
                y: {
                    min: 0,
                    max: Y_AXIS_MAX,
                    ticks: {
                        stepSize: 500,
                        autoSkip: false
                    },
                    grid: {
                        drawBorder: true
                    },
                    title: {
                        display: true,
                        text: 'Energy (mJ)'
                    }
                }
            },

            plugins: {
                legend: {
                    display: true
                }
            }
        },
        plugins: [lockYAxisPlugin] // 🔒 HARD LOCK
    });
}

// --------------------------------------------------
// SIMULATE FOOTSTEP
// --------------------------------------------------
async function simulateFootstep() {
    const btn = document.getElementById('simulateBtn');
    btn.disabled = true;
    btn.innerText = 'Simulating…';

    try {
        const res = await fetch('/simulate-step', { method: 'POST' });
        const data = await res.json();

        if (!data.success) throw new Error();

        const safeEnergy = Math.min(data.energy_mj, Y_AXIS_MAX);

        energyChart.data.labels.push(`Step ${data.step}`);
        energyChart.data.datasets[0].data.push(safeEnergy);

        if (energyChart.data.labels.length > MAX_POINTS) {
            energyChart.data.labels.shift();
            energyChart.data.datasets[0].data.shift();
        }

        energyChart.update('none');

        addTableRow(data);
        incrementStats(safeEnergy);

        showNotification('success', `⚡ ${safeEnergy} mJ generated`);

    } catch {
        showNotification('error', 'Simulation failed');
    } finally {
        btn.disabled = false;
        btn.innerText = 'Simulate Footstep';
    }
}

// --------------------------------------------------
// LOAD DASHBOARD DATA
// --------------------------------------------------
async function loadDashboardData() {
    try {
        const res = await fetch('/get-energy-data?limit=50');
        const data = await res.json();
        if (!data.success) return;

        energyChart.data.labels =
            data.chart_data.labels.slice(-MAX_POINTS);

        energyChart.data.datasets[0].data =
            data.chart_data.energy
                .slice(-MAX_POINTS)
                .map(v => Math.min(v, Y_AXIS_MAX));

        energyChart.update('none');

        updateStatistics(data.statistics);
        updateTable(data.recent_records);

    } catch {
        showNotification('error', 'Failed to load data');
    }
}

// --------------------------------------------------
// UI HELPERS
// --------------------------------------------------
function updateStatistics(s) {
    document.getElementById('totalEnergy').textContent = `${s.total_energy_mj} mJ`;
    document.getElementById('energyWh').textContent = `${s.total_energy_wh} Wh`;
    document.getElementById('stepsToday').textContent = s.total_steps;
    document.getElementById('avgEnergy').textContent = `${s.avg_energy} mJ`;
    document.getElementById('totalSteps').textContent = `Total: ${s.total_steps}`;
    document.getElementById('energyValue').textContent = `₹${s.energy_value_inr}`;
}

function incrementStats(v) {
    const el = document.getElementById('totalEnergy');
    const curr = parseFloat(el.textContent) || 0;
    el.textContent = `${(curr + v).toFixed(2)} mJ`;
}

// --------------------------------------------------
// TABLE
// --------------------------------------------------
function updateTable(records) {
    const body = document.getElementById('dataTableBody');

    if (!records.length) {
        body.innerHTML = `<tr><td colspan="5">No data yet</td></tr>`;
        return;
    }

    body.innerHTML = records.slice(0, 10).map(r => `
        <tr>
            <td>${r.step}</td>
            <td>${new Date(r.time).toLocaleTimeString()}</td>
            <td>${r.force}</td>
            <td>${r.displacement}</td>
            <td>${r.energy}</td>
        </tr>
    `).join('');
}

function addTableRow(d) {
    const body = document.getElementById('dataTableBody');
    const row = document.createElement('tr');

    row.innerHTML = `
        <td>${d.step}</td>
        <td>Just now</td>
        <td>—</td>
        <td>—</td>
        <td>${Math.min(d.energy_mj, Y_AXIS_MAX)}</td>
    `;

    body.prepend(row);
    while (body.children.length > 10) body.lastChild.remove();
}

// --------------------------------------------------
// CLEAR DATA
// --------------------------------------------------
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

// --------------------------------------------------
// NOTIFICATIONS
// --------------------------------------------------
function showNotification(type, msg) {
    const n = document.createElement('div');
    n.className = `notification ${type}`;
    n.textContent = msg;
    document.body.appendChild(n);
    setTimeout(() => n.remove(), 2500);
}
