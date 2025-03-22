from flask import Flask, request, render_template, redirect, url_for, flash, session
import mysql.connector as my
import smtplib
from email.message import EmailMessage


app = Flask(__name__)
app.secret_key = "your_secret_key"  # Required for session & flash messages

# Database connection
mydb = my.connect(
    host="localhost",
    user="root",
    password="",
    database="compass"
)

mycursor = mydb.cursor(dictionary=True)  # Ensure it's in dictionary mode
@app.route('/')
def home():
    return render_template('entry.html')

@app.route('/student_login')
def student_login():
    return render_template('student_login.html')

@app.route('/recruiter_login')
def recruiter_login():
    return render_template('recruiter_login.html')

@app.route('/check_student', methods=['POST'])
def check_student():
    email = request.form['email']
    password = request.form['password']

    # Query the database to check student credentials
    mycursor.execute("SELECT * FROM students WHERE email = %s", (email,))
    student_data = mycursor.fetchone()  # Fetch one matching record

    if student_data:
        stored_password = student_data["password"]  # Get stored password (plain text)
        # Direct string comparison (Since passwords are NOT hashed)
        if stored_password == password:
            session['student_id'] = student_data["student_id"]  # Store student ID in session
            # session['student_data']=student_data
            # return redirect(url_for('student_dashboard',student_data))  # Redirect to student dashboard
            # return render_template("student_dashboard.html",student_name=student_data["student_name"],about=student_data["about"])
            return redirect(url_for('student_dashboard'))  # Redirect to recruiter dashboard
        else:
            flash("Invalid password!", "danger")
    else:
        flash("No account found with this email!", "danger")
    
    return redirect(url_for('student_login'))  # Redirect back to login page


@app.route('/check_recruiter', methods=['POST'])
def check_recruiter():
    email = request.form['email']
    password = request.form['password']

    # Query the database to check recruiter credentials
    mycursor.execute("SELECT * FROM recruiters WHERE recruiter_email = %s", (email,))
    recruiter = mycursor.fetchone()  # Fetch one matching record
    
    
    if recruiter:
        stored_password = recruiter['password']  # Get stored password (plain text)

        # Direct string comparison (Since passwords are NOT hashed)
        if stored_password == password:
            session['recruiter_id'] = recruiter['recruiter_id']  # Store recruiter ID in session
            session['company_name'] = recruiter['company_name']
            session['recruiter_name'] = recruiter['recruiter_name']
            session['recruiter_email'] = recruiter['recruiter_email']
            session['recruiter_position'] = recruiter['position']
            session['about_company'] = recruiter['about_company']
            return redirect(url_for('recruiter_dashboard'))  # Redirect to recruiter dashboard
        else:
            flash("Invalid password!", "danger")
    else:
        flash("No account found with this email!", "danger")
    
    return redirect(url_for('recruiter_login'))  # Redirect back to login page

# route for recruiter_dashboard
@app.route('/recruiter_dashboard')
def recruiter_dashboard():
    id=session["recruiter_id"]
    mycursor.execute('SELECT * FROM recruiters where recruiter_id=%s',(id,))
    recruiter_data = mycursor.fetchone()  # Fetch one matching record
    
    mycursor.execute("select * from internships where recruiter_id=%s order by created_at desc",(id,))
    recruiter_internships = mycursor.fetchall()  # Fetch all internships added recently
    return render_template('recruiter_dashboard.html',recruiter_data=recruiter_data, internships=recruiter_internships)

@app.route('/student_dashboard')
def student_dashboard():
    id=session["student_id"]
    mycursor.execute('SELECT * FROM students where student_id=%s',(id,))
    student_data = mycursor.fetchone()  # Fetch one matching record
    
    mycursor.execute("select * from internships")
    recent_internships = mycursor.fetchall()  # Fetch all internships added recently
    
    mycursor.execute("select * from applications join internships on applications.internship_id=internships.internship_id where applications.student_id=%s",(id,))
    applied_internships = mycursor.fetchall()  # Fetch all internships added recently

    mycursor.execute("select * from saved_internships join internships on saved_internships.internship_id=internships.internship_id where saved_internships.student_id=%s",(id,))
    saved_internships = mycursor.fetchall()  # Fetch all internships added recently

    return render_template("student_dashboard.html",student_data=student_data, recent_internships=recent_internships,applied_internships=applied_internships,saved_internships=saved_internships)

