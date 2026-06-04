/* =====================================================
   dashboard.js — Energy Dashboard Logic + Chart.js
   ===================================================== */

'use strict';

// =====================================================
// State
// =====================================================
let energyChart = null;
let isSimulating = false;

// =====================================================
// DOM References
// =====================================================
const statTotalEnergy  = document.getElementById('statTotalEnergy');
const statEnergyWh     = document.getElementById('statEnergyWh');
const statTotalSteps   = document.getElementById('statTotalSteps');
const statStepsSub     = document.getElementById('statStepsSub');
const statAvgEnergy    = document.getElementById('statAvgEnergy');
const statEnergyValue  = document.getElementById('statEnergyValue');
const simulateBtn      = document.getElementById('simulateBtn');
const simulateResult   = document.getElementById('simulateResult');
const clearDataBtn     = document.getElementById('clearDataBtn');
const refreshBtn       = document.getElementById('refreshBtn');
const tableBody        = document.getElementById('tableBody');
const recordBadge      = document.getElementById('recordBadge');
const chartEmptyMsg    = document.getElementById('chartEmpty');

// =====================================================
// Animated Counter
// =====================================================
function animateValue(element, start, end, suffix, decimals = 0, duration = 500) {
  if (!element) return;
  const range = end - start;
  const startTime = performance.now();

  function update(now) {
    const elapsed = now - startTime;
    const progress = Math.min(elapsed / duration, 1);
    const eased = 1 - Math.pow(1 - progress, 3); // ease-out cubic
    const current = start + range * eased;
    element.textContent = current.toFixed(decimals) + suffix;
    element.classList.remove('stat-value-animate');
    void element.offsetWidth;
    element.classList.add('stat-value-animate');
    if (progress < 1) requestAnimationFrame(update);
  }
  requestAnimationFrame(update);
}

// =====================================================
// Update Stats UI
// =====================================================
function updateStats(stats) {
  if (!stats) return;

  const prevSteps  = parseInt(statTotalSteps.dataset.val  || '0');
  const prevEnergy = parseFloat(statTotalEnergy.dataset.val || '0');

  statTotalEnergy.dataset.val  = stats.total_energy_mj;
  statTotalSteps.dataset.val   = stats.total_steps;

  animateValue(statTotalEnergy, prevEnergy, stats.total_energy_mj, ' mJ', 2);
  statEnergyWh.textContent = stats.total_energy_wh.toFixed(8) + ' Wh';

  animateValue(statTotalSteps, prevSteps, stats.total_steps, '', 0);
  statStepsSub.textContent = stats.total_steps > 0
    ? `${stats.total_steps} step${stats.total_steps !== 1 ? 's' : ''} recorded`
    : 'Start stepping!';

  animateValue(statAvgEnergy, 0, stats.avg_energy, ' mJ', 2);
  statEnergyValue.textContent = '₹' + stats.energy_value_inr.toFixed(6);
}

// =====================================================
// Update Table
// =====================================================
function updateTable(records) {
  recordBadge.textContent = records.length + ' records';

  if (!records.length) {
    tableBody.innerHTML = `
      <tr class="empty-row">
        <td colspan="5">No data yet. Click "Step on Tile" to get started!</td>
      </tr>`;
    return;
  }

  tableBody.innerHTML = records.map(r => {
    const time = r.timestamp
      ? new Date(r.timestamp).toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' })
      : '—';
    return `
      <tr>
        <td class="step-num">#${r.step}</td>
        <td>${r.force} N</td>
        <td>${r.displacement} mm</td>
        <td class="energy-val">${r.energy} mJ</td>
        <td style="color:var(--text-muted);font-size:0.8rem;">${time}</td>
      </tr>`;
  }).join('');
}

