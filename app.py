from flask import Flask, render_template, url_for, redirect, request, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, login_user, LoginManager, login_required, logout_user, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, SelectField
from wtforms.validators import InputRequired, Length, ValidationError
from flask_bcrypt import Bcrypt
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
                return redirect(url_for('dashboard'))

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

if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # This will create the tables
        print("Database and tables created!")
    app.run(debug=True)