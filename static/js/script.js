let map;
let directionsService;
let directionsRenderer;
let trafficLayer = null;

document.addEventListener("DOMContentLoaded", function () {
    console.log("DOM fully loaded");
    
    if (typeof google === "undefined" || !google.maps) {
        console.error("Google Maps API failed to load.");
        document.getElementById("map").innerHTML = "<p>Sorry, we couldn't load the map.</p>";
        return;
    }

    initMap();
    setupEventListeners();
});

function initMap() {
    const mapDiv = document.getElementById("map");
    if (!mapDiv) return console.error("Map div not found");

    map = new google.maps.Map(mapDiv, {
        center: { lat: 28.6139, lng: 77.2090 },
        zoom: 12
    });

    const inputStart = document.getElementById("start-location");
    const inputEnd = document.getElementById("end-location");

    if (inputStart && inputEnd) {
        new google.maps.places.Autocomplete(inputStart);
        new google.maps.places.Autocomplete(inputEnd);
    } else {
        console.error("Input elements for locations not found");
    }

    directionsService = new google.maps.DirectionsService();
    directionsRenderer = new google.maps.DirectionsRenderer();
    directionsRenderer.setMap(map);
}

function getRoute() {
    const start = document.getElementById("start-location").value;
    const end = document.getElementById("end-location").value;

    if (!start || !end) {
        alert("Please enter both start and end locations.");
        return;
    }

    const request = {
        origin: start,
        destination: end,
        travelMode: google.maps.TravelMode.DRIVING,
        provideRouteAlternatives: true,
    };

    directionsService.route(request, function(result, status) {
        if (status === google.maps.DirectionsStatus.OK) {
            directionsRenderer.setDirections(result);

            const route = result.routes[0].legs[0];
            document.getElementById("distance").textContent = route.distance.text;
            document.getElementById("duration").textContent = route.duration.text;
            document.getElementById("save-route").classList.remove("d-none");
        } else {
            alert("Could not find a valid route. Please check your locations.");
            console.error("Directions request failed due to", status);
        }
    });
}

function saveRoute() {
    const start = document.getElementById("start-location").value;
    const end = document.getElementById("end-location").value;
    const distance = document.getElementById("distance").textContent;
    const duration = document.getElementById("duration").textContent;

    if (!start || !end || distance === '-' || duration === '-') {
        alert("Please find a valid route first.");
        return;
    }

    fetch("/save_route", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ start, end, distance, duration }),  // FIXED KEYS
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            alert("Error: " + data.error);
        } else {
            alert("Success: " + data.message);
        }
    })
    .catch(error => console.error("Error saving route:", error));
}

// Attach event listener
document.addEventListener("DOMContentLoaded", function () {
    document.getElementById("saveRouteButton").addEventListener("click", saveRoute);
});


function toggleTrafficLayer(button) {
    if (!trafficLayer) {
        trafficLayer = new google.maps.TrafficLayer();
        trafficLayer.setMap(map);
        button.textContent = "Hide Traffic";
    } else {
        trafficLayer.setMap(null);
        trafficLayer = null;
        button.textContent = "Show Traffic";
    }
}

function setupEventListeners() {
    const form = document.getElementById("routeForm");
    if (form) {
        form.addEventListener("submit", function (e) {
            e.preventDefault();
            getRoute();
        });
    }

    const saveButton = document.getElementById("saveRouteButton");
    if (saveButton) {
        saveButton.addEventListener("click", saveRoute);
    }

    const trafficButton = document.getElementById("toggle-traffic");
    if (trafficButton) {
        trafficButton.addEventListener("click", function () {
            toggleTrafficLayer(this);
        });
    }
}
