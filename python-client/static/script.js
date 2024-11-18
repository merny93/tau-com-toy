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

    // Helper function to traverse and render nested changes
    function renderChanges(changes, parent) {
        for (const [field, value] of Object.entries(changes)) {
            const logEntry = document.createElement("div");

            if (typeof value === "object" && value !== null) {
                // If the value is a nested object, render it recursively
                const nestedHeader = document.createElement("strong");
                nestedHeader.textContent = `${field}:`;
                logEntry.appendChild(nestedHeader);

                const nestedDiv = document.createElement("div");
                nestedDiv.style.marginLeft = "20px"; // Indent nested changes
                renderChanges(value, nestedDiv); // Recursive call
                logEntry.appendChild(nestedDiv);
            } else {
                // If the value is a primitive, display it directly
                logEntry.textContent = `${field}: ${value}`;
            }

            parent.appendChild(logEntry);
        }
    }

    renderChanges(changes, changeLogDiv);
}


function sendCommand(){
    fetch('/submit', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert('Message submitted successfully');
        } else {
            alert('Error: ' + data.error);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('An error occurred while submitting the message');
    });
}