// =====================================================
// Chart.js Setup
// =====================================================
function initChart() {
  const ctx = document.getElementById('energyChart')?.getContext('2d');
  if (!ctx) return null;

  Chart.defaults.color = '#64748b';
  Chart.defaults.font.family = "'Inter', system-ui, sans-serif";

  const gradient = ctx.createLinearGradient(0, 0, 0, 280);
  gradient.addColorStop(0, 'rgba(0, 240, 255, 0.3)');
  gradient.addColorStop(1, 'rgba(0, 240, 255, 0.01)');

  return new Chart(ctx, {
    type: 'line',
    data: {
      labels: [],
      datasets: [{
        label: 'Energy (mJ)',
        data: [],
        borderColor: '#00f0ff',
        backgroundColor: gradient,
        borderWidth: 2.5,
        fill: true,
        tension: 0.45,
        pointBackgroundColor: '#00f0ff',
        pointBorderColor: '#090d18',
        pointBorderWidth: 2,
        pointRadius: 5,
        pointHoverRadius: 7,
        pointHoverBackgroundColor: '#fff',
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: {
        mode: 'index',
        intersect: false,
      },
      plugins: {
        legend: { display: false },
        tooltip: {
          backgroundColor: 'rgba(9, 13, 24, 0.95)',
          borderColor: 'rgba(0, 240, 255, 0.3)',
          borderWidth: 1,
          titleColor: '#f1f5f9',
          bodyColor: '#00f0ff',
          padding: 12,
          cornerRadius: 10,
          callbacks: {
            label: ctx => ` ${ctx.parsed.y.toFixed(2)} mJ`
          }
        }
      },
      scales: {
        x: {
          grid: { color: 'rgba(255,255,255,0.04)' },
          ticks: {
            color: '#475569',
            font: { size: 11 },
            maxTicksLimit: 10,
          }
        },
        y: {
          grid: { color: 'rgba(255,255,255,0.04)' },
          ticks: {
            color: '#475569',
            font: { size: 11 },
            callback: v => v.toFixed(0) + ' mJ'
          },
          beginAtZero: true,
        }
      },
      animation: {
        duration: 400,
        easing: 'easeOutCubic',
      }
    }
  });
}

// =====================================================
// Update Chart
// =====================================================
function updateChart(labels, data) {
  const isEmpty = !labels.length;
  chartEmptyMsg.style.display = isEmpty ? 'flex' : 'none';

  if (!energyChart) return;

  energyChart.data.labels = labels;
  energyChart.data.datasets[0].data = data;
  energyChart.update('active');
}

// =====================================================
// Load Dashboard Data
// =====================================================
async function loadDashboardData(silent = false) {
  try {
    const [energyRes, chartRes] = await Promise.all([
      fetch('/get-energy-data'),
      fetch('/get-chart-data')
    ]);

    const energyJson = await energyRes.json();
    const chartJson  = await chartRes.json();

    if (energyJson.success) {
      updateStats(energyJson.statistics);
      updateTable(energyJson.recent_records);
    }

    if (chartJson.success) {
      updateChart(chartJson.labels, chartJson.energy);
    }

  } catch (err) {
    if (!silent) console.error('Failed to load data:', err);
  }
}

// =====================================================
// Simulate Step
// =====================================================
async function simulateStep() {
  if (isSimulating) return;
  isSimulating = true;

  // Button animation
  simulateBtn.classList.add('rippling');
  simulateBtn.disabled = true;
  simulateResult.textContent = '';

  const origContent = simulateBtn.innerHTML;
  simulateBtn.innerHTML = `
    <span class="spinner" style="border-color:rgba(0,0,0,0.2);border-top-color:#000;"></span>
    Generating…`;

  try {
    const res = await fetch('/simulate-step', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' }
    });
    const data = await res.json();

    if (data.success) {
      simulateResult.textContent =
        `Step #${data.step} — ${data.energy_mj} mJ (Force: ${data.force}N · Displacement: ${data.displacement}mm)`;

      await loadDashboardData(true);
      showToast(`⚡ Step #${data.step}: ${data.energy_mj} mJ generated!`, 'success', 3000);
    }
  } catch (err) {
    showToast('Failed to simulate step. Please try again.', 'error');
  } finally {
    simulateBtn.innerHTML = origContent;
    simulateBtn.disabled = false;
    isSimulating = false;

    setTimeout(() => {
      simulateBtn.classList.remove('rippling');
    }, 700);
  }
}

// =====================================================
// Clear Data
// =====================================================
function clearData() {
  showConfirm(
    'Clear All Data',
    'This will permanently delete all your energy records. This cannot be undone.',
    async () => {
      try {
        const res = await fetch('/clear-data', { method: 'POST' });
        const data = await res.json();
        if (data.success) {
          await loadDashboardData(true);
          simulateResult.textContent = '';
          showToast('All energy data cleared.', 'info');
        }
      } catch {
        showToast('Failed to clear data.', 'error');
      }
    }
  );
}

// =====================================================
// Init
// =====================================================
document.addEventListener('DOMContentLoaded', () => {
  energyChart = initChart();
  loadDashboardData();

  simulateBtn?.addEventListener('click', simulateStep);
  clearDataBtn?.addEventListener('click', clearData);
  refreshBtn?.addEventListener('click', () => {
    loadDashboardData();
    showToast('Data refreshed', 'info', 1500);
  });
});
