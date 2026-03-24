from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'college_portal_secret_2024'

DB_PATH = os.path.join(os.path.dirname(__file__), 'database.db')

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    c = conn.cursor()

    c.execute('''CREATE TABLE IF NOT EXISTS students (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id TEXT UNIQUE NOT NULL,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        department TEXT,
        year INTEGER,
        cgpa REAL,
        phone TEXT,
        avatar_initials TEXT
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS courses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        code TEXT NOT NULL,
        name TEXT NOT NULL,
        instructor TEXT,
        credits INTEGER,
        schedule TEXT,
        room TEXT,
        department TEXT
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS enrollments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id INTEGER,
        course_id INTEGER,
        grade TEXT,
        attendance INTEGER DEFAULT 0,
        FOREIGN KEY(student_id) REFERENCES students(id),
        FOREIGN KEY(course_id) REFERENCES courses(id)
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS announcements (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        content TEXT NOT NULL,
        date TEXT NOT NULL,
        category TEXT DEFAULT 'General'
    )''')

    # Seed demo data
    c.execute("SELECT COUNT(*) FROM students")
    if c.fetchone()[0] == 0:
        students = [
            ('CS2021001', 'Arjun Sharma', 'arjun@college.edu', 'password123', 'Computer Science', 3, 8.7, '9876543210', 'AS'),
            ('EC2021042', 'Priya Nair', 'priya@college.edu', 'password123', 'Electronics', 2, 9.1, '9123456789', 'PN'),
            ('ME2022015', 'Rahul Verma', 'rahul@college.edu', 'password123', 'Mechanical', 2, 7.8, '9988776655', 'RV'),
        ]
        c.executemany("INSERT INTO students (student_id, name, email, password, department, year, cgpa, phone, avatar_initials) VALUES (?,?,?,?,?,?,?,?,?)", students)

        courses = [
            ('CS301', 'Data Structures & Algorithms', 'Dr. Ramesh Kumar', 4, 'Mon/Wed 10:00-11:30', 'CSE-101', 'Computer Science'),
            ('CS302', 'Database Management Systems', 'Prof. Sunita Rao', 3, 'Tue/Thu 09:00-10:30', 'CSE-102', 'Computer Science'),
            ('CS303', 'Operating Systems', 'Dr. Anil Mehta', 4, 'Mon/Fri 14:00-15:30', 'CSE-103', 'Computer Science'),
            ('MA301', 'Engineering Mathematics III', 'Prof. Lakshmi Devi', 4, 'Daily 08:00-09:00', 'MATH-201', 'Mathematics'),
            ('CS304', 'Computer Networks', 'Dr. Vijay Patel', 3, 'Wed/Fri 11:00-12:30', 'CSE-104', 'Computer Science'),
        ]
        c.executemany("INSERT INTO courses (code, name, instructor, credits, schedule, room, department) VALUES (?,?,?,?,?,?,?)", courses)

        enrollments = [
            (1, 1, 'A', 92), (1, 2, 'B+', 88), (1, 3, 'A+', 95), (1, 4, 'B', 79), (1, 5, 'A', 90),
        ]
        c.executemany("INSERT INTO enrollments (student_id, course_id, grade, attendance) VALUES (?,?,?,?)", enrollments)

        announcements = [
            ('Mid-Semester Examinations Schedule', 'Mid-semester exams will be held from April 10–18. Timetable posted on notice board. All students must carry their ID cards.', '2024-03-28', 'Academic'),
            ('Annual Tech Fest – TechNova 2024', 'Register now for TechNova 2024! Events include hackathon, paper presentation, robotics, and cultural programs. Last date: April 5.', '2024-03-25', 'Events'),
            ('Library New Arrivals', 'Over 200 new books added across CS, ECE, and Mechanical departments. Visit the library or check the portal catalog.', '2024-03-22', 'General'),
            ('Scholarship Applications Open', 'Merit-based scholarships for students with CGPA above 8.5. Submit applications to the scholarship cell by April 15.', '2024-03-20', 'Important'),
        ]
        c.executemany("INSERT INTO announcements (title, content, date, category) VALUES (?,?,?,?)", announcements)

    conn.commit()
    conn.close()

@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        student_id = request.form.get('student_id', '').strip()
        password = request.form.get('password', '').strip()
        conn = get_db()
        student = conn.execute(
            "SELECT * FROM students WHERE student_id=? AND password=?", (student_id, password)
        ).fetchone()
        conn.close()
        if student:
            session['student_id'] = student['id']
            session['student_name'] = student['name']
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid Student ID or Password. Try: CS2021001 / password123', 'error')
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'student_id' not in session:
        return redirect(url_for('login'))
    conn = get_db()
    student = conn.execute("SELECT * FROM students WHERE id=?", (session['student_id'],)).fetchone()
    enrollments = conn.execute("""
        SELECT c.code, c.name, c.instructor, c.schedule, c.room, c.credits, e.grade, e.attendance
        FROM enrollments e JOIN courses c ON e.course_id = c.id
        WHERE e.student_id=?
    """, (session['student_id'],)).fetchall()
    announcements = conn.execute("SELECT * FROM announcements ORDER BY date DESC LIMIT 4").fetchall()
    conn.close()

    total_credits = sum(e['credits'] for e in enrollments)
    avg_attendance = round(sum(e['attendance'] for e in enrollments) / len(enrollments)) if enrollments else 0

    return render_template('dashboard.html',
        student=student,
        enrollments=enrollments,
        announcements=announcements,
        total_credits=total_credits,
        avg_attendance=avg_attendance,
        current_date=datetime.now().strftime('%B %d, %Y')
    )

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    init_db()
    app.run(debug=True)