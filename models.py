from . import db, login_manager, bcrypt
from flask_login import UserMixin
from datetime import datetime


@login_manager.user_loader
def load_user(user_id):
    """Required by Flask-Login to load the current user."""
    return User.query.get(int(user_id))


class User(db.Model, UserMixin):
    """Database model for the Manager (User)."""
    __tablename__ = 'user'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)

    # This 'relationship' connects a Manager to all their employees
    employees = db.relationship('Employee', back_populates='manager', lazy=True)

    def set_password(self, password):
        """Hashes and sets the password."""
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')

    def check_password(self, password):
        """Checks if the provided password matches the hash."""
        return bcrypt.check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.username}>'


class Employee(db.Model):
    """Database model for Employees."""
    __tablename__ = 'employee'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    employee_login = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    photo_url = db.Column(db.String(255), nullable=False, default='default_avatar.png')

    # Foreign key to link Employee to their Manager (User)
    manager_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    # Relationships
    manager = db.relationship('User', back_populates='employees')
    projects = db.relationship('Project', back_populates='employee', lazy='dynamic', cascade="all, delete-orphan")
    attendance_records = db.relationship('Attendance', back_populates='employee', lazy='dynamic',
                                         cascade="all, delete-orphan")

    def __repr__(self):
        return f'<Employee {self.name}>'


class Project(db.Model):
    """Database model for Projects."""
    __tablename__ = 'project'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False, default='New Project')
    description = db.Column(db.Text, nullable=True)
    actions_taken = db.Column(db.Text, nullable=True)
    solution = db.Column(db.Text, nullable=True)
    impact_usd = db.Column(db.Float, nullable=True, default=0.0)
    stakeholder_login = db.Column(db.String(80), nullable=True)
    status = db.Column(db.String(20), nullable=False, default='In Progress')  # 'In Progress' or 'Completed'

    # Foreign key to link Project to an Employee
    employee_id = db.Column(db.Integer, db.ForeignKey('employee.id'), nullable=False)

    employee = db.relationship('Employee', back_populates='projects')

    def __repr__(self):
        return f'<Project {self.title}>'


class Attendance(db.Model):
    """Database model for Attendance/Leave."""
    __tablename__ = 'attendance'

    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False)
    # Leave types: Present, Annual, Casual, Sick, Maternity
    leave_type = db.Column(db.String(20), nullable=False, default='Present')

    # Foreign key to link Attendance to an Employee
    employee_id = db.Column(db.Integer, db.ForeignKey('employee.id'), nullable=False)

    employee = db.relationship('Employee', back_populates='attendance_records')

    def __repr__(self):
        return f'<Attendance {self.employee.name} - {self.date} - {self.leave_type}>'