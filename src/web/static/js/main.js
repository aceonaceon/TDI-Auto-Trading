// TDI Auto Trading Dashboard - Main JavaScript

// Global variables
let priceChart = null;
let tdiChart = null;
let availableSymbols = [];
let selectedSymbols = [];
let currentSymbol = '';

// DOM ready
document.addEventListener('DOMContentLoaded', function() {
    // Initialize navigation
    initNavigation();
    
    // Load initial data
    loadConfig();
    loadTradingSymbols();
    updateDashboardStats();
    
    // Initialize event listeners
    initEventListeners();
});

// Initialize navigation
function initNavigation() {
    const navLinks = document.querySelectorAll('.nav-link');
    const sections = document.querySelectorAll('section');
    
    navLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            
            // Remove active class from all links
            navLinks.forEach(l => l.classList.remove('active'));
            
            // Add active class to clicked link
            this.classList.add('active');
            
            // Show the corresponding section
            const targetId = this.getAttribute('href').substring(1);
            sections.forEach(section => {
                if (section.id === targetId) {
                    section.style.display = 'block';
                } else {
                    section.style.display = 'none';
                }
            });
        });
    });
    
    // Show dashboard by default
    sections.forEach(section => {
        if (section.id !== 'dashboard') {
            section.style.display = 'none';
        }
    });
}

// Initialize event listeners
function initEventListeners() {
    // Config form submission
    document.getElementById('config-form').addEventListener('submit', function(e) {
        e.preventDefault();
        saveConfig();
    });
    
    // Symbol search
    document.getElementById('symbol-search').addEventListener('input', function() {
        filterSymbols(this.value);
    });
    
    // Refresh symbols button
    document.getElementById('refresh-symbols').addEventListener('click', function() {
        loadAvailableSymbols();
    });
    
    // Save symbols button
    document.getElementById('save-symbols').addEventListener('click', function() {
        saveSelectedSymbols();
    });
    
    // Performance symbol selection
    document.getElementById('performance-symbol').addEventListener('change', function() {
        currentSymbol = this.value;
        if (currentSymbol) {
            loadPerformanceData(currentSymbol);
        }
    });
    
    // Refresh performance button
    document.getElementById('refresh-performance').addEventListener('click', function() {
        if (currentSymbol) {
            loadPerformanceData(currentSymbol);
        }
    });
    
    // Run strategy button
    document.getElementById('run-strategy').addEventListener('click', function() {
        if (currentSymbol) {
            runStrategy(currentSymbol);
        }
    });
}

// Load configuration from server
function loadConfig() {
    showLoading('config-form');
    
    fetch('/api/config')
        .then(response => response.json())
        .then(data => {
            // Fill form with config values
            const form = document.getElementById('config-form');
            
            for (const [key, value] of Object.entries(data)) {
                const element = form.elements[key];
                if (element) {
                    if (element.type === 'checkbox') {
                        element.checked = (value.toLowerCase() === 'true');
                    } else {
                        element.value = value;
                    }
                }
            }
            
            hideLoading('config-form');
        })
        .catch(error => {
            console.error('Error loading configuration:', error);
            hideLoading('config-form');
            showAlert('Failed to load configuration. Please try again.', 'danger');
        });
}

// Save configuration to server
function saveConfig() {
    showLoading('config-form');
    
    const form = document.getElementById('config-form');
    const formData = new FormData(form);
    
    // Handle checkboxes
    const checkboxes = form.querySelectorAll('input[type="checkbox"]');
    checkboxes.forEach(checkbox => {
        if (!checkbox.checked) {
            formData.set(checkbox.name, 'False');
        }
    });
    
    fetch('/api/config', {
        method: 'POST',
        body: formData
    })
        .then(response => response.json())
        .then(data => {
            hideLoading('config-form');
            
            if (data.success) {
                showAlert('Configuration saved successfully!', 'success');
                // Reload trading symbols in case they changed
                loadTradingSymbols();
                updateDashboardStats();
            } else {
                showAlert('Failed to save configuration: ' + data.error, 'danger');
            }
        })
        .catch(error => {
            console.error('Error saving configuration:', error);
            hideLoading('config-form');
            showAlert('Failed to save configuration. Please try again.', 'danger');
        });
}

