// =====================================
// Smart Tile Dashboard (NO GRAPH VERSION)
// Stable, Fast, Demo-Ready
// =====================================

document.addEventListener('DOMContentLoaded', () => {
    loadDashboardData();

    document.getElementById('simulateBtn')?.addEventListener('click', simulateFootstep);
    document.getElementById('clearDataBtn')?.addEventListener('click', clearAllData);
});

// -------------------------------------
// SIMULATE FOOTSTEP
// -------------------------------------
async function simulateFootstep() {
    const btn = document.getElementById('simulateBtn');
    const original = btn.innerText;

    try {
        btn.disabled = true;
        btn.innerText = 'Simulating...';

        const res = await fetch('/simulate-step', { method: 'POST' });
        const data = await res.json();

        if (!data.success) {
            showNotification('error', 'Simulation failed');
            return;
        }

        incrementStats(data.energy_mj);
        addTableRow(data);

        showNotification(
            'success',
            `⚡ Step ${data.step} → ${data.energy_mj} mJ`
        );

    } catch {
        showNotification('error', 'Server error');
    } finally {
        btn.disabled = false;
        btn.innerText = original;
    }
}

// -------------------------------------
// LOAD DASHBOARD DATA
// -------------------------------------
async function loadDashboardData() {
    try {
        const res = await fetch('/get-energy-data?limit=50');
        const data = await res.json();

        if (!data.success) return;

        updateStatistics(data.statistics);
        updateTable(data.recent_records);

    } catch {
        showNotification('error', 'Failed to load data');
    }
}

// -------------------------------------
// STATS
// -------------------------------------
function updateStatistics(stats) {
    document.getElementById('totalEnergy').textContent =
        `${stats.total_energy_mj} mJ`;

    document.getElementById('energyWh').textContent =
        `${stats.total_energy_wh} Wh`;

    document.getElementById('stepsToday').textContent =
        stats.total_steps;

    document.getElementById('avgEnergy').textContent =
        `${stats.avg_energy} mJ`;

    document.getElementById('totalSteps').textContent =
        `Total: ${stats.total_steps} steps`;

    document.getElementById('energyValue').textContent =
        `₹${stats.energy_value_inr}`;
}

function incrementStats(energy) {
    const el = document.getElementById('totalEnergy');
    const current = parseFloat(el.textContent) || 0;
    el.textContent = `${(current + energy).toFixed(2)} mJ`;
}

// -------------------------------------
// TABLE
// -------------------------------------
function updateTable(records) {
    const tbody = document.getElementById('dataTableBody');

    if (!records.length) {
        tbody.innerHTML =
            `<tr><td colspan="5">No data yet</td></tr>`;
        return;
    }

    tbody.innerHTML = records.slice(0, 10).map(r => `
        <tr>
            <td>${r.step}</td>
            <td>${new Date(r.time).toLocaleTimeString()}</td>
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
    while (tbody.children.length > 10) {
        tbody.removeChild(tbody.lastChild);
    }
}

// -------------------------------------
// CLEAR DATA
// -------------------------------------
async function clearAllData() {
    if (!confirm('Clear all data?')) return;

    await fetch('/clear-data', { method: 'POST' });

    document.getElementById('dataTableBody').innerHTML =
        `<tr><td colspan="5">No data</td></tr>`;

    showNotification('success', 'All data cleared');
}

// -------------------------------------
// NOTIFICATION
// -------------------------------------
function showNotification(type, message) {
    const n = document.createElement('div');
    n.className = `notification ${type}`;
    n.textContent = message;
    document.body.appendChild(n);
    setTimeout(() => n.remove(), 2500);
}
