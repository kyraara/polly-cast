const COLORS = {
  actual:   'rgba(27, 42, 140, 1)',      // Corporate Blue (#1b2a8c)
  actualBg: 'rgba(27, 42, 140, 0.05)',
  sarima:   'rgba(220, 38, 38, 1)',      // Vibrant Red (#dc2626)
  sarimaBg: 'rgba(220, 38, 38, 0.05)',
  hw:       'rgba(22, 163, 74, 1)',       // Vibrant Green (#16a34a)
  hwBg:     'rgba(22, 163, 74, 0.05)',
  trend:    'rgba(139, 92, 246, 1)',     // Purple (#8b5cf6)
  seasonal: 'rgba(245, 158, 11, 1)',     // Amber (#f59e0b)
  residual: 'rgba(100, 116, 139, 1)'     // Slate (#64748b)
};

function renderTimeSeriesChart(canvasId, labels, data) {
  const canvas = document.getElementById(canvasId);
  if (!canvas) return null;
  const ctx = canvas.getContext('2d');
  return new Chart(ctx, {
    type: 'line',
    data: {
      labels: labels,
      datasets: [{
        label: 'Volume Distribusi (kg)',
        data: data,
        borderColor: COLORS.actual,
        backgroundColor: COLORS.actualBg,
        borderWidth: 2.5,
        fill: true,
        tension: 0.3,
        pointRadius: 0,
        pointHoverRadius: 5,
        pointHitRadius: 12
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          display: false
        }
      },
      scales: {
        y: {
          beginAtZero: false,
          grid: {
            color: '#f1f5f9',
            drawBorder: false
          },
          ticks: {
            color: '#64748b',
            font: { size: 10 },
            callback: function(value) {
              return value.toLocaleString('id-ID') + ' kg';
            }
          }
        },
        x: {
          grid: {
            display: false
          },
          ticks: {
            color: '#64748b',
            font: { size: 10 },
            autoSkip: false,
            maxRotation: 0,
            minRotation: 0,
            callback: function(val, index) {
              const label = this.getLabelForValue(val);
              if (label && typeof label === 'string' && label.endsWith('-01')) {
                return label.substring(0, 4);
              }
              return '';
            }
          }
        }
      }
    }
  });
}

function renderDecompositionCharts(trendId, seasonalId, residualId, labels, decomp) {
  const trendEl = document.getElementById(trendId);
  const seasonalEl = document.getElementById(seasonalId);
  const residualEl = document.getElementById(residualId);
  if (!trendEl || !seasonalEl || !residualEl) return null;
  const trendCtx = trendEl.getContext('2d');
  const trendChart = new Chart(trendCtx, {
    type: 'line',
    data: {
      labels: labels,
      datasets: [{
        label: 'Trend Component',
        data: decomp.trend,
        borderColor: COLORS.trend,
        borderWidth: 2,
        fill: false,
        tension: 0.3,
        pointRadius: 0,
        pointHoverRadius: 5,
        pointHitRadius: 12
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
          grid: { color: '#f1f5f9', drawBorder: false },
          ticks: { color: '#64748b', font: { size: 10 } }
        },
        x: {
          grid: { display: false },
          ticks: {
            color: '#64748b',
            font: { size: 10 },
            autoSkip: false,
            maxRotation: 0,
            minRotation: 0,
            callback: function(val, index) {
              const label = this.getLabelForValue(val);
              if (label && typeof label === 'string' && label.endsWith('-01')) {
                return label.substring(0, 4);
              }
              return '';
            }
          }
        }
      }
    }
  });

  const seasonalChart = new Chart(seasonalEl, {
    type: 'line',
    data: {
      labels: labels,
      datasets: [{
        label: 'Seasonal Component',
        data: decomp.seasonal,
        borderColor: COLORS.seasonal,
        borderWidth: 2,
        fill: false,
        tension: 0.3,
        pointRadius: 0,
        pointHoverRadius: 5,
        pointHitRadius: 12
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
          grid: { color: '#f1f5f9', drawBorder: false },
          ticks: { color: '#64748b', font: { size: 10 } }
        },
        x: {
          grid: { display: false },
          ticks: {
            color: '#64748b',
            font: { size: 10 },
            autoSkip: false,
            maxRotation: 0,
            minRotation: 0,
            callback: function(val, index) {
              const label = this.getLabelForValue(val);
              if (label && typeof label === 'string' && label.endsWith('-01')) {
                return label.substring(0, 4);
              }
              return '';
            }
          }
        }
      }
    }
  });

  const residualChart = new Chart(residualEl, {
    type: 'line',
    data: {
      labels: labels,
      datasets: [{
        label: 'Residual Component',
        data: decomp.residual,
        borderColor: COLORS.residual,
        borderWidth: 2,
        fill: false,
        tension: 0.3,
        pointRadius: 0,
        pointHoverRadius: 5,
        pointHitRadius: 12
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
          grid: { color: '#f1f5f9', drawBorder: false },
          ticks: { color: '#64748b', font: { size: 10 } }
        },
        x: {
          grid: { display: false },
          ticks: {
            color: '#64748b',
            font: { size: 10 },
            autoSkip: false,
            maxRotation: 0,
            minRotation: 0,
            callback: function(val, index) {
              const label = this.getLabelForValue(val);
              if (label && typeof label === 'string' && label.endsWith('-01')) {
                return label.substring(0, 4);
              }
              return '';
            }
          }
        }
      }
    }
  });

  return { trend: trendChart, seasonal: seasonalChart, residual: residualChart };
}