// Load trading symbols
function loadTradingSymbols() {
    fetch('/api/trading_symbols')
        .then(response => response.json())
        .then(data => {
            selectedSymbols = data;
            
            // Update selected symbols list
            updateSelectedSymbolsList();
            
            // Update performance symbol dropdown
            const symbolSelect = document.getElementById('performance-symbol');
            symbolSelect.innerHTML = '<option value="">Select a symbol...</option>';
            
            data.forEach(symbol => {
                const option = document.createElement('option');
                option.value = symbol;
                option.textContent = symbol;
                symbolSelect.appendChild(option);
            });
            
            // Load available symbols
            loadAvailableSymbols();
        })
        .catch(error => {
            console.error('Error loading trading symbols:', error);
            showAlert('Failed to load trading symbols. Please try again.', 'danger');
        });
}

// Load available symbols from Binance
function loadAvailableSymbols() {
    showLoading('available-symbols');
    
    fetch('/api/symbols')
        .then(response => response.json())
        .then(data => {
            availableSymbols = data;
            
            // Filter out already selected symbols
            const filteredSymbols = availableSymbols.filter(symbol => !selectedSymbols.includes(symbol));
            
            // Update available symbols list
            updateAvailableSymbolsList(filteredSymbols);
            
            hideLoading('available-symbols');
        })
        .catch(error => {
            console.error('Error loading available symbols:', error);
            hideLoading('available-symbols');
            showAlert('Failed to load available symbols. Please try again.', 'danger');
        });
}

// Update available symbols list
function updateAvailableSymbolsList(symbols) {
    const container = document.getElementById('available-symbols');
    container.innerHTML = '';
    
    if (symbols.length === 0) {
        container.innerHTML = '<p class="text-center text-muted">No symbols available</p>';
        return;
    }
    
    symbols.forEach(symbol => {
        const item = document.createElement('a');
        item.href = '#';
        item.className = 'list-group-item list-group-item-action';
        item.textContent = symbol;
        
        item.addEventListener('click', function(e) {
            e.preventDefault();
            
            // Add to selected symbols
            if (!selectedSymbols.includes(symbol)) {
                selectedSymbols.push(symbol);
                
                // Remove from available symbols list
                this.remove();
                
                // Update selected symbols list
                updateSelectedSymbolsList();
            }
        });
        
        container.appendChild(item);
    });
}

// Update selected symbols list
function updateSelectedSymbolsList() {
    const container = document.getElementById('selected-symbols');
    container.innerHTML = '';
    
    if (selectedSymbols.length === 0) {
        container.innerHTML = '<p class="text-center text-muted">No symbols selected</p>';
        return;
    }
    
    selectedSymbols.forEach(symbol => {
        const item = document.createElement('a');
        item.href = '#';
        item.className = 'list-group-item list-group-item-action d-flex justify-content-between align-items-center';
        
        const symbolText = document.createElement('span');
        symbolText.textContent = symbol;
        item.appendChild(symbolText);
        
        const removeButton = document.createElement('button');
        removeButton.className = 'btn btn-sm btn-danger';
        removeButton.innerHTML = '<i class="fas fa-times"></i>';
        
        removeButton.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            
            // Remove from selected symbols
            const index = selectedSymbols.indexOf(symbol);
            if (index !== -1) {
                selectedSymbols.splice(index, 1);
            }
            
            // Update lists
            updateSelectedSymbolsList();
            
            // Add back to available symbols if not already there
            const availableList = document.getElementById('available-symbols');
            if (!availableSymbols.includes(symbol)) {
                availableSymbols.push(symbol);
            }
            
            // Filter available symbols
            const searchInput = document.getElementById('symbol-search');
            filterSymbols(searchInput.value);
        });
        
        item.appendChild(removeButton);
        container.appendChild(item);
    });
    
    // Update dashboard stats
    document.getElementById('active-symbols-count').textContent = selectedSymbols.length;
}

