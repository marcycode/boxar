from flask import Flask, render_template, Response, request
from camera import VideoCamera

app = Flask(__name__)


@app.route("/")
def index():
    return render_template("index.html")


def gen(camera):
    while True:
        frame = camera.get_frame()
        yield (b"--frame\r\n" b"Content-Type: image/jpeg\r\n\r\n" + frame + b"\r\n\r\n")


@app.route("/video_feed")
def video_feed():
    page_width = int(request.args.get("page_width"))
    page_height = int(request.args.get("page_height"))
    response = Response(
        gen(VideoCamera(page_width, page_height)),
        mimetype="multipart/x-mixed-replace; boundary=frame",
    )
    response.headers.add("Access-Control-Allow-Origin", "*")
    return response


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, threaded=True, use_reloader=False)