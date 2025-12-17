from flask import Flask, render_template, request, redirect, url_for, session, flash # Import Flask, Render html, handles request , Redirects users to different routes
import requests, json # JSON data for API communication
from datetime import date
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image # Used for generating PDF
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle # PDF styling and layout
from reportlab.lib.enums import TA_CENTER # Centers textin PDF paragraphs
from reportlab.lib.pagesizes import A4 # Set the page size to A4
from reportlab.lib.utils import ImageReader # Imge processing
import io # In memory file

app = Flask(__name__)
app.secret_key = "super_secret_key"

# Rails API deployed on Render cloud with postgresql 
RAILS_API_URL = "https://skillzone-api.onrender.com"

def get_current_employee(): # Retrieves the Employeed Id
    return session.get("employee")

# Declaring all CRUD helper Functions 
def api_get(path):  # GET PATH
    try: # Get the current authenticated employee
        employee = get_current_employee()
        params = {"employee_id": employee["id"]} if employee else {} # Passes the employee for authorisation purposes

        r = requests.get(f"{RAILS_API_URL}/{path}", params=params) # Constructs the full API endpoint
        if r.status_code != 200:
            return None

        data = r.json()
        if isinstance(data, str):
            return json.loads(data)
        return data
    
    except Exception as e:
        print("GET error:", e)
        return None

def api_post(path, data, files=None): # POST PATH
    try: # Post for creating new records
        employee = get_current_employee()
        params = {"employee_id": employee["id"]} if employee else {} # Passes the employee for authorisation purposes

        url = f"{RAILS_API_URL}/{path}" # Constructs the full API endpoint
        if files:
            return requests.post(url, params=params, data=data, files=files)
        return requests.post(url, params=params, json=data)
    except Exception as e:
        print("POST error:", e)
        return None


def api_patch(path, data): # PATCH PATH
    try: # Patch request for partial updates
        employee = get_current_employee()
        params = {"employee_id": employee["id"]} if employee else {} # Passes the employee for authorisation purposes

        return requests.patch(f"{RAILS_API_URL}/{path}", params=params, json=data) # Constructs the full API endpoint
    except Exception as e:
        print("PATCH error:", e)
        return None


def api_delete(path): # DELETE PATH
    try: # Delete request for deleting
        employee = get_current_employee()
        params = {"employee_id": employee["id"]} if employee else {} # Passes the employee for authorisation purposes

        return requests.delete(f"{RAILS_API_URL}/{path}", params=params) # Constructs the full API endpoint
    except Exception as e:
        print("DELETE error:", e)
        return None

# Login helper wrapper to ensure proper authentication
def login_required(func): 
    def wrapper(*args, **kwargs):
        if not get_current_employee():
            return redirect(url_for("login"))
        return func(*args, **kwargs) # Returns the wrapped route function if authentication is valid.
    wrapper.__name__ = func.__name__
    return wrapper

# Admin helper wrapper to ensure admins employee only
def admin_required(func):
    def wrapper(*args, **kwargs):
        user = get_current_employee()
        if not user or not user.get("admin"):
            return redirect(url_for("dashboard"))
        return func(*args, **kwargs) # Returns the route function only if admin privileges are verified.
    wrapper.__name__ = func.__name__
    return wrapper

# Public Routes Index route initial page 
@app.route("/")
def index():
    return render_template("Index.html")


# Register routes
@app.route("/register", methods=["GET", "POST"]) # Register route accepted CRUD function
def register():
    if request.method == "POST": # Post is expected to create new employee record
        employee_data = { 
            "employee": {
                "first_name": request.form["first_name"],
                "last_name": request.form["last_name"],
                "email": request.form["email"],
                "position": request.form["position"],
                "department": request.form["department"],
                "phone": request.form["phone"],
                "hire_date": request.form["hire_date"].strip(), # Re format the dates
                "gender": request.form["gender"].capitalize()   # Make first letter in gender capital for for the db
            }
        }

        res = api_post("employees", employee_data) # Sends the new employee 

        if res and res.status_code == 201:
            session["employee"] = res.json()
            flash("Account created!", "success")
            return redirect(url_for("dashboard"))

        flash("Failed to register.", "danger")
    return render_template("Register.html")


