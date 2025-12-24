// Settings page functionality
document.addEventListener('DOMContentLoaded', function() {
    const changePasswordForm = document.getElementById('changePasswordForm');
    const deleteAccountForm = document.getElementById('deleteAccountForm');
    
    // Handle password change form
    if (changePasswordForm) {
        const newPassword = document.getElementById('new_password');
        const confirmPassword = document.getElementById('confirm_password');
        
        confirmPassword.addEventListener('input', function() {
            if (this.value && this.value !== newPassword.value) {
                this.setCustomValidity('Passwords do not match');
            } else {
                this.setCustomValidity('');
            }
        });
        
        changePasswordForm.addEventListener('submit', function(e) {
            const submitBtn = this.querySelector('button[type="submit"]');
            const btnText = submitBtn.querySelector('.btn-text');
            const btnLoader = submitBtn.querySelector('.btn-loader');
            
            submitBtn.disabled = true;
            btnText.style.display = 'none';
            btnLoader.style.display = 'inline-block';
        });
    }
    
    // Handle delete account form
    if (deleteAccountForm) {
        deleteAccountForm.addEventListener('submit', function(e) {
            const submitBtn = this.querySelector('button[type="submit"]');
            const btnText = submitBtn.querySelector('.btn-text');
            const btnLoader = submitBtn.querySelector('.btn-loader');
            
            submitBtn.disabled = true;
            btnText.style.display = 'none';
            btnLoader.style.display = 'inline-block';
        });
    }
    
    // Auto-hide alerts
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        setTimeout(() => {
            alert.style.transition = 'opacity 0.5s ease';
            alert.style.opacity = '0';
            setTimeout(() => alert.remove(), 500);
        }, 5000);
    });
});

// Modal functions
function showDeleteModal() {
    const modal = document.getElementById('deleteModal');
    modal.classList.add('show');
    document.body.style.overflow = 'hidden';
}

function closeDeleteModal() {
    const modal = document.getElementById('deleteModal');
    modal.classList.remove('show');
    document.body.style.overflow = 'auto';
    
    // Clear password field
    const passwordField = document.getElementById('delete_password');
    if (passwordField) {
        passwordField.value = '';
    }
}

// Close modal on outside click
document.addEventListener('click', function(e) {
    const modal = document.getElementById('deleteModal');
    if (e.target === modal) {
        closeDeleteModal();
    }
});

// Close modal on escape key
document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape') {
        closeDeleteModal();
    }
});