// Filter symbols based on search input
function filterSymbols(query) {
    query = query.toUpperCase();
    
    // Filter out already selected symbols and match search query
    const filteredSymbols = availableSymbols.filter(symbol => 
        !selectedSymbols.includes(symbol) && symbol.includes(query)
    );
    
    updateAvailableSymbolsList(filteredSymbols);
}

// Save selected symbols to server
function saveSelectedSymbols() {
    showLoading('selected-symbols');
    
    fetch('/api/trading_symbols', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ symbols: selectedSymbols })
    })
        .then(response => response.json())
        .then(data => {
            hideLoading('selected-symbols');
            
            if (data.success) {
                showAlert('Trading symbols saved successfully!', 'success');
                
                // Update performance symbol dropdown
                const symbolSelect = document.getElementById('performance-symbol');
                symbolSelect.innerHTML = '<option value="">Select a symbol...</option>';
                
                selectedSymbols.forEach(symbol => {
                    const option = document.createElement('option');
                    option.value = symbol;
                    option.textContent = symbol;
                    symbolSelect.appendChild(option);
                });
                
                // Update dashboard stats
                updateDashboardStats();
            } else {
                showAlert('Failed to save trading symbols: ' + data.error, 'danger');
            }
        })
        .catch(error => {
            console.error('Error saving trading symbols:', error);
            hideLoading('selected-symbols');
            showAlert('Failed to save trading symbols. Please try again.', 'danger');
        });
}

// Update dashboard stats
function updateDashboardStats() {
    // Update active symbols count
    document.getElementById('active-symbols-count').textContent = selectedSymbols.length;
    
    // For other stats, we would need to fetch data from the server
    // This is a placeholder for now
    document.getElementById('open-positions-count').textContent = '0';
    document.getElementById('total-trades-count').textContent = '0';
    document.getElementById('win-rate').textContent = '0%';
    
    // In a real implementation, we would fetch this data from the server
    // and update the dashboard stats accordingly
}

// Load performance data for a specific symbol
function loadPerformanceData(symbol) {
    showLoading('performance-stats');
    
    // Clear previous data
    document.getElementById('symbol-total-trades').textContent = '0';
    document.getElementById('symbol-win-rate').textContent = '0%';
    document.getElementById('symbol-avg-profit').textContent = '0%';
    document.getElementById('symbol-max-drawdown').textContent = '0%';
    
    // Clear current position
    document.getElementById('current-position').innerHTML = `
        <div class="text-center">
            <span class="position-badge position-none">Loading...</span>
        </div>
    `;
    
    // Clear trade history
    document.getElementById('trade-history').innerHTML = '<tr><td colspan="8" class="text-center">Loading trade history...</td></tr>';
    
    fetch(`/api/performance/${symbol}`)
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            hideLoading('performance-stats');
            
            if (data.error) {
                showAlert(`Failed to load performance data: ${data.error}`, 'danger');
                
                // Determine if this is a Binance client error
                let errorMessage = data.error;
                let additionalInfo = "This may happen if you've just added this trading pair. Please wait a few minutes for data to be collected, then try again.";
                
                if (data.error.includes("Binance client is not initialized") || 
                    data.error.includes("API keys") || 
                    data.error.includes("'NoneType' object has no attribute 'get_historical_klines'")) {
                    additionalInfo = "There seems to be an issue with the Binance API connection. Please check your API keys in the configuration and ensure they have the correct permissions.";
                }
                
                // Show error message in performance section
                document.getElementById('current-position').innerHTML = `
                    <div class="alert alert-danger">
                        <h5>Error Loading Data</h5>
                        <p>${errorMessage}</p>
                        <p>${additionalInfo}</p>
                        <button class="btn btn-primary" onclick="loadPerformanceData('${symbol}')">Try Again</button>
                    </div>
                `;
                
                // Clear charts
                if (priceChart) {
                    priceChart.destroy();
                    priceChart = null;
                }
                if (tdiChart) {
                    tdiChart.destroy();
                    tdiChart = null;
                }
                
                return;
            }
            
            // Update performance stats
            updatePerformanceStats(data.stats);
            
            // Update current position
            updateCurrentPosition(data.current_position);
            
            // Update charts
            updatePriceChart(data.price_data);
            updateTDIChart(data.tdi_data);
            
            // Update trade history
            updateTradeHistory(data.trades);
        })
        .catch(error => {
            console.error('Error loading performance data:', error);
            hideLoading('performance-stats');
            showAlert('Failed to load performance data. Please try again.', 'danger');
            
            // Show error message in performance section
            document.getElementById('current-position').innerHTML = `
                <div class="alert alert-danger">
                    <h5>Error Loading Data</h5>
                    <p>An unexpected error occurred while loading performance data.</p>
                    <p>This may happen if you've just added this trading pair. Please wait a few minutes for data to be collected, then try again.</p>
                    <button class="btn btn-primary" onclick="loadPerformanceData('${symbol}')">Try Again</button>
                </div>
            `;
        });
}

