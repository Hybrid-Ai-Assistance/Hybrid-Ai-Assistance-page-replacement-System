from flask import Flask, render_template, request, jsonify
import random

app = Flask(__name__)

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/simulate", methods=["POST"])
def simulate():
    data = request.json
    frames = int(data.get("frames", 3))
    seq_length = int(data.get("seq_length", 30))

    timeline = []
    frame_state = [-1] * frames
    last_used = {}
    faults = 0

    for t in range(seq_length):
        page = random.randint(0, 20)
        isFault = page not in frame_state

        if isFault:
            faults += 1
            if -1 in frame_state:
                idx = frame_state.index(-1)
                frame_state[idx] = page
            else:
                # LRU eviction
                lru_page = min(frame_state, key=lambda p: last_used.get(p, -1))
                idx = frame_state.index(lru_page)
                frame_state[idx] = page
                del last_used[lru_page]

        last_used[page] = t
        timeline.append({
            "t": t,
            "page": page,
            "frames": frame_state.copy(),
            "isFault": isFault
        })

    return jsonify({
        "timeline": timeline,
        "summary": {"faults": faults, "hits": seq_length - faults}
    })

if __name__ == "__main__":
    app.run(debug=True)
