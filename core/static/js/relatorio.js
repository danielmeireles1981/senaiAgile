// Função para gerar uma cor aleatória dentro de uma gama de tons
function getRandomColorFromTones(tones) {
    var color = tones[Math.floor(Math.random() * tones.length)];
    return `rgba(${color[0]}, ${color[1]}, ${color[2]}, 0.6)`; // 0.6 é a transparência
}

// Tons de cores específicas
var redTones = [[255, 99, 132], [255, 69, 0], [255, 0, 0]];
var blueTones = [[54, 162, 235], [0, 0, 255], [70, 130, 180]];
var blackTones = [[0, 0, 0], [105, 105, 105], [169, 169, 169]];
var grayTones = [[128, 128, 128], [192, 192, 192], [211, 211, 211]];
var greenTones = [[75, 192, 192], [0, 128, 0], [34, 139, 34]];

var allTones = redTones.concat(blueTones, blackTones, grayTones, greenTones);

var ctx = document.getElementById('myChart').getContext('2d');

var barColors = [];
for (var i = 0; i < data.length; i++) {
    barColors.push(getRandomColorFromTones(allTones));
}

var myChart = new Chart(ctx, {
    type: 'bar',  // ou 'bar', 'line', etc.
    data: {
        labels: labels,  // Labels fornecidas pela view
        datasets: [{
            data: data,  // Dados fornecidos pela view
            backgroundColor: barColors,
            borderColor: '#ffffff',
            borderWidth: 1
        }]
    },
    options: {
        responsive: true,
        plugins: {
            legend: {
                display: false  // Oculta a legenda
            },
            tooltip: {
                callbacks: {
                    label: function(tooltipItem) {
                        return tooltipItem.label + ': ' + tooltipItem.raw;
                    }
                }
            }
        },
        scales: {
            x: {
                beginAtZero: true
            },
            y: {
                beginAtZero: true
            }
        }
    }
});
