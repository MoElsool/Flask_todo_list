# Lab 2: Login & To-Do Application

## Team
- Name :Mohamed Osama-2304071
       :Seif El-din Tarek-2304080  

Seif: (Backend & Database):Set up database connection and .env file.   Create user authentication API (Login & Register).Handle server-side validation and database queries.

Mohamed(Frontend & UI):Design registration and login forms.Connect frontend forms with backend APIs.Add client-side validation and responsive design.
Testing & Bug Fixing. 

## Technology
- Back end: Flask (Python), PyMySQL, bcrypt
- Front end: HTML, CSS, JavaScript
- Database: MySQL

## How to run
1. Install Python, MySQL, Git.
2. `python -m venv venv` then activate it.
3. `pip install -r requirements.txt`
4. Run `database/schema.sql` in MySQL.
5. Copy `.env.example` to `.env` and fill in your values.
6. `python main.py`
7. Open http://127.0.0.1:5000

## Features
4. Features Built

- R1: Environment & Database Configuration
  Database credentials and the Flask secret key are loaded from a `.env` file (not committed; `.env.example` is provided).

- R2: User Registration
  New users create an account with name, email and password; passwords are stored as bcrypt hashes and duplicate emails are rejected.

- R3: User Authentication & Login
  Login verifies the password against the stored bcrypt hash and keeps the user logged in with a Flask session; logout clears it.

- R4: Input Validation
  Client-side (JavaScript) and server-side validation: required fields, email format, matching passwords, password length limit, and to-do title length.

- R5: Database Integration
  The app stores users and to-do items in MySQL (`database/schema.sql`); each to-do belongs to a user through a foreign key.

- R7: Error Handling
  Validation and login errors are shown to the user as clear messages, and a custom error page is shown for 404/500 errors.

- R9: User Notifications
  Flash messages report errors (invalid login, duplicate email, invalid input) on the page.

- R10: Security & Password Hashing
  Passwords are hashed with bcrypt, all SQL queries are parameterized (prevents SQL injection), and to-do queries are filtered by `user_id` so users only access their own items.

- To-Do list: add, edit, mark done/undone, and delete tasks (per user).

## Bonus
- Dark mode: a toggle button on every page; the choice is saved in the browser (`localStorage`) and the first visit follows the system theme.
- Open tasks counter: the to-do page shows how many tasks are still not done.

## Answers
(a) It ensures Authorization and Data Ownership. Adding AND user_id = ? prevents users from updating or deleting tasks that belong to other users.

What changes if you remove it?

If removed (e.g., matching only by id), any authenticated user could modify or delete another user's to-do item simply by guessing or passing its item ID (leading to an IDOR / Insecure Direct Object Reference vulnerability).

(b) The database will reject the operation and throw a database error (foreign key constraint violation).

Constraint:

Foreign Key Constraint (which enforces Referential Integrity).

(c) For Security and Privacy. Storing plain-text passwords exposes users to security risks if the database is breached or accessed by unauthorized personnel. Password hashes (using strong algorithms like Bcrypt or Argon2) are one-way functions, ensuring that original passwords cannot be recovered even if the database is compromised.

(d) Because NOT NULL in SQL only prevents NULL values; it does not prevent empty strings (e.g., "" or spaces "   "). The application-level check is necessary to validate business logic, sanitize user inputs, and provide custom, user-friendly error messages before querying the database.