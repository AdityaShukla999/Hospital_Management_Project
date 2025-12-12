# Made with 💖 By Aditya Shukla
import sqlite3
from datetime import date
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, login_user, login_required, logout_user, UserMixin, current_user
from database import get_user_by_email, create_user, get_user_by_id
from werkzeug.security import check_password_hash

# As this Hospital Managment System is built using bootstrap it can work on almost every screen size

app=Flask(__name__)

app.secret_key = "dsjcn34y7r3fbf9218wdneuf#^%#&@()" # Secret key

# Login Manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

@app.route("/") # Home Page
def home():
    return render_template('home.html')


@app.route("/login", methods=["GET","POST"]) # Used to login by admin, doctor, and patient
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        user_row = get_user_by_email(email)

        if not user_row:
            flash("Invalid email or password")
            return render_template("login.html")

        stored_hash = user_row[3]

        if not check_password_hash(stored_hash, password): 
            flash("Invalid email or password")
            return render_template("login.html")

        user_obj = User(user_row[0], user_row[1], user_row[2], user_row[4])
        login_user(user_obj)

        if user_obj.role=="admin":
            return redirect(url_for("admin"))
        elif user_obj.role=="doctor":
            return redirect(url_for("doctor"))
        else:
            return redirect(url_for("patient"))

    return render_template("login.html")


@app.route("/register", methods=["GET","POST"]) # Used to register new patients
def register():
    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")
        password = request.form.get("password")
        age = request.form.get("age")
        gender = request.form.get("gender")
        contact = request.form.get("contact")
        address = request.form.get("address")

        create_user(name, email, password, "patient")

        con = sqlite3.connect("hospital.db")
        cur = con.cursor()
        cur.execute("SELECT id FROM users WHERE email=?", (email,))
        user_id = cur.fetchone()[0]

        cur.execute("INSERT INTO patients (user_id, age, gender, contact, address) VALUES (?,?,?,?,?)",(user_id, age, gender, contact, address))

        con.commit()
        con.close()

        flash("Registration successful! You can now login.")
        return redirect(url_for("login"))

    return render_template("register.html")


@app.route("/admin") # Admin dashboard
@login_required
def admin():
    if current_user.role != "admin":
        return "Access Denied", 403

    con = sqlite3.connect("hospital.db")
    cur = con.cursor()

    cur.execute("SELECT COUNT(*) FROM users WHERE role='doctor'")
    total_doctors = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM users WHERE role='patient'")
    total_patients = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM appointments")
    total_appointments = cur.fetchone()[0]

    cur.execute("""SELECT users.name, doctors.specialization, users.email, doctors.id FROM doctors JOIN users ON doctors.user_id = users.id""")
    doctors = cur.fetchall()

    cur.execute("""
        SELECT appointments.date, appointments.time, 
               p.name AS patient_name,
               d.name AS doctor_name,
               appointments.status
        FROM appointments
        JOIN patients ON appointments.patient_id = patients.id
        JOIN users p ON patients.user_id = p.id
        JOIN doctors ON appointments.doctor_id = doctors.id
        JOIN users d ON doctors.user_id = d.id
        ORDER BY appointments.date, appointments.time
    """)
    appointments = cur.fetchall()

    con.close()

    return render_template('admin_dashboard.html',total_doctors=total_doctors,total_patients=total_patients,total_appointments=total_appointments,doctors=doctors,appointments=appointments)


@app.route("/admin/search", methods=["GET"]) # Admin uses it to search doctors and patients
@login_required
def admin_search():
    if current_user.role != "admin":
        return "Access Denied", 403

    query = request.args.get("query", "").lower()

    con = sqlite3.connect("hospital.db")
    cur = con.cursor()

    cur.execute("""
        SELECT u.name, d.specialization, u.email, d.id
        FROM doctors d
        JOIN users u ON d.user_id = u.id
        WHERE LOWER(u.name) LIKE ? OR LOWER(d.specialization) LIKE ?
    """, (f"%{query}%", f"%{query}%"))
    doctor_results = cur.fetchall()

    cur.execute("""
        SELECT u.name, p.age, p.gender, p.contact, u.id
        FROM patients p
        JOIN users u ON p.user_id = u.id
        WHERE LOWER(u.name) LIKE ? OR p.contact LIKE ?
    """, (f"%{query}%", f"%{query}%"))
    patient_results = cur.fetchall()

    con.close()

    return render_template("admin_search.html",doctor_results=doctor_results,patient_results=patient_results,query=query)


