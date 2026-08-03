// Chart.js Configuration & Data Fetching
document.addEventListener('DOMContentLoaded', () => {
  const pieCanvas = document.getElementById('categoryPieChart');
  const barCanvas = document.getElementById('monthlyBarChart');
  const lineCanvas = document.getElementById('expenseLineChart');

  if (!pieCanvas && !barCanvas && !lineCanvas) return;

  fetch('/api/chart-data/')
    .then(response => response.json())
    .then(data => {
      // Color Palettes
      const pieColors = [
        '#6366f1', '#10b981', '#f59e0b', '#ef4444', 
        '#06b6d4', '#8b5cf6', '#ec4899', '#3b82f6'
      ];

      // 1. Pie Chart: Expenses by Category
      if (pieCanvas && data.pie) {
        new Chart(pieCanvas, {
          type: 'doughnut',
          data: {
            labels: data.pie.labels.length > 0 ? data.pie.labels : ['No Data'],
            datasets: [{
              data: data.pie.values.length > 0 ? data.pie.values : [1],
              backgroundColor: data.pie.values.length > 0 ? pieColors : ['#334155'],
              borderWidth: 0,
            }]
          },
          options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
              legend: {
                position: 'bottom',
                labels: { color: '#94a3b8', font: { family: 'Outfit', size: 12 } }
              }
            },
            cutout: '70%'
          }
        });
      }

      // 2. Bar Chart: Monthly Expenses vs Income
      if (barCanvas && data.bar) {
        new Chart(barCanvas, {
          type: 'bar',
          data: {
            labels: data.bar.labels,
            datasets: [
              {
                label: 'Expenses (₹)',
                data: data.bar.expenses,
                backgroundColor: 'rgba(239, 68, 68, 0.75)',
                borderColor: '#ef4444',
                borderRadius: 6,
              },
              {
                label: 'Income (₹)',
                data: data.bar.incomes,
                backgroundColor: 'rgba(16, 185, 129, 0.75)',
                borderColor: '#10b981',
                borderRadius: 6,
              }
            ]
          },
          options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
              x: {
                ticks: { color: '#94a3b8' },
                grid: { color: 'rgba(255, 255, 255, 0.05)' }
              },
              y: {
                ticks: { color: '#94a3b8' },
                grid: { color: 'rgba(255, 255, 255, 0.05)' }
              }
            },
            plugins: {
              legend: {
                labels: { color: '#94a3b8', font: { family: 'Outfit' } }
              }
            }
          }
        });
      }

      // 3. Line Chart: Expense Trend
      if (lineCanvas && data.line) {
        new Chart(lineCanvas, {
          type: 'line',
          data: {
            labels: data.line.labels,
            datasets: [{
              label: 'Expense Trend (₹)',
              data: data.line.expenses,

              borderColor: '#6366f1',
              backgroundColor: 'rgba(99, 102, 241, 0.15)',
              fill: true,
              tension: 0.4,
              pointBackgroundColor: '#6366f1',
              pointRadius: 5
            }]
          },
          options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
              x: {
                ticks: { color: '#94a3b8' },
                grid: { color: 'rgba(255, 255, 255, 0.05)' }
              },
              y: {
                ticks: { color: '#94a3b8' },
                grid: { color: 'rgba(255, 255, 255, 0.05)' }
              }
            },
            plugins: {
              legend: {
                labels: { color: '#94a3b8', font: { family: 'Outfit' } }
              }
            }
          }
        });
      }
    })
    .catch(err => console.error('Error fetching chart data:', err));
});