function renderBoxplot(canvasId, boxplotData) {
  const canvas = document.getElementById(canvasId);
  if (!canvas) return null;
  const ctx = canvas.getContext('2d');
  return new Chart(ctx, {
    type: 'bar',
    data: {
      labels: ['Min', 'Q1 (25%)', 'Median (Q2)', 'Q3 (75%)', 'Max'],
      datasets: [{
        label: 'Nilai Distribusi (kg)',
        data: [boxplotData.min, boxplotData.q1, boxplotData.median, boxplotData.q3, boxplotData.max],
        backgroundColor: [
          'rgba(100, 116, 139, 0.75)', // Slate
          'rgba(59, 130, 246, 0.75)',  // Blue
          'rgba(27, 42, 140, 0.85)',   // Deep Blue
          'rgba(16, 185, 129, 0.75)',  // Green
          'rgba(220, 38, 38, 0.75)'    // Red
        ],
        borderWidth: 0,
        borderRadius: 6
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
          beginAtZero: false,
          grid: { color: '#f1f5f9', drawBorder: false },
          ticks: {
            color: '#64748b',
            font: { size: 10 },
            callback: function(value) {
              return value.toLocaleString('id-ID') + ' kg';
            }
          }
        },
        x: {
          grid: { display: false },
          ticks: { color: '#64748b', font: { size: 10 } }
        }
      }
    }
  });
}