# Login routes
@app.route("/login", methods=["GET", "POST"]) # Login route accepted CRUD function
def login():
    if request.method == "POST": # Post sends the employee data to backends= to be verified
        login_data = {
            "email": request.form["email"].lower(),
            "hire_date": request.form["hire_date"]
        }

        res = requests.post(f"{RAILS_API_URL}/employees/login", json=login_data) # Constructs the endpoint to login a user 

        if res.status_code == 200:
            employee = res.json()
            session["employee"] = employee

            if employee.get("admin"):
                return redirect(url_for("admin_dashboard")) # If employee is an admin render the admin dashoboard

            return redirect(url_for("dashboard")) # Anything else render the dashboard

        flash("Invalid login details", "danger")
    return render_template("Login.html")

# Employee Dashboard 
@app.route("/dashboard")
@login_required # Ensure an employee is logged in
def dashboard():
    employee = get_current_employee() # GET employeee and set as current employee
    if not employee:
        return redirect(url_for("login"))

    if employee.get("admin"):
        return redirect(url_for("admin_dashboard"))

    enrollments = api_get("enrollments") or [] # Retrieves all the enrollments of the employee

    my_courses = [ #  Retrieves all the employee available course
        e["course"] for e in enrollments
        if e["employee"]["id"] == employee["id"]
    ]

    completed_course_ids = [ # Retrieve all the employee completed course
        e["course"]["id"] for e in enrollments
        if e["employee"]["id"] == employee["id"] and e["status"] == "completed"
    ]

    all_certs = api_get("certificates") or [] # Retrieve all the available certificate with available course

    my_certificates = [
        cert for cert in all_certs
        if cert["course"]["id"] in completed_course_ids
    ]

    return render_template(
        "Dashboard.html",
        employee=employee,
        my_courses=my_courses,
        certificates=my_certificates
    )

# Employees can update their profile
@app.route("/employee/profile", methods=["GET", "POST"])
def employee_profile():
    employee = get_current_employee()
    if not employee:
        return redirect(url_for("login"))

    # Retrieve form with existing values
    if request.method == "GET":
        return render_template("Employee_profile.html", employee=employee)

    # POST update employee
    update_data = {
        "employee": {
            "first_name": request.form["first_name"],
            "last_name": request.form["last_name"],
            "email": request.form["email"],
            "position": request.form["position"],
            "department": request.form["department"],
            "phone": request.form["phone"],
            "gender": request.form["gender"],
        }
    }

    # Send update request to Rails
    res = api_patch(f"employees/{employee['id']}", update_data)

    if res and res.status_code == 200:
        session["employee"] = res.json()  
        flash("Profile updated!", "success")
    else:
        flash("Update failed.", "danger")

    return redirect(url_for("employee_profile"))

# Admin Dashboard 
@app.route("/admin-dashboard")
@admin_required
def admin_dashboard():
    admin = get_current_employee()
    if not admin or not admin.get("admin"):  # Authorisation check
        return redirect(url_for("dashboard"))

    employees = api_get("employees") or [] # Retrieve all employees
    courses = api_get("courses") or [] # Retrieve all courses
    enrollments = api_get("enrollments") or [] # Retrieve all enrollments 
    certificates = api_get("certificates") or [] # Retrieve all certificates

    return render_template(
        "Admin_dashboard.html",
        employees=employees,
        enrollments=enrollments,
        courses=courses,
        certificates=certificates
    )

# Manage Employees 
@app.route("/manage_employees")
def manage_employees():
    admin = get_current_employee()
    if not admin or not admin.get("admin"):  # Authorisation check
        return redirect(url_for("dashboard"))

    employees = api_get("employees") or []
    enrollments = api_get("enrollments") or []  

    return render_template("Manage_employee.html", employees=employees, enrollments=enrollments)

