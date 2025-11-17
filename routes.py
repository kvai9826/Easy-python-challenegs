from flask import render_template, redirect, url_for, flash, request, Blueprint, abort
from flask_login import login_user, current_user, logout_user, login_required
from . import db, bcrypt
from .models import User, Employee, Project, Attendance
from .forms import LoginForm, EmployeeForm, ProjectForm, AttendanceForm
from datetime import datetime
import calendar
import os
import secrets
from werkzeug.utils import secure_filename
from flask import current_app

# Using Blueprint to organize routes
main_bp = Blueprint('main', __name__)


# --- Helper Function for Calendar ---
def get_calendar_data(year, month, records):
    """Generates data for the HTML calendar."""
    cal = calendar.Calendar()
    month_days = cal.monthdatescalendar(year, month)

    # Create a dictionary for quick lookup of leave types
    leave_map = {record.date.day: record.leave_type for record in records if
                 record.date.month == month and record.date.year == year}

    today = datetime.utcnow().date()

    calendar_data = {
        'month_name': datetime(year, month, 1).strftime('%B %Y'),
        'month_num': month,  # <-- MODIFIED LINE
        'weeks': [],
        'weekdays': [day for day in calendar.day_abbr]
    }

    for week in month_days:
        week_data = []
        for day in week:
            day_status = 'default'  # Default for days not in the month
            day_class = 'calendar-day'

            if day.month == month:
                if day.day in leave_map:
                    day_status = leave_map[day.day].lower()  # e.g., 'sick', 'annual'
                elif day.weekday() < 5 and day <= today:  # Weekday (Mon-Fri) and in the past/present
                    day_status = 'present'
                else:  # Weekend or future date
                    day_status = 'weekend'

                day_class += f' day-{day_status}'

                if day == today:
                    day_class += ' day-today'

            week_data.append({'date': day, 'class': day_class})
        calendar_data['weeks'].append(week_data)

    return calendar_data

def save_picture(form_picture):
    """Saves uploaded picture to the static folder with a secure name."""
    # Create a random, secure filename
    random_hex = secrets.token_hex(8)
    # Get the file extension (e.g., .png, .jpg)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    # Get the full path to save the file
    picture_path = os.path.join(current_app.root_path, 'static/profile_pics', picture_fn)

    # Save the file
    form_picture.save(picture_path)

    return picture_fn

# --- Authentication Routes ---

