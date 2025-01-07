from flask import Flask, render_template, url_for, redirect, request, flash, make_response
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, login_user, LoginManager, login_required, logout_user, current_user
from flask_wtf import FlaskForm
from flask_weasyprint import HTML, render_pdf
from wtforms import StringField, PasswordField, SubmitField, SelectField, IntegerField
from wtforms.validators import InputRequired, Length, ValidationError
from flask_bcrypt import Bcrypt
from sbert_similarity import serve_ai_question, add_question_to_faq_wannabe
import json

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SECRET_KEY'] = 'my_secret_key'
app.config['SQLALCHEMY_ECHO'] = True

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), nullable=False, unique=True)
    password = db.Column(db.String(80), nullable=False)
    role = db.Column(db.String(20), nullable=False)

    # Relationship to link with the Student table
    student = db.relationship('Student', back_populates='user', uselist=False)

    # Relationship to Employee
    employee = db.relationship('Employee', back_populates='user', uselist=False)

class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    name = db.Column(db.String(100), nullable=False)
    address = db.Column(db.String(200), nullable=False)
    courses = db.Column(db.Text, nullable=True) # Store as JSON or comma-separated values
    grades = db.Column(db.Text, nullable=True)  # Store as JSON or other formats
    group = db.Column(db.Text, nullable=True)   # Student group. 311CA 322CC 432CB

    # Relationship to User
    user = db.relationship('User', back_populates='student')

    def enroll_in_course(self, course_name, teacher_name):
        # Add a new course to the list of courses
        course_entry = f"{course_name} - {teacher_name}"
        courses_list = json.loads(self.courses) if self.courses else []
        if course_entry not in courses_list:
            courses_list.append(course_entry)
        self.courses = json.dumps(courses_list)

    def grade_student(self, course_name, teacher_name, course_grade):
        entry = f"{course_name} - {teacher_name} - Grade: {course_grade}"
        grades_list = json.loads(self.grades) if self.grades else []
        if entry not in grades_list:
            grades_list.append(entry)
        self.grades = json.dumps(grades_list)

