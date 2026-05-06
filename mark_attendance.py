import cv2
import face_recognition
import os
import csv
from datetime import datetime
import numpy as np

# Path configurations
KNOWN_FACES_DIR = "known_faces"
ATTENDANCE_FILE = "attendance.csv"

# Function to load known faces and encodings
def load_known_faces():
    known_encodings = []
    known_names = []
    known_ids = []

    print("Loading known faces...")
    
    if not os.path.exists(KNOWN_FACES_DIR):
        print(f"Directory '{KNOWN_FACES_DIR}' does not exist. Please register faces first.")
        return [], [], []

    for filename in os.listdir(KNOWN_FACES_DIR):
        if filename.endswith(".jpg") or filename.endswith(".png"):
            # Extract student ID and name from filename (format: id_name.jpg)
            try:
                base_name = os.path.splitext(filename)[0]
                student_id, student_name = base_name.split("_", 1)
                student_name = student_name.replace("_", " ") # Convert back to spaces
            except ValueError:
                continue # Skip files that don't match the format
            
            filepath = os.path.join(KNOWN_FACES_DIR, filename)
            
            # Load the image and get the encoding
            image = face_recognition.load_image_file(filepath)
            encodings = face_recognition.face_encodings(image)
            
            if encodings:
                known_encodings.append(encodings[0])
                known_names.append(student_name)
                known_ids.append(student_id)
            else:
                print(f"Warning: No face found in {filename}")

    print(f"Loaded {len(known_encodings)} known faces.")
    return known_encodings, known_names, known_ids

# Function to get students already marked present today
def get_marked_today():
    marked_today = set()
    today_date = datetime.now().strftime("%Y-%m-%d")
    
    if not os.path.exists(ATTENDANCE_FILE):
        return marked_today
        
    with open(ATTENDANCE_FILE, 'r') as file:
        reader = csv.reader(file)
        next(reader, None) # Skip header
        for row in reader:
            if len(row) >= 3:
                # row = [Name, Student ID, Date, Time, Status]
                date_in_csv = row[2]
                student_id = row[1]
                if date_in_csv == today_date:
                    marked_today.add(student_id)
                    
    return marked_today

# Function to mark attendance in CSV
def mark_attendance(name, student_id):
    today_date = datetime.now().strftime("%Y-%m-%d")
    current_time = datetime.now().strftime("%H:%M:%S")
    
    # Check if file exists to write headers
    file_exists = os.path.exists(ATTENDANCE_FILE)
    
    with open(ATTENDANCE_FILE, 'a', newline='') as file:
        writer = csv.writer(file)
        if not file_exists:
            writer.writerow(["Name", "Student ID", "Date", "Time", "Status"])
            
        writer.writerow([name, student_id, today_date, current_time, "Present"])
        print(f"Marked Present: {name} ({student_id}) at {current_time}")

def main():
    known_encodings, known_names, known_ids = load_known_faces()
    
    if not known_encodings:
        print("Exiting: No known faces available.")
        return

    marked_today = get_marked_today()
    
    print("\nStarting webcam for attendance...")
    print("Press 'q' to quit.")
    
    cap = cv2.VideoCapture(0)
    
    if not cap.isOpened():
        print("Error: Could not open webcam.")
        return

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Failed to grab frame")
            break

        # Resize frame of video to 1/4 size for faster face recognition processing
        small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
        
        # Convert the image from BGR color (which OpenCV uses) to RGB color (which face_recognition uses)
        rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)
        
        # Find all the faces and face encodings in the current frame of video
        face_locations = face_recognition.face_locations(rgb_small_frame)
        face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)

        # Loop through each face found in the frame
        for (top, right, bottom, left), face_encoding in zip(face_locations, face_encodings):
            # See if the face is a match for the known face(s)
            matches = face_recognition.compare_faces(known_encodings, face_encoding)
            name = "Unknown"
            student_id = "N/A"

            # Use the known face with the smallest distance to the new face
            face_distances = face_recognition.face_distance(known_encodings, face_encoding)
            
            if len(face_distances) > 0:
                best_match_index = np.argmin(face_distances)
                if matches[best_match_index]:
                    name = known_names[best_match_index]
                    student_id = known_ids[best_match_index]
                    
                    # Mark attendance if not already marked today
                    if student_id not in marked_today:
                        mark_attendance(name, student_id)
                        marked_today.add(student_id)

            # Scale back up face locations since the frame we detected in was scaled to 1/4 size
            top *= 4
            right *= 4
            bottom *= 4
            left *= 4

            # Draw a box around the face
            color = (0, 255, 0) if name != "Unknown" else (0, 0, 255)
            cv2.rectangle(frame, (left, top), (right, bottom), color, 2)

            # Draw a label with a name below the face
            cv2.rectangle(frame, (left, bottom - 35), (right, bottom), color, cv2.FILLED)
            font = cv2.FONT_HERSHEY_DUPLEX
            display_text = f"{name} ({student_id})" if name != "Unknown" else "Unknown"
            cv2.putText(frame, display_text, (left + 6, bottom - 6), font, 0.6, (255, 255, 255), 1)

        # Display the resulting image
        cv2.imshow('Attendance System - Press "q" to quit', frame)

        # Hit 'q' on the keyboard to quit!
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    # Release handle to the webcam
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