// Update performance stats
function updatePerformanceStats(stats) {
    document.getElementById('symbol-total-trades').textContent = stats.total_trades;
    document.getElementById('symbol-win-rate').textContent = `${(stats.win_rate * 100).toFixed(2)}%`;
    document.getElementById('symbol-avg-profit').textContent = `${(stats.avg_profit * 100).toFixed(2)}%`;
    document.getElementById('symbol-max-drawdown').textContent = `${(stats.max_drawdown * 100).toFixed(2)}%`;
}

// Update current position display
function updateCurrentPosition(position) {
    const container = document.getElementById('current-position');
    
    if (!position.position) {
        container.innerHTML = `
            <div class="text-center">
                <span class="position-badge position-none">No Active Position</span>
                <p>No active position for ${position.symbol}</p>
            </div>
        `;
        return;
    }
    
    const positionType = position.position === 'long' ? 'Long' : 'Short';
    const badgeClass = position.position === 'long' ? 'position-long' : 'position-short';
    
    container.innerHTML = `
        <div class="text-center mb-3">
            <span class="position-badge ${badgeClass}">${positionType} Position</span>
        </div>
        <div class="row">
            <div class="col-md-6">
                <table class="table table-sm">
                    <tr>
                        <th>Symbol:</th>
                        <td>${position.symbol}</td>
                    </tr>
                    <tr>
                        <th>Entry Price:</th>
                        <td>${position.entry_price ? position.entry_price.toFixed(2) : 'N/A'}</td>
                    </tr>
                    <tr>
                        <th>Position Size:</th>
                        <td>${position.position_size ? position.position_size.toFixed(6) : 'N/A'}</td>
                    </tr>
                </table>
            </div>
            <div class="col-md-6">
                <table class="table table-sm">
                    <tr>
                        <th>Stop Loss:</th>
                        <td>${position.stop_loss ? position.stop_loss.toFixed(2) : 'N/A'}</td>
                    </tr>
                    <tr>
                        <th>Take Profit:</th>
                        <td>${position.take_profit_levels && position.take_profit_levels.length > 0 ? 
                            position.take_profit_levels[0].toFixed(2) : 'N/A'}</td>
                    </tr>
                    <tr>
                        <th>Risk/Reward:</th>
                        <td>${calculateRiskReward(position)}</td>
                    </tr>
                </table>
            </div>
        </div>
    `;
}

// Calculate risk/reward ratio
function calculateRiskReward(position) {
    if (!position.position || !position.entry_price || !position.stop_loss || 
        !position.take_profit_levels || position.take_profit_levels.length === 0) {
        return 'N/A';
    }
    
    const entryPrice = position.entry_price;
    const stopLoss = position.stop_loss;
    const takeProfit = position.take_profit_levels[0];
    
    if (position.position === 'long') {
        const risk = entryPrice - stopLoss;
        const reward = takeProfit - entryPrice;
        return (reward / risk).toFixed(2);
    } else {
        const risk = stopLoss - entryPrice;
        const reward = entryPrice - takeProfit;
        return (reward / risk).toFixed(2);
    }
}

