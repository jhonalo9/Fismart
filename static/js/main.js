// Funciones globales
function formatCurrency(amount) {
    return 'S/. ' + parseFloat(amount).toFixed(2).replace(/\B(?=(\d{3})+(?!\d))/g, ',');
}

function formatDate(dateString) {
    if (!dateString) return '-';
    const date = new Date(dateString);
    return date.toLocaleString('es-ES', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

// Función para mostrar notificaciones
function showNotification(message, type = 'success') {
    Swal.fire({
        icon: type,
        title: message,
        toast: true,
        position: 'top-end',
        showConfirmButton: false,
        timer: 3000,
        timerProgressBar: true
    });
}

// Función para confirmar acciones
function confirmAction(message, callback) {
    Swal.fire({
        title: '¿Estás seguro?',
        text: message,
        icon: 'warning',
        showCancelButton: true,
        confirmButtonColor: '#dc3545',
        confirmButtonText: 'Sí, confirmar',
        cancelButtonText: 'Cancelar'
    }).then((result) => {
        if (result.isConfirmed && callback) {
            callback();
        }
    });
}

// Función para manejar errores
function handleError(error) {
    console.error(error);
    let message = 'Ocurrió un error inesperado';
    if (error.responseJSON && error.responseJSON.message) {
        message = error.responseJSON.message;
    } else if (error.message) {
        message = error.message;
    }
    Swal.fire('Error', message, 'error');
}

// Función para obtener token CSRF (si se usa)
function getCSRFToken() {
    return document.querySelector('meta[name="csrf-token"]')?.getAttribute('content');
}

// Inicialización de DataTables con configuración en español
$.extend(true, $.fn.dataTable.defaults, {
    language: {
        url: '//cdn.datatables.net/plug-ins/1.13.4/i18n/es-ES.json'
    },
    responsive: true,
    pageLength: 25
});

// Función para actualizar selectores con AJAX
function updateSelect(selectId, url, idField, nameField) {
    $.getJSON(url, function(data) {
        const select = $(selectId);
        select.empty();
        select.append('<option value="">Seleccionar...</option>');
        data.forEach(item => {
            select.append(`<option value="${item[idField]}">${item[nameField]}</option>`);
        });
    });
}

// Inicialización al cargar la página
$(document).ready(function() {
    // Agregar clase activa al menú
    const currentPath = window.location.pathname;
    $('.navbar-nav .nav-link').each(function() {
        const href = $(this).attr('href');
        if (href && currentPath.startsWith(href) && href !== '/') {
            $(this).addClass('active');
        }
    });
    
    // Tooltips
    $('[data-bs-toggle="tooltip"]').tooltip();
    
    // Auto-dismiss alerts
    setTimeout(function() {
        $('.alert').alert('close');
    }, 5000);
});

// Exportar funciones para uso en otros scripts
window.formatCurrency = formatCurrency;
window.formatDate = formatDate;
window.showNotification = showNotification;
window.confirmAction = confirmAction;
window.handleError = handleError;