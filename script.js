let socket;

function connectWebSocket() {
    socket = new WebSocket("ws://" + window.location.hostname + ":8888/ws");

    socket.onopen = function () {
        console.log("WebSocket connected.");
        getSensorData();
    };

    socket.onmessage = function (event) {
        console.log("Received message:", event.data);

        const response = JSON.parse(event.data);

        if (response.type === "sensor_data") {
            updateSensorUI(response.data);
        } else {
            document.getElementById("status").innerText = "Response: " + event.data;
        }

        if (response.type === "watering_data") {
            updateWateringUI(response);
        } else {
            document.getElementById("status").innerText = "Response: " + event.data;
        }
    };

    socket.onclose = function () {
        console.log("WebSocket disconnected.");
    };
}

function getSensorData() {
    sendCommand("status");
}

function updateSensorUI(data) {
    const { temperatura, vlaga, timestamp } = data[0];

    const tempElement = document.getElementById("temperature-text");
    const vlagaElement = document.getElementById("humidity-text");
    const timeElement = document.getElementById("time-text");
    const stateElement = document.getElementById("state");

    tempElement.innerText = `Trenutna temperatura: ${temperatura}°C`;
    vlagaElement.innerText = `Trenutna vlaga: ${vlaga}%`;
    timeElement.innerText = `Vrijeme učitavanja: ${timestamp}h`;

    stateElement.innerText = "NORMALNO";

    if (temperatura < 10) {
        stateElement.innerText = "NISKA TEMPERATURA";
    } else if ( temperatura > 40) {
        stateElement.innerText = "VISOKA TEMPERATURA";
    } else if (vlaga < 40) {
        stateElement.innerText = "NISKI POSTOTAK VLAGE";
    } else if (vlaga > 80) {
        stateElement.innerText = "VISOKI POSTOTAK VLAGE";
    } else if (temperatura < 10 || temperatura > 40 || vlaga < 40 || vlaga > 80) {
        stateElement.innerText = "KRITIČNE VRIJEDNOSTI TEMPERATURE I VLAGE";
    }

    tempElement.style.color = (temperatura < 10 || temperatura > 40) ? "red" : "green";
    vlagaElement.style.color = (vlaga < 40 || vlaga > 80) ? "red" : "green";
}

function updateWateringUI(message) {
    if (!message) {
        document.getElementById("water-text").innerText = "Nema dostupnih podataka o zalijevanju.";
        document.getElementById("state").innerText = "";
        return;
    }

    const { last_watering, next_watering, should_water } = message.data;

    document.getElementById("water-text").innerText = `Posljednje zalijevanje: ${last_watering}`;
    document.getElementById("next-water-text").innerText = should_water === 1
        ? "POTREBNO ZALITI BILJKU" 
        : `Sljedeće zalijevanje: ${next_watering}`;
}

function sendCommand(command) {
    if (socket && socket.readyState === WebSocket.OPEN) {
        socket.send(command);
        document.getElementById("status").innerText = "Sent watering command...";
    } else {
        alert("WebSocket is not connected. Try refreshing the page.");
    }
}

window.onload = connectWebSocket;
