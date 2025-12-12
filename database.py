# Made with 💖 By Aditya Shukla
import sqlite3
from werkzeug.security import generate_password_hash

# Creating the SQL Tables
connection = sqlite3.connect("hospital.db")
cursor = connection.cursor()

# Creating all the required tables
userTable="""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        hashed_password TEXT NOT NULL,
        role TEXT CHECK(role IN ('admin', 'doctor', 'patient')) NOT NULL
    );
"""

patientTable="""
    CREATE TABLE IF NOT EXISTS patients (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        age INTEGER,
        gender TEXT CHECK(gender IN ('male', 'female', 'other')),
        contact TEXT,
        address TEXT,
        FOREIGN KEY (user_id) REFERENCES users(id)
    );
"""

doctorTable="""
    CREATE TABLE IF NOT EXISTS doctors (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        specialization TEXT NOT NULL,
        availability TEXT,
        FOREIGN KEY (user_id) REFERENCES users(id)
    );
"""

appointmentTable="""
    CREATE TABLE IF NOT EXISTS appointments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        patient_id INTEGER NOT NULL,
        doctor_id INTEGER NOT NULL,
        date TEXT NOT NULL,
        time TEXT NOT NULL,
        status TEXT CHECK(status IN ('Booked', 'Completed', 'Cancelled')) DEFAULT 'Booked',
        FOREIGN KEY (patient_id) REFERENCES patients(id),
        FOREIGN KEY (doctor_id) REFERENCES doctors(id)
    );
"""

treatmentTable="""
    CREATE TABLE IF NOT EXISTS treatments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        appointment_id INTEGER NOT NULL,
        diagnosis TEXT,
        prescription TEXT,
        notes TEXT,
        FOREIGN KEY (appointment_id) REFERENCES appointments(id)
    );
"""

availabilityTable = """
CREATE TABLE IF NOT EXISTS doctor_availability (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    doctor_id INTEGER NOT NULL,
    date TEXT NOT NULL,      -- YYYY-MM-DD
    time_slot TEXT NOT NULL, -- Example: '09:00 AM – 10:00 AM'
    FOREIGN KEY (doctor_id) REFERENCES doctors(id)
);
"""

# Executing the tables
cursor.execute(availabilityTable)
cursor.execute(treatmentTable)
cursor.execute(appointmentTable)
cursor.execute(doctorTable)
cursor.execute(patientTable)
cursor.execute(userTable)

# This will create an default admin if no other admin is present
cursor.execute("SELECT id FROM users WHERE role='admin' LIMIT 1")
if not cursor.fetchone():
    cursor.execute("INSERT INTO users (name, email, hashed_password, role) VALUES (?, ?, ?, ?)",
                ("Admin", "admin@hospital.com", generate_password_hash("admin123"), "admin"))
    connection.commit()


connection.commit()
connection.close()


# Login & Register Logic
def get_user_by_email(email):
    con=sqlite3.connect("hospital.db")
    cursor=con.cursor()
    cursor.execute("SELECT * FROM users WHERE email=?",(email,))
    user=cursor.fetchone()
    con.close()
    return user

def get_user_by_id(user_id):
    con = sqlite3.connect("hospital.db")
    cursor = con.cursor()
    cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    user = cursor.fetchone()
    con.close()
    return user

def create_user(name,email,password,role):
    con=sqlite3.connect("hospital.db")
    cursor=con.cursor()
    cursor.execute("INSERT INTO users(name,email,hashed_password,role) VALUES(?,?,?,?)",(name,email,generate_password_hash(password),role))
    con.commit()
    con.close()

# Made with 💖 By Aditya Shukla