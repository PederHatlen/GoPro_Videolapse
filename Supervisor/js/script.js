var socket = io();

let logContainer = document.getElementById("logs");
let timerContainer = document.getElementById("timer");
let statusContainer = document.getElementById("status");

let countdownEl = document.getElementById("countdown");
let eventTimeEl = document.getElementById("eventTime");

let nextEvent = new Date();

let countdownTimer;

const statChartEl = document.getElementById('statChart').getContext("2d");
// const tempChartEl = document.getElementById('tempChart').getContext("2d");

// tempChartEl.canvas.width = 300;
// tempChartEl.canvas.height = 300;

// voltChartEl.canvas.width = 300;
// voltChartEl.canvas.height = 300;

let statChart = new Chart(statChartEl, {
    type: 'line',
    data: {
        labels: [],
        datasets: [
            {label: 'Spening (Volt), på batteriet', borderColor: '#0d0',data:[]},
            {label: 'Temperatur', borderColor: '#09f', data:[]}
        ],
    },
    options:{responsive: true, maintainAspectRatio: false,}
});

function time_renderer(){
    let timeLeft = new Date(nextEvent-Date.now());
    countdownEl.innerHTML = `${("00"+timeLeft.getHours()).slice(-2)} timer, ${("00"+timeLeft.getMinutes()).slice(-2)} min og ${("00"+timeLeft.getSeconds()).slice(-2)} sek`
    eventTimeEl.innerHTML = `${("00"+nextEvent.getHours()).slice(-2)}:${("00"+nextEvent.getMinutes()).slice(-2)}:${("00"+nextEvent.getSeconds()).slice(-2)}`
}

function log_renderer(data){
    if(!("time" in data) || !("text" in data)) return false;

    let time = new Date(Date.parse(data["time"]));

    let el = document.createElement("p");
    el.innerHTML = `[${("00"+time.getDate()).slice(-2)}/${("00"+time.getMonth()).slice(-2)} ${("00"+time.getHours()).slice(-2)}:${("00"+time.getMinutes()).slice(-2)}:${("00"+time.getSeconds()).slice(-2)}]&emsp;${data["text"]}`;

    let doScroll = (logContainer.scrollTopMax == logContainer.scrollTop);

    logContainer.appendChild(el);

    if(doScroll) el.scrollIntoView();
}
function stat_renderer(data){
    if(!("volt" in data) || !("temp" in data) || !("next_event" in data) || !("current_event_name" in data) || !("time" in data)) return false;

    let time = new Date(Date.parse(data["time"]));

    statChart.data.datasets[0]["data"].push(data["volt"]);
    statChart.data.datasets[1]["data"].push(data["temp"]);
    statChart.data.labels.push(`Sun${data["current_event_name"].toLowerCase()} ${time.getDate()}/${time.getMonth()}`);

    if(statChart.data.labels.length > 21){
        statChart.data.datasets[0]["data"].shift();
        statChart.data.datasets[1]["data"].shift();
        statChart.data.labels.shift();
    }

    statChart.update();

    nextEvent = new Date(data["next_event"]);
}


socket.on('connect', ()=>{
    console.log("CONNECTED!!!!!!");
    socket.emit('connected');
});
socket.on('prev_logs', (data)=>{
    for (let message of data) {
        console.log(message);
        log_renderer(message);
    }
});
socket.on('prev_status', (data)=>{
    for (let message of data) {
        console.log(message);
        stat_renderer(message);
    }
    countdownTimer = setInterval(time_renderer, 0.5);
});

socket.on('log', log_renderer);
socket.on('status', stat_renderer);