# Admin dashboard route for certificate management
@app.route("/admin/certificates")
def admin_certificates():
    admin = get_current_employee() 
    if not admin or not admin.get("admin"): # Authorisation check
        return redirect(url_for("dashboard"))

    courses = api_get("courses") or [] # Retrieve courses
    certificates = api_get("certificates") or [] # Retrieve certificate

    return render_template(
        "admin_certificate.html",   
        courses=courses,
        certificates=certificates
    )

# Admin can delete any employee record 
@app.route("/employee/delete/<int:employee_id>", methods=["POST"])
def delete_employee(employee_id):
    admin = get_current_employee()
    if not admin or not admin.get("admin"):  # Authorisation check
        return redirect(url_for("dashboard"))

    res = api_delete(f"employees/{employee_id}")

    flash("Employee deleted" if res and res.status_code == 204 else "Failed", "info")
    return redirect(url_for("manage_employees"))

# Admin can create new employees on their dashboard 
@app.route("/admin/create-employee", methods=["POST"])
def admin_create_employee():
    admin = get_current_employee()
    if not admin or not admin.get("admin"):
        return redirect(url_for("login"))

    employee_data = {
        "employee": {
            "first_name": request.form["first_name"],
            "last_name": request.form["last_name"],
            "email": request.form["email"],
            "position": request.form["position"],
            "department": request.form["department"],
            "phone": request.form["phone"],
            "hire_date": request.form["hire_date"].strip(),
            "gender": request.form["gender"].capitalize(),
        }
    }

    res = api_post("employees", employee_data)

    if res and res.status_code == 201:
        flash("Employee created successfully!", "success")
    else:
        flash("Failed to create employee.", "danger")

    # Do not log the created employee in on creation
    return redirect(url_for("manage_employees"))

# Course List and Enrollment
@app.route("/courses", methods=["GET", "POST"])
def courses():
    employee = get_current_employee()
    if not employee:
        return redirect(url_for("login"))

    # Enrollment actions
    if request.method == "POST":
        course_id = int(request.form["course_id"])

        enroll_data = { # Send enroll data to the backedn
            "enrollment": {
                "employee_id": employee["id"],
                "course_id": course_id,
                "status": "active"
            }
        }

        res = api_post("enrollments", enroll_data)

        if res and res.status_code == 201:
            flash("Enrolled successfully!", "success")
        else:
            flash("Failed to enroll.", "danger")

        return redirect(url_for("courses"))

    # Retrieve all courses available 
    courses_list = api_get("courses") or []


    # Filter courses by employee department
    department_courses = [
        c for c in courses_list
        if c.get("department") == employee.get("department")
    ]

    # Render filtered courses
    return render_template(
        "Courses.html",
        courses=department_courses,
        employee=employee
    )

# Manage Courses and  Certificate Upload 
@app.route("/manage-courses", methods=["GET", "POST"])
def manage_courses():
    admin = get_current_employee()
    if not admin or not admin.get("admin"):  # Authorisation check
        return redirect(url_for("dashboard"))

    courses = api_get("courses") or []
    if request.method == "POST":   # Create new course
        course_data = {
            "course": {
                "title": request.form["title"],
                "description": request.form["description"],
                "duration_minutes": request.form["duration"],
                "capacity": request.form["capacity"],
                "level": request.form["level"],
                "start_date": request.form["start_date"],
                "end_date": request.form["end_date"],
                "youtube_url": request.form["youtube_url"],
                "department": admin["department"]
            }
        }

        res = api_post("courses", course_data)

        if not res or res.status_code != 201:
            flash("Course creation failed.", "danger")
            return redirect(url_for("manage_courses"))

        flash("Course created successfully!", "success")
        return redirect(url_for("manage_courses"))

    return render_template("Manage_course.html", courses=courses, employee=admin)    # Jinja has employee available