@app.route('/student_signup')
def student_signup():
    return render_template('student_signup.html')

@app.route('/recruiter_signup')
def recruiter_signup():
    return render_template('recruiter_signup.html')

# route fro "create_student_acc"
@app.route('/create_student_acc', methods=['POST'])
def create_student_acc():
    try:
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        institute = request.form['institute']
        about = request.form['about']
        skills = request.form['skills']
        phone = request.form['phone']
        experience = request.form['experience']
        location = request.form['location']
        interests = request.form.getlist('interest')
        resume = request.files['resume'] if 'resume' in request.files else None

        # Debugging - Print received data
        print("Received Data:", request.form)
        print("Received File:", resume.filename if resume else "No file uploaded")

        # Convert interests list to comma-separated string
        interests_str = ', '.join(interests)

        # # Ensure "resumes" folder exists
        # resume_folder = "resumes"
        # if not os.path.exists(resume_folder):
        #     os.makedirs(resume_folder)

        # # Store resume if uploaded
        # resume_filename = None
        # if resume:
        #     resume_filename = os.path.join(resume_folder, f"{email}_resume.pdf")
        #     resume.save(resume_filename)

        # Hash password before storing
        # password_hashed = bcrypt.generate_password_hash(password).decode('utf-8')

        # Insert into database
        sql = """
            INSERT INTO students (student_name, email, password, institution, skills, phone, 
                                  experience, location, interest,about) 
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s,%s)
        """
        values = (name, email, password, institute, skills, phone, experience, location, interests_str,about)

        mycursor.execute(sql, values)
        mydb.commit()

        flash("Account created successfully! You can now log in.", "success")

        #smtp logic
        sender="compass.internships@gmail.com"
        receiver=email
        sender_password="sxlt gfnf xfoh zevm"

        message = EmailMessage()
        message["From"]= sender
        message["To"]= receiver
        message["Subject"]=" Welcome to Compass! Your Account Has Been Successfully Created"
        
        content= f"""\
        Dear {name},

        We are thrilled to have you on board! Your account has been successfully created on Compass. Below are your account details:

        🔹 Name: {name}
        🔹 Email: {email}
        🔹 Account Type: Student

        You can now log in using your registered email and start exploring our platform.

        For security reasons, please do not share your credentials with anyone. If you have any questions or need assistance, feel free to contact our support team.

        Welcome aboard! 🚀

        Best regards,  
        Compass  
        📧 compass.internships@gmail.com
        """
        message.set_content(content)

        with smtplib.SMTP_SSL("smtp.gmail.com",465) as server:
            server.login(sender,sender_password)
            server.send_message(message)

        return redirect(url_for('student_login'))

    except Exception as e:
        mydb.rollback()
        print(f"Error: {e}")  # Debugging
        flash(f"Error creating account: {str(e)}", "danger")
        return redirect(url_for('student_signup'))

