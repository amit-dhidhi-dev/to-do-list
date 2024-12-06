from datetime import datetime
from lib2to3.pygram import python_symbols
from os.path import curdir

import bcrypt
from flask import Flask, render_template, url_for, session, flash, request
from flask_wtf import FlaskForm
from werkzeug.utils import redirect
from wtforms.fields.simple import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Email, ValidationError
from flask_mysqldb import MySQL

app = Flask(__name__)

#mysql connection
app.config["MYSQL_HOST"]='localhost'
app.config["MYSQL_USER"]='root'
app.config["MYSQL_PASSWORD"]='password'
app.config["MYSQL_DB"]='to_do_list'
app.secret_key="this my secrete key"

mysql = MySQL(app)


class RegisterForm(FlaskForm):
    email=StringField("Email",validators=[DataRequired(), Email()])
    password=PasswordField("Password",validators=[DataRequired()])
    submit=SubmitField("Register")

    def validate_email(self,field):
        cursor=mysql.connection.cursor()
        cursor.execute("SELECT * FROM users WHERE email=%s",{field.data,})
        user=cursor.fetchone()
        cursor.close()
        if user:
            raise ValidationError("Email already taken...")

class LoginForm(FlaskForm):
    email=StringField("Email",validators=[DataRequired(), Email()])
    password=PasswordField("Password",validators=[DataRequired()])
    submit=SubmitField("Login")



@app.route('/')
def index():

   if "user" in session:

       cursor=mysql.connection.cursor()
       cursor.execute("SELECT * FROM tasks WHERE user_id=%s",(session['user'][0],))
       task =cursor.fetchall()
       session['tasks']=task
       cursor.close()
       print(task)

       return render_template('index.html', user=session["user"], tasks=task, number_of_task=len(task))

   return render_template('index.html')


@app.route('/about')
def about():
    return render_template('about.html')


@app.route('/log_out')
def log_out():
    session['user']=None
    session['tasks']=None
    return render_template('index.html')

@app.route('/login',methods=["GET","POST"])
def login():
    form=LoginForm()
    if form.validate_on_submit():
        email=form.email.data
        password=form.password.data

        cursor=mysql.connection.cursor()
        cursor.execute("SELECT * FROM users WHERE email=%s",(email,))
        user=cursor.fetchone()
        cursor.close()
        if user and bcrypt.checkpw(password.encode('utf-8'),user[2].encode('utf-8')):
            session['user']=user
            return redirect(url_for('index'))
        else:
            flash("login failed.....")
            return redirect(url_for('login'))

    return render_template('login.html', form=form)

@app.route('/register',methods=["GET","POST"])
def register():
    form=RegisterForm()
    if form.validate_on_submit():
        email=form.email.data
        password=form.password.data

        hash_password = bcrypt.hashpw(password.encode('utf-8'),bcrypt.gensalt())

        # store data in database
        cursor=mysql.connection.cursor()
        cursor.execute("INSERT INTO users (email, password) VALUES (%s, %s)",(email,hash_password,))
        mysql.connection.commit()
        cursor.close()

        return redirect(url_for('login'))

    return render_template('register.html', form=form)

@app.route('/edit/<item>', methods=["GET","POST"])
def edit(item):
    if 'user' in session:
        if 'tasks' in session:
            if request.method == "POST":
                title=request.form['title']
                desc =request.form['desc']

                cursor=mysql.connection.cursor()
                cursor.execute("UPDATE tasks SET title=%s, description=%s,date=%s WHERE id=%s", (title, desc,datetime.now(), item,))
                mysql.connection.commit()
                cursor.close()

                return redirect(url_for('index'))

        else:
            return "<h1> You have not any task </h1> "
    else:
        redirect(url_for('login'))

    return render_template("edit.html",item=item)




@app.route('/delete/<id>')
def delete(id):
    if 'user' in session:
        if 'tasks' in session:
            cursor=mysql.connection.cursor()
            cursor.execute("DELETE FROM `tasks` WHERE id=%s",(id))
            mysql.connection.commit()
            cursor.close()

        else:
            redirect(url_for('add_task'))
    else:
        redirect(url_for("login"))
    return redirect(url_for('index'))
@app.route('/add_task' , methods=["GET","POST"])
def add_task():
    if "user" in session:
        if request.method == "POST":
            title=request.form['title']
            desc=request.form['desc']

            print(session['user'])
            cursor=mysql.connection.cursor()
            cursor.execute("INSERT INTO tasks (title, description, date, user_id) VALUES (%s,%s,%s,%s)",(title,desc,datetime.now(),session['user'][0]))
            mysql.connection.commit()
            cursor.close()

            return redirect(url_for('index'))


        return render_template('add_task.html')
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)