/* =====================================================
   auth.js — Auth page logic (password strength, validation)
   ===================================================== */

'use strict';

// =====================================================
// Password Strength Checker
// =====================================================
function checkPasswordStrength(password) {
  let score = 0;
  const checks = {
    length:    password.length >= 8,
    longer:    password.length >= 12,
    lowercase: /[a-z]/.test(password),
    uppercase: /[A-Z]/.test(password),
    number:    /\d/.test(password),
    symbol:    /[!@#$%^&*()_+\-=\[\]{}|;:,.<>?]/.test(password),
  };

  if (checks.length)     score++;
  if (checks.longer)     score++;
  if (checks.lowercase)  score++;
  if (checks.uppercase)  score++;
  if (checks.number)     score++;
  if (checks.symbol)     score++;

  let level, label, pct;

  if (score <= 2) {
    level = 'weak';   label = '🔴 Weak';    pct = 25;
  } else if (score === 3) {
    level = 'fair';   label = '🟠 Fair';    pct = 50;
  } else if (score <= 4) {
    level = 'good';   label = '🟡 Good';    pct = 75;
  } else {
    level = 'strong'; label = '🟢 Strong';  pct = 100;
  }

  return { level, label, pct };
}

function initPasswordStrength(inputId, wrapId, barId, labelId) {
  const input = document.getElementById(inputId);
  const wrap  = document.getElementById(wrapId);
  const bar   = document.getElementById(barId);
  const label = document.getElementById(labelId);

  if (!input || !wrap || !bar || !label) return;

  input.addEventListener('input', () => {
    const val = input.value;
    if (!val) {
      wrap.style.display = 'none';
      return;
    }
    wrap.style.display = 'block';
    const { level, label: lbl, pct } = checkPasswordStrength(val);
    bar.style.width = pct + '%';
    bar.className = `strength-bar-fill ${level}`;
    label.textContent = lbl;
  });
}

// =====================================================
// Password Match Indicator
// =====================================================
function initPasswordMatch(pwId, confirmId, indicatorId) {
  const pw      = document.getElementById(pwId);
  const confirm = document.getElementById(confirmId);
  const ind     = document.getElementById(indicatorId);

  if (!pw || !confirm || !ind) return;

  function check() {
    const cVal = confirm.value;
    if (!cVal) { ind.style.display = 'none'; return; }
    ind.style.display = 'block';
    if (pw.value === cVal) {
      ind.textContent = '✓ Passwords match';
      ind.className = 'match-indicator match';
    } else {
      ind.textContent = '✕ Passwords do not match';
      ind.className = 'match-indicator mismatch';
    }
  }

  pw.addEventListener('input', check);
  confirm.addEventListener('input', check);
}

// =====================================================
// Auto-init on page load
// =====================================================
document.addEventListener('DOMContentLoaded', () => {

  // --- Register page ---
  if (document.getElementById('registerForm')) {
    initPasswordStrength('password', 'strengthWrap', 'strengthBar', 'strengthLabel');
    initPasswordMatch('password', 'confirm_password', 'matchIndicator');
  }

  // --- Reset password page ---
  if (document.getElementById('resetForm')) {
    initPasswordStrength('password', 'strengthWrap', 'strengthBar', 'strengthLabel');
    initPasswordMatch('password', 'confirm_password', 'matchIndicator');
  }

  // --- Settings page (change password) ---
  if (document.getElementById('changePasswordForm')) {
    initPasswordStrength('new_password', 'settingsStrengthWrap', 'settingsStrengthBar', 'settingsStrengthLabel');
    initPasswordMatch('new_password', 'confirm_password', 'settingsMatchIndicator');

    document.getElementById('changePasswordForm').addEventListener('submit', function() {
      const btn = document.getElementById('changePwBtn');
      if (btn) {
        btn.innerHTML = '<span class="spinner" style="border-color:rgba(255,255,255,0.2);border-top-color:#fff;"></span><span>Saving…</span>';
        btn.disabled = true;
      }
    });
  }
});