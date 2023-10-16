google.charts.load('current', {'packages':['corechart']});

var socket = io();

let logContainer = document.getElementById("logs");
let timerContainer = document.getElementById("timer");
let statusContainer = document.getElementById("statusChart");
let countdownEl = document.getElementById("countdown");
let eventTimeEl = document.getElementById("eventTime");

let countdownInfoTextEl = document.getElementById("countdownInfotext");

let nextEvent = new Date();

let countdownTimer;

let chartData = [];
var chartOptions = {
    title: 'Spenning (Volt) av batteri og temperatur under boot.',
    colors: ['#09f', '#0d0'],
    legend: {position: 'top'},
    // series: {0: {targetAxisIndex: 0},1: {targetAxisIndex: 1}},
    // vAxes: {0: {title: 'Temperatur'},1: {title: 'Volt'}},
};

function time_renderer(){
    let timeLeft = Math.round(nextEvent.getTime()/1000 - (new Date().getTime()/1000));

    if (timeLeft < 0){
        timeLeft = Math.abs(timeLeft);
        countdownInfoTextEl.innerHTML = "Tid siden opptak skulle skjedd (Overtid)";
    }else countdownInfoTextEl.innerHTML = "Tid til neste opptak";

    countdownEl.innerHTML = `${Math.floor(timeLeft/3600)} time${Math.floor(timeLeft/3600) == 1? "":"r"}, ${Math.floor((timeLeft%3600) / 60)} min og ${timeLeft%60} sek`;
    eventTimeEl.innerHTML = `${("00"+nextEvent.getHours()).slice(-2)}:${("00"+nextEvent.getMinutes()).slice(-2)}:${("00"+nextEvent.getSeconds()).slice(-2)}`;
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

function drawChart(newData = null) {
    if(newData != null && ["volt", "temp", "next_event", "current_event_name"].every(k => k in newData)){
        let time = new Date(Date.parse(newData["time"]));
        chartData.push([`Sun${newData["current_event_name"].toLowerCase()} ${time.getDate()}/${time.getMonth()}`, newData["temp"], newData["volt"]]);
        if(chartData.length > 21) chartData.shift();

        nextEvent = new Date(newData["next_event"]);
    }

    var data = google.visualization.arrayToDataTable([['Time', 'Temp', 'Voltage'], ...chartData]);
    var chart = new google.visualization.LineChart(statusContainer);
    chart.draw(data, chartOptions);
}

// socket.io world
socket.on('connect', ()=>{
    console.log("CONNECTED!");
    socket.emit('connected');
    chartData = [];
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
        drawChart(message);
    }
    countdownTimer = setInterval(time_renderer, 250);
});

socket.on('log', log_renderer);
socket.on('status', drawChart);