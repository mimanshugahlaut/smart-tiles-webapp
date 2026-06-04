/* =====================================================
   settings.js — Settings page logic
   ===================================================== */

'use strict';

document.addEventListener('DOMContentLoaded', () => {

  // ===== Clear Data Button (Danger Zone) =====
  const clearDataBtn = document.getElementById('clearDataBtn');
  if (clearDataBtn) {
    clearDataBtn.addEventListener('click', () => {
      showConfirm(
        'Clear All Energy Data',
        'This will permanently delete all your footstep records and cannot be undone.',
        async () => {
          clearDataBtn.disabled = true;
          clearDataBtn.innerHTML = '<span class="spinner spinner-light"></span> Clearing…';

          try {
            const res = await fetch('/clear-data', { method: 'POST' });
            const data = await res.json();

            if (data.success) {
              showToast('All energy data cleared successfully.', 'success');
              // Reload to update step count in status card
              setTimeout(() => window.location.reload(), 1500);
            } else {
              showToast('Failed to clear data.', 'error');
              clearDataBtn.disabled = false;
              clearDataBtn.innerHTML = '🗑️ Clear Data';
            }
          } catch {
            showToast('An error occurred. Please try again.', 'error');
            clearDataBtn.disabled = false;
            clearDataBtn.innerHTML = '🗑️ Clear Data';
          }
        }
      );
    });
  }

});