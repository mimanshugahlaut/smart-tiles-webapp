// =====================================
// Smart Tile Dashboard (NO GRAPH VERSION)
// Stable, Backend-Synced, Demo-Ready
// =====================================

document.addEventListener('DOMContentLoaded', () => {
    loadDashboardData();

    document.getElementById('simulateBtn')?.addEventListener('click', simulateFootstep);
    document.getElementById('clearDataBtn')?.addEventListener('click', clearAllData);
});

// -------------------------------------
// SIMULATE FOOTSTEP (NO FRONTEND MATH)
// -------------------------------------
async function simulateFootstep() {
    const btn = document.getElementById('simulateBtn');
    const originalText = btn.innerText;

    try {
        btn.disabled = true;
        btn.innerText = 'Simulating...';

        const res = await fetch('/simulate-step', { method: 'POST' });
        const data = await res.json();

        if (!data.success) {
            showNotification('error', 'Simulation failed');
            return;
        }

        // ✅ Always reload backend data (single source of truth)
        await loadDashboardData();

        // Add latest row instantly for UX
        addTableRow(data);

        showNotification(
            'success',
            `⚡ Step ${data.step} → ${data.energy_mj} mJ`
        );

    } catch (err) {
        console.error(err);
        showNotification('error', 'Server error');
    } finally {
        btn.disabled = false;
        btn.innerText = originalText;
    }
}

// -------------------------------------
// LOAD DASHBOARD DATA (BACKEND ONLY)
// -------------------------------------
async function loadDashboardData() {
    try {
        const res = await fetch('/get-energy-data?limit=50');
        const data = await res.json();

        if (!data.success) return;

        updateStatistics(data.statistics);
        updateTable(data.recent_records);

        const recordCount = document.getElementById('recordCount');
        if (recordCount) {
            recordCount.textContent = `${data.statistics.total_steps} records`;
        }

    } catch (err) {
        console.error(err);
        showNotification('error', 'Failed to load dashboard data');
    }
}

// -------------------------------------
// STATISTICS (BACKEND VALUES ONLY)
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

// -------------------------------------
// TABLE (RECENT FOOTSTEPS)
// -------------------------------------
function updateTable(records) {
    const tbody = document.getElementById('dataTableBody');

    if (!records || records.length === 0) {
        tbody.innerHTML =
            `<tr><td colspan="4">No data yet. Click "Simulate Footstep".</td></tr>`;
        return;
    }

    tbody.innerHTML = records.slice(0, 10).map(r => `
        <tr>
            <td>${r.step}</td>
            <td>${r.force}</td>
            <td>${r.displacement}</td>
            <td>${r.energy}</td>
        </tr>
    `).join('');
}

// Add newest row instantly (UX only)
function addTableRow(data) {
    const tbody = document.getElementById('dataTableBody');

    const row = document.createElement('tr');
    row.innerHTML = `
        <td>${data.step}</td>
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
    if (!confirm('Are you sure you want to clear all data?')) return;

    try {
        await fetch('/clear-data', { method: 'POST' });
        await loadDashboardData();

        showNotification('success', 'All data cleared');

    } catch (err) {
        console.error(err);
        showNotification('error', 'Failed to clear data');
    }
}

// -------------------------------------
// NOTIFICATIONS
// -------------------------------------
function showNotification(type, message) {
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.textContent = message;

    document.body.appendChild(notification);

    setTimeout(() => {
        notification.remove();
    }, 2500);
}
