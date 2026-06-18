document.addEventListener('DOMContentLoaded', (event) => {
    const autoReloadToggle = document.getElementById('autoReloadToggle');
    let reloadIntervalId;

    const isReloadEnabled = localStorage.getItem('autoReload') === 'true';
    if (isReloadEnabled) {
        autoReloadToggle.checked = true;
        startReloading();
    }

    autoReloadToggle.addEventListener('change', () => {
        if (autoReloadToggle.checked) {
            localStorage.setItem('autoReload', 'true');
            startReloading();
        } else {
            localStorage.setItem('autoReload', 'false');
            stopReloading();
        }
    });

    function startReloading() {
        reloadIntervalId = setInterval(() => {
            window.location.reload();
        }, 5000); 
        console.log('Start auto reloading.');
    }

    function stopReloading() {
        clearInterval(reloadIntervalId);
        console.log('Stop auto reloading.');
    }
});