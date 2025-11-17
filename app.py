from flask import Flask, render_template, request, redirect, url_for, session, flash
import requests

app = Flask(__name__)
app.secret_key = "super_secret_key"
RAILS_API_URL = "http://localhost:3000"

# ---------------- Crud Functions ----------------
def get_current_employee():
    return session.get("employee")

def api_get(path):
    try:
        res = requests.get(f"{RAILS_API_URL}/{path}")
        return res.json() if res.status_code == 200 else None
    except:
        return None

def api_post(path, data, files=None):
    try:
        if files:
            return requests.post(f"{RAILS_API_URL}/{path}", data=data, files=files)
        return requests.post(f"{RAILS_API_URL}/{path}", json=data)
    except:
        return None

def api_patch(path, data):
    try:
        return requests.patch(f"{RAILS_API_URL}/{path}", json=data)
    except:
        return None

def api_delete(path):
    try:
        return requests.delete(f"{RAILS_API_URL}/{path}")
    except:
        return None

# ------ Index Page ------
@app.route("/")
def index():
    return render_template("Index.html")

# ------ Register -------
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        employee_data = {
            "employee": {
                "first_name": request.form["first_name"],
                "last_name": request.form["last_name"],
                "email": request.form["email"],
                "position": request.form["position"],
                "department": request.form["department"],
                "phone": request.form["phone"],
                "hire_date": request.form["hire_date"].strip(),
                "gender": request.form["gender"].capitalize()
            }
        }
        res = api_post("employees", employee_data)

        if res and res.status_code == 201:
            session["employee"] = res.json()
            flash("Account created successfully!", "success")
            return redirect(url_for("dashboard"))

        flash("Failed to create employee.", "danger")

    return render_template("Register.html")


# -------- Login --------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        res = requests.post(
            f"{RAILS_API_URL}/employees/login",
            json={
                "email": request.form["email"].lower(),
                "hire_date": request.form["hire_date"].strip()
            }
        )

        if res.status_code == 200:
            employee = res.json()
            session["employee"] = employee

            if employee.get("admin"):
                return redirect(url_for("admin_dashboard"))

            return redirect(url_for("dashboard"))

        flash("Invalid login details", "danger")

    return render_template("Login.html")


# ------- Employee Dashboard --------
@app.route("/dashboard")
def dashboard():
    employee = get_current_employee()
    if not employee:
        return redirect(url_for("login"))

    if employee.get("admin"):
        return redirect(url_for("admin_dashboard"))

    enrollments = api_get("enrollments") or []

    my_courses = [
        {**e["course"], "enrollment_id": e["id"]}
        for e in enrollments
        if e["employee"]["id"] == employee["id"]
    ]

    return render_template("Dashboard.html", employee=employee, my_courses=my_courses)


# ------ Admin Dashboard --------
@app.route("/admin-dashboard")
def admin_dashboard():
    employee = get_current_employee()
    if not employee or not employee.get("admin"):
        flash("Admins only", "danger")
        return redirect(url_for("dashboard"))

    employees = api_get("employees") or []
    enrollments = api_get("enrollments") or []

    employee_data = []

    for emp in employees:
        emp_courses = []
        for e in enrollments:
            if e["employee"]["id"] == emp["id"]:
                emp_courses.append({
                    "title": e["course"]["title"],
                    "enrollment_id": e["id"]
                })

        employee_data.append({"employee": emp, "courses": emp_courses})

    return render_template("Admin_dashboard.html", employee_data=employee_data)


# ----- Manage Employees ------
@app.route("/manage-employees")
def manage_employees():
    emp = get_current_employee()
    if not emp or not emp.get("admin"):
        return redirect(url_for("dashboard"))

    employees_list = api_get("employees") or []
    return render_template("Manage_employee.html", employees=employees_list)


@app.route("/employee/delete/<int:employee_id>", methods=["POST"])
def delete_employee(employee_id):
    emp = get_current_employee()
    if not emp or not emp.get("admin"):
        return redirect(url_for("dashboard"))

    res = api_delete(f"employees/{employee_id}")

    flash("Employee deleted" if res and res.status_code == 204 else "Failed to delete", "info")
    return redirect(url_for("admin_dashboard"))

@app.route("/courses", methods=["GET"])
def courses():
    employee = get_current_employee()
    if not employee:
        return redirect(url_for("login"))

    courses_list = api_get("courses") or []
    return render_template("Courses.html", courses=courses_list, employee=employee)


# ------ Manage Courses ------
@app.route("/manage-courses", methods=["GET", "POST"])
def manage_courses():
    employee = get_current_employee()
    if not employee or not employee.get("admin"):
        return redirect(url_for("dashboard"))

    courses_list = api_get("courses") or []


    if request.method == "POST":
        course_data = {
            "course": {
                "title": request.form["title"],
                "duration_minutes": request.form["duration"],
                "capacity": request.form["capacity"],
                "level": request.form["level"],
                "start_date": request.form["start_date"],
                "end_date": request.form["end_date"]
            }
        }
        res = api_post("courses", course_data)
        flash("Course created!" if res and res.status_code == 201 else "Failed.", "info")
        return redirect(url_for("manage_courses"))

    return render_template("Manage_course.html", courses=courses_list)


@app.route("/course/edit/<int:course_id>", methods=["POST"])
def edit_course(course_id):
    employee = get_current_employee()
    if not employee or not employee.get("admin"):
        return redirect(url_for("dashboard"))

    course_data = {
        "course": {
            "title": request.form["title"],
            "duration_minutes": request.form["duration"],
            "capacity": request.form["capacity"],
            "level": request.form["level"],
            "start_date": request.form["start_date"],
            "end_date": request.form["end_date"]
        }
    }

    res = api_patch(f"courses/{course_id}", course_data)
    flash("Updated!" if res and res.status_code == 200 else "Update failed", "info")
    return redirect(url_for("manage_courses"))


@app.route("/course/delete/<int:course_id>", methods=["POST"])
def delete_course(course_id):
    employee = get_current_employee()
    if not employee or not employee.get("admin"):
        return redirect(url_for("dashboard"))

    res = api_delete(f"courses/{course_id}")
    flash("Course deleted" if res and res.status_code == 204 else "Delete failed", "info")

    return redirect(url_for("manage_courses"))


# ------- Enrollment Control --------
@app.route("/unenroll/<int:enrollment_id>", methods=["POST"])
def unenroll(enrollment_id):
    employee = get_current_employee()
    if not employee or not employee.get("admin"):
        return redirect(url_for("dashboard"))

    res = api_delete(f"enrollments/{enrollment_id}")

    flash("Unenrolled" if res and res.status_code == 204 else "Failed", "info")
    return redirect(url_for("admin_dashboard"))


# ----- Certificates --------
@app.route("/certificates", methods=["GET", "POST"])
def certificates():
    employee = get_current_employee()
    if not employee:
        return redirect(url_for("login"))

    if request.method == "POST":
        file = request.files.get("document")
        certificate_data = {
            "certificate": {
                "name": request.form["name"],
                "issued_on": request.form["issued_on"],
                "expiry_date": request.form["expiry_date"],
                "employee_id": employee["id"],
                "course_id": int(request.form["course_id"])
            }
        }

        files = {"certificate[document]": (file.filename, file.read())} if file else None
        api_post("certificates", certificate_data, files=files)

        flash("Certificate uploaded", "success")
        return redirect(url_for("certificates"))

    courses_list = api_get("courses") or []
    return render_template("Certificates.html", courses=courses_list)


# ------- Logout --------
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))


# ------- Run -------
if __name__ == "__main__":
    app.run(debug=True, port=5000)
