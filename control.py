from flask import Flask, render_template, redirect, url_for, request, session
from binascii import b2a_hex
from datetime import datetime
from flask_user import login_required, UserManager, UserMixin
import bcrypt
import pymongo
import re
import os

app = Flask(__name__)
client = pymongo.MongoClient("mongodb://localhost:27017")
db = client['mongo']

app.config['SECRET_KEY'] = os.urandom(24)

salt = b'$2b$11$Za4hFNuzn3Rvw7gLnUVZCu'

def login_required(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if session['USERNAME'] == username:
            return f(*args, **kwargs)
        else:
            return redirect(url_for('login'))

    return wrap

@app.route('/control/login', methods=('GET', 'POST'))
def controlLogin():

    error_message = ""

    if request.method == 'POST':
        username = request.form.get('username')
        masterPassword = bcrypt.hashpw(request.form['password'].encode('utf-8'), salt)

        user = db.Credentials.find_one({'username': username})

        if user != None :
            dbUsername = user['username']
            dbPassword = bytes(user['password'])

            if username != dbUsername or bcrypt.hashpw(request.form['password'].encode('utf-8'),salt) != dbPassword:
                error_message = 'Invalid Credentials. Please try again.'
            else:
                session['USERNAME'] = username
                return redirect(url_for('controlHome'))
        else:
            error_message = 'Invalid Credentials. Please try again.'

    return render_template('admin_login.html', Error_Message=error_message, System_Name="")


@app.route('/control/logout')
def controlLogout():
    sess.clear()
    return redirect(url_for('controlLogin'))

@app.route('/control/home')
def controlHome():
    app.jinja_env.globals.update(zip=zip)
    app.jinja_env.globals.update(join=str.join)
    
    posts = db.Vacancies.find() #query : vacancies
    active = 0
    expired = 0
    archived = 0

    for i in posts:
        if i['deadline'] < datetime.now():
            expired += 1
        else:
            active += 1 
    
    usersRegistered = db.Credentials.find().count() #query : users 
    applicants = db.applicants.find().count()  #query : applicants
    print(applicants)
    online = db.Credentials.find({"active":"True"}).count()

    activeUsers = db.Credentials.find({"active":"True"})
    uactive, email = ([], [])

    for i in activeUsers:
        uactive.append(i['username'])
        email.append(i['_id'])

    post = db.applicants.find({}, {'post':'1'})
    posts, totals, vac = ([], [], [])
    p = ""
    t = ""
    for i in post:
        posts.append(i['post'])
    posts = list(set(posts)).copy()

    for i in posts:
     
        if posts.index(i) == 0:
            p += i 
            t += str(db.applicants.find({'post':i}).count())
        else :
            p += " " + i
            t += " " + str(db.applicants.find({'post':i}).count())

    


    return render_template('true_admin.html' ,active=active, expired=expired, archived=archived, uRegistered=usersRegistered, uOnline=online,  applicants=applicants, uactive=uactive, email=email, posts=p, totals=t)

@app.route('/control/addUser', methods=('GET', 'POST'))
def controlAddUser():
    
    if request.method == 'POST':
        email = request.form.get('email')
        username = request.form.get('username')

        db.Credentials.insert_one({'_id':email, 'username':username})
        return redirect(url_for('controlHome'))

@app.route('/control/changePassword', methods=('GET', 'POST'))
def controlChangePassword():

    if request.method == 'POST':
        oldPassword = bcrypt.hashpw(request.form.get('current-password'), salt)
        dbPassword = db.Admin.find_one({}, {'password':'1', '_id':'0'})

        if bcrypt.hashpw(request.form.get('password').encode('utf-8'), oldPassword) != dbPassword:
            newPassword = request.form.get('repeat-new-password')

        db.Admin.update_one({'password':oldPassword}, {'$set':{'password':newPassword}})

if __name__ == '__main__':
    app.run(debug = True)