@main_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Manager Login Page."""
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            flash('Login successful!', 'success')
            return redirect(url_for('main.dashboard'))
        else:
            flash('Login Unsuccessful. Please check username and password', 'danger')

    return render_template('login.html', title='Login', form=form)


@main_bp.route('/logout')
@login_required
def logout():
    """Logs the current manager out."""
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('main.login'))


# --- Main Application Routes ---

@main_bp.route('/')
@main_bp.route('/dashboard')
@login_required
def dashboard():
    """Dashboard page showing all employees under the logged-in manager."""
    employees = Employee.query.filter_by(manager_id=current_user.id).order_by(Employee.name).all()
    form = EmployeeForm()  # For the 'Add Employee' modal/form
    return render_template('dashboard.html', title='Dashboard', employees=employees, form=form)


@main_bp.route('/employee/add', methods=['POST'])
@login_required
def add_employee():
    """Handles adding a new employee."""
    form = EmployeeForm()
    if form.validate_on_submit():

        # Check if a photo was uploaded and save it
        if form.photo.data:
            picture_file = save_picture(form.photo.data)
            photo_url_to_save = picture_file
        else:
            photo_url_to_save = 'default_avatar.png' # Use default if no file

        new_employee = Employee(
            name=form.name.data,
            employee_login=form.employee_login.data,
            email=form.email.data,
            photo_url=photo_url_to_save,  # Use the new filename
            manager_id=current_user.id
        )
        db.session.add(new_employee)
        db.session.commit()
        flash(f'Employee {new_employee.name} has been added!', 'success')
    else:
        flash('Error adding employee. Please check the data.', 'danger')
    return redirect(url_for('main.dashboard'))


@main_bp.route('/employee/<int:employee_id>')
@login_required
def employee_detail(employee_id):
    """Shows the detailed page for a single employee."""
    employee = Employee.query.get_or_404(employee_id)

    # Security check: Ensure manager can only see their own employees
    if employee.manager_id != current_user.id:
        abort(403)  # Forbidden

    # --- Calendar Data ---
    today = datetime.utcnow()
    # Get month/year from query params, or use current month
    view_month = request.args.get('month', default=today.month, type=int)
    view_year = request.args.get('year', default=today.year, type=int)

    # Simple navigation logic
    if view_month == 1:
        prev_month, prev_year = 12, view_year - 1
    else:
        prev_month, prev_year = view_month - 1, view_year

    if view_month == 12:
        next_month, next_year = 1, view_year + 1
    else:
        next_month, next_year = view_month + 1, view_year

    nav_urls = {
        'prev': url_for('main.employee_detail', employee_id=employee_id, month=prev_month, year=prev_year),
        'next': url_for('main.employee_detail', employee_id=employee_id, month=next_month, year=next_year),
        'today': url_for('main.employee_detail', employee_id=employee_id)
    }

    attendance_records = employee.attendance_records.all()
    calendar_data = get_calendar_data(view_year, view_month, attendance_records)
    # --- End Calendar ---

    # Forms for this page
    project_form = ProjectForm()
    attendance_form = AttendanceForm()

    return render_template('employee_detail.html',
                           title=employee.name,
                           employee=employee,
                           project_form=project_form,
                           attendance_form=attendance_form,
                           calendar_data=calendar_data,
                           nav_urls=nav_urls)


@main_bp.route('/employee/<int:employee_id>/edit', methods=['POST'])
@login_required
def edit_employee(employee_id):
    """Handles editing employee details (from a modal on dashboard)."""
    employee = Employee.query.get_or_404(employee_id)
    if employee.manager_id != current_user.id:
        abort(403)

    form = EmployeeForm(request.form)  # Populate form from request
    if form.validate_on_submit():
        employee.name = form.name.data
        employee.employee_login = form.employee_login.data
        employee.email = form.email.data
        employee.photo_url = form.photo_url.data or employee.photo_url
        db.session.commit()
        flash('Employee details updated!', 'success')
    else:
        flash('Error updating employee.', 'danger')

    return redirect(url_for('main.dashboard'))  # Or employee_detail


@main_bp.route('/employee/<int:employee_id>/delete', methods=['POST'])
@login_required
def delete_employee(employee_id):
    """Handles deleting an employee."""
    employee = Employee.query.get_or_404(employee_id)
    if employee.manager_id != current_user.id:
        abort(403)

    db.session.delete(employee)
    db.session.commit()
    flash(f'Employee {employee.name} has been deleted.', 'success')
    return redirect(url_for('main.dashboard'))


# --- Project CRUD Routes ---

@main_bp.route('/employee/<int:employee_id>/add_project', methods=['POST'])
@login_required
def add_project(employee_id):
    """Handles adding a new project for an employee."""
    employee = Employee.query.get_or_404(employee_id)
    if employee.manager_id != current_user.id:
        abort(403)

    form = ProjectForm()
    if form.validate_on_submit():
        new_project = Project(
            title=form.title.data,
            description=form.description.data,
            actions_taken=form.actions_taken.data,
            solution=form.solution.data,
            impact_usd=form.impact_usd.data,
            stakeholder_login=form.stakeholder_login.data,
            status=form.status.data,
            employee_id=employee.id
        )
        db.session.add(new_project)
        db.session.commit()
        flash('New project added!', 'success')
    else:
        flash('Error adding project.', 'danger')

    return redirect(url_for('main.employee_detail', employee_id=employee_id))


@main_bp.route('/project/<int:project_id>/edit', methods=['POST'])
@login_required
def edit_project(project_id):
    """Handles editing an existing project."""
    project = Project.query.get_or_404(project_id)
    if project.employee.manager_id != current_user.id:
        abort(403)

    form = ProjectForm(request.form)
    if form.validate_on_submit():
        project.title = form.title.data
        project.description = form.description.data
        project.actions_taken = form.actions_taken.data
        project.solution = form.solution.data
        project.impact_usd = form.impact_usd.data
        project.stakeholder_login = form.stakeholder_login.data
        project.status = form.status.data
        db.session.commit()
        flash(f'Project "{project.title}" updated!', 'success')
    else:
        flash('Error updating project.', 'danger')

    return redirect(url_for('main.employee_detail', employee_id=project.employee_id))


@main_bp.route('/project/<int:project_id>/delete', methods=['POST'])
@login_required
def delete_project(project_id):
    """Handles deleting a project."""
    project = Project.query.get_or_404(project_id)
    if project.employee.manager_id != current_user.id:
        abort(403)

    employee_id = project.employee_id
    db.session.delete(project)
    db.session.commit()
    flash(f'Project "{project.title}" has been deleted.', 'success')
    return redirect(url_for('main.employee_detail', employee_id=employee_id))


# --- Attendance CRUD Routes ---

@main_bp.route('/employee/<int:employee_id>/add_attendance', methods=['POST'])
@login_required
def add_attendance(employee_id):
    """Handles adding a leave day."""
    employee = Employee.query.get_or_404(employee_id)
    if employee.manager_id != current_user.id:
        abort(403)

    form = AttendanceForm()
    if form.validate_on_submit():
        # Check if a record for this day already exists
        existing_record = Attendance.query.filter_by(
            employee_id=employee_id,
            date=form.date.data
        ).first()

        if existing_record:
            existing_record.leave_type = form.leave_type.data
            flash('Leave record updated for that date.', 'success')
        else:
            new_record = Attendance(
                date=form.date.data,
                leave_type=form.leave_type.data,
                employee_id=employee_id
            )
            db.session.add(new_record)
            flash('Leave record added.', 'success')

        db.session.commit()
    else:
        flash('Error adding leave record.', 'danger')

    return redirect(url_for('main.employee_detail', employee_id=employee_id))