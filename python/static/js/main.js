// Main JavaScript file for Restaurant Inventory Management

document.addEventListener('DOMContentLoaded', function() {
    console.log('Restaurant Inventory Management System loaded!');
    
    // Set minimum date for expiry date inputs to today
    const expiryDateInputs = document.querySelectorAll('input[type="date"]');
    const today = new Date().toISOString().split('T')[0];
    
    expiryDateInputs.forEach(input => {
        if (input.id === 'expiry_date' && !input.value) {
            input.min = today;
        }
    });
    
    // Add visual indicators for items that are close to expiry
    const checkExpiryDates = () => {
        const rows = document.querySelectorAll('table tbody tr');
        const today = new Date();
        const oneWeekFromNow = new Date();
        oneWeekFromNow.setDate(today.getDate() + 7);
        
        rows.forEach(row => {
            const expiryDateCell = row.querySelector('td:nth-child(4)');
            if (expiryDateCell) {
                const expiryDate = new Date(expiryDateCell.textContent);
                if (expiryDate <= today) {
                    row.classList.add('expired');
                } else if (expiryDate <= oneWeekFromNow) {
                    row.classList.add('expiring-soon');
                }
            }
        });
    };
    
    // Check quantities against thresholds
    const checkThresholds = () => {
        const rows = document.querySelectorAll('table tbody tr');
        
        rows.forEach(row => {
            const quantityCell = row.querySelector('td:nth-child(3)');
            const thresholdCell = row.querySelector('td:nth-child(5)');
            
            if (quantityCell && thresholdCell) {
                const quantity = parseFloat(quantityCell.textContent);
                const threshold = parseFloat(thresholdCell.textContent);
                
                if (quantity <= threshold) {
                    row.classList.add('below-threshold');
                }
            }
        });
    };
    
    // Run checks if we're on the orders page
    if (window.location.pathname.includes('/orders') && !window.location.pathname.includes('/add')) {
        checkExpiryDates();
        checkThresholds();
    }
    
    // Form validation for add/edit order forms
    const orderForm = document.querySelector('form[action*="/orders"]');
    if (orderForm) {
        orderForm.addEventListener('submit', function(e) {
            const quantityInput = document.getElementById('quantity');
            const thresholdInput = document.getElementById('autobuy_threshold');
            
            if (quantityInput && thresholdInput) {
                const quantity = parseFloat(quantityInput.value);
                const threshold = parseFloat(thresholdInput.value);
                
                if (threshold < 0) {
                    e.preventDefault();
                    alert('Auto-buy threshold cannot be negative.');
                    return;
                }
                
                if (quantity < 0) {
                    e.preventDefault();
                    alert('Quantity cannot be negative.');
                    return;
                }
            }
        });
    }
});