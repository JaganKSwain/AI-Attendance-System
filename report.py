import csv
import os
from datetime import datetime

ATTENDANCE_FILE = "attendance.csv"

def generate_report():
    print("=== Attendance Report ===")
    
    if not os.path.exists(ATTENDANCE_FILE):
        print(f"Error: {ATTENDANCE_FILE} not found. No attendance has been marked yet.")
        return

    # Ask the user if they want to see today's report or a specific date
    date_input = input("Enter date for report (YYYY-MM-DD) or press Enter for today: ").strip()
    
    if not date_input:
        target_date = datetime.now().strftime("%Y-%m-%d")
    else:
        target_date = date_input

    print(f"\n--- Report for {target_date} ---")
    
    present_students = []
    
    try:
        with open(ATTENDANCE_FILE, 'r') as file:
            reader = csv.reader(file)
            headers = next(reader, None)
            
            for row in reader:
                if len(row) >= 5:
                    name, student_id, date, time, status = row
                    if date == target_date:
                        present_students.append({
                            "name": name,
                            "id": student_id,
                            "time": time
                        })
    except Exception as e:
        print(f"Error reading file: {e}")
        return

    if not present_students:
        print("No attendance records found for this date.")
    else:
        print(f"Total Present: {len(present_students)}\n")
        print(f"{'Student ID':<15} | {'Name':<25} | {'Time'}")
        print("-" * 60)
        for student in present_students:
            print(f"{student['id']:<15} | {student['name']:<25} | {student['time']}")
    print("-" * 60)

if __name__ == "__main__":
    generate_report()
