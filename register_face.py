import cv2
import os

# Create the directory if it doesn't exist just in case
if not os.path.exists("known_faces"):
    os.makedirs("known_faces")

print("=== Face Registration ===")
student_name = input("Enter Student Name: ").strip()
student_id = input("Enter Student ID: ").strip()

if not student_name or not student_id:
    print("Error: Name and ID cannot be empty!")
    exit()

print("\nStarting webcam...")
print("Press 'c' to CAPTURE your face.")
print("Press 'q' to QUIT without saving.")

# Open the default webcam (index 0)
cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("Error: Could not open webcam.")
    exit()

while True:
    # Read a frame from the webcam
    ret, frame = cap.read()
    if not ret:
        print("Failed to grab frame")
        break

    # Display the resulting frame
    cv2.imshow("Face Registration - Press 'c' to capture, 'q' to quit", frame)

    # Wait for a key press for 1 millisecond
    key = cv2.waitKey(1) & 0xFF

    # If 'c' is pressed, capture and save the image
    if key == ord('c'):
        # Format the filename: student_id_student_name.jpg
        # Replacing spaces with underscores for safer filenames
        safe_name = student_name.replace(" ", "_")
        filename = f"known_faces/{student_id}_{safe_name}.jpg"
        
        cv2.imwrite(filename, frame)
        print(f"\nSuccess! Image saved as {filename}")
        break
    
    # If 'q' is pressed, exit without saving
    elif key == ord('q'):
        print("\nRegistration cancelled.")
        break

# Release the webcam and close any open windows
cap.release()
cv2.destroyAllWindows()
