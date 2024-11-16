function updateField(fieldName, value) {
    fetch('/update', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ field_name: fieldName, value: value })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            updateChangeLog(data.changes);
        } else {
            alert(data.error);
        }
    });
}

function updateChangeLog(changes) {
    const changeLogDiv = document.getElementById("change-log");
    changeLogDiv.innerHTML = ""; // Clear existing log
    for (const [field, value] of Object.entries(changes)) {
        const logEntry = document.createElement("p");
        logEntry.textContent = `${field}: ${value}`;
        changeLogDiv.appendChild(logEntry);
    }
}
