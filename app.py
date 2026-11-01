# ============================================================
# Campus Skill Marketplace System
# app.py - Main Flask Application
# ============================================================
# HOW TO RUN:
#   pip install flask flask-mysqldb werkzeug
#   python app.py
# ============================================================

from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_mysqldb import MySQL
from werkzeug.security import generate_password_hash, check_password_hash
import os

# ── App Setup ────────────────────────────────────────────────
app = Flask(__name__)

# Secret key for session management (change in production)
app.secret_key = 'campus_marketplace_secret_key_2024'

# ── MySQL Configuration ──────────────────────────────────────
# Edit these values to match your MySQL setup
app.config['MYSQL_HOST']     = 'localhost'
app.config['MYSQL_USER']     = 'root'
app.config['MYSQL_PASSWORD'] = 'Rohan#8733'          # Your MySQL password
app.config['MYSQL_DB']       = 'campus_marketplace'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'  # Return rows as dicts

mysql = MySQL(app)

# ============================================================
# HELPER FUNCTION
# ============================================================

def login_required(f):
    """Decorator to protect routes that need login."""
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'student_id' not in session:
            flash('Please login first.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated

def admin_required(f):
    """Decorator to protect routes that need admin privileges."""
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'student_id' not in session:
            flash('Please login first.', 'warning')
            return redirect(url_for('login'))
        if not session.get('is_admin'):
            flash('Access denied: Admins only.', 'danger')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated


# ============================================================
# MODULE 1: AUTHENTICATION
# Routes: /register, /login, /logout
# ============================================================

@app.route('/')
def index():
    """Home page - redirect to dashboard if logged in, else to login."""
    if 'student_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    """
    Register a new student.
    GET  → Show registration form
    POST → Save student to DB (with hashed password)
    """
    if request.method == 'POST':
        name     = request.form['name'].strip()
        email    = request.form['email'].strip().lower()
        password = request.form['password']
        branch   = request.form['branch'].strip()
        year     = request.form['year']
        bio      = request.form.get('bio', '').strip()

        # Hash the password before saving (never store plain text)
        hashed_pw = generate_password_hash(password)

        cursor = mysql.connection.cursor()
        try:
            cursor.execute(
                "INSERT INTO Students (name, email, password, branch, year, bio) "
                "VALUES (%s, %s, %s, %s, %s, %s)",
                (name, email, hashed_pw, branch, year, bio)
            )
            mysql.connection.commit()
            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            # Email already exists → show error
            flash('Email already registered. Try logging in.', 'danger')
        finally:
            cursor.close()

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    """
    Login an existing student.
    GET  → Show login form
    POST → Verify credentials, set session
    """
    if request.method == 'POST':
        email    = request.form['email'].strip().lower()
        password = request.form['password']

        cursor = mysql.connection.cursor()
        cursor.execute("SELECT * FROM Students WHERE email = %s", (email,))
        student = cursor.fetchone()
        cursor.close()

        if student and check_password_hash(student['password'], password):
            # Save student info in session (like a login cookie)
            session['student_id']   = student['student_id']
            session['student_name'] = student['name']
            session['is_admin']     = bool(student.get('is_admin'))
            flash(f"Welcome back, {student['name']}!", 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid email or password.', 'danger')

    return render_template('login.html')


@app.route('/logout')
def logout():
    """Clear session and logout."""
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))


# ============================================================
# MODULE 2: DASHBOARD
# ============================================================

@app.route('/dashboard')
@login_required
def dashboard():
    """
    Main dashboard showing:
    - Open service requests
    - Student's own tasks
    - Quick stats
    """
    sid = session['student_id']
    cursor = mysql.connection.cursor()

    # Count open requests
    cursor.execute("SELECT COUNT(*) as cnt FROM Service_Requests WHERE status='Open'")
    open_requests = cursor.fetchone()['cnt']

    # Count my posted requests
    cursor.execute("SELECT COUNT(*) as cnt FROM Service_Requests WHERE posted_by=%s", (sid,))
    my_requests = cursor.fetchone()['cnt']

    # Count tasks assigned to me
    cursor.execute("SELECT COUNT(*) as cnt FROM Transactions WHERE assigned_to=%s", (sid,))
    my_tasks = cursor.fetchone()['cnt']

    # Recent open requests (latest 5)
    cursor.execute("""
        SELECT sr.*, s.name as poster_name, sk.skill_name
        FROM Service_Requests sr
        JOIN Students s  ON sr.posted_by = s.student_id
        JOIN Skills sk   ON sr.skill_id  = sk.skill_id
        WHERE sr.status = 'Open'
        ORDER BY sr.created_at DESC
        LIMIT 5
    """)
    recent_requests = cursor.fetchall()
    cursor.close()

    return render_template('dashboard.html',
        open_requests=open_requests,
        my_requests=my_requests,
        my_tasks=my_tasks,
        recent_requests=recent_requests
    )


# ============================================================
# MODULE 3: STUDENT PROFILE & SKILLS
# Routes: /profile, /profile/<id>, /add_skill, /remove_skill
# ============================================================

@app.route('/profile')
@login_required
def profile():
    """Show logged-in student's own profile."""
    return redirect(url_for('view_profile', student_id=session['student_id']))


@app.route('/profile/<int:student_id>')
@login_required
def view_profile(student_id):
    """
    View any student's profile.
    Shows their skills, posted requests, and average rating.
    """
    cursor = mysql.connection.cursor()

    # Get student info
    cursor.execute("SELECT * FROM Students WHERE student_id = %s", (student_id,))
    student = cursor.fetchone()
    if not student:
        flash('Student not found.', 'danger')
        return redirect(url_for('dashboard'))

    # Get student's skills
    cursor.execute("""
        SELECT sk.skill_id, sk.skill_name, sk.category, ss.is_verified
        FROM Student_Skills ss
        JOIN Skills sk ON ss.skill_id = sk.skill_id
        WHERE ss.student_id = %s
    """, (student_id,))
    skills = cursor.fetchall()

    # Get average rating for this student
    cursor.execute("""
        SELECT ROUND(AVG(f.rating), 1) as avg_rating, COUNT(*) as total_reviews
        FROM Feedback f
        JOIN Transactions t ON f.txn_id = t.txn_id
        WHERE t.assigned_to = %s
    """, (student_id,))
    rating_info = cursor.fetchone()

    # Get all skills for the "Add Skill" dropdown
    cursor.execute("SELECT * FROM Skills ORDER BY skill_name")
    all_skills = cursor.fetchall()

    cursor.close()

    return render_template('profile.html',
        student=student,
        skills=skills,
        rating_info=rating_info,
        all_skills=all_skills,
        is_own_profile=(student_id == session['student_id'])
    )


@app.route('/add_skill', methods=['POST'])
@login_required
def add_skill():
    """Add a skill to the logged-in student's profile."""
    sid      = session['student_id']
    skill_id = request.form['skill_id']

    cursor = mysql.connection.cursor()
    try:
        cursor.execute(
            "INSERT INTO Student_Skills (student_id, skill_id) VALUES (%s, %s)",
            (sid, skill_id)
        )
        mysql.connection.commit()
        flash('Skill added successfully!', 'success')
    except:
        flash('You already have this skill.', 'warning')
    finally:
        cursor.close()

    return redirect(url_for('profile'))


@app.route('/remove_skill/<int:skill_id>')
@login_required
def remove_skill(skill_id):
    """Remove a skill from the logged-in student's profile."""
    sid = session['student_id']
    cursor = mysql.connection.cursor()
    cursor.execute(
        "DELETE FROM Student_Skills WHERE student_id=%s AND skill_id=%s",
        (sid, skill_id)
    )
    mysql.connection.commit()
    cursor.close()
    flash('Skill removed.', 'info')
    return redirect(url_for('profile'))


# ============================================================
# MODULE 4: BROWSE STUDENTS
# Route: /students
# ============================================================

@app.route('/students')
@login_required
def students():
    """
    Browse and search all students by skill.
    Supports optional ?skill= query parameter for filtering.
    """
    skill_filter = request.args.get('skill', '').strip()
    cursor = mysql.connection.cursor()

    if skill_filter:
        # Filter students who have the searched skill
        cursor.execute("""
            SELECT DISTINCT s.student_id, s.name, s.branch, s.year, s.bio,
                   ROUND(AVG(f.rating),1) as avg_rating
            FROM Students s
            JOIN Student_Skills ss ON s.student_id = ss.student_id
            JOIN Skills sk         ON ss.skill_id  = sk.skill_id
            LEFT JOIN Transactions t ON t.assigned_to = s.student_id
            LEFT JOIN Feedback f     ON f.txn_id = t.txn_id
            WHERE sk.skill_name LIKE %s AND s.student_id != %s
            GROUP BY s.student_id
        """, (f'%{skill_filter}%', session['student_id']))
    else:
        # Show all students except logged-in user
        cursor.execute("""
            SELECT s.student_id, s.name, s.branch, s.year, s.bio,
                   ROUND(AVG(f.rating),1) as avg_rating
            FROM Students s
            LEFT JOIN Transactions t ON t.assigned_to = s.student_id
            LEFT JOIN Feedback f     ON f.txn_id = t.txn_id
            WHERE s.student_id != %s
            GROUP BY s.student_id
            ORDER BY s.name
        """, (session['student_id'],))

    all_students = cursor.fetchall()

    # For each student, fetch their skills
    for student in all_students:
        cursor.execute("""
            SELECT sk.skill_name, ss.is_verified
            FROM Student_Skills ss
            JOIN Skills sk ON ss.skill_id = sk.skill_id
            WHERE ss.student_id = %s
        """, (student['student_id'],))
        student['skills'] = cursor.fetchall()

    # All skills for the filter dropdown
    cursor.execute("SELECT skill_name FROM Skills ORDER BY skill_name")
    all_skills = cursor.fetchall()

    cursor.close()
    return render_template('students.html',
        students=all_students,
        all_skills=all_skills,
        skill_filter=skill_filter
    )


# ============================================================
# MODULE 5: SERVICE REQUESTS
# Routes: /requests, /post_request, /assign/<id>
# ============================================================

@app.route('/requests')
@login_required
def requests_list():
    """View all open service requests."""
    cursor = mysql.connection.cursor()
    cursor.execute("""
        SELECT sr.*, s.name as poster_name, sk.skill_name
        FROM Service_Requests sr
        JOIN Students s  ON sr.posted_by = s.student_id
        JOIN Skills sk   ON sr.skill_id  = sk.skill_id
        ORDER BY sr.created_at DESC
    """)
    reqs = cursor.fetchall()

    # Check which requests are already assigned
    for r in reqs:
        cursor.execute(
            "SELECT * FROM Transactions WHERE request_id=%s", (r['request_id'],)
        )
        r['transaction'] = cursor.fetchone()

    cursor.close()
    return render_template('requests.html', requests=reqs)


@app.route('/post_request', methods=['GET', 'POST'])
@login_required
def post_request():
    """
    Post a new service request.
    GET  → Show the form with skill dropdown
    POST → Save the request to DB
    """
    cursor = mysql.connection.cursor()

    if request.method == 'POST':
        title       = request.form['title'].strip()
        description = request.form['description'].strip()
        skill_id    = request.form['skill_id']
        posted_by   = session['student_id']

        cursor.execute(
            "INSERT INTO Service_Requests (posted_by, skill_id, title, description) "
            "VALUES (%s, %s, %s, %s)",
            (posted_by, skill_id, title, description)
        )
        mysql.connection.commit()
        cursor.close()
        flash('Service request posted!', 'success')
        return redirect(url_for('requests_list'))

    # GET: load skill list for dropdown
    cursor.execute("SELECT * FROM Skills ORDER BY skill_name")
    all_skills = cursor.fetchall()
    cursor.close()
    return render_template('post_request.html', all_skills=all_skills)


@app.route('/assign/<int:request_id>', methods=['POST'])
@login_required
def assign_task(request_id):
    """
    Assign a task to the currently logged-in student.
    Only works if the request is still 'Open'.
    """
    sid = session['student_id']
    cursor = mysql.connection.cursor()

    # Check request exists and is open
    cursor.execute("SELECT * FROM Service_Requests WHERE request_id=%s", (request_id,))
    req = cursor.fetchone()

    if req and req['status'] == 'Open' and req['posted_by'] != sid:
        # Create transaction record
        cursor.execute(
            "INSERT INTO Transactions (request_id, assigned_to) VALUES (%s, %s)",
            (request_id, sid)
        )
        # Update request status to Assigned
        cursor.execute(
            "UPDATE Service_Requests SET status='Assigned' WHERE request_id=%s",
            (request_id,)
        )
        mysql.connection.commit()
        flash('Task assigned to you!', 'success')
    else:
        flash('Cannot assign this task.', 'warning')

    cursor.close()
    return redirect(url_for('requests_list'))


# ============================================================
# MODULE 6: TASK MANAGEMENT (MY TASKS)
# Routes: /my_tasks, /update_status/<txn_id>
# ============================================================

@app.route('/my_tasks')
@login_required
def my_tasks():
    """
    Show all tasks assigned to the logged-in student.
    Also shows requests posted BY the student.
    """
    sid = session['student_id']
    cursor = mysql.connection.cursor()

    # Tasks assigned TO me
    cursor.execute("""
        SELECT t.*, sr.title, sr.description, sk.skill_name,
               s.name as poster_name, sr.request_id
        FROM Transactions t
        JOIN Service_Requests sr ON t.request_id  = sr.request_id
        JOIN Skills sk           ON sr.skill_id   = sk.skill_id
        JOIN Students s          ON sr.posted_by  = s.student_id
        WHERE t.assigned_to = %s
        ORDER BY t.assigned_at DESC
    """, (sid,))
    assigned_tasks = cursor.fetchall()

    # Check if feedback already given for each task
    for task in assigned_tasks:
        cursor.execute(
            "SELECT * FROM Feedback WHERE txn_id=%s AND given_by=%s",
            (task['txn_id'], sid)
        )
        task['my_feedback'] = cursor.fetchone()

    # Requests POSTED by me
    cursor.execute("""
        SELECT sr.*, sk.skill_name, t.task_status, t.txn_id,
               s.name as assignee_name
        FROM Service_Requests sr
        JOIN Skills sk ON sr.skill_id = sk.skill_id
        LEFT JOIN Transactions t ON t.request_id = sr.request_id
        LEFT JOIN Students s     ON t.assigned_to = s.student_id
        WHERE sr.posted_by = %s
        ORDER BY sr.created_at DESC
    """, (sid,))
    posted_requests = cursor.fetchall()

    cursor.close()
    return render_template('my_tasks.html',
        assigned_tasks=assigned_tasks,
        posted_requests=posted_requests
    )


@app.route('/update_status/<int:txn_id>', methods=['POST'])
@login_required
def update_status(txn_id):
    """
    Update the task status (Pending → In Progress → Completed).
    Only the assigned student can update their own task status.
    """
    new_status = request.form['status']
    sid        = session['student_id']

    cursor = mysql.connection.cursor()
    cursor.execute(
        "UPDATE Transactions SET task_status=%s "
        "WHERE txn_id=%s AND assigned_to=%s",
        (new_status, txn_id, sid)
    )
    # If completed, also update the parent request
    if new_status == 'Completed':
        cursor.execute("""
            UPDATE Service_Requests SET status='Completed'
            WHERE request_id = (SELECT request_id FROM Transactions WHERE txn_id=%s)
        """, (txn_id,))
    mysql.connection.commit()
    cursor.close()
    flash('Task status updated!', 'success')
    return redirect(url_for('my_tasks'))


# ============================================================
# MODULE 7: FEEDBACK & RATINGS
# Routes: /give_feedback/<txn_id>
# ============================================================

@app.route('/give_feedback/<int:txn_id>', methods=['GET', 'POST'])
@login_required
def give_feedback(txn_id):
    """
    Give feedback for a completed task.
    GET  → Show feedback form
    POST → Save rating + comment
    """
    sid = session['student_id']
    cursor = mysql.connection.cursor()

    # Get transaction details for display
    cursor.execute("""
        SELECT t.*, sr.title, s.name as assignee_name
        FROM Transactions t
        JOIN Service_Requests sr ON t.request_id = sr.request_id
        JOIN Students s          ON t.assigned_to = s.student_id
        WHERE t.txn_id = %s
    """, (txn_id,))
    txn = cursor.fetchone()

    if not txn:
        flash('Transaction not found.', 'danger')
        cursor.close()
        return redirect(url_for('my_tasks'))

    if request.method == 'POST':
        rating  = request.form['rating']
        comment = request.form.get('comment', '').strip()

        try:
            cursor.execute(
                "INSERT INTO Feedback (txn_id, given_by, rating, comment) "
                "VALUES (%s, %s, %s, %s)",
                (txn_id, sid, rating, comment)
            )
            mysql.connection.commit()
            flash('Feedback submitted! Thank you.', 'success')
        except:
            flash('You have already given feedback for this task.', 'warning')
        finally:
            cursor.close()
        return redirect(url_for('my_tasks'))

    cursor.close()
    return render_template('feedback.html', txn=txn)


# ============================================================
# MODULE 8: ADMIN - SKILL VERIFICATION
# Route: /admin/verify_skills
# ============================================================

@app.route('/admin/verify_skills')
@admin_required
def verify_skills():
    """
    Simple admin panel to verify student skills.
    In a real app, you'd add an admin role check here.
    """
    cursor = mysql.connection.cursor()
    cursor.execute("""
        SELECT ss.id, s.name as student_name, sk.skill_name, ss.is_verified
        FROM Student_Skills ss
        JOIN Students s ON ss.student_id = s.student_id
        JOIN Skills sk  ON ss.skill_id   = sk.skill_id
        ORDER BY ss.is_verified ASC, s.name ASC
    """)
    all_student_skills = cursor.fetchall()
    cursor.close()
    return render_template('verify_skills.html', all_student_skills=all_student_skills)


@app.route('/admin/toggle_verify/<int:ss_id>')
@admin_required
def toggle_verify(ss_id):
    """Toggle a skill's verified status."""
    cursor = mysql.connection.cursor()
    cursor.execute(
        "UPDATE Student_Skills SET is_verified = NOT is_verified WHERE id = %s",
        (ss_id,)
    )
    mysql.connection.commit()
    cursor.close()
    flash('Skill verification status updated.', 'success')
    return redirect(url_for('verify_skills'))


# ============================================================
# RUN THE APP
# ============================================================
if __name__ == '__main__':
    # debug=True → auto-reloads on code changes (turn off in production)
    app.run(debug=True, port=5000)