# Admin can edit any employee data
@app.route("/edit-employee/<int:employee_id>", methods=["POST"])
def edit_employee(employee_id):
    admin = get_current_employee()
    if not admin or not admin.get("admin"): # Authorisation check
        return redirect(url_for("dashboard"))

    update_data = {  # Updated data is sent to the backend
        "employee": { 
            "first_name": request.form["first_name"],
            "last_name": request.form["last_name"],
            "email": request.form["email"],
            "position": request.form["position"],
            "department": request.form["department"],
            "phone": request.form["phone"],
            "hire_date": request.form["hire_date"],
            "gender": request.form["gender"]
        }
    }

    res = api_patch(f"employees/{employee_id}", update_data)

    flash("Employee updated!" if res and res.status_code == 200 else "Failed to update employee.", "info")
    return redirect(url_for("manage_employees"))

# Admin can edit any employee enrollment status
@app.route("/admin/edit-enrollment/<int:enrollment_id>", methods=["POST"])
def admin_edit_enrollment(enrollment_id):
    admin = get_current_employee()
    if not admin or not admin.get("admin"):
        return redirect(url_for("dashboard"))

    new_status = request.form.get("status")
    new_course_id = request.form.get("course_id")

    update_data = { # Updated data is sent to the backend
        "enrollment": {
            "status": new_status,
            "course_id": int(new_course_id)
        }
    }

    res = api_patch(f"enrollments/{enrollment_id}", update_data)
    if res and res.status_code == 200:
        flash("Enrollment updated!", "success")
    else:
        flash("Failed to update enrollment.", "danger")

    return redirect(url_for("admin_enrollments"))


# Edit Course Admin
@app.route("/course/edit/<int:course_id>", methods=["POST"])
def edit_course(course_id):
    admin = get_current_employee()
    if not admin or not admin.get("admin"): # Authorisation check
        return redirect(url_for("dashboard"))

    course_data = {
        "course": {
            "title": request.form["title"],
            "description": request.form["description"],
            "duration_minutes": request.form["duration"],
            "capacity": request.form["capacity"],
            "level": request.form["level"],
            "start_date": request.form["start_date"],
            "end_date": request.form["end_date"],
            "youtube_url": request.form["youtube_url"], 
            "department": request.form["department"]
        }
    }

    res = api_patch(f"courses/{course_id}", course_data)
    flash("Course updated!" if res and res.status_code == 200 else "Update failed", "info")
    return redirect(url_for("manage_courses"))


# Delete Course 
@app.route("/course/delete/<int:course_id>", methods=["POST"])
def delete_course(course_id):
    admin = get_current_employee()
    if not admin or not admin.get("admin"): # Authorisation check
        return redirect(url_for("dashboard"))

    res = api_delete(f"courses/{course_id}")
    flash("Course deleted" if res and res.status_code == 204 else "Delete failed", "info")
    return redirect(url_for("manage_courses"))

# Allows the employee to take courses
@app.route("/course/<int:course_id>/take")
def take_course(course_id):
    employee = get_current_employee()
    if not employee:
        return redirect(url_for("login"))

    course = api_get(f"courses/{course_id}") # Retrieve the courses from 
    if not course:
        flash("Course not found.", "danger")
        return redirect(url_for("dashboard"))

    youtube_url = course.get("youtube_url") or ""  # Ensure URL is safe string 
    video_id = None

    if "v=" in youtube_url:
        video_id = youtube_url.split("v=")[1].split("&")[0]  # Handle full YouTube link
    elif "youtu.be/" in youtube_url:
        video_id = youtube_url.split("youtu.be/")[1].split("?")[0]  # Handle youtu.be short link
    elif "/embed/" in youtube_url:
        video_id = youtube_url.split("/embed/")[1].split("?")[0]    # Handle embed link


    embed_url = video_id if video_id else None  # Pass only the video ID 
    enrollments = api_get("enrollments") or []   # Get enrollment for this user
    enrollment = next(
        (e for e in enrollments
         if e["course"]["id"] == course_id
         and e["employee"]["id"] == employee["id"]),
        None
    )
    if not enrollment:
        flash("You must be enrolled to take this course.", "danger")
        return redirect(url_for("courses"))

    return render_template(
        "take_course.html",
        course=course,
        enrollment=enrollment,
        embed_url=embed_url  
    )

