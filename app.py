from flask import Flask, render_template, request, redirect, url_for, session, flash
import requests
from config import API_BASE_URL, SECRET_KEY

app = Flask(__name__)
app.secret_key = SECRET_KEY


# ============= Authentication Routes ============= #

@app.route('/')
def index():
    user = session.get('user')
    return render_template('index.html', user=user)

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        data = {
            "employee": {
                "first_name": request.form['first_name'],
                "last_name": request.form['last_name'],
                "email": request.form['email'],
                "phone": request.form['phone'],
                "position": request.form['position'],
                "department": request.form['department'],
                "gender": request.form['gender'],
                "hire_date": request.form['hire_date']
            }
        }
        response = requests.post(f"{API_BASE_URL}/employees", json=data)
        if response.ok:
            flash("Signup successful! You can now log in.", "success")
            return redirect(url_for('login'))
        else:
            flash("Signup failed. Check input details.", "danger")
    return render_template('signup.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        # Simulate authentication by checking employee existence
        response = requests.get(f"{API_BASE_URL}/employees")
        if response.ok:
            employees = response.json()
            user = next((e for e in employees if e['email'] == email), None)
            if user:
                session['user'] = user
                flash(f"Welcome, {user['first_name']}!", "success")
                return redirect(url_for('index'))
        flash("Invalid email or user not found.", "danger")
    return render_template('login.html')


# ============= Employee View (Admin Only Edit) ============= #
@app.route('/employees')
def employees():
    user = session.get('user')
    if not user:
        return redirect(url_for('login'))
    response = requests.get(f"{API_BASE_URL}/employees")
    employees = response.json() if response.ok else []
    return render_template('employees.html', employees=employees, user=user)


# ============= Course Management ============= #
@app.route('/courses')
def courses():
    user = session.get('user')
    response = requests.get(f"{API_BASE_URL}/courses")
    courses = response.json() if response.ok else []
    return render_template('courses.html', courses=courses, user=user)

@app.route('/courses/new', methods=['GET', 'POST'])
def create_course():
    user = session.get('user')
    if not user or user.get('position') != 'Manager':
        flash("Access denied. Only managers can create courses.", "danger")
        return redirect(url_for('courses'))

    if request.method == 'POST':
        data = {
            "course": {
                "title": request.form['title'],
                "duration_minutes": request.form['duration_minutes'],
                "capacity": request.form['capacity'],
                "level": request.form['level'],
                "start_date": request.form['start_date'],
                "end_date": request.form['end_date']
            }
        }
        response = requests.post(f"{API_BASE_URL}/courses", json=data)
        if response.ok:
            flash("Course created successfully!", "success")
            return redirect(url_for('courses'))
        flash("Failed to create course.", "danger")
    return render_template('course_form.html', user=user)


@app.route('/courses/delete/<int:id>')
def delete_course(id):
    user = session.get('user')
    if not user or user.get('position') != 'Manager':
        flash("Only managers can delete courses.", "danger")
        return redirect(url_for('courses'))
    requests.delete(f"{API_BASE_URL}/courses/{id}")
    flash("Course deleted successfully.", "info")
    return redirect(url_for('courses'))


# ============= Enrollments ============= #
@app.route('/enrollments')
def enrollments():
    user = session.get('user')
    if not user:
        return redirect(url_for('login'))
    response = requests.get(f"{API_BASE_URL}/enrollments")
    enrollments = response.json() if response.ok else []
    return render_template('enrollments.html', enrollments=enrollments, user=user)


@app.route('/enroll/<int:course_id>')
def enroll(course_id):
    user = session.get('user')
    if not user:
        return redirect(url_for('login'))
    data = {
        "enrollment": {
            "employee_id": user['id'],
            "course_id": course_id,
            "status": "active",
            "progress": 0
        }
    }
    response = requests.post(f"{API_BASE_URL}/enrollments", json=data)
    if response.ok:
        flash("Enrolled successfully!", "success")
    else:
        flash("Enrollment failed.", "danger")
    return redirect(url_for('courses'))


# ============= Certificates (Manager Only) ============= #
@app.route('/certificates')
def certificates():
    user = session.get('user')
    response = requests.get(f"{API_BASE_URL}/certificates")
    certificates = response.json() if response.ok else []
    return render_template('certificates.html', certificates=certificates, user=user)


@app.route('/logout')
def logout():
    session.clear()
    flash("Logged out successfully.", "info")
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