@app.route('/create_recruiter_acc', methods=['POST'])
def create_recruiter_acc():
    try:
        email = request.form['email']
        password = request.form['password']
        name = request.form['name']
        phone = request.form['phone']
        company_name = request.form['company']
        job_position = request.form['position']
        location = request.form['location']
        about_company = request.form['about_company']

        # Insert into database
        sql = """
            INSERT INTO recruiters (company_name, about_company, location, recruiter_name, recruiter_email, password,position) 
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        values = (company_name,about_company,location,name,email,password,job_position)

        mycursor.execute(sql, values)
        mydb.commit()

        flash("Account created successfully! You can now log in.", "success")

        #smtp logic
        sender="compass.internships@gmail.com"
        receiver=email
        sender_password="sxlt gfnf xfoh zevm"

        message = EmailMessage()
        message["From"]= sender
        message["To"]= receiver
        message["Subject"]=" Welcome to Compass! Your Account Has Been Successfully Created"
        
        content= f"""\
        Dear {name},

        We are thrilled to have you on board! Your account has been successfully created on Compass. Below are your account details:

        🔹 Name: {name}
        🔹 Email: {email}
        🔹 Account Type: Recruiter

        You can now log in using your registered email and start exploring our platform.

        For security reasons, please do not share your credentials with anyone. If you have any questions or need assistance, feel free to contact our support team.

        Welcome aboard! 🚀

        Best regards,  
        Compass  
        📧 compass.internships@gmail.com
        """
        message.set_content(content)

        with smtplib.SMTP_SSL("smtp.gmail.com",465) as server:
            server.login(sender,sender_password)
            server.send_message(message)

        return redirect(url_for('recruiter_login'))

    except Exception as e:
        mydb.rollback()
        print(f"Error: {e}")  # Debugging
        flash(f"Error creating account: {str(e)}", "danger")
        return redirect(url_for('recruiter_signup'))

@app.route('/create_internship', methods=['POST'])
def create_internship():
    try:
        # Example: Fetch recruiter ID in another route
        if 'recruiter_id' in session:
            recruiter_id = session['recruiter_id']
            company_name = session['company_name']
            recruiter_name = session['recruiter_name']
            print(f"Recruiter ID: {recruiter_id} ,company name: {company_name}, recruiter_name: {recruiter_name}")
        else:
            print("No recruiter logged in")
        position = request.form['position'].title()
        description=request.form["description"]
        responsibilities=request.form["responsibilities"]
        required_skills=request.form["skills"].title()
        print(required_skills,type(required_skills))
        stipend = request.form['stipend']
        duration = request.form['duration']+" months"
        work_model=request.form["work-model"]
        location = request.form['location'].title()
        deadline=request.form["deadline"]
        work_type=request.form["work_type"]
        # Insert into database
        sql = """
            INSERT INTO internships (recruiter_id,company_name,recruiter_name,position,description,responsibilities,required_skills,stipend,duration,parttime_fulltime,work_model,location,deadline) 
            VALUES ( %s, %s, %s, %s, %s, %s, %s,%s,%s,%s,%s,%s,%s)
        """
        values = (recruiter_id,company_name,recruiter_name,position,description,responsibilities,required_skills,stipend,duration,work_type,work_model,location,deadline)
        mycursor.execute(sql, values)
        mydb.commit()
        print("bloddy point here....")
        # flash("Internship created successfully!")
        return redirect(url_for('recruiter_dashboard'))
    except Exception as e:
        mydb.rollback()
        print(f"Error that's a bloody point: {e}")  # Debugging
        flash(f"Error creating internship: {str(e)}", "danger")
        return redirect(url_for('recruiter_login'))
    
    
@app.route('/recruiter_internship_details')
def recruiter_internship_details():
    internship_id = request.args.get('id')# Fetch 'id' from URL
    internship_id=int(internship_id)
    # Fetch internship details from database
    sql = "SELECT * FROM internships WHERE internship_id=%s"
    values = (internship_id,)
    mycursor.execute(sql, values)
    internship_data = mycursor.fetchone()

    sql = """SELECT * FROM applications JOIN students ON students.student_id = applications.student_id
    WHERE applications.internship_id=%s"""
    values = (internship_id,)
    mycursor.execute(sql,values)
    applied_students = mycursor.fetchall()
    return render_template('recruiter_internship_details.html', internship_data=internship_data,applied_students=applied_students)
    
    
# internship_details_route
@app.route('/student_internship_details')
def student_internship_details():
    internship_id = request.args.get('id')# Fetch 'id' from URL
    internship_id = int(internship_id)
    # Fetch internship details from database
    sql = "SELECT * FROM internships where internship_id=%s"
    values = (internship_id,)
    mycursor.execute(sql, values)
    internship_data = mycursor.fetchone()

    # company_name = request.args.get('company_name')
    # sql = "SELECT * FROM internships where company_name=%s"
    # values = (company_name,)
    # mycursor.execute(sql, values)
    # similar_data = mycursor.fetchone()

    # return render_template('student_internship_details.html', recent_internship_data=internship_data,similar_data=similar_data)
    return render_template('student_internship_details.html', recent_internship_data=internship_data)
@app.route('/apply_internship')
def apply_internship():
    try:
        internship_id = int(request.args.get('id')) # Fetch 'id' from URL
        student_id = session['student_id']
        status = 'pending'
        sql = """
                INSERT INTO applications (student_id,internship_id,status) 
                VALUES ( %s, %s, %s)
            """
        values = (student_id,internship_id,status,)
        mycursor.execute(sql,values)
        mydb.commit()

        return redirect(url_for('student_dashboard'))
    except Exception as e:
        mydb.rollback()
        print(f"Error that's a bloody point: {e}")  # Debugging
        flash(f"Error creating internship: {str(e)}", "danger")
        return redirect(url_for('student_login'))

@app.route('/save_internship')
def save_internship():
    try :
        internship_id = int(request.args.get('id')) # Fetch 'id' from URL
        student_id = session['student_id']
        sql = """
                INSERT INTO saved_internships (student_id,internship_id) 
                VALUES ( %s, %s)
            """
        values = (student_id,internship_id,)
        mycursor.execute(sql,values)
        mydb.commit()

        return redirect(url_for('student_dashboard'))
    except Exception as e:
        mydb.rollback()
        print(f"Error that's a bloody point: {e}")  # Debugging
        flash(f"Error creating internship: {str(e)}", "danger")
        return redirect(url_for('student_login'))
    
@app.route('/update_internship',methods=['POST'])  
def update_internship():
    id=int(request.form.get('id', 0))
    try:
        if 'recruiter_id' in session:
            recruiter_id = session['recruiter_id']
            company_name = session['company_name']
            recruiter_name = session['recruiter_name']
            print(f"Recruiter ID: {recruiter_id}, Company Name: {company_name}, Recruiter Name: {recruiter_name}")
        else:
            print("No recruiter logged in")
            return redirect(url_for('recruiter_login'))

        # Get form data
        position = request.form['position'].title()
        description = request.form['description']
        skills = request.form['skills'].title()
        stipend = request.form['stipend']
        duration = request.form['duration']+" months"
        work_model = request.form['work-model']
        deadline = request.form['deadline']

        # Update database
        sql = """
            UPDATE internships 
            SET position=%s, description=%s, required_skills=%s, stipend=%s, duration=%s, work_model=%s, deadline=%s
            WHERE recruiter_id=%s AND company_name=%s AND internship_id=%s
        """
        values = (position, description, skills, stipend, duration, work_model, deadline, recruiter_id, company_name,id)
        mycursor.execute(sql, values)
        mydb.commit()

        print("Internship updated successfully!")
        return redirect(url_for('recruiter_internship_details'))
    
    except Exception as e:
        mydb.rollback()
        print(f"Error updating internship: {e}")
        return redirect(url_for('recruiter_internship_details'))
    
@app.route('/accept_applicant', methods=['GET', 'POST'])
def accept_applicant():
    try:
        internship_id = int(request.args.get('internship_id'))
        student_id = int(request.args.get('student_id'))
        student_name=request.args.get('s_name')
        email = request.args.get('email')
        status = 'accepted'
        sql = """
                UPDATE applications SET status = 'accepted'
                WHERE student_id = %s AND internship_id = %s
            """
        values = (student_id, internship_id)  # ✅ Tuple with multiple values
        mycursor.execute(sql, values)
        mydb.commit()

        #smtp
        sender="compass.internships@gmail.com"
        receiver=email
        sender_password="sxlt gfnf xfoh zevm"

        message = EmailMessage()
        message["From"]= sender
        message["To"]= receiver
        message["Subject"]="Your Internship Application Has Been Accepted! 🎉"
        mycursor.execute("select * from internships where internship_id=%s",(internship_id,))
        internship_deatil=mycursor.fetchone()
        content=f"""Dear {student_name},

