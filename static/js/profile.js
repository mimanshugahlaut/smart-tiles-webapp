/* =====================================================
   profile.js — Profile page logic
   ===================================================== */

'use strict';

document.addEventListener('DOMContentLoaded', () => {

  // Track form changes to warn on unsaved navigate
  const form = document.getElementById('profileForm');
  if (!form) return;

  let isDirty = false;

  const inputs = form.querySelectorAll('input:not([readonly])');
  inputs.forEach(input => {
    input.dataset.original = input.value;
    input.addEventListener('input', () => {
      isDirty = input.value !== input.dataset.original;
    });
  });

  form.addEventListener('submit', () => {
    isDirty = false;
    const btn = document.getElementById('saveProfileBtn');
    if (btn) {
      btn.innerHTML = '<span class="spinner" style="border-color:rgba(255,255,255,0.2);border-top-color:#fff;"></span><span>Saving…</span>';
      btn.disabled = true;
    }
  });

  window.addEventListener('beforeunload', (e) => {
    if (isDirty) {
      e.preventDefault();
      e.returnValue = '';
    }
  });

});