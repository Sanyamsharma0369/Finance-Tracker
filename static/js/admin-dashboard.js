/**
 * Admin Dashboard JavaScript
 * Enhances the admin dashboard with interactive charts, data filtering, and modern interactions
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialize statistics card animations
    initStatsCardsAnimation();
    
    // Initialize interactive charts
    initCharts();
    
    // Setup system logs refresh
    setupSystemLogsRefresh();
    
    // Initialize tooltips and popovers
    initTooltips();

    // Initialize diagnostics modal
    setupDiagnosticsModal();
    
    // Initialize system load and server traffic charts
    initSystemLoadChart();
    initServerTrafficChart();
});

// Function to animate stats cards with a staggered delay
function initStatsCardsAnimation() {
    const statsCards = document.querySelectorAll('.stats-card');
    
    statsCards.forEach((card, index) => {
        setTimeout(() => {
            card.classList.add('fade-in');
        }, 100 * (index + 1));
    });
}

// Function to initialize dashboard charts
function initCharts() {
    // Revenue chart (example using Chart.js)
    if (document.getElementById('revenueChart')) {
        const ctx = document.getElementById('revenueChart').getContext('2d');
        const revenueChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'],
                datasets: [{
                    label: 'Monthly Revenue',
                    data: [5000, 8000, 6000, 9000, 10000, 12000, 11000, 13000, 14000, 15000, 13500, 17000],
                    borderColor: '#4e73df',
                    backgroundColor: 'rgba(78, 115, 223, 0.1)',
                    borderWidth: 2,
                    pointBackgroundColor: '#4e73df',
                    tension: 0.3
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                let label = context.dataset.label || '';
                                if (label) {
                                    label += ': ';
                                }
                                if (context.parsed.y !== null) {
                                    label += '₹' + context.parsed.y.toLocaleString('en-IN');
                                }
                                return label;
                            }
                        }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        grid: {
                            color: 'rgba(0, 0, 0, 0.05)'
                        },
                        ticks: {
                            callback: function(value, index, values) {
                                return '₹' + value.toLocaleString('en-IN');
                            }
                        }
                    },
                    x: {
                        grid: {
                            display: false
                        }
                    }
                }
            }
        });
    }

    // User activity chart
    if (document.getElementById('userActivityChart')) {
        const ctx = document.getElementById('userActivityChart').getContext('2d');
        const userActivityChart = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
                datasets: [{
                    label: 'Daily Active Users',
                    data: [320, 450, 380, 490, 550, 310, 280],
                    backgroundColor: '#36b9cc',
                    borderRadius: 4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        grid: {
                            color: 'rgba(0, 0, 0, 0.05)'
                        }
                    },
                    x: {
                        grid: {
                            display: false
                        }
                    }
                }
            }
        });
    }
}

// Function to refresh system logs every minute
function setupSystemLogsRefresh() {
    const systemLogsContainer = document.getElementById('systemLogs');
    
    if (systemLogsContainer) {
        // Initial load
        fetchSystemLogs();
        
        // Set up interval for refreshing
        setInterval(fetchSystemLogs, 60000);
    }
    
    function fetchSystemLogs() {
        // In a real application, this would be an API call
        // For demo purposes, we'll simulate with random logs
        const dummyLogs = [
            { type: 'info', message: 'User login successful', time: '2 minutes ago' },
            { type: 'warning', message: 'High CPU usage detected', time: '5 minutes ago' },
            { type: 'danger', message: 'Failed database backup', time: '10 minutes ago' },
            { type: 'success', message: 'Payment processed successfully', time: '15 minutes ago' },
            { type: 'info', message: 'System update available', time: '20 minutes ago' }
        ];
        
        // Randomly select 3-5 logs to display
        const logCount = Math.floor(Math.random() * 3) + 3;
        const selectedLogs = [];
        
        for (let i = 0; i < logCount; i++) {
            const randomIndex = Math.floor(Math.random() * dummyLogs.length);
            selectedLogs.push(dummyLogs[randomIndex]);
        }
        
        // Update the logs in the DOM
        systemLogsContainer.innerHTML = '';
        
        selectedLogs.forEach(log => {
            const logItem = document.createElement('div');
            logItem.className = `log-item bg-${log.type}-soft mb-2 p-2 rounded`;
            logItem.innerHTML = `
                <div class="d-flex justify-content-between align-items-center">
                    <span>${log.message}</span>
                    <small class="text-muted">${log.time}</small>
                </div>
            `;
            systemLogsContainer.appendChild(logItem);
        });
    }
}

// Function to initialize tooltips and popovers
function initTooltips() {
    // Add hover effect for cards with data attributes
    const hoverCards = document.querySelectorAll('[data-hover="true"]');
    
    hoverCards.forEach(card => {
        card.classList.add('hover-lift');
    });
    
    // Initialize tooltips (if using Bootstrap)
    if (typeof bootstrap !== 'undefined' && bootstrap.Tooltip) {
        const tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]');
        [...tooltipTriggerList].map(tooltipTriggerEl => new bootstrap.Tooltip(tooltipTriggerEl));
    }
    
    // Add click handlers for system status
    const statusItems = document.querySelectorAll('.system-status-item');
    
    statusItems.forEach(item => {
        item.addEventListener('click', function() {
            const statusType = this.getAttribute('data-status');
            const statusName = this.querySelector('.status-name').textContent;
            
            // Show a modal or alert with more details
            alert(`${statusName} Details:\nStatus: ${statusType}\nLast checked: Just now\nMore details would be shown in a real application.`);
        });
    });
}

// Function to set up the diagnostics modal
function setupDiagnosticsModal() {
    const runDiagnosticsButton = document.getElementById('runDiagnosticsButton');
    const diagnosticsModal = document.getElementById('diagnosticsModal');
    const closeDiagnosticsButton = document.getElementById('closeDiagnosticsButton');

    if (runDiagnosticsButton && diagnosticsModal) {
        // Show the modal when the button is clicked
        runDiagnosticsButton.addEventListener('click', function() {
            diagnosticsModal.classList.add('show');
            diagnosticsModal.style.display = 'block';
            diagnosticsModal.setAttribute('aria-hidden', 'false');
            diagnosticsModal.focus();
        });

        // Close the modal when the close button is clicked
        if (closeDiagnosticsButton) {
            closeDiagnosticsButton.addEventListener('click', function() {
                diagnosticsModal.classList.remove('show');
                diagnosticsModal.style.display = 'none';
                diagnosticsModal.setAttribute('aria-hidden', 'true');
            });
        }

        // Close the modal when clicking outside of it
        diagnosticsModal.addEventListener('click', function(event) {
            if (event.target === diagnosticsModal) {
                diagnosticsModal.classList.remove('show');
                diagnosticsModal.style.display = 'none';
                diagnosticsModal.setAttribute('aria-hidden', 'true');
            }
        });
    }
}

// Function to initialize system load chart
function initSystemLoadChart() {
    if (document.getElementById('systemLoadChart')) {
        const ctx = document.getElementById('systemLoadChart').getContext('2d');
        const systemLoadChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: ['00:00', '02:00', '04:00', '06:00', '08:00', '10:00', '12:00', '14:00', '16:00'],
                datasets: [{
                    label: 'CPU Usage',
                    data: [30, 35, 25, 45, 60, 35, 40, 45, 35],
                    borderColor: '#4e73df',
                    backgroundColor: 'rgba(78, 115, 223, 0.1)',
                    borderWidth: 2,
                    pointBackgroundColor: '#4e73df',
                    tension: 0.3
                }, {
                    label: 'Memory Usage',
                    data: [45, 50, 55, 60, 65, 70, 65, 60, 55],
                    borderColor: '#1cc88a',
                    backgroundColor: 'rgba(28, 200, 138, 0.1)',
                    borderWidth: 2,
                    pointBackgroundColor: '#1cc88a',
                    tension: 0.3
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: true,
                        position: 'top'
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        max: 100,
                        grid: {
                            color: 'rgba(0, 0, 0, 0.05)'
                        },
                        ticks: {
                            callback: function(value) {
                                return value + '%';
                            }
                        }
                    },
                    x: {
                        grid: {
                            display: false
                        }
                    }
                }
            }
        });
    }
}

// Function to initialize server traffic chart
function initServerTrafficChart() {
    if (document.getElementById('serverTrafficChart')) {
        const ctx = document.getElementById('serverTrafficChart').getContext('2d');
        const serverTrafficChart = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'],
                datasets: [{
                    label: 'Transactions',
                    data: [25000, 32000, 28000, 38000, 42000, 18000, 15000],
                    backgroundColor: '#f6c23e',
                    borderRadius: 4
                }, {
                    label: 'Traffic (Requests)',
                    data: [5000, 6500, 5800, 7200, 8500, 3200, 2800],
                    backgroundColor: '#36b9cc',
                    borderRadius: 4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: true,
                        position: 'top'
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                let label = context.dataset.label || '';
                                if (label) {
                                    label += ': ';
                                }
                                if (context.parsed.y !== null) {
                                    if (label.includes('Transaction')) {
                                        label += '₹' + context.parsed.y.toLocaleString('en-IN');
                                    } else {
                                        label += context.parsed.y.toLocaleString('en-IN');
                                    }
                                }
                                return label;
                            }
                        }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        grid: {
                            color: 'rgba(0, 0, 0, 0.05)'
                        },
                        ticks: {
                            callback: function(value, index, values) {
                                if (value >= 1000) {
                                    return value / 1000 + 'k';
                                }
                                return value;
                            }
                        }
                    },
                    x: {
                        grid: {
                            display: false
                        }
                    }
                }
            }
        });
    }
}