# Admin view All Enrollments
@app.route("/admin/enrollments")
def admin_enrollments():
    admin = get_current_employee()
    if not admin or not admin.get("admin"): # Authorisation check
        return redirect(url_for("dashboard"))

    enrollments = api_get("enrollments") or []
    courses = api_get("courses") or []

    return render_template(
        "Admin_enrollments.html",
        enrollments=enrollments,
        courses=courses
    )

# Admin can unenroll an employee from any course
@app.route("/unenroll/<int:enrollment_id>", methods=["POST"])
def unenroll(enrollment_id):
    admin = get_current_employee()
    if not admin or not admin.get("admin"): # Authorisation check
        return redirect(url_for("dashboard"))

    res = api_delete(f"enrollments/{enrollment_id}")
    flash("Unenrolled" if res and res.status_code == 204 else "Failed", "info")
    return redirect(url_for("admin_enrollments"))

# Route for when a user starts a course their progess is updated
@app.route("/update-progress/<int:course_id>", methods=["POST"])
def update_progress(course_id):
    employee = get_current_employee()
    if not employee:
        return "", 401

    data = request.get_json()
    progress = data.get("progress", 0)
    enrollments = api_get("enrollments") or []
    enrollment = next(
        (e for e in enrollments
         if e["course"]["id"] == course_id and e["employee"]["id"] == employee["id"]),
        None
    )
    if not enrollment:
        return "", 404

    update_data = {
        "enrollment": {
            "progress": progress
        }
    }

    api_patch(f"enrollments/{enrollment['id']}", update_data)
    return "", 200

# Route to mark a completed course and store record 
@app.route("/mark-completed/<int:course_id>", methods=["POST"])
def mark_completed(course_id):
    employee = get_current_employee()
    if not employee:
        return redirect(url_for("login"))

    enrollments = api_get("enrollments") or [] # Retrieve the enrollments
    enrollment = next(
        (e for e in enrollments
         if e["course"]["id"] == course_id and e["employee"]["id"] == employee["id"]),
        None
    )
    if not enrollment:
        flash("You are not enrolled in this course.", "danger")
        return redirect(url_for("courses"))

    update_data = {
        "enrollment": {
            "status": "completed",
            "progress": 100,
            "completed_on": date.today().isoformat()  # Rails expects date format  YYYY-MM-DD
        }
    }
    res = api_patch(f"enrollments/{enrollment['id']}", update_data)

    if res and res.status_code == 200:
        flash("Course marked as completed!", "success")
    else:
        flash("Failed to update course status.", "danger")
    return redirect(url_for("courses"))

# Admin route for admin to update
@app.route("/certificate/update/<int:cert_id>", methods=["POST"])
def update_certificate(cert_id):
    admin = get_current_employee()
    if not admin or not admin.get("admin"): # Authorisation check
        return redirect(url_for("dashboard"))

    name = request.form.get("name")
    description = request.form.get("description")
    issued_on = request.form.get("issued_on")
    expiry_date = request.form.get("expiry_date")
    logo = request.files.get("logo")
    if logo and logo.filename:
        data = {
            "certificate[name]": name,
            "certificate[description]": description,
            "certificate[issued_on]": issued_on,
            "certificate[expiry_date]": expiry_date,
            "certificate[employee_id]": admin["id"],  
        }
        files = {
            "certificate[document]": (logo.filename, logo.read())
        }
        try:
            res = requests.patch(
                f"{RAILS_API_URL}/certificates/{cert_id}",
                params={"employee_id": admin["id"]},
                data=data,
                files=files
            )
        except Exception as e:
            print("PATCH error:", e)
            res = None
    else:
        update_data = {
            "certificate": {
                "name": name,
                "description": description,
                "issued_on": issued_on,
                "expiry_date": expiry_date
            }
        }
        res = api_patch(f"certificates/{cert_id}", update_data)

    flash("Certificate updated!" if res and res.status_code == 200 else "Failed to update certificate.", "info")
    return redirect(url_for("admin_certificates"))