We are pleased to inform you that your application for the {internship_deatil["position"]} at {session['company_name']} has been accepted! 🎉

Our team has reviewed your application, and we believe you would be a great fit for this role. Next, we will be sharing further details regarding the onboarding process and required documentation.

📌 Next Steps:
✅ Onboarding Details: We will share further instructions once we receive your confirmation.  
     
If you have any questions, feel free to reach out. We are excited to have you on board and look forward to working with you! 🚀

Best regards,
{session['recruiter_name']}
{session['company_name']}"""
        message.set_content(content)

        with smtplib.SMTP_SSL("smtp.gmail.com",465) as server:
            server.login(sender,sender_password)
            server.send_message(message)

        return redirect(url_for('recruiter_dashboard', id=internship_id))

    except Exception as e:
        mydb.rollback()
        print(f"Error that's a bloody point: {e}")  # Debugging
        flash(f"Error creating internship: {str(e)}", "danger")
        return redirect(url_for('recruiter_login'))

@app.route('/reject_applicant', methods=['POST','GET'])
def reject_applicant():
    try:
        internship_id = int(request.args.get('internship_id'))
        student_id = int(request.args.get('student_id'))
        student_name=request.args.get('s_name')
        email = request.args.get('email')
        status = 'accepted'
        sql = """
                UPDATE applications SET status = 'rejected'
                WHERE student_id = %s AND internship_id = %s
            """
        values = (student_id, internship_id)  # ✅ Tuple with multiple values
        mycursor.execute(sql, values)
        mydb.commit()

        #smtp
        sender="compass.internships@gmail.com"
        receiver=email
        sender_password="sxlt gfnf xfoh zevm"

        message = EmailMessage()
        message["From"]= sender
        message["To"]= receiver
        message["Subject"]=" Update on Your Internship Application"
        mycursor.execute("select * from internships where internship_id=%s",(internship_id,))
        internship_deatil=mycursor.fetchone()
        content=f"""Dear {student_name},