@app.route("/edit_doctor/<int:doctor_id>", methods=["GET","POST"]) # Used to edit doctor information
@login_required
def edit_doctor(doctor_id):
    if current_user.role != "admin":
        return "Access Denied", 403

    con = sqlite3.connect("hospital.db")
    cur = con.cursor()

    if request.method == "POST":
        name = request.form.get("name")
        specialization = request.form.get("specialization")

        cur.execute("""UPDATE users SET name=? WHERE id = (SELECT user_id FROM doctors WHERE id=?)""", (name, doctor_id))
        
        cur.execute("UPDATE doctors SET specialization=? WHERE id=?", (specialization, doctor_id))
        con.commit()
        con.close()
        flash("Doctor updated successfully")
        return redirect(url_for("admin"))

    cur.execute("""SELECT u.name, d.specialization FROM doctors d JOIN users u ON d.user_id=u.id WHERE d.id=?""", (doctor_id,))
    doctor = cur.fetchone()
    con.close()

    return render_template("edit_doctor.html", doctor=doctor, doctor_id=doctor_id)


@app.route("/delete_doctor/<int:doctor_id>") # Used by admin to delete doctor
@login_required
def delete_doctor(doctor_id):
    if current_user.role != "admin":
        return "Access Denied", 403

    con = sqlite3.connect("hospital.db")
    cur = con.cursor()

    cur.execute("DELETE FROM users WHERE id = (SELECT user_id FROM doctors WHERE id=?)", (doctor_id,))
    cur.execute("DELETE FROM doctors WHERE id=?", (doctor_id,))
    con.commit()
    con.close()

    flash("Doctor removed successfully")
    return redirect(url_for("admin"))


@app.route("/blacklist_patient/<int:user_id>") # used by admin to blacklist patients
@login_required
def blacklist_patient(user_id):
    if current_user.role != "admin":
        return "Access Denied", 403

    con=sqlite3.connect("hospital.db")
    cur=con.cursor()

    cur.execute("DELETE FROM patients WHERE user_id=?", (user_id,))
    cur.execute("DELETE FROM users WHERE id=?", (user_id,))
    con.commit()
    con.close()

    flash("Patient removed/blacklisted successfully.")
    return redirect(url_for("admin"))


@app.route("/doctor") # Doctor dashboard
@login_required
def doctor():
    if current_user.role != "doctor":
        return "Access Denied", 403

    con = sqlite3.connect("hospital.db")
    cur = con.cursor()

    cur.execute("SELECT id FROM doctors WHERE user_id=?", (current_user.id,))
    row = cur.fetchone()
    if not row:
        flash("Doctor profile not found.")
        return redirect(url_for("home"))

    doctor_id = row[0]

    cur.execute("""
        SELECT appointments.id, appointments.date, appointments.time,
               users.name, appointments.status
        FROM appointments
        JOIN patients ON appointments.patient_id = patients.id
        JOIN users ON patients.user_id = users.id
        WHERE appointments.doctor_id=? AND appointments.status='Booked'
        ORDER BY date,time
    """, (doctor_id,))
    appointments = cur.fetchall()

    cur.execute("""
        SELECT users.name, patients.age, patients.gender,
               treatments.diagnosis, treatments.prescription, treatments.notes
        FROM treatments
        JOIN appointments ON treatments.appointment_id = appointments.id
        JOIN patients ON appointments.patient_id = patients.id
        JOIN users ON patients.user_id = users.id
        WHERE appointments.doctor_id=? AND appointments.status='Completed'
        ORDER BY treatments.id DESC LIMIT 10
    """, (doctor_id,))
    patient_history = cur.fetchall()

    con.close()
    return render_template("doctor_dashboard.html", appointments=appointments, patient_history=patient_history)


@app.route("/patient") # Patient Dashboard
@login_required
def patient():
    if current_user.role != "patient":
        return "Access Denied", 403
    
    con = sqlite3.connect("hospital.db")
    cur = con.cursor()

    cur.execute("SELECT id FROM patients WHERE user_id=?", (current_user.id,))
    row = cur.fetchone()
    if not row:
        cur.execute("INSERT INTO patients (user_id) VALUES (?)", (current_user.id,))
        con.commit()

    cur.execute("SELECT id FROM patients WHERE user_id=?", (current_user.id,))
    patient_id = cur.fetchone()[0]

    cur.execute("""
        SELECT users.name, users.email, doctors.specialization, doctors.id
        FROM doctors 
        JOIN users ON doctors.user_id = users.id
    """)
    doctors = cur.fetchall()

    cur.execute("""
        SELECT appointments.id, appointments.date, appointments.time,
               users.name AS doctor_name, appointments.status
        FROM appointments
        JOIN doctors ON appointments.doctor_id = doctors.id
        JOIN users ON doctors.user_id = users.id
        WHERE appointments.patient_id=? AND appointments.status='Booked'
        ORDER BY appointments.date, appointments.time
    """, (patient_id,))
    upcoming_appointments = cur.fetchall()

    cur.execute("""
        SELECT appointments.date, users.name AS doctor_name,
               treatments.diagnosis, treatments.prescription
        FROM appointments
        JOIN doctors ON appointments.doctor_id = doctors.id
        JOIN users ON doctors.user_id = users.id
        JOIN treatments ON treatments.appointment_id = appointments.id
        WHERE appointments.patient_id=? AND appointments.status='Completed'
        ORDER BY appointments.date DESC
    """, (patient_id,))
    past_appointments = cur.fetchall()

    con.close()

    return render_template('patient_dashboard.html',doctors=doctors,upcoming_appointments=upcoming_appointments,past_appointments=past_appointments)


