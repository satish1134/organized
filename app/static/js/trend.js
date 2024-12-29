document.addEventListener('DOMContentLoaded', () => {
    const app = TrendAnalysisApp.getInstance();

    // Create a chart and add it as an observer
    const chartElement = document.getElementById('trend-chart');
    const chart = ChartFactory.createChart('line', chartElement);
    const chartObserver = new ChartObserver(chart);
    app.addObserver(chartObserver);

    // Fetch initial data
    app.fetchData();

    // Set up periodic data refresh
    setInterval(() => app.fetchData(), 120000);
});

// Singleton for managing global state
const TrendAnalysisApp = (function() {
    let instance;

    function init() {
        // Private variables and methods
        const observers = [];

        function notifyObservers(data) {
            observers.forEach(observer => observer.update(data));
        }

        return {
            // Public methods
            addObserver(observer) {
                observers.push(observer);
            },
            removeObserver(observer) {
                const index = observers.indexOf(observer);
                if (index > -1) {
                    observers.splice(index, 1);
                }
            },
            notify(data) {
                notifyObservers(data);
            },
            fetchData() {
                // Fetch data and notify observers
                fetch('/api/trend-data')
                    .then(response => response.json())
                    .then(data => {
                        this.notify(data);
                    })
                    .catch(error => console.error('Error fetching trend data:', error));
            }
        };
    }

    return {
        getInstance() {
            if (!instance) {
                instance = init();
            }
            return instance;
        }
    };
})();

// Observer for updating the chart
class ChartObserver {
    constructor(chartElement) {
        this.chartElement = chartElement;
    }

    update(data) {
        // Update the chart with new data
        Plotly.newPlot(this.chartElement, data);
    }
}

// Factory for creating charts
class ChartFactory {
    static createChart(type, element) {
        switch (type) {
            case 'line':
                return new LineChart(element);
            case 'bar':
                return new BarChart(element);
            default:
                throw new Error('Unknown chart type');
        }
    }
}

// Example chart classes
class LineChart {
    constructor(element) {
        this.element = element;
    }

    update(data) {
        // Update line chart with new data
        Plotly.newPlot(this.element, data);
    }
}

class BarChart {
    constructor(element) {
        this.element = element;
    }

    update(data) {
        // Update bar chart with new data
        Plotly.newPlot(this.element, data);
    }
}