Thank you for applying for the {internship_deatil['position']} at {session['company_name']}. We appreciate the time and effort you put into your application.

After careful consideration, we regret to inform you that we will not be moving forward with your application at this time. This decision was difficult, as we received many strong applications, including yours. However, we encourage you to apply for future opportunities with us.

We truly appreciate your interest in our organization and wish you the very best in your career journey. Keep striving for success! 🚀

Best regards,
{session['recruiter_name']}
{session['company_name']}"""
        message.set_content(content)

        with smtplib.SMTP_SSL("smtp.gmail.com",465) as server:
            server.login(sender,sender_password)
            server.send_message(message)

        return redirect(url_for('recruiter_dashboard', id=internship_id))

    except Exception as e:
        mydb.rollback()
        print(f"Error that's a bloody point: {e}")  # Debugging
        flash(f"Error creating internship: {str(e)}", "danger")
        return redirect(url_for('recruiter_login'))

@app.route('/delete_internship', methods=['GET', 'POST'])
def delete_internship():
    try :
        internship_id = int(request.args.get('id')) # Fetch 'id' from URL
        sql = """
                DELETE FROM internships WHERE internship_id = %s

            """
        values = (internship_id,)
        mycursor.execute(sql,values)
        mydb.commit()

        return redirect(url_for('recruiter_dashboard'))
    except Exception as e:
        mydb.rollback()
        print(f"Error that's a bloody point: {e}")  # Debugging
        flash(f"Error creating internship: {str(e)}", "danger")
        return redirect(url_for('recruiter_login'))
    
@app.route('/view_profile', methods=['GET', 'POST'])
def view_profile():
    return "profile"
    
if __name__ == '__main__':
    app.run(debug=True)
