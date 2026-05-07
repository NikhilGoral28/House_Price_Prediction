document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('predictForm');
    const typeSelect = document.getElementById('type');
    const areaInput = document.getElementById('area');
    const bhkInput = document.getElementById('bhk');
    const areaInfo = document.getElementById('areaInfo');
    const bhkInfo = document.getElementById('bhkInfo');
    const resultsCard = document.getElementById('resultsCard');
    const priceDisplay = document.getElementById('priceDisplay');
    const rangeDisplay = document.getElementById('rangeDisplay');
    const rateMetric = document.getElementById('rateMetric');
    const predictBtn = document.getElementById('predictBtn');

    let chart = null;

    // Intelligent BHK-Area Mapping (Area determines valid BHK)
    function getValidBHKRange(type, area) {
        if (type === 'Apartment') {
            if (area <= 500) return [1, 1];
            if (area < 700) return [1, 2];
            if (area < 1100) return [2, 3];
            if (area < 1600) return [3, 4];
            return [3, 10];
        } else if (type === 'Row bunglow') {
            if (area < 800) return [0, 0]; // Unlikely
            if (area < 1200) return [2, 2];
            if (area < 1800) return [2, 3];
            if (area < 2600) return [3, 4];
            return [4, 10];
        } else if (type === 'Independent house') {
            if (area < 900) return [1, 2];
            if (area < 1500) return [2, 3];
            if (area < 2500) return [3, 4];
            if (area < 4000) return [4, 5];
            return [5, 10];
        }
        return [1, 10];
    }

    // Dynamic UI update
    function updateConstraints() {
        const type = typeSelect.value;
        const area = parseFloat(areaInput.value) || 0;
        const maxArea = type === 'Apartment' ? 2000 : 3000;
        areaInput.placeholder = `500 - ${maxArea.toLocaleString()}`;
        const range = getValidBHKRange(type, area);
        const currentBHK = parseInt(bhkInput.value) || 0;

        if (range[0] === 0) {
            bhkInfo.textContent = "⚠️ Unlikely for this area";
            bhkInfo.style.color = "#ef4444";
        } else {
            bhkInfo.textContent = `Valid: ${range[0]} - ${range[1] === 10 ? '5+' : range[1]} BHK`;
            bhkInfo.style.color = "";
        }

        // Visual validation for BHK input
        if (currentBHK < range[0] || currentBHK > range[1]) {
            if (area > 0) {
                bhkInput.style.borderColor = '#ef4444';
                bhkInfo.style.color = '#ef4444';
            }
        } else {
            bhkInput.style.borderColor = '';
            bhkInfo.style.color = '';
        }

        // General Area Limits (Absolute bounds)
        if (area > maxArea || (area < 500 && area > 0)) {
            areaInput.style.borderColor = '#ef4444';
            areaInfo.textContent = `Area for ${typeSelect.value} must be between 500 and ${maxArea.toLocaleString()} sqft`;
        } else {
            areaInput.style.borderColor = '';
            areaInfo.textContent = "Estimated square footage.";
        }
    }

    typeSelect.addEventListener('change', updateConstraints);
    bhkInput.addEventListener('input', updateConstraints);
    areaInput.addEventListener('input', updateConstraints);
    updateConstraints();

    // Handle form submission
    form.addEventListener('submit', async (e) => {
        e.preventDefault();

        const type = typeSelect.value;
        const area = parseFloat(areaInput.value);
        const bhk = parseInt(bhkInput.value);

        const maxArea = type === 'Apartment' ? 2000 : 3000;
        if (area < 500 || area > maxArea) {
            alert(`Area for ${type} must be between 500 and ${maxArea.toLocaleString()} sqft.`);
            areaInput.focus();
            return;
        }

        const range = getValidBHKRange(type, area);

        // Area-based BHK Validation
        if (range[0] === 0) {
            alert(`Property type ${type} is unlikely for an area of ${area} sq.ft.`);
            areaInput.focus();
            return;
        }

        if (bhk < range[0] || bhk > range[1]) {
            alert(`For an area of ${area} sq.ft., a ${type} typically has ${range[0]} to ${range[1] === 10 ? '5+' : range[1]} BHK. Please adjust your input.`);
            bhkInput.focus();
            return;
        }

        predictBtn.textContent = 'Analyzing Market...';
        predictBtn.disabled = true;

        const payload = {
            type: type,
            area: area,
            bhk: bhkInput.value,
            status: document.getElementById('status').value
        };

        try {
            const response = await fetch('/predict', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });

            const result = await response.json();

            if (result.success) {
                renderResults(result);
            } else {
                alert('Error: ' + result.error);
            }
        } catch (err) {
            console.error(err);
            alert('Failed to connect to the prediction engine.');
        } finally {
            predictBtn.textContent = 'Calculate Valuation';
            predictBtn.disabled = false;
        }
    });

    function renderResults(data) {
        const grid = document.querySelector('.card-grid');
        grid.classList.add('prediction-active');

        resultsCard.classList.remove('hidden');
        resultsCard.scrollIntoView({ behavior: 'smooth' });

        const priceStr = formatPrice(data.prediction);
        priceDisplay.textContent = priceStr;

        const lowStr = formatPrice(data.range_low, true);
        const highStr = formatPrice(data.range_high, true);
        rangeDisplay.textContent = `Market Range: ${lowStr} - ${highStr}`;

        // Debug and fallback for price_per_sqft
        const rate = data.price_per_sqft || (data.prediction / parseFloat(areaInput.value));
        rateMetric.textContent = `₹ ${Math.round(rate).toLocaleString()}`;

        updateChart(data.comparison);
    }

    function formatPrice(num, short = false) {
        if (num >= 10000000) {
            return `₹ ${(num / 10000000).toFixed(2)} Cr`;
        } else if (num >= 100000) {
            return `₹ ${(num / 100000).toFixed(2)} L`;
        }
        return `₹ ${num.toLocaleString()}`;
    }

    function updateChart(comp) {
        const ctx = document.getElementById('comparisonChart').getContext('2d');

        if (chart) chart.destroy();

        chart = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: [comp.current_status, comp.other_status],
                datasets: [{
                    label: 'Investment Comparison (₹)',
                    data: [comp.current_price, comp.other_price],
                    backgroundColor: ['#10b981', '#cbd5e1'],
                    borderRadius: 8
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            callback: (val) => val >= 10000000 ? (val / 10000000).toFixed(1) + 'Cr' : (val / 100000).toFixed(0) + 'L'
                        }
                    }
                }
            }
        });
    }

    // Fetch Model Metadata on load
    async function fetchMetadata() {
        try {
            const response = await fetch('/api/metadata');
            const data = await response.json();
            const modelEl = document.getElementById('activeModel');
            if (data.model_name && modelEl) {
                modelEl.textContent = `Powered by ${data.model_name} (Acc: ${data.accuracy_r2 * 100}%)`;
            }
        } catch (err) {
            const modelEl = document.getElementById('activeModel');
            if (modelEl) modelEl.textContent = 'AI Engine Active';
        }
    }
    fetchMetadata();
});