@app.route("/edit_profile", methods=["GET","POST"]) # Used by patient to edit there profile
@login_required
def edit_profile():
    if current_user.role != "patient":
        return "Access Denied", 403

    con = sqlite3.connect("hospital.db")
    cur = con.cursor()

    cur.execute("""
        SELECT users.name, users.email, patients.age, patients.gender, patients.contact, patients.address
        FROM users
        JOIN patients ON users.id = patients.user_id
        WHERE users.id=?
    """,(current_user.id,))
    data = cur.fetchone()

    if request.method == "POST":
        name = request.form.get("name")
        age = request.form.get("age")
        gender = request.form.get("gender")
        contact = request.form.get("contact")
        address = request.form.get("address")

        cur.execute("UPDATE users SET name=? WHERE id=?", (name, current_user.id))
        cur.execute("""UPDATE patients SET age=?, gender=?, contact=?, address=? WHERE user_id=?""",(age, gender, contact, address, current_user.id))

        con.commit()
        con.close()
        flash("Profile updated successfully!")
        return redirect(url_for("patient"))

    con.close()
    return render_template("edit_profile.html", data=data)


@app.route("/logout") # Used to logout the user
@login_required
def logout():
    logout_user()
    flash("You have been logged out.")
    return redirect(url_for('login'))


@app.route("/add_doctor", methods=["GET","POST"]) # Used by admin to add doctors
@login_required
def add_doctor():
    if current_user.role != "admin":
        return "Access Denied", 403

    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")
        password = request.form.get("password")
        specialization = request.form.get("specialization")

        con = sqlite3.connect("hospital.db")
        cur = con.cursor()
        cur.execute("SELECT id FROM users WHERE email=?", (email,))
        exists = cur.fetchone()

        if exists:
            con.close()
            flash("❗ Email already exists — choose another email.")
            return redirect(url_for("add_doctor"))

        create_user(name, email, password, "doctor")

        cur.execute("SELECT id FROM users WHERE email=?", (email,))
        user_id = cur.fetchone()[0]

        cur.execute("INSERT INTO doctors (user_id, specialization) VALUES (?,?)",(user_id, specialization))

        con.commit()
        con.close()

        flash("Doctor Added Successfully!")
        return redirect(url_for("admin"))

    return render_template("add_doctor.html")


@app.route("/book/<int:doctor_id>", methods=["GET","POST"]) # Used by the patient to book doctor appointment
@login_required
def book_appointment(doctor_id):

    if current_user.role != "patient":
        return "Access Denied",403

    con = sqlite3.connect("hospital.db")
    cur = con.cursor()

    cur.execute("""SELECT DISTINCT date FROM doctor_availability WHERE doctor_id=? ORDER BY date""", (doctor_id,))
    available_dates = [row[0] for row in cur.fetchall()]

    selected_date = request.args.get("date")
    available_slots = []

    if selected_date:
        cur.execute("""
            SELECT da.time_slot 
            FROM doctor_availability da
            WHERE da.doctor_id=? AND da.date=? 
            AND da.time_slot NOT IN (
                SELECT time 
                FROM appointments 
                WHERE doctor_id=? AND date=? AND status='Booked'
            )
            ORDER BY da.time_slot
        """, (doctor_id, selected_date, doctor_id, selected_date))

        available_slots = [s[0] for s in cur.fetchall()]

    if request.method=="POST":
        date = request.form.get("date")
        time = request.form.get("time")

        cur.execute("""SELECT 1 FROM appointments WHERE doctor_id=? AND date=? AND time=? AND status='Booked'""", (doctor_id, date, time))

        if cur.fetchone():
            flash("Slot already booked by another patient. Try another!")
            return redirect(url_for("book_appointment", doctor_id=doctor_id, date=date))

        cur.execute("SELECT id FROM patients WHERE user_id=?", (current_user.id,))
        patient_id = cur.fetchone()[0]

        cur.execute("""INSERT INTO appointments (patient_id,doctor_id,date,time,status) VALUES (?,?,?,?, 'Booked')""", (patient_id, doctor_id, date, time))
        
        con.commit()
        con.close()

        flash("Appointment booked successfully!")
        return redirect(url_for("patient"))

    con.close()

    return render_template("book_appointment.html", doctor_id=doctor_id, available_dates=available_dates,available_slots=available_slots,selected_date=selected_date)


