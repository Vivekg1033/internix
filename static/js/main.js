// static/js/main.js

document.addEventListener('DOMContentLoaded', function() {
    // Enable all tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'))
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl)
    });
    
    // Auto-hide alerts after 5 seconds
    setTimeout(function() {
        var alerts = document.querySelectorAll('.alert');
        alerts.forEach(function(alert) {
            var bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        });
    }, 5000);
    
    // Handle paid internship toggle
    var isPaidCheckbox = document.getElementById('is_paid');
    if (isPaidCheckbox) {
        isPaidCheckbox.addEventListener('change', function() {
            var salaryField = document.getElementById('salaryField');
            if (salaryField) {
                salaryField.style.display = this.checked ? 'block' : 'none';
            }
        });
    }
    
    // Add character counter for textareas
    var textareas = document.querySelectorAll('textarea[data-maxlength]');
    textareas.forEach(function(textarea) {
        var maxLength = textarea.getAttribute('data-maxlength');
        var counter = document.createElement('div');
        counter.className = 'form-text text-end';
        counter.innerHTML = textarea.value.length + '/' + maxLength;
        
        textarea.parentNode.appendChild(counter);
        
        textarea.addEventListener('input', function() {
            counter.innerHTML = this.value.length + '/' + maxLength;
            if (this.value.length > maxLength) {
                counter.style.color = 'red';
            } else {
                counter.style.color = '';
            }
        });
    });
    
    // Form validation
    var forms = document.querySelectorAll('.needs-validation');
    Array.from(forms).forEach(function(form) {
        form.addEventListener('submit', function(event) {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            form.classList.add('was-validated');
        }, false);
    });
});

// Function to format dates as "time ago"
function timeAgo(date) {
    var seconds = Math.floor((new Date() - date) / 1000);
    var interval = seconds / 31536000;
  
    if (interval > 1) {
        return Math.floor(interval) + " years ago";
    }
    interval = seconds / 2592000;
    if (interval > 1) {
        return Math.floor(interval) + " months ago";
    }
    interval = seconds / 86400;
    if (interval > 1) {
        return Math.floor(interval) + " days ago";
    }
    interval = seconds / 3600;
    if (interval > 1) {
        return Math.floor(interval) + " hours ago";
    }
    interval = seconds / 60;
    if (interval > 1) {
        return Math.floor(interval) + " minutes ago";
    }
    return Math.floor(seconds) + " seconds ago";
}

// Filter by location map
document.addEventListener('DOMContentLoaded', function() {
    var locationFilter = document.getElementById('location-filter');
    
    if (locationFilter) {
        locationFilter.addEventListener('change', function() {
            var value = this.value.toLowerCase();
            var internshipCards = document.querySelectorAll('.internship-card');
            
            internshipCards.forEach(function(card) {
                var location = card.getAttribute('data-location').toLowerCase();
                if (value === 'all' || location.includes(value)) {
                    card.style.display = '';
                } else {
                    card.style.display = 'none';
                }
            });
        });
    }
});

// Custom file input label
document.addEventListener('DOMContentLoaded', function() {
    var fileInputs = document.querySelectorAll('.custom-file-input');
    
    fileInputs.forEach(function(input) {
        input.addEventListener('change', function(e) {
            var fileName = this.files[0].name;
            var label = this.nextElementSibling;
            label.innerHTML = fileName;
        });
    });
});