class Employee(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    # Relationship to User
    user = db.relationship('User', back_populates='employee')

    # Store questions as JSON (for flexibility)
    questions = db.Column(db.Text, nullable=True)  # JSON format

    # request_queue = db.Column(db.Text, nullable=True)

    # def set_request_queue(self, requests):
    #     self.request_queue = json.dumps(requests)

    def set_questions(self, question_list):
        # Set the questions for the employee.
        self.questions = json.dumps(question_list)

    # def get_requests(self):
    #     return json.loads(self.request_queue) if self.request_queue else []

    def get_questions(self):
        # Get the list of questions.
        return json.loads(self.questions) if self.questions else []

    # def add_request_to_queue(self, request_text, student_id):
    #     request_entry = f"{request_text} - {student_id}"
    #     request_list = json.loads(self.request_queue) if self.request_queue else []
    #     request_list.append(request_entry)
    #     self.set_request_queue(request_list)

    def add_question(self, question_text, student_id):
        question_entry = f"{question_text} - {student_id}"
        questions_list = json.loads(self.questions) if self.questions else []
        questions_list.append(question_entry)
        self.set_questions(questions_list)

class RegisterForm(FlaskForm):
    username = StringField(validators=[
                           InputRequired(), Length(min=4, max=20)], render_kw={"placeholder": "Username"})

    password = PasswordField(validators=[
                             InputRequired(), Length(min=8, max=20)], render_kw={"placeholder": "Password"})

    role = SelectField('Role', choices=[('admin', 'Admin'), ('employee', 'Employee'), ('student', 'Student')],
                       validators=[InputRequired()], render_kw={"placeholder": "Role"})


    # Student-specific fields
    name = StringField(validators=[Length(max=100)], render_kw={"placeholder": "Full Name"})
    address = StringField(validators=[Length(max=200)], render_kw={"placeholder": "Address"})
    group = StringField(validators=[Length(max=7)], render_kw={"placeholder": "324CC"})


    submit = SubmitField('Register')

    def validate_username(self, username):
        existing_user_username = User.query.filter_by(
            username=username.data).first()
        if existing_user_username:
            raise ValidationError(
                'That username already exists. Please choose a different one.')

class LoginForm(FlaskForm):
    username = StringField(validators=[
                           InputRequired(), Length(min=4, max=20)], render_kw={"placeholder": "Username"})

    password = PasswordField(validators=[
                             InputRequired(), Length(min=8, max=20)], render_kw={"placeholder": "Password"})

    submit = SubmitField('Login')

# Employee Form for Adding Courses
class AddCourseForm(FlaskForm):
    student_id = IntegerField(validators=[InputRequired()], render_kw={"placeholder": "Student ID"})
    course_name = StringField(validators=[InputRequired()], render_kw={"placeholder": "Course Name"})
    teacher_name = StringField(validators=[InputRequired()], render_kw={"placeholder": "Teacher Name"})
    submit = SubmitField("Add Course")

# Employee Form for Grading Students
class GradeStudentForm(FlaskForm):
    student_id = IntegerField(validators=[InputRequired()], render_kw={"placeholder": "Student ID"})
    course_name = StringField(validators=[InputRequired()], render_kw={"placeholder": "Course Name"})
    teacher_name = StringField(validators=[InputRequired()], render_kw={"placeholder": "Teacher Name"})
    grade = IntegerField(validators=[InputRequired()], render_kw={"placeholder": "Grade"})
    submit = SubmitField("Add Grade")

@app.route('/')
def home():
    return render_template('home.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()

    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user:
            if bcrypt.check_password_hash(user.password, form.password.data):
                login_user(user)
                if user.role == 'student':
                    return redirect(url_for('dashboard'))
                if user.role == 'employee':
                    return redirect(url_for('employee_dashborad'))
                if user.role == 'admin':
                    return redirect(url_for('admin_dashboard'))


    return render_template('login.html', form=form)


@app.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


@app.route('/dashboard', methods=['GET', 'POST'])
@login_required
def dashboard():
    return render_template('dashboard.html')


@app.route('/ask_question', methods=['POST'])
@login_required
def ask_question():
    if current_user.role != 'student':
        flash("Only students can ask questions!")
        return redirect(url_for('home'))

    question = request.form.get('question')
    student_id = current_user.id

    if not question:
        flash("Please provide a valid question.")
        return redirect(url_for('dashboard'))

    answer = serve_ai_question(question)
    if answer != []:
        return answer

    # Find the first employee with fewer than 5 questions
    employees = Employee.query.all()
    for emp in employees:
        if emp.questions is None:  # Initialize if it's None
            emp.questions = "[]"

        if len(emp.get_questions()) < 5:
            emp.add_question(question, student_id)
            db.session.commit()
            flash(f"Your question has been assigned to {emp.user.username}.")
            return redirect(url_for('dashboard'))

    flash("All employees currently have the maximum number of questions.")
    return redirect(url_for('dashboard'))

@app.route('/answer_question', methods=['POST'])
@login_required
def answer_question():
    if current_user.role != 'employee':
        flash("You must be an employee!")
        return redirect(url_for('home'))

    recipient_id = request.form['recipient_id']
    answer = request.form['answer']
    # add_question_to_faq_wannabe(question, answer)

    # Find the student based on the recipient_id
    student = Student.query.filter_by(id=recipient_id).first()

    if student:
        # You can store the answer in a list or a new field, for example:
        student_answer = f"Answer for student {recipient_id}: {answer}"

        # For now, you could print it or store it as part of the answer record
        print(student_answer)  # Or save it somewhere appropriate

        flash('Answer sent successfully.')
        return redirect(url_for('employee_dashborad'))
    else:
        flash('Student not found.')
        return redirect(url_for('employee_dashborad'))

@app.route('/employee_dashborad', methods=['GET', 'POST'])
@login_required
def employee_dashborad():
    if current_user.role != 'employee':
        flash("You must be an employee!")
        return redirect(url_for('home'))

    # Get the username of the current user
    username = current_user.username

    employee = current_user.employee
    # Check if the employee exists (just to be safe)
    if not employee:
        flash("Employee entry not found!")
        return redirect(url_for('home'))

    # Get the questions (we assume the `questions` are stored in JSON format)
    questions = json.loads(employee.questions) if employee.questions else []
    # requests = json.loads(employee.request_queue) if employee.request_queue else []

    return render_template('employee_dashborad.html', username=username, questions=questions)

# @app.route('/accept_request', methods=['POST'])
# @login_required
# def accept_request():
#     if current_user.role != 'employee':
#         flash("Unauthorized access!")
#         return redirect(url_for('home'))

#     student_id = request.form.get('student_id')

#     # Process the accepted request here (e.g., mark it as processed in the DB)
#     # Example: Remove the request from the employee's queue
#     employee = Employee.query.filter_by(id=current_user.id).first()
#     requests = json.loads(employee.request_queue) if employee.request_queue else []

#     # Remove the accepted request (this is just an example of removing it)
#     requests = [req for req in requests if req != student_id]

#     employee.set_request_queue(requests)  # Update the request queue in DB
#     db.session.commit()

#     flash(f"Request from student {student_id} has been accepted.")
#     return redirect(url_for('employee_dashborad'))

@app.route('/admin_dashboard', methods=['GET', 'POST'])
@login_required
def admin_dashboard():
    if current_user.role != 'admin':
        flash("You must be an admin!")
        return redirect(url_for('home'))

    # Get all non-admin users (students and employees)
    users_to_delete = User.query.filter(User.role != 'admin').all()

    if request.method == 'POST':
        user_id_to_delete = request.form['user_id_to_delete']

        # Find the user by id
        user_to_delete = User.query.get(user_id_to_delete)

        if user_to_delete:
            if user_to_delete.role == 'student':
                student = Student.query.filter_by(user_id=user_to_delete.id).first()
                if student:
                    db.session.delete(student)  # Delete the student's data
            elif user_to_delete.role == 'employee':
                employee = Employee.query.filter_by(user_id=user_to_delete.id).first()
                if employee:
                    db.session.delete(employee)  # Delete the employee's data

            # Delete the user from the User table
            db.session.delete(user_to_delete)
            db.session.commit()

            flash(f'{user_to_delete.role.capitalize()} deleted successfully!')

        else:
            flash("User not found!")

    return render_template('admin_dashboard.html', users=users_to_delete)

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()

    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data)

        # Create a User entry
        new_user = User(username=form.username.data, password=hashed_password, role=form.role.data)
        db.session.add(new_user)
        db.session.commit()

        # If the role is 'student', create a Student entry
        if form.role.data == 'student':
            # Create a new student
            new_student = Student(
                user_id=new_user.id,
                name=form.name.data,
                address=form.address.data,
                group=form.group.data,
                courses="[]",   # Placeholder for courses
                grades="[]"     # Placeholder for grades
            )

            # Add the new student
            db.session.add(new_student)
            db.session.commit()

        # If the role is 'employee', create an Employee entry
        elif form.role.data == 'employee':
            # Create a new employee
            new_employee = Employee(
                user_id=new_user.id,
                questions="[]"  # Initialize with an empty list for questions
            )
            db.session.add(new_employee)
            db.session.commit()

        return redirect(url_for('login'))

    return render_template('register.html', form=form)

@app.route('/student/<int:student_id>')
@login_required
def view_student(student_id):
    if current_user.role != 'student':
        return redirect(url_for('home'))

    # Access the student's data
    student_data = current_user.student
    return render_template('student_profile.html', student=student_data)
    # student = Student.query.get_or_404(student_id)
    # return render_template('student_profile.html', student=student)


@app.route('/enroll', methods=['POST'])
@login_required
def enroll_course():
    if current_user.role != 'student':
        return redirect(url_for('home'))

    course_name = request.form.get('course_name')
    teacher_name = request.form.get('teacher_name')

    if not course_name or not teacher_name:
        flash("Course name and teacher name are required!")
        return redirect(url_for('dashboard'))

    # Access the current student's data
    student = current_user.student

    # Enroll in the course
    student.enroll_in_course(course_name, teacher_name)

    # Save changes to the database
    db.session.commit()
    flash(f"Enrolled in {course_name} taught by {teacher_name}!")

    return redirect(url_for('dashboard'))

# Route for adding a course
@app.route('/add_course', methods=['GET', 'POST'])
@login_required
def add_course():
    if current_user.role != 'employee':
        flash("Unauthorized access!")
        return redirect(url_for('home'))

    form = AddCourseForm()
    if form.validate_on_submit():
        student = Student.query.get(form.student_id.data)
        if not student:
            flash("Student not found!")
            return redirect(url_for('add_course'))

        student.enroll_in_course(form.course_name.data, form.teacher_name.data)
        db.session.commit()
        flash(f"Course {form.course_name.data} taught by {form.teacher_name.data} added to student {student.id}!")
        return redirect(url_for('add_course'))

    return render_template('add_course.html', form=form)

# Route for grading a student
@app.route('/grade_student', methods=['GET', 'POST'])
@login_required
def grade_student():
    if current_user.role != 'employee':
        flash("Unauthorized access!")
        return redirect(url_for('home'))

    form = GradeStudentForm()
    if form.validate_on_submit():
        student = Student.query.get(form.student_id.data)
        if not student:
            flash("Student not found!")
            return redirect(url_for('grade_student'))

        student.grade_student(form.course_name.data, form.teacher_name.data, form.grade.data)
        db.session.commit()
        flash(f"Grade {form.grade.data} added for student {student.id} in {form.course_name.data}!")
        return redirect(url_for('grade_student'))

    return render_template('grade_student.html', form=form)

@app.route('/generate_pdf', methods=['GET'])
@login_required
def generate_pdf():
    if current_user.role != 'student':
        flash("Unauthorized access!")
        return redirect(url_for('home'))

    # Retrieve student grades
    student = current_user.student
    grades_list = json.loads(student.grades) if student.grades else []

    # Render the HTML template for the PDF
    rendered_html = render_template('grades_pdf.html', grades=grades_list, student=student)

    # Generate the PDF
    pdf = render_pdf(HTML(string=rendered_html))

    # Return the PDF as a response
    response = make_response(pdf)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = 'inline; filename=grades.pdf'
    return response

@app.route('/generate_request', methods=['GET', 'POST'])
def generate_request():
    if current_user.role != 'student':
        flash("Unauthorized access!")
        return redirect(url_for('home'))

    if request.method == 'POST':
        current_subject = request.form.get('current_subject')
        new_subject = request.form.get('new_subject')
        new_teacher = request.form.get('new_teacher')

        # Validate form data
        if not current_subject or not new_subject or not new_teacher:
            flash("All fields are required!", "error")
            return redirect(url_for('generate_request'))

        # Process the request (e.g., save it to a database, generate a PDF, etc.)
        # For demonstration purposes, let's just print the values
        student_data = current_user.student
        student_name = student_data.name
        student_group = student_data.group
        courses = json.loads(student_data.courses) if student_data.courses else []

        first_employee = Employee.query.first()

        if not first_employee:
            flash("No employee available!")

        request_text = f"Student {student_name} needs to change the subject {current_subject} with {new_subject}, tought by {new_teacher}!"
        first_employee.add_request_to_queue(request_text, current_user.id)

        print(f"Request to change {current_subject} to {new_subject} with teacher {new_teacher}")

        # Provide feedback to the user
        flash("Request successfully submitted!", "success")
        return redirect(url_for('dashboard'))  # Redirect to dashboard or a confirmation page

    return render_template('generate_request.html')


if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # This will create the tables
        print("Database and tables created!")
    app.run(debug=True)