@app.route("/doctor/availability", methods=["GET","POST"]) # Used by doctor to set there availability slots
@login_required
def set_availability():
    if current_user.role != "doctor":
        return "Access Denied", 403

    con = sqlite3.connect("hospital.db")
    cur = con.cursor()

    cur.execute("SELECT id FROM doctors WHERE user_id=?", (current_user.id,))
    doctor_id = cur.fetchone()[0]

    if request.method == "POST":
        selected_date = request.form.get("date")
        time_slots = request.form.getlist("time_slots")

        if not time_slots:
            flash("Please select at least one time slot!")
            return redirect(url_for("set_availability"))

        for slot in time_slots:
            cur.execute("""SELECT 1 FROM doctor_availability 
                           WHERE doctor_id=? AND date=? AND time_slot=?""",
                        (doctor_id, selected_date, slot))
            if not cur.fetchone(): 
                cur.execute("INSERT INTO doctor_availability (doctor_id,date,time_slot) VALUES (?,?,?)",
                            (doctor_id, selected_date, slot))

        con.commit()
        con.close()
        flash("Availability Added Successfully!")
        return redirect(url_for("doctor"))

    cur.execute("SELECT date,time_slot FROM doctor_availability WHERE doctor_id=?", (doctor_id,))
    slots = cur.fetchall()
    con.close()

    from datetime import date
    return render_template("doctor_availability.html", slots=slots, min_date=str(date.today()))


@app.route("/cancel_appointment/<int:appointment_id>") # Used by doctor to cancel patients appointments
@login_required
def cancel_appointment(appointment_id):
    if current_user.role!="doctor":
        return "Access Denied", 403
    
    con=sqlite3.connect("hospital.db")
    cur=con.cursor()

    cur.execute("UPDATE appointments SET status='Cancelled' WHERE id=?",(appointment_id,))
    con.commit()
    con.close()

    flash("Appointment cancelled")
    return redirect(url_for('doctor'))


@app.route("/cancel_by_patient/<int:appointment_id>") # Used by patients to cancel there appointment
@login_required
def cancel_by_patient(appointment_id):
    if current_user.role!="patient":
        return "Access Denied", 403
    
    con = sqlite3.connect("hospital.db")
    cur = con.cursor()

    cur.execute("""UPDATE appointments SET status='Cancelled' WHERE id=? AND patient_id=(SELECT id FROM patients WHERE user_id=?)""",(appointment_id, current_user.id))

    con.commit()
    con.close()

    flash("Appointment cancelled successfully!")
    return redirect(url_for("patient"))


@app.route("/treat/<int:appointment_id>", methods=["GET","POST"]) # Used by doctor to perform diagnosis and give prescriptions
@login_required
def treat_patient(appointment_id):
    if current_user.role != "doctor":
        return "Access Denied", 403

    con = sqlite3.connect("hospital.db")
    cur = con.cursor()

    if request.method == "POST":
        diagnosis = request.form.get("diagnosis")
        prescription = request.form.get("prescription")
        notes = request.form.get("notes")

        cur.execute("UPDATE appointments SET status='Completed' WHERE id=?", (appointment_id,))

        cur.execute("""INSERT INTO treatments (appointment_id, diagnosis, prescription, notes)VALUES (?,?,?,?)""", (appointment_id, diagnosis, prescription, notes))

        con.commit()
        con.close()

        flash("Treatment submitted successfully")
        return redirect(url_for("doctor"))

    return render_template("treat_patient.html", appointment_id=appointment_id)


class User(UserMixin):
    def __init__(self,id,name,email,role):
        self.id=id
        self.name=name
        self.email=email
        self.role=role

@login_manager.user_loader # This is used by login manager to manage users
def load_user(user_id):
    row = get_user_by_id(user_id)
    if not row:
        return None
    return User(row[0], row[1], row[2], row[4])

if __name__=="__main__":
    app.run(host="0.0.0.0", port=5000,debug=True)  # Used to locally host on other devices connected on the same wifi network


# Made with 💖 By Aditya Shukla