// Update price chart
function updatePriceChart(priceData) {
    const ctx = document.getElementById('price-chart').getContext('2d');
    
    // Destroy existing chart if it exists
    if (priceChart) {
        priceChart.destroy();
    }
    
    // Prepare data
    const labels = priceData.map(d => {
        const date = new Date(d.timestamp);
        return date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
    });
    
    const data = {
        labels: labels,
        datasets: [{
            label: 'Price',
            data: priceData.map(d => d.close),
            borderColor: 'rgb(75, 192, 192)',
            tension: 0.1,
            pointRadius: 0,
            borderWidth: 2
        }]
    };
    
    // Create new chart
    priceChart = new Chart(ctx, {
        type: 'line',
        data: data,
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                x: {
                    display: true,
                    title: {
                        display: true,
                        text: 'Time'
                    }
                },
                y: {
                    display: true,
                    title: {
                        display: true,
                        text: 'Price'
                    }
                }
            },
            plugins: {
                tooltip: {
                    mode: 'index',
                    intersect: false
                },
                legend: {
                    position: 'top',
                }
            }
        }
    });
}

// Update TDI chart
function updateTDIChart(tdiData) {
    const ctx = document.getElementById('tdi-chart').getContext('2d');
    
    // Destroy existing chart if it exists
    if (tdiChart) {
        tdiChart.destroy();
    }
    
    // Prepare data
    const labels = tdiData.map(d => {
        const date = new Date(d.timestamp);
        return date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
    });
    
    const data = {
        labels: labels,
        datasets: [
            {
                label: 'RSI',
                data: tdiData.map(d => d.rsi),
                borderColor: 'rgb(75, 192, 192)',
                backgroundColor: 'rgba(75, 192, 192, 0.2)',
                tension: 0.1,
                pointRadius: 0,
                borderWidth: 2
            },
            {
                label: 'Fast Line',
                data: tdiData.map(d => d.fast_line),
                borderColor: 'rgb(255, 99, 132)',
                tension: 0.1,
                pointRadius: 0,
                borderWidth: 2
            },
            {
                label: 'Slow Line',
                data: tdiData.map(d => d.slow_line),
                borderColor: 'rgb(54, 162, 235)',
                tension: 0.1,
                pointRadius: 0,
                borderWidth: 2
            },
            {
                label: 'Market Baseline',
                data: tdiData.map(d => d.market_baseline),
                borderColor: 'rgb(255, 159, 64)',
                tension: 0.1,
                pointRadius: 0,
                borderWidth: 2,
                borderDash: [5, 5]
            },
            {
                label: 'Upper Band',
                data: tdiData.map(d => d.upper_band),
                borderColor: 'rgba(153, 102, 255, 0.5)',
                tension: 0.1,
                pointRadius: 0,
                borderWidth: 1,
                borderDash: [2, 2]
            },
            {
                label: 'Lower Band',
                data: tdiData.map(d => d.lower_band),
                borderColor: 'rgba(153, 102, 255, 0.5)',
                tension: 0.1,
                pointRadius: 0,
                borderWidth: 1,
                borderDash: [2, 2]
            }
        ]
    };
    
    // Create new chart
    tdiChart = new Chart(ctx, {
        type: 'line',
        data: data,
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                x: {
                    display: true,
                    title: {
                        display: true,
                        text: 'Time'
                    }
                },
                y: {
                    display: true,
                    title: {
                        display: true,
                        text: 'Value'
                    },
                    min: 0,
                    max: 100
                }
            },
            plugins: {
                tooltip: {
                    mode: 'index',
                    intersect: false
                },
                legend: {
                    position: 'top',
                }
            }
        }
    });
}

