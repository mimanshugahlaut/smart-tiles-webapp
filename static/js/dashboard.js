// Dashboard functionality - Optimized for cloud deployment
let energyChart = null;

document.addEventListener('DOMContentLoaded', function () {
    // Initialize chart only once
    initializeChart();

    // Initial load (only once)
    loadDashboardData();

    // Button listeners
    const simulateBtn = document.getElementById('simulateBtn');
    const clearDataBtn = document.getElementById('clearDataBtn');
    const timeRange = document.getElementById('timeRange');

    if (simulateBtn) simulateBtn.addEventListener('click', simulateFootstep);
    if (clearDataBtn) clearDataBtn.addEventListener('click', clearAllData);
    if (timeRange) timeRange.addEventListener('change', loadDashboardData);
});

// --------------------------------------------------
// CHART INITIALIZATION (NO ANIMATION = FAST)
// --------------------------------------------------
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
                legend: { display: true },
                tooltip: { intersect: false }
            },
            scales: {
                y: { beginAtZero: true },
                x: { ticks: { maxRotation: 45 } }
            }
        }
    });
}

// --------------------------------------------------
// SIMULATE FOOTSTEP (NO EXTRA API CALLS)
// --------------------------------------------------
async function simulateFootstep() {
    const btn = document.getElementById('simulateBtn');
    const originalText = btn.innerHTML;

    try {
        btn.disabled = true;
        btn.innerText = "Simulating...";

        const response = await fetch('/simulate-step', { method: 'POST' });
        const result = await response.json();

        if (!result.success) {
            showNotification('error', 'Simulation failed');
            return;
        }

        // Update UI directly (NO reload)
        addTableRow(result);
        incrementStats(result.energy_mj);

        showNotification(
            'success',
            `⚡ Step ${result.step} → ${result.energy_mj} mJ`
        );

    } catch {
        showNotification('error', 'Server error');
    } finally {
        btn.disabled = false;
        btn.innerHTML = originalText;
    }
}

// --------------------------------------------------
// LOAD DASHBOARD DATA (MANUAL ONLY)
// --------------------------------------------------
async function loadDashboardData() {
    try {
        const range = document.getElementById('timeRange')?.value || 50;
        const limit = range === 'all' ? 1000 : range === '24h' ? 100 : 50;

        const res = await fetch(`/get-energy-data?limit=${limit}`);
        const data = await res.json();

        if (!data.success) return;

        // Chart update (fast)
        energyChart.data.labels = data.chart_data.labels;
        energyChart.data.datasets[0].data = data.chart_data.energy;
        energyChart.update('none');

        // Stats
        updateStatistics(data.statistics);

        // Table
        updateTable(data.recent_records);

    } catch {
        showNotification('error', 'Failed to load data');
    }
}

// --------------------------------------------------
// UI UPDATE HELPERS
// --------------------------------------------------
function updateStatistics(stats) {
    document.getElementById('totalEnergy').textContent = `${stats.total_energy_mj} mJ`;
    document.getElementById('energyWh').textContent = `${stats.total_energy_wh} Wh`;
    document.getElementById('stepsToday').textContent = stats.total_steps;
    document.getElementById('avgEnergy').textContent = `${stats.avg_energy} mJ`;
    document.getElementById('totalSteps').textContent = `Total: ${stats.total_steps}`;
    document.getElementById('energyValue').textContent = `₹${stats.energy_value_inr}`;
}

function incrementStats(energy) {
    const totalEnergyEl = document.getElementById('totalEnergy');
    const current = parseFloat(totalEnergyEl.textContent) || 0;
    totalEnergyEl.textContent = `${(current + energy).toFixed(2)} mJ`;
}

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
// UTILS
// --------------------------------------------------
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