function renderForecastChart(canvasId, histLabels, histValues, futureLabels, futureValues, modelName, color, testLabels, testValues, predTestValues) {
  const ctx = document.getElementById(canvasId).getContext('2d');

  const hasTest = testLabels && testLabels.length > 0 && predTestValues && predTestValues.length > 0;
  const trainLen = hasTest ? (histLabels.length - testLabels.length) : histLabels.length;

  const allLabels = [...histLabels, ...futureLabels];

  // Training data: show only train portion, then nulls
  const trainData = [
    ...histValues.slice(0, trainLen),
    ...Array(testLabels ? testLabels.length : 0).fill(null),
    ...Array(futureLabels.length).fill(null)
  ];

  // Actual test data (shown in solid line)
  const testActualData = hasTest
    ? [...Array(trainLen - 1).fill(null), histValues[trainLen - 1], ...testValues, ...Array(futureLabels.length).fill(null)]
    : [];

  // Test period prediction (faint dashed)
  const testPredData = hasTest
    ? [...Array(trainLen - 1).fill(null), histValues[trainLen - 1], ...predTestValues, ...Array(futureLabels.length).fill(null)]
    : [];

  // Future prediction (from last historical point)
  const futurePredData = [
    ...Array(histLabels.length - 1).fill(null),
    histValues[histLabels.length - 1],
    ...futureValues
  ];

  const borderDash = modelName === 'SARIMA' ? [5, 4] : [8, 4];
  const forecastColor = modelName === 'SARIMA' ? COLORS.sarima : COLORS.hw;
  const forecastColorLight = modelName === 'SARIMA' ? COLORS.sarimaBg : COLORS.hwBg;
  const forecastColorFaint = modelName === 'SARIMA' ? 'rgba(220, 38, 38, 0.45)' : 'rgba(22, 163, 74, 0.45)';

  const datasets = [
    {
      label: 'Data Training',
      data: trainData,
      borderColor: COLORS.actual,
      backgroundColor: COLORS.actualBg,
      borderWidth: 2,
      fill: true,
      tension: 0.3,
      pointRadius: 0,
      pointHoverRadius: 5,
      pointHitRadius: 12
    }
  ];

  if (hasTest) {
    datasets.push({
      label: 'Data Testing Aktual',
      data: testActualData,
      borderColor: 'rgba(51, 65, 85, 0.9)',
      backgroundColor: 'rgba(51, 65, 85, 0.04)',
      borderWidth: 2,
      fill: true,
      tension: 0.3,
      pointRadius: 0,
      pointHoverRadius: 5,
      pointHitRadius: 12
    });
    datasets.push({
      label: `Prediksi ${modelName} (Testing)`,
      data: testPredData,
      borderColor: forecastColorFaint,
      borderWidth: 1.8,
      borderDash: [4, 4],
      fill: false,
      tension: 0.3,
      pointRadius: 0,
      pointHoverRadius: 5,
      pointHitRadius: 12
    });
  }

  datasets.push({
    label: `Proyeksi ${modelName}`,
    data: futurePredData,
    borderColor: forecastColor,
    backgroundColor: forecastColorLight,
    borderWidth: 2.5,
    borderDash: borderDash,
    fill: true,
    tension: 0.3,
    pointRadius: 0,
    pointHoverRadius: 5,
    pointHitRadius: 12
  });

  new Chart(ctx, {
    type: 'line',
    data: {
      labels: allLabels,
      datasets: datasets
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          display: true,
          position: 'top',
          align: 'start',
          labels: {
            boxWidth: 22,
            font: { size: 11 }
          }
        }
      },
      scales: {
        y: {
          beginAtZero: false,
          grid: { color: '#f1f5f9', drawBorder: false },
          ticks: {
            color: '#64748b',
            font: { size: 10 },
            callback: function(value) {
              return value.toLocaleString('id-ID') + ' kg';
            }
          }
        },
        x: {
          grid: { display: false },
          ticks: {
            color: '#64748b',
            font: { size: 10 },
            autoSkip: false,
            maxRotation: 0,
            minRotation: 0,
            callback: function(val, index) {
              const label = this.getLabelForValue(val);
              if (label && typeof label === 'string' && label.endsWith('-01')) {
                return label.substring(0, 4);
              }
              return '';
            }
          }
        }
      }
    },
    plugins: [{
      id: 'verticalBoundary',
      afterDraw: function(chart) {
        if (!hasTest || !chart.scales.x) return;
        const activeScale = chart.scales.x;
        const lastTrainIdx = trainLen - 1;
        const lastHistIdx = histLabels.length - 1;
        const drawLine = (idx, color, dash) => {
          if (idx >= 0 && idx + 1 < allLabels.length) {
            const x1 = activeScale.getPixelForValue(idx);
            const x2 = activeScale.getPixelForValue(idx + 1);
            const xVal = (x1 + x2) / 2;
            const yTop = chart.chartArea.top;
            const yBottom = chart.chartArea.bottom;
            const c = chart.ctx;
            c.save();
            c.beginPath();
            c.setLineDash(dash);
            c.strokeStyle = color;
            c.lineWidth = 1.5;
            c.moveTo(xVal, yTop);
            c.lineTo(xVal, yBottom);
            c.stroke();
            c.restore();
          }
        };
        drawLine(lastTrainIdx, 'rgba(245, 158, 11, 0.8)', [4, 4]);  // amber: train/test boundary
        drawLine(lastHistIdx, 'rgba(139, 92, 246, 0.9)', [3, 3]);   // purple: actual/forecast boundary
      }
    }]
  });
}