// Update trade history table
function updateTradeHistory(trades) {
    const container = document.getElementById('trade-history');
    container.innerHTML = '';
    
    if (!trades || trades.length === 0) {
        container.innerHTML = '<tr><td colspan="8" class="text-center">No trade history available</td></tr>';
        return;
    }
    
    trades.forEach(trade => {
        const row = document.createElement('tr');
        
        // Format dates
        const entryTime = new Date(trade.entry_time);
        const exitTime = new Date(trade.exit_time);
        
        // Format P&L with color
        const pnlClass = trade.pnl_pct >= 0 ? 'text-success' : 'text-danger';
        const pnlText = `${(trade.pnl_pct * 100).toFixed(2)}%`;
        
        row.innerHTML = `
            <td>${entryTime.toLocaleString()}</td>
            <td>${exitTime.toLocaleString()}</td>
            <td>${trade.direction === 'long' ? 'Long' : 'Short'}</td>
            <td>${trade.entry_price.toFixed(2)}</td>
            <td>${trade.exit_price.toFixed(2)}</td>
            <td>${trade.position_size.toFixed(6)}</td>
            <td class="${pnlClass}">${pnlText}</td>
            <td>${trade.exit_reason}</td>
        `;
        
        container.appendChild(row);
    });
    
    // Update total trades count in dashboard
    document.getElementById('total-trades-count').textContent = trades.length;
    
    // Calculate win rate
    const winningTrades = trades.filter(t => t.pnl_pct > 0);
    const winRate = (winningTrades.length / trades.length) * 100;
    document.getElementById('win-rate').textContent = `${winRate.toFixed(2)}%`;
}

// Run strategy once for a specific symbol
function runStrategy(symbol) {
    showLoading('run-strategy');
    
    fetch(`/api/run_strategy/${symbol}`, {
        method: 'POST'
    })
        .then(response => response.json())
        .then(data => {
            hideLoading('run-strategy');
            
            if (data.success) {
                showAlert(`Strategy executed successfully! Action: ${data.action}`, 'success');
                
                // Reload performance data to see the results
                loadPerformanceData(symbol);
            } else {
                showAlert(`Failed to run strategy: ${data.error}`, 'danger');
            }
        })
        .catch(error => {
            console.error('Error running strategy:', error);
            hideLoading('run-strategy');
            showAlert('Failed to run strategy. Please try again.', 'danger');
        });
}

// Show loading indicator
function showLoading(elementId) {
    const element = document.getElementById(elementId);
    if (!element) return;
    
    // Add loading class
    element.classList.add('loading-container');
    
    // Create loading indicator if it doesn't exist
    if (!element.querySelector('.loading-indicator')) {
        const loadingIndicator = document.createElement('div');
        loadingIndicator.className = 'loading-indicator';
        loadingIndicator.innerHTML = '<div class="loading"></div>';
        element.appendChild(loadingIndicator);
    }
}

// Hide loading indicator
function hideLoading(elementId) {
    const element = document.getElementById(elementId);
    if (!element) return;
    
    // Remove loading class
    element.classList.remove('loading-container');
    
    // Remove loading indicator
    const loadingIndicator = element.querySelector('.loading-indicator');
    if (loadingIndicator) {
        loadingIndicator.remove();
    }
}

// Show alert message
function showAlert(message, type = 'info') {
    // Create alert container if it doesn't exist
    let alertContainer = document.getElementById('alert-container');
    if (!alertContainer) {
        alertContainer = document.createElement('div');
        alertContainer.id = 'alert-container';
        alertContainer.style.position = 'fixed';
        alertContainer.style.top = '20px';
        alertContainer.style.right = '20px';
        alertContainer.style.zIndex = '9999';
        document.body.appendChild(alertContainer);
    }
    
    // Create alert
    const alert = document.createElement('div');
    alert.className = `alert alert-${type} alert-dismissible fade show`;
    alert.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;
    
    // Add alert to container
    alertContainer.appendChild(alert);
    
    // Auto-dismiss after 5 seconds
    setTimeout(() => {
        alert.classList.remove('show');
        setTimeout(() => {
            alert.remove();
        }, 150);
    }, 5000);
