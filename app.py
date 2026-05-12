import csv
import os
import subprocess
import sys
import threading
from datetime import datetime

from flask import Flask, jsonify, render_template, request, send_from_directory

# Configuration
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
KNOWN_FACES_DIR = os.path.join(BASE_DIR, "known_faces")
ATTENDANCE_FILE = os.path.join(BASE_DIR, "attendance.csv")

app = Flask(
    __name__,
    template_folder=os.path.join(BASE_DIR, "templates"),
    static_folder=os.path.join(BASE_DIR, "static"),
)

# Track whether a recognition session is running
recognition_running = False
recognition_error = ""
recognition_lock = threading.Lock()


# Helpers
def _parse_students():
    """Parse the known_faces directory and return a list of student dicts."""
    students = []
    if not os.path.exists(KNOWN_FACES_DIR):
        return students

    for fname in os.listdir(KNOWN_FACES_DIR):
        if fname.lower().endswith((".jpg", ".png", ".jpeg")):
            base = os.path.splitext(fname)[0]
            try:
                student_id, name = base.split("_", 1)
                name = name.replace("_", " ")
            except ValueError:
                continue
            students.append({
                "id": student_id,
                "name": name,
                "photo": fname,
            })
    return students


def _read_attendance(date_filter=None):
    """Read attendance.csv and return rows, optionally filtered by date."""
    rows = []
    if not os.path.exists(ATTENDANCE_FILE):
        return rows

    with open(ATTENDANCE_FILE, "r", newline="") as f:
        reader = csv.reader(f)
        header = next(reader, None)
        if header is None:
            return rows
        for row in reader:
            if len(row) < 5:
                continue
            name, student_id, date, time, status = row[0], row[1], row[2], row[3], row[4]
            if date_filter and date != date_filter:
                continue
            rows.append({
                "name": name,
                "studentId": student_id,
                "date": date,
                "time": time,
                "status": status,
            })
    return rows


# Page routes
@app.route("/")
def index():
    return render_template("index.html")


# API routes
@app.route("/api/students", methods=["GET"])
def get_students():
    students = _parse_students()
    return jsonify(students)


@app.route("/api/students", methods=["POST"])
def add_student():
    """Register a new student via image upload."""
    student_name = request.form.get("name", "").strip()
    student_id = request.form.get("id", "").strip()
    photo = request.files.get("photo")

    if not student_name or not student_id:
        return jsonify({"error": "Name and ID are required"}), 400
    if not photo:
        return jsonify({"error": "Photo is required"}), 400

    # Ensure directory exists
    os.makedirs(KNOWN_FACES_DIR, exist_ok=True)

    safe_name = student_name.replace(" ", "_")
    ext = os.path.splitext(photo.filename)[1] or ".jpg"
    filename = f"{student_id}_{safe_name}{ext}"
    filepath = os.path.join(KNOWN_FACES_DIR, filename)
    photo.save(filepath)

    return jsonify({
        "message": f"Student {student_name} registered successfully",
        "student": {"id": student_id, "name": student_name, "photo": filename},
    }), 201


@app.route("/api/students/<student_id>", methods=["DELETE"])
def delete_student(student_id):
    """Remove a student's face image."""
    if not os.path.exists(KNOWN_FACES_DIR):
        return jsonify({"error": "No students registered"}), 404

    for fname in os.listdir(KNOWN_FACES_DIR):
        if fname.startswith(f"{student_id}_"):
            os.remove(os.path.join(KNOWN_FACES_DIR, fname))
            return jsonify({"message": f"Student {student_id} removed"})

    return jsonify({"error": "Student not found"}), 404


@app.route("/api/attendance", methods=["GET"])
def get_attendance():
    date_filter = request.args.get("date")
    rows = _read_attendance(date_filter)
    return jsonify(rows)


@app.route("/api/attendance/stats", methods=["GET"])
def get_stats():
    students = _parse_students()
    total_students = len(students)

    today = datetime.now().strftime("%Y-%m-%d")
    today_rows = _read_attendance(today)
    today_present = len(today_rows)

    # Overall attendance rate: unique (student, date) pairs / (total_students * unique dates)
    all_rows = _read_attendance()
    unique_dates = set(r["date"] for r in all_rows)
    total_possible = total_students * len(unique_dates) if unique_dates and total_students else 1
    total_present = len(all_rows)
    attendance_rate = round((total_present / total_possible) * 100, 1) if total_possible else 0

    return jsonify({
        "totalStudents": total_students,
        "todayPresent": today_present,
        "attendanceRate": attendance_rate,
        "totalRecords": len(all_rows),
        "todayDate": today,
    })


@app.route("/api/attendance/start", methods=["POST"])
def start_recognition():
    """Launch the mark_attendance.py script in a separate process."""
    global recognition_running, recognition_error

    with recognition_lock:
        if recognition_running:
            return jsonify({"error": "Recognition session already running"}), 409
        recognition_running = True
        recognition_error = ""

    def _run():
        global recognition_running, recognition_error
        try:
            # Use CREATE_NEW_CONSOLE on Windows so the OpenCV GUI window
            # gets its own display context and can render properly.
            flags = 0
            if sys.platform == "win32":
                flags = subprocess.CREATE_NEW_CONSOLE

            proc = subprocess.Popen(
                [sys.executable, os.path.join(BASE_DIR, "mark_attendance.py")],
                cwd=BASE_DIR,
                creationflags=flags,
            )
            proc.wait()  # Block until the user closes the OpenCV window

            if proc.returncode != 0:
                recognition_error = f"Process exited with code {proc.returncode}"
                print(f"Recognition error: {recognition_error}")
        except Exception as e:
            recognition_error = str(e)
        finally:
            with recognition_lock:
                recognition_running = False

    thread = threading.Thread(target=_run, daemon=True)
    thread.start()

    return jsonify({"message": "Recognition session started. An OpenCV window will open."})


@app.route("/api/recognition-status", methods=["GET"])
def recognition_status():
    return jsonify({"running": recognition_running, "error": recognition_error})


@app.route("/api/student-photo/<path:filename>")
def student_photo(filename):
    return send_from_directory(KNOWN_FACES_DIR, filename)


# Entry point
if __name__ == "__main__":
    os.makedirs(KNOWN_FACES_DIR, exist_ok=True)
    print("\n  AI Attendance System")
    print("  Open http://localhost:5000 in your browser\n")
    app.run(debug=True, host="0.0.0.0", port=5000)