# Admin View All Certificates 
@app.route("/certificate/delete/<int:cert_id>", methods=["POST"])
def delete_certificate(cert_id):
    admin = get_current_employee()
    if not admin or not admin.get("admin"): # Authorisation check
        return redirect(url_for("dashboard"))

    res = api_delete(f"certificates/{cert_id}")
    flash("Certificate deleted" if res and res.status_code == 204 else "Failed", "danger")
    return redirect(url_for("admin_certificates"))


# Route for admin to create a certificate 
@app.route("/admin/certificates/create", methods=["POST"])
def create_certificate():
    admin = get_current_employee()

    # Authorisation check
    if not admin or not admin.get("admin"):
        return redirect(url_for("dashboard"))

    # Safely read form data
    name = (request.form.get("name") or "").strip()
    description = (request.form.get("description") or "").strip()
    issued_on = request.form.get("issued_on")
    expiry_date = request.form.get("expiry_date")
    course_id = request.form.get("course_id")
    logo = request.files.get("logo")

    # Validation
    if not all([name, description, issued_on, expiry_date, course_id]):
        flash("All fields are required.", "danger")
        return redirect(url_for("admin_certificates"))

    # Create PDF using ReportLab
    pdf_buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        pdf_buffer,
        pagesize=A4,
        leftMargin=40,
        rightMargin=40,
        topMargin=60,
        bottomMargin=40
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        name="Title",
        parent=styles["Heading1"],
        fontSize=28,
        alignment=TA_CENTER,
        spaceAfter=20
    )

    desc_style = ParagraphStyle(
        name="Description",
        parent=styles["BodyText"],
        fontSize=14,
        alignment=TA_CENTER,
        leading=18,
        spaceAfter=30
    )

    footer_style = ParagraphStyle(
        name="Footer",
        parent=styles["BodyText"],
        fontSize=12,
        alignment=TA_CENTER,
        leading=16
    )

    content = []

    #logo
    if logo and logo.filename:
        try:
            logo.seek(0)
            img = Image(logo, width=120, height=120)
            content.append(img)
            content.append(Spacer(1, 20))
        except Exception:
            pass  # Ignore logo errors for testing

    content.append(Paragraph(name, title_style))
    content.append(Paragraph(description, desc_style))

    footer_html = f"""
    Issued by: {admin['first_name']} {admin['last_name']}<br/>
    Issued On: {issued_on}<br/>
    Expiry Date: {expiry_date}
    """
    content.append(Paragraph(footer_html, footer_style))

    # Build PDF
    doc.build(content)
    pdf_buffer.seek(0)

    # Send PDF to Rails API
    data = {
        "certificate[name]": name,
        "certificate[description]": description,
        "certificate[issued_on]": issued_on,
        "certificate[expiry_date]": expiry_date,
        "certificate[employee_id]": admin["id"], 
        "certificate[course_id]": course_id,
    }

    files = {
        "certificate[document]": (
            "certificate.pdf",
            pdf_buffer,
            "application/pdf"
        )
    }

    res = api_post("certificates", data, files=files)

    if res and res.status_code == 201:
        flash("Certificate created successfully!", "success")
    else:
        error_msg = "Failed to create certificate."
        if res:
            try:
                body = res.json()
                if body.get("errors"):
                    error_msg = ", ".join(body["errors"])
                else:
                    error_msg = f"Failed (status {res.status_code})."
            except Exception:
                pass

        flash(error_msg, "danger")
    return redirect(url_for("admin_certificates"))


# Logout user from session 
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))

# Standalone application on http://127.0.0.1:5000/
if __name__ == "__main__":
    app.run(debug=True, port=5000)
