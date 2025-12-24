// Form submission handling with loading states
document.addEventListener('DOMContentLoaded', function() {
    // Handle all auth forms - just show loading, let form submit normally
    const forms = ['loginForm', 'registerForm', 'forgotPasswordForm', 'resetPasswordForm'];
    
    forms.forEach(formId => {
        const form = document.getElementById(formId);
        if (form) {
            form.addEventListener('submit', function(e) {
                const submitBtn = this.querySelector('button[type="submit"]');
                if (submitBtn) {
                    const btnText = submitBtn.querySelector('.btn-text');
                    const btnLoader = submitBtn.querySelector('.btn-loader');
                    
                    // Show loading state
                    submitBtn.disabled = true;
                    if (btnText) btnText.style.display = 'none';
                    if (btnLoader) btnLoader.style.display = 'inline-block';
                }
                // Let the form submit naturally - don't prevent default
            });
        }
    });
    
    // Password strength indicator for register form
    const registerForm = document.getElementById('registerForm');
    if (registerForm) {
        const passwordInput = document.getElementById('password');
        const strengthDiv = document.getElementById('passwordStrength');
        
        if (passwordInput && strengthDiv) {
            passwordInput.addEventListener('input', function() {
                const password = this.value;
                if (password.length > 0) {
                    strengthDiv.style.display = 'block';
                    updatePasswordStrength(password, strengthDiv);
                } else {
                    strengthDiv.style.display = 'none';
                }
            });
        }
        
        // Password match validation
        const confirmPassword = document.getElementById('confirm_password');
        if (confirmPassword && passwordInput) {
            confirmPassword.addEventListener('input', function() {
                if (this.value && this.value !== passwordInput.value) {
                    this.setCustomValidity('Passwords do not match');
                } else {
                    this.setCustomValidity('');
                }
            });
        }
    }
    
    // Password match validation for reset form
    const resetForm = document.getElementById('resetPasswordForm');
    if (resetForm) {
        const passwordInput = document.getElementById('password');
        const confirmPassword = document.getElementById('confirm_password');
        
        if (passwordInput && confirmPassword) {
            confirmPassword.addEventListener('input', function() {
                if (this.value && this.value !== passwordInput.value) {
                    this.setCustomValidity('Passwords do not match');
                } else {
                    this.setCustomValidity('');
                }
            });
        }
    }
});

function updatePasswordStrength(password, strengthDiv) {
    let strength = 0;
    let strengthText = '';
    
    // Length check
    if (password.length >= 8) strength++;
    if (password.length >= 12) strength++;
    
    // Complexity checks
    if (/[a-z]/.test(password) && /[A-Z]/.test(password)) strength++;
    if (/[0-9]/.test(password)) strength++;
    if (/[^a-zA-Z0-9]/.test(password)) strength++;
    
    // Remove old classes
    strengthDiv.className = 'password-strength';
    
    // Apply strength class and text
    if (strength <= 2) {
        strengthDiv.classList.add('strength-weak');
        strengthText = 'Weak password';
    } else if (strength <= 4) {
        strengthDiv.classList.add('strength-medium');
        strengthText = 'Medium strength';
    } else {
        strengthDiv.classList.add('strength-strong');
        strengthText = 'Strong password';
    }
    
    const strengthTextEl = strengthDiv.querySelector('.strength-text');
    if (strengthTextEl) {
        strengthTextEl.textContent = strengthText;
    }
}

// Auto-hide alerts after 5 seconds
document.addEventListener('DOMContentLoaded', function() {
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        setTimeout(() => {
            alert.style.transition = 'opacity 0.5s ease';
            alert.style.opacity = '0';
            setTimeout(() => alert.remove(), 500);
        }, 5000);
    });
});