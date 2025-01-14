from flask import Flask, render_template, Response, request
from flask_cors import CORS, cross_origin
from camera import VideoCamera
from multiplayer import MultiPlayerConnectionData

app = Flask(__name__)
cors = CORS(app)  # allow CORS for all domains on all routes.
app.config["CORS_HEADERS"] = "Content-Type"
score = 0
flag = True
CORS(app)  # Enable CORS for all routes

# Global variables
score = 0
video_camera_instance = None  # Initialize as None
mode = ""


@app.route("/")
def index():
    return "Hello world"


@app.route("/ping")
def ping():
    return "Successfully pinged"


@app.route("/score")
def points():
    global score
    global flag
    return {"score": str(score), "finished": str(not flag)}


@app.route("/restart", methods=["POST"])
def restart():
    global video_camera_instance
    global flag
    flag = True
    try:
        if video_camera_instance is not None:
            video_camera_instance.restart()
            return "Game restarted successfully", 200
        else:
            return "No active game instance to restart", 400
    except Exception as e:
        # Log the error to the server console
        print(f"Error during restart: {e}")
        return f"An error occurred: {str(e)}", 500


def gen(mode, page_width, page_height):
    global flag
    global score
    global video_camera_instance
    del video_camera_instance
    multiplayerData = None
    if mode == "multiplayer":
        multiplayerData = MultiPlayerConnectionData(
            peer_ip="10.217.13.79", peer_port=8000
        )
    video_camera_instance = VideoCamera(
        page_width, page_height, multiplayerData=multiplayerData
    )
    s = 0
    while flag:
        if mode == "survival":
            frame, flag, s = video_camera_instance.survival_mode()
        elif mode == "scoring-mode":
            frame, flag, s = video_camera_instance.score_mode()
        elif mode == "free-play":
            frame = video_camera_instance.free_mode()
        elif mode == "multiplayer":
            # TODO add multiplayer mode logic
            frame, flag = video_camera_instance.multiplayer_mode()
        else:
            frame = video_camera_instance.free_mode()
        score = s
        yield (b"--frame\r\n" b"Content-Type: image/jpeg\r\n\r\n" + frame + b"\r\n\r\n")


@app.route("/boxing_feed")
def boxing_feed():
    global video_camera_instance  # Access the global instance
    global mode
    global flag
    flag = True
    mode = request.args.get("mode")
    if mode is None:
        mode = "free-play"
    page_width = int(request.args.get("page_width"))
    page_height = int(request.args.get("page_height"))
    if not video_camera_instance:
        multiplayerData = None
        # TEMP TESTING CODE
        if mode == "multiplayer":
            multiplayerData = MultiPlayerConnectionData(
                peer_ip="10.217.13.79", peer_port=8000
            )
        video_camera_instance = VideoCamera(
            page_width, page_height, multiplayerData=multiplayerData
        )
    response = Response(
        gen(mode, page_width, page_height),
        mimetype="multipart/x-mixed-replace; boundary=frame",
    )
    response.headers.add("Access-Control-Allow-Origin", "*")
    return response


@app.post("/api/punch")
def receive_punch():
    global mode
    if mode != "multiplayer":
        return
    global video_camera_instance
    data = request.json
    assert "punchLocation" in data

    if not video_camera_instance:
        res = Response("Camera not initialized", status=500)
        return res

    punchLocation = data.get("punchLocation")
    try:
        punchLocation = (float(punchLocation[0]), float(punchLocation[1]))
    except ValueError:
        res = Response("Invalid punch location", status=400)
        return res
    video_camera_instance.challengeManager.addPunchChallenge(
        data.get("punchLocation"), multiplayerPunch=True, observer=video_camera_instance.collisionObserver
    )
    return "Punch received"


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, threaded=True, use_reloader=False)