function renderForecastComparison(
  canvasId, 
  histLabels, 
  histValues, 
  testLabels = [], 
  testValues = [], 
  predTestSarima = [], 
  predTestHW = [], 
  futureLabels = [], 
  predFutureSarima = [], 
  predFutureHW = []
) {
  // Extract year range for dynamic labels
  function getYearRange(labels) {
    if (!labels || labels.length === 0) return '';
    var first = labels[0].substring(0, 4);
    var last = labels[labels.length - 1].substring(0, 4);
    return first === last ? first : first + '-' + last;
  }
  function getYear(label) {
    return label ? label.substring(0, 4) : '';
  }
  var histYears = getYearRange(histLabels);
  var testYears = getYearRange(testLabels);
  var futureYear = getYear(futureLabels && futureLabels.length > 0 ? futureLabels[0] : '');

  const ctx = document.getElementById(canvasId).getContext('2d');
  
  if (!testLabels || testLabels.length === 0) {
    const compatFutureLabels = futureLabels || [];
    const compatSarimaValues = predFutureSarima || [];
    const compatHwValues = predFutureHW || [];
    
    const allLabels = [...histLabels, ...compatFutureLabels];
    const sarimaData = Array(histLabels.length - 1).fill(null);
    sarimaData.push(histValues[histValues.length - 1]);
    sarimaData.push(...compatSarimaValues);

    const hwData = Array(histLabels.length - 1).fill(null);
    hwData.push(histValues[histValues.length - 1]);
    hwData.push(...compatHwValues);

    new Chart(ctx, {
      type: 'line',
      data: {
        labels: allLabels,
        datasets: [
          {
            label: 'Data Historis (' + histYears + ')',
            data: histValues,
            borderColor: COLORS.actual,
            borderWidth: 2,
            fill: false,
            tension: 0.3,
            pointRadius: 0,
            pointHoverRadius: 5,
            pointHitRadius: 12
          },
          {
            label: 'Proyeksi SARIMA (' + futureYear + ')',
            data: sarimaData,
            borderColor: COLORS.sarima,
            borderWidth: 2,
            borderDash: [5, 4],
            fill: false,
            tension: 0.3,
            pointRadius: 0,
            pointHoverRadius: 5,
            pointHitRadius: 12
          },
          {
            label: 'Proyeksi HWES (' + futureYear + ')',
            data: hwData,
            borderColor: COLORS.hw,
            borderWidth: 2,
            borderDash: [8, 4],
            fill: false,
            tension: 0.3,
            pointRadius: 0,
            pointHoverRadius: 5,
            pointHitRadius: 12
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
          y: {
            beginAtZero: false,
            grid: { color: '#f1f5f9', drawBorder: false },
            ticks: {
              color: '#64748b',
              font: { size: 10 },
              callback: function(value) {
                return value.toLocaleString('id-ID') + ' kg';
              }
            }
          },
          x: {
            grid: { display: false },
            ticks: {
              color: '#64748b',
              font: { size: 10 },
              autoSkip: false,
              maxRotation: 0,
              minRotation: 0,
              callback: function(val, index) {
                const label = this.getLabelForValue(val);
                if (label && typeof label === 'string' && label.endsWith('-01')) {
                  return label.substring(0, 4);
                }
                return '';
              }
            }
          }
        }
      }
    });
    return;
  }

  const allLabels = [...histLabels, ...futureLabels];
  const trainLen = histLabels.length - testLabels.length;

  const trainData = [...histValues.slice(0, trainLen + 1), ...Array(testLabels.length + futureLabels.length - 1).fill(null)];
  const testData = [...Array(trainLen).fill(null), ...histValues.slice(trainLen), ...Array(futureLabels.length).fill(null)];
  const sarimaFutureData = [...Array(histLabels.length - 1).fill(null), histValues[histLabels.length - 1], ...predFutureSarima];
  const hwFutureData = [...Array(histLabels.length - 1).fill(null), histValues[histLabels.length - 1], ...predFutureHW];
  const sarimaTestData = [...Array(trainLen - 1).fill(null), histValues[trainLen - 1], ...predTestSarima, ...Array(futureLabels.length).fill(null)];
  const hwTestData = [...Array(trainLen - 1).fill(null), histValues[trainLen - 1], ...predTestHW, ...Array(futureLabels.length).fill(null)];

  new Chart(ctx, {
    type: 'line',
    data: {
      labels: allLabels,
      datasets: [
        {
          label: 'Data Training (' + histYears + ')',
          data: trainData,
          borderColor: 'rgba(27, 42, 140, 0.75)', // Corporate Blue
          borderWidth: 2,
          fill: false,
          tension: 0.3,
          pointRadius: 0,
          pointHoverRadius: 5,
          pointHitRadius: 12
        },
        {
          label: 'Data Testing (' + testYears + ')',
          data: testData,
          borderColor: 'rgba(51, 65, 85, 0.95)', // Slate Grey
          borderWidth: 2,
          fill: false,
          tension: 0.3,
          pointRadius: 0,
          pointHoverRadius: 5,
          pointHitRadius: 12
        },
        {
          label: 'Proyeksi SARIMA (' + futureYear + ')',
          data: sarimaFutureData,
          borderColor: COLORS.sarima,
          borderWidth: 2.5,
          borderDash: [5, 4],
          fill: false,
          tension: 0.3,
          pointRadius: 0,
          pointHoverRadius: 5,
          pointHitRadius: 12
        },
        {
          label: 'Proyeksi HWES (' + futureYear + ')',
          data: hwFutureData,
          borderColor: COLORS.hw,
          borderWidth: 2.5,
          borderDash: [8, 4],
          fill: false,
          tension: 0.3,
          pointRadius: 0,
          pointHoverRadius: 5,
          pointHitRadius: 12
        },
        {
          label: 'Batas Data Aktual / Peramalan (' + futureYear + ')',
          data: [],
          borderColor: 'rgba(139, 92, 246, 1)', // Purple
          borderWidth: 1.5,
          borderDash: [3, 3],
          fill: false,
          pointRadius: 0
        },
        {
          label: '_sarima_test',
          data: sarimaTestData,
          borderColor: 'rgba(220, 38, 38, 0.55)', // Transparent Red
          borderWidth: 1.8,
          borderDash: [5, 5],
          fill: false,
          tension: 0.3,
          pointRadius: 0
        },
        {
          label: '_hw_test',
          data: hwTestData,
          borderColor: 'rgba(22, 163, 74, 0.55)', // Transparent Green
          borderWidth: 1.8,
          borderDash: [8, 4],
          fill: false,
          tension: 0.3,
          pointRadius: 0
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          position: 'top',
          align: 'start',
          labels: {
            boxWidth: 25,
            font: { size: 11 },
            filter: function(item) {
              return !item.text.startsWith('_');
            }
          }
        }
      },
      scales: {
        y: {
          beginAtZero: false,
          grid: {
            color: '#f1f5f9',
            drawBorder: false
          },
          title: {
            display: true,
            text: 'Jumlah Distribusi (kg)',
            color: '#475569',
            font: {
              size: 11,
              weight: 'bold'
            }
          },
          ticks: {
            color: '#64748b',
            font: { size: 10 },
            callback: function(value) {
              return value.toLocaleString('id-ID');
            }
          }
        },
        x: {
          grid: {
            display: false
          },
          title: {
            display: true,
            text: 'Periode (Tahun)',
            color: '#475569',
            font: {
              size: 11,
              weight: 'bold'
            }
          },
          ticks: {
            color: '#64748b',
            font: { size: 10 },
            autoSkip: false,
            maxRotation: 0,
            minRotation: 0,
            callback: function(val, index) {
              const label = this.getLabelForValue(val);
              if (label && typeof label === 'string' && label.endsWith('-01')) {
                return label.substring(0, 4);
              }
              return '';
            }
          }
        }
      }
    },
    plugins: [{
      id: 'verticalLine',
      afterDraw: function(chart) {
        if (chart.scales.x) {
          const activeScale = chart.scales.x;
          const lastActualIndex = histLabels.length - 1;
          
          if (lastActualIndex >= 0 && lastActualIndex + 1 < allLabels.length) {
            const x1 = activeScale.getPixelForValue(lastActualIndex);
            const x2 = activeScale.getPixelForValue(lastActualIndex + 1);
            const xVal = (x1 + x2) / 2;
            
            const yTop = chart.chartArea.top;
            const yBottom = chart.chartArea.bottom;
            const ctx = chart.ctx;
            
            ctx.save();
            ctx.beginPath();
            ctx.setLineDash([3, 3]);
            ctx.strokeStyle = 'rgba(139, 92, 246, 1)'; // Purple border boundary
            ctx.lineWidth = 1.5;
            ctx.moveTo(xVal, yTop);
            ctx.lineTo(xVal, yBottom);
            ctx.stroke();
            ctx.restore();
          }
        }
      }
    }]
  });
}
