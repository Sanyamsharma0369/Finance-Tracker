document.addEventListener('DOMContentLoaded', function() {
    // Sidebar Toggle
    const sidebarCollapse = document.getElementById('sidebarCollapse');
    const sidebar = document.getElementById('sidebar');
    
    if (sidebarCollapse && sidebar) {
        sidebarCollapse.addEventListener('click', function() {
            sidebar.classList.toggle('active');
        });
    }

    // Close sidebar on mobile when clicking outside
    document.addEventListener('click', function(event) {
        if (window.innerWidth <= 768 && sidebar && sidebar.classList.contains('active')) {
            if (!sidebar.contains(event.target) && !sidebarCollapse.contains(event.target)) {
                sidebar.classList.remove('active');
            }
        }
    });

    // Form Validation
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', function(event) {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            form.classList.add('was-validated');
        });
    });

    // Dynamic Form Fields
    const transactionType = document.getElementById('id_type');
    const categorySelect = document.getElementById('id_category');
    
    if (transactionType && categorySelect) {
        transactionType.addEventListener('change', function() {
            const selectedType = this.value;
            const categories = categorySelect.options;
            
            for (let option of categories) {
                if (option.dataset.type === selectedType) {
                    option.style.display = '';
                } else {
                    option.style.display = 'none';
                }
            }
        });
    }

    // Chart Responsiveness
    window.addEventListener('resize', function() {
        const charts = document.querySelectorAll('canvas');
        charts.forEach(chart => {
            if (chart.chart) {
                chart.chart.resize();
            }
        });
    });

    // Alert Auto-dismiss
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        setTimeout(() => {
            alert.classList.add('fade');
            setTimeout(() => alert.remove(), 150);
        }, 5000);
    });

    // Budget Progress Bar Animation
    const progressBars = document.querySelectorAll('.progress-bar');
    progressBars.forEach(bar => {
        const width = bar.style.width;
        bar.style.width = '0';
        setTimeout(() => {
            bar.style.width = width;
        }, 100);
    });

    // File Input Preview
    const fileInput = document.getElementById('id_receipt');
    if (fileInput) {
        fileInput.addEventListener('change', function() {
            const preview = document.getElementById('receipt-preview');
            if (preview && this.files && this.files[0]) {
                const reader = new FileReader();
                reader.onload = function(e) {
                    preview.src = e.target.result;
                    preview.style.display = 'block';
                };
                reader.readAsDataURL(this.files[0]);
            }
        });
    }
}); 