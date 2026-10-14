"""Small, single-process task API. Restarting the process clears all tasks."""
import os
from threading import Lock
from flask import Flask, jsonify, render_template, request
from werkzeug.exceptions import HTTPException

APP_VERSION = "1.0.0"


def create_app(test_config=None):
    app = Flask(__name__)
    app.config.update(MAX_CONTENT_LENGTH=16 * 1024, VERSION=os.getenv("APP_VERSION", APP_VERSION))
    if test_config:
        app.config.update(test_config)
    tasks = {}
    lock = Lock()
    next_id = 1

    @app.get("/")
    def index():
        return render_template("index.html")

    @app.get("/health")
    def health():
        return jsonify(status="healthy")

    @app.get("/version")
    def version():
        return jsonify(version=app.config["VERSION"])

    @app.get("/api/tasks")
    def list_tasks():
        with lock:
            return jsonify(tasks=list(tasks.values()))

    @app.post("/api/tasks")
    def add_task():
        nonlocal next_id
        body = request.get_json(silent=True)
        if not isinstance(body, dict) or set(body) != {"title"}:
            return jsonify(error="Send a JSON object containing only a title."), 400
        title = body["title"]
        if not isinstance(title, str) or not 1 <= len(title.strip()) <= 200:
            return jsonify(error="Task title must contain 1–200 characters."), 400
        with lock:
            task = {"id": next_id, "title": title.strip(), "completed": False}
            tasks[next_id] = task
            next_id += 1
            return jsonify(task=task), 201

    @app.patch("/api/tasks/<int:task_id>")
    def update_task(task_id):
        body = request.get_json(silent=True)
        if not isinstance(body, dict) or set(body) != {"completed"} or type(body["completed"]) is not bool:
            return jsonify(error="Send a JSON object containing a boolean completed field."), 400
        with lock:
            if task_id not in tasks:
                return jsonify(error="Task not found. Refresh your list."), 404
            tasks[task_id]["completed"] = body["completed"]
            return jsonify(task=tasks[task_id])

    @app.delete("/api/tasks/<int:task_id>")
    def delete_task(task_id):
        with lock:
            if task_id not in tasks:
                return jsonify(error="Task not found. Refresh your list."), 404
            del tasks[task_id]
        return "", 204

    @app.errorhandler(HTTPException)
    def http_error(error):
        return jsonify(error=error.description), error.code

    @app.errorhandler(Exception)
    def unexpected_error(error):
        app.logger.exception("Unexpected request failure")
        return jsonify(error="Something went wrong. Please try again."), 500

    return app


app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
