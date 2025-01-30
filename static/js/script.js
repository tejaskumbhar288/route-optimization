let map, directionsService, directionsRenderer;

function initMap() {
    // Initialize the map
    map = new google.maps.Map(document.getElementById('map'), {
        center: { lat: 12.9716, lng: 77.5946 }, // Default to Bangalore
        zoom: 12
    });

    directionsService = new google.maps.DirectionsService();
    directionsRenderer = new google.maps.DirectionsRenderer();
    directionsRenderer.setMap(map);

    // Form submission to calculate route
    document.getElementById('route-form').addEventListener('submit', function (e) {
        e.preventDefault();
        calculateRoute();
    });
}

function calculateRoute() {
    const startLocation = document.getElementById('start').value;
    const endLocation = document.getElementById('end').value;

    const request = {
        origin: startLocation,
        destination: endLocation,
        travelMode: google.maps.TravelMode.DRIVING
    };

    directionsService.route(request, function (result, status) {
        if (status === google.maps.DirectionsStatus.OK) {
            directionsRenderer.setDirections(result);
            displayRouteDetails(result.routes[0].legs[0]);
        } else {
            alert('Could not find route. Please try again.');
        }
    });
}

function displayRouteDetails(leg) {
    const distance = leg.distance.text;
    const duration = leg.duration.text;
    const cost = calculateCost(leg.distance.value); // Example cost calculation based on distance

    document.getElementById('distance').textContent = distance;
    document.getElementById('duration').textContent = duration;
    document.getElementById('cost').textContent = cost;
}

function calculateCost(distance) {
    // Simple cost calculation based on distance (example)
    const costPerKm = 5; // Example rate
    return (distance / 1000) * costPerKm; // Convert meters to kilometers
}
