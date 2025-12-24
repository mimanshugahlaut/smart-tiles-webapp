// Profile page functionality
document.addEventListener('DOMContentLoaded', function() {
    const profileForm = document.getElementById('profileForm');
    
    if (profileForm) {
        profileForm.addEventListener('submit', function(e) {
            const submitBtn = this.querySelector('button[type="submit"]');
            const btnText = submitBtn.querySelector('.btn-text');
            const btnLoader = submitBtn.querySelector('.btn-loader');
            
            submitBtn.disabled = true;
            btnText.style.display = 'none';
            btnLoader.style.display = 'inline-block';
        });
    }
    
    // Load energy statistics
    loadEnergyStats();
    
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

async function loadEnergyStats() {
    try {
        const response = await fetch('/get-dashboard-stats');
        const result = await response.json();
        
        if (result.success) {
            // Update Total Energy
            const totalEnergyEl = document.getElementById('profileTotalEnergy');
            if (totalEnergyEl) {
                totalEnergyEl.textContent = `${result.total_energy_mj} mJ`;
            }
            
            // Update Total Footsteps
            const totalStepsEl = document.getElementById('profileTotalSteps');
            if (totalStepsEl) {
                totalStepsEl.textContent = result.total_steps.toLocaleString();
            }
            
            // Update Average Energy
            const avgEnergyEl = document.getElementById('profileAvgEnergy');
            if (avgEnergyEl) {
                avgEnergyEl.textContent = `${result.avg_energy} mJ`;
            }
        } else {
            // Show zero values if no data
            document.getElementById('profileTotalEnergy').textContent = '0.00 mJ';
            document.getElementById('profileTotalSteps').textContent = '0';
            document.getElementById('profileAvgEnergy').textContent = '0.00 mJ';
        }
    } catch (error) {
        console.error('Failed to load energy stats:', error);
        // Set default values on error
        document.getElementById('profileTotalEnergy').textContent = '0.00 mJ';
        document.getElementById('profileTotalSteps').textContent = '0';
        document.getElementById('profileAvgEnergy').textContent = '0.00 mJ';
    }
}