/**
 * Institute Management System
 * Main JavaScript File
 */

document.addEventListener('DOMContentLoaded', function() {
    // Sidebar Toggle
    const sidebarToggle = document.getElementById('sidebarToggle');
    const menuToggle = document.getElementById('menuToggle');
    const sidebar = document.querySelector('.sidebar');
    const appContainer = document.querySelector('.app-container');
    const mainContent = document.querySelector('.main-content');
    const overlay = document.createElement('div');
    overlay.className = 'sidebar-overlay';
    document.body.appendChild(overlay);

    if (sidebarToggle) {
        sidebarToggle.addEventListener('click', function() {
            // Only toggle if not on mobile
            if (window.innerWidth >= 992) {
                sidebar.classList.toggle('sidebar-collapsed');
                appContainer.classList.toggle('sidebar-collapsed');

                // Force a reflow to ensure transitions work properly
                void sidebar.offsetWidth;
                void mainContent.offsetWidth;

                // Save preference to localStorage
                if (sidebar.classList.contains('sidebar-collapsed')) {
                    localStorage.setItem('sidebar-collapsed', 'true');
                } else {
                    localStorage.setItem('sidebar-collapsed', 'false');
                }
            }
        });
    }

    // Check if sidebar was collapsed in previous session
    if (localStorage.getItem('sidebar-collapsed') === 'true' && window.innerWidth >= 992) {
        sidebar.classList.add('sidebar-collapsed');
        appContainer.classList.add('sidebar-collapsed');

        // Force a reflow to ensure transitions work properly
        void sidebar.offsetWidth;
        void mainContent.offsetWidth;
    }

    // Mobile Menu Toggle
    if (menuToggle) {
        menuToggle.addEventListener('click', function(e) {
            e.preventDefault();
            sidebar.classList.toggle('show');
            overlay.classList.toggle('show');
            document.body.classList.toggle('sidebar-open');
        });
    }

    // Sidebar Close Button
    const sidebarClose = document.getElementById('sidebarClose');
    if (sidebarClose) {
        sidebarClose.addEventListener('click', function() {
            sidebar.classList.remove('show');
            overlay.classList.remove('show');
            document.body.classList.remove('sidebar-open');
        });
    }

    // Close sidebar when clicking on overlay
    overlay.addEventListener('click', function() {
        sidebar.classList.remove('show');
        overlay.classList.remove('show');
        document.body.classList.remove('sidebar-open');
    });

    // Close sidebar when clicking on menu items on mobile
    const sidebarLinks = document.querySelectorAll('.sidebar-nav a');
    if (window.innerWidth < 992) {
        sidebarLinks.forEach(link => {
            link.addEventListener('click', function() {
                sidebar.classList.remove('show');
                overlay.classList.remove('show');
                document.body.classList.remove('sidebar-open');
            });
        });
    }

    // Handle window resize
    window.addEventListener('resize', function() {
        if (window.innerWidth < 992) {
            // On mobile, ensure sidebar is not collapsed
            sidebar.classList.remove('sidebar-collapsed');
            appContainer.classList.remove('sidebar-collapsed');
            // No need to set margin-left since we're using flex layout

            // Also close mobile sidebar if open
            if (sidebar.classList.contains('show')) {
                sidebar.classList.remove('show');
                overlay.classList.remove('show');
                document.body.classList.remove('sidebar-open');
            }
        } else {
            // No need to reset margin-left since we're using flex layout

            if (localStorage.getItem('sidebar-collapsed') === 'true') {
                // On desktop, restore collapsed state if it was collapsed before
                sidebar.classList.add('sidebar-collapsed');
                appContainer.classList.add('sidebar-collapsed');
            } else {
                sidebar.classList.remove('sidebar-collapsed');
                appContainer.classList.remove('sidebar-collapsed');
            }

            // Force a reflow to ensure transitions work properly
            void sidebar.offsetWidth;
            void mainContent.offsetWidth;
        }
    });

    // Close Alert Messages
    const closeButtons = document.querySelectorAll('.alert .close-btn');
    closeButtons.forEach(button => {
        button.addEventListener('click', function() {
            const alert = this.closest('.alert');
            alert.style.opacity = '0';
            setTimeout(() => {
                alert.style.display = 'none';
            }, 300);
        });
    });

    // Form Validation
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        const requiredInputs = form.querySelectorAll('[required]');

        form.addEventListener('submit', function(event) {
            let isValid = true;

            requiredInputs.forEach(input => {
                if (!input.value.trim()) {
                    isValid = false;
                    input.classList.add('is-invalid');

                    // Create error message if it doesn't exist
                    let errorDiv = input.nextElementSibling;
                    if (!errorDiv || !errorDiv.classList.contains('field-errors')) {
                        errorDiv = document.createElement('div');
                        errorDiv.classList.add('field-errors');
                        const errorMsg = document.createElement('p');
                        errorMsg.classList.add('error-message');
                        errorMsg.textContent = 'This field is required.';
                        errorDiv.appendChild(errorMsg);
                        input.parentNode.insertBefore(errorDiv, input.nextSibling);
                    }
                } else {
                    input.classList.remove('is-invalid');

                    // Remove error message if it exists
                    const errorDiv = input.nextElementSibling;
                    if (errorDiv && errorDiv.classList.contains('field-errors')) {
                        errorDiv.remove();
                    }
                }
            });

            if (!isValid) {
                event.preventDefault();
            }
        });

        // Clear validation on input
        requiredInputs.forEach(input => {
            input.addEventListener('input', function() {
                if (input.value.trim()) {
                    input.classList.remove('is-invalid');

                    // Remove error message if it exists
                    const errorDiv = input.nextElementSibling;
                    if (errorDiv && errorDiv.classList.contains('field-errors')) {
                        errorDiv.remove();
                    }
                }
            });
        });
    });

    // Formset Management (for Django formsets)
    const addFormsetRowButtons = document.querySelectorAll('.add-formset-row');
    addFormsetRowButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();

            const formsetContainer = this.closest('.formset-container');
            const totalFormsInput = formsetContainer.querySelector('[name$="-TOTAL_FORMS"]');
            const formRows = formsetContainer.querySelectorAll('.formset-row');

            if (formRows.length > 0) {
                // Clone the last form
                const lastForm = formRows[formRows.length - 1];
                const newForm = lastForm.cloneNode(true);

                // Update form index
                const currentFormCount = parseInt(totalFormsInput.value);
                const newFormHtml = newForm.innerHTML.replace(
                    new RegExp(`-${currentFormCount - 1}-`, 'g'),
                    `-${currentFormCount}-`
                );
                newForm.innerHTML = newFormHtml;

                // Clear input values
                const inputs = newForm.querySelectorAll('input:not([type="hidden"]), select, textarea');
                inputs.forEach(input => {
                    input.value = '';
                });

                // Increment form count
                totalFormsInput.value = currentFormCount + 1;

                // Add the new form
                formsetContainer.querySelector('.formset-rows').appendChild(newForm);
            }
        });
    });

    // Delete formset row
    document.addEventListener('click', function(e) {
        if (e.target && e.target.classList.contains('delete-formset-row')) {
            e.preventDefault();

            const row = e.target.closest('.formset-row');
            const formsetContainer = row.closest('.formset-container');
            const deleteInput = row.querySelector('input[name$="-DELETE"]');

            if (deleteInput) {
                // Mark for deletion (Django formset style)
                deleteInput.value = 'on';
                row.style.display = 'none';
            } else {
                // Just remove the row if it's a new form
                row.remove();

                // Update total forms count
                const totalFormsInput = formsetContainer.querySelector('[name$="-TOTAL_FORMS"]');
                const formRows = formsetContainer.querySelectorAll('.formset-row');
                totalFormsInput.value = formRows.length;
            }
        }
    });

    // Initialize Select2 if available
    if (typeof $.fn.select2 !== 'undefined') {
        $('.select2').select2({
            theme: 'bootstrap4',
            width: '100%'
        });
    }

    // Initialize Datepicker if available
    if (typeof $.fn.datepicker !== 'undefined') {
        $('.datepicker').datepicker({
            format: 'yyyy-mm-dd',
            autoclose: true,
            todayHighlight: true
        });
    }

    // Initialize Charts if available
    if (typeof Chart !== 'undefined') {
        // Example chart initialization
        const chartElements = document.querySelectorAll('.chart-canvas');
        chartElements.forEach(canvas => {
            const ctx = canvas.getContext('2d');
            const chartType = canvas.dataset.chartType || 'bar';
            const chartData = JSON.parse(canvas.dataset.chartData || '{}');

            new Chart(ctx, {
                type: chartType,
                data: chartData,
                options: {
                    responsive: true,
                    maintainAspectRatio: false
                }
            });
        });
    }

    // Add animation classes to elements
    const animateElements = document.querySelectorAll('.animate');
    animateElements.forEach(element => {
        const animationType = element.dataset.animation || 'fade-in';
        element.classList.add(animationType);
    });
});
