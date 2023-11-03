import secrets, json, time, os
from datetime import datetime
from flask import Flask, send_file, send_from_directory, abort, request
from flask_socketio import SocketIO, emit

message_log = []
status_log = []

tz = datetime.now(timezone.utc).astimezone().tzinfo # Timezone used for dates

os.makedirs("data", exist_ok=True)

logmessages_file = "data/messageLog.json"
statuslog_file = "data/statusLog.json"

# Terrible way of getting contents of a file with unknown existance
if os.path.exists(logmessages_file):
    with open(logmessages_file, "r") as f: message_log = json.load(f)
else:
    with open(logmessages_file, "w+") as f: f.write("[]")

if os.path.exists(statuslog_file):
    with open(statuslog_file, "r") as f: status_log = json.load(f)
else:
    with open(statuslog_file, "w+") as f: f.write("[]")


app = Flask(__name__)
app.config['SECRET_KEY'] = secrets.token_urlsafe(16)
socketio = SocketIO(app)

# Flask world
@app.route("/")
@app.route("/index.html")
def index(): return send_file("./index.html")

@app.route('/<folder>/<path:path>')
def send_allowed(folder, path):
    if folder in ["img", "js", "css"]: return send_from_directory(folder, path)
    abort(404)

@app.route("/log", methods=["POST"])
def add_to_log():
    data = request.get_json()

    if "text" not in data: abort(406)
    processed = {"text":data["text"], "time":datetime.now(tz).isoformat()}

    print(data, processed)
    # print(f"[From: {data['from']}] {data['text']}")

    socketio.emit("log", processed)

    message_log.append(processed)
    with open(logmessages_file, 'w') as f: json.dump(message_log, f)

    return "success!"

@app.route("/status", methods=["POST"])
def status():
    data = request.get_json()
    if ("volt" not in data) or ("temp" not in data) or ("current_event_name" not in data) or ("next_event" not in data): abort(406)

    print(f"Battery voltage is {data['volt']}V, temperature is {data['temp']} and next event is at unix-epoc {data['next_event']}")

    processed = {"volt":data["volt"], "temp":data["temp"], "current_event_name":data["current_event_name"], "next_event":data["next_event"], "time":datetime.now(tz).isoformat()}
    socketio.emit("status", processed)
    status_log.append(processed)
    with open(statuslog_file, 'w') as f: json.dump(status_log, f)

    return "success!"


# SocketIO world
@socketio.on('connected')
def on_connection():
    print(f"Client connected {request.sid}")
    emit("prev_logs", message_log)
    emit("prev_status", status_log[-21:])

def main():
    socketio.run(app=app, port="1337")


if __name__ == '__main__':
    while True:
        try: main()
        except KeyboardInterrupt:
            print("Keyboard interupt")
            exit()
        # except: print("Program failed, restarting...")
        time.sleep(2)