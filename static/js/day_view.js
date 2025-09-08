// day_view.js
document.addEventListener('DOMContentLoaded', () => {
    const deleteButton = document.getElementById('deleteButton');
    const masterCheckbox = document.getElementById('masterCheckbox');
    const checkboxes = document.querySelectorAll('.entry-checkbox');
    const confirmDeleteButton = document.getElementById('confirmDeleteButton');
    const deleteForm = document.getElementById('deleteForm');

    function updateDeleteButtonState() {
        const anyChecked = Array.from(checkboxes).some(cb => cb.checked);
        deleteButton.disabled = !anyChecked;
    }
    if (masterCheckbox) {
        masterCheckbox.addEventListener('change', () => {
            checkboxes.forEach(checkbox => {
                checkbox.checked = masterCheckbox.checked;
            });
            updateDeleteButtonState();
        });
    }
    checkboxes.forEach(checkbox => {
        checkbox.addEventListener('change', updateDeleteButtonState);
    });
    if (confirmDeleteButton) {
        confirmDeleteButton.addEventListener('click', () => {
            deleteForm.submit();
        });
    }
    updateDeleteButtonState();
});
