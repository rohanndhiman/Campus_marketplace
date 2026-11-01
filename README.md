# 🎓 Campus Skill Marketplace System
### A DBMS Mini-Project | Flask + MySQL

---

## 📁 Folder Structure

```
campus_skill_marketplace/
│
├── app.py                  ← Flask backend (all routes & logic)
├── database.sql            ← MySQL schema + sample data
├── requirements.txt        ← Python dependencies
│
├── templates/              ← HTML pages (Jinja2 templates)
│   ├── base.html           ← Common navbar & layout
│   ├── login.html          ← Login page
│   ├── register.html       ← Registration page
│   ├── dashboard.html      ← Home dashboard
│   ├── profile.html        ← Student profile & skills
│   ├── students.html       ← Browse all students
│   ├── requests.html       ← All service requests
│   ├── post_request.html   ← Post a new request
│   ├── my_tasks.html       ← My tasks & posted requests
│   ├── feedback.html       ← Give rating & review
│   └── verify_skills.html  ← Admin: verify skills
│
└── static/
    └── css/
        └── style.css       ← All styling
```

---

## ⚙️ Step-by-Step Setup

### Step 1: Install Python dependencies

```bash
pip install flask flask-mysqldb werkzeug
```

### Step 2: Setup MySQL

Make sure MySQL is running on your machine.
Open MySQL shell and run:

```sql
mysql -u root -p < database.sql
```

OR open MySQL Workbench, open the `database.sql` file, and run it.

### Step 3: Configure MySQL password in app.py

Open `app.py` and update this section (around line 25):

```python
app.config['MYSQL_HOST']     = 'localhost'
app.config['MYSQL_USER']     = 'root'
app.config['MYSQL_PASSWORD'] = 'your_password_here'   ← EDIT THIS
app.config['MYSQL_DB']       = 'campus_marketplace'
```

### Step 4: Run the Flask app

```bash
python app.py
```

### Step 5: Open in browser

```
http://localhost:5000
```

---

## 🧪 Test Credentials (Sample Data)

Register a new account on the app, OR manually insert into MySQL.
Sample students in `database.sql` have placeholder hashed passwords.

**Recommended**: Just register fresh accounts via the web UI at `/register`.

---

## 📊 Database Tables Explained

| Table | Purpose |
|-------|---------|
| `Students` | All registered users (students) |
| `Skills` | Master list of available skills |
| `Student_Skills` | Which student has which skill (with verified flag) |
| `Service_Requests` | Tasks posted by students |
| `Transactions` | Task assignments (who does which task) |
| `Feedback` | Ratings and comments after task completion |

### Relationships:
- A student can have **many** skills → via `Student_Skills`
- A student can post **many** service requests → `Service_Requests.posted_by`
- A request can be assigned to **one** student → `Transactions`
- A transaction can have **one** feedback → `Feedback`

---

## 🗣️ Module-wise Viva Explanation

### Module 1: Authentication
- `register()` — saves new student with `werkzeug`-hashed password
- `login()` — verifies password using `check_password_hash`, sets Flask session
- `logout()` — clears the session

### Module 2: Dashboard
- Shows quick stats (open requests, my tasks, my posts)
- Lists latest 5 open requests as a quick overview

### Module 3: Profile & Skills
- Each student has a profile with branch, year, bio
- Students add/remove skills; admin can mark them as verified
- Average rating is computed from Feedback table via a JOIN query

### Module 4: Browse Students
- Shows all students as cards; can filter by skill
- Uses a `LIKE` query to match skill names

### Module 5: Service Requests
- Students post tasks describing what help they need
- Any other student can "Accept" to assign themselves
- Status flows: Open → Assigned → Completed

### Module 6: Task Management
- Assigned student sees tasks and updates status (Pending / In Progress / Completed)
- When marked Completed, the parent Service_Request also updates

### Module 7: Feedback
- After task completion, feedback can be given (1–5 stars + comment)
- One feedback per transaction per user (enforced by UNIQUE constraint in DB)

### Module 8: Admin
- Simple panel to toggle `is_verified` for student skills
- In production, this would be role-restricted

---

## 🔑 Key SQL Concepts Used

- `PRIMARY KEY`, `FOREIGN KEY` with `ON DELETE CASCADE`
- `UNIQUE` constraint on `email`, `Student_Skills (student_id, skill_id)`
- `ENUM` for status fields
- `JOIN` queries (INNER + LEFT) across multiple tables
- `AVG()`, `COUNT()`, `ROUND()` aggregate functions
- `LIKE` for search/filter

---
