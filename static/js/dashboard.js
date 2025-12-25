let energyChart = null;

const MAX_POINTS = 20;
const Y_AXIS_MAX = 4000;

document.addEventListener('DOMContentLoaded', () => {
    initChart();
    loadDashboardData();

    document.getElementById('simulateBtn')?.addEventListener('click', simulateFootstep);
    document.getElementById('clearDataBtn')?.addEventListener('click', clearAllData);
    document.getElementById('timeRange')?.addEventListener('change', loadDashboardData);
});

// ===============================
// INITIALIZE CHART (LOCKED)
// ===============================
function initChart() {
    const ctx = document.getElementById('energyChart');
    if (!ctx) return;

    energyChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [{
                label: 'Energy (mJ)',
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
            parsing: false,
            plugins: {
                legend: { display: true }
            },
            scales: {
                x: {
                    bounds: 'ticks'
                },
                y: {
                    beginAtZero: true,
                    min: 0,
                    max: Y_AXIS_MAX,
                    grace: 0,
                    ticks: {
                        stepSize: 500
                    }
                }
            }
        }
    });
}

// ===============================
// FORCE Y-AXIS LOCK
// ===============================
function lockYAxis() {
    if (!energyChart) return;
    energyChart.options.scales.y.min = 0;
    energyChart.options.scales.y.max = Y_AXIS_MAX;
}

// ===============================
// SIMULATE STEP
// ===============================
async function simulateFootstep() {
    const btn = document.getElementById('simulateBtn');
    btn.disabled = true;
    btn.innerText = 'Simulating...';

    try {
        const res = await fetch('/simulate-step', { method: 'POST' });
        const data = await res.json();

        if (!data.success) throw new Error();

        const energy = Math.min(data.energy_mj, Y_AXIS_MAX);

        energyChart.data.labels.push(`Step ${data.step}`);
        energyChart.data.datasets[0].data.push(energy);

        if (energyChart.data.labels.length > MAX_POINTS) {
            energyChart.data.labels.shift();
            energyChart.data.datasets[0].data.shift();
        }

        lockYAxis();
        energyChart.update('none');

        addTableRow(data);
        incrementStats(energy);

        showNotification('success', `⚡ ${energy} mJ generated`);

    } catch {
        showNotification('error', 'Simulation failed');
    } finally {
        btn.disabled = false;
        btn.innerText = 'Simulate Footstep';
    }
}

// ===============================
// LOAD DATA
// ===============================
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

        lockYAxis();
        energyChart.update('none');

        updateStatistics(data.statistics);
        updateTable(data.recent_records);

    } catch {
        showNotification('error', 'Load failed');
    }
}

// ===============================
// HELPERS
// ===============================
function incrementStats(v) {
    const el = document.getElementById('totalEnergy');
    const curr = parseFloat(el.textContent) || 0;
    el.textContent = `${(curr + v).toFixed(2)} mJ`;
}

function updateStatistics(s) {
    document.getElementById('totalEnergy').textContent = `${s.total_energy_mj} mJ`;
    document.getElementById('energyWh').textContent = `${s.total_energy_wh} Wh`;
    document.getElementById('stepsToday').textContent = s.total_steps;
    document.getElementById('avgEnergy').textContent = `${s.avg_energy} mJ`;
    document.getElementById('totalSteps').textContent = `Total: ${s.total_steps}`;
    document.getElementById('energyValue').textContent = `₹${s.energy_value_inr}`;
}

function updateTable(records) {
    const body = document.getElementById('dataTableBody');
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

async function clearAllData() {
    await fetch('/clear-data', { method: 'POST' });
    energyChart.data.labels = [];
    energyChart.data.datasets[0].data = [];
    lockYAxis();
    energyChart.update('none');
}

function showNotification(type, msg) {
    const d = document.createElement('div');
    d.className = `notification ${type}`;
    d.textContent = msg;
    document.body.appendChild(d);
    setTimeout(() => d.remove(), 2500);
}
