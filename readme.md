Hospital Management System (HMS)

A complete web-based hospital management project built using Flask, SQLite, HTML, CSS, Bootstrap, and Jinja2. It includes three user roles — Admin, Doctor, and Patient — each with different permissions and features.

Patients can register, log in, update their profile, book appointments only in available time slots, cancel appointments, and view diagnosis/prescriptions from completed visits. Past medical history is stored and always accessible.

Doctors can log in, view upcoming appointments, mark consultations as completed, submit diagnosis and medications, and set availability for the next 7 days with multiple selectable time slots. Booked slots automatically stop showing for other patients.

Admin can manage doctors and patients, add/edit/delete doctors, remove or blacklist users, and search doctors/patients by name or specialization. Admin dashboard displays total doctors, patients, and appointments.

The database is auto-created through Python scripts, no manual DB setup required. This system aims to replace traditional manual hospital records with a functional digital interface that is easy to use and scalable.

<!-- Made with 💖 By Aditya Shukla -->