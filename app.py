import pymongo
import bcrypt
import pandas as pd
import collections
import smsConfig
import emailConfig
import os
import numpy as np
from bson import Binary
from functools import wraps
from datetime import datetime, date
from itsdangerous import SignatureExpired, URLSafeTimedSerializer
from twilio.rest import Client
from flask import Flask, render_template, url_for, request, session, redirect, flash
from flask_mail import Mail,Message
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config.from_pyfile('config.cfg')
app.config['SECRET_KEY'] = os.urandom(24)
UPLOAD_FOLDER = './static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
mail = Mail(app)

s = URLSafeTimedSerializer('GOMOGOMONO...')

salt = b'$2b$11$Za4hFNuzn3Rvw7gLnUVZCu'

newpassword = None
dbEmail = ""
postDepart=""
postSession = ""
nameSession = ""
idSession , idToken = ("", "")
username = ""

#one-time MongoDB connection
client = pymongo.MongoClient("mongodb://localhost:27017")
db = client['mongo']

#Unrouted functions
def login_required(f):
    @wraps(f)
    def wrap(*args, **kwargs):

        if 'USERNAME' in session:
            return f(*args, **kwargs)
        else:
            return redirect(url_for('login'))

    return wrap

def smss(sendTo):
	'''uses one phone number for a free trail, function used in other functions as a extra feature'''
	account_sid = smsConfig.accountSID
	auth_token = smsConfig.authToken
	client = Client(account_sid, auth_token)
	message = client.messages.create(body='Hello there!',from_=smsConfig.twilioNumber,to='+263784428853')
	return message.sid


@app.route('/', methods=('GET', 'POST'))
@app.route('/home', methods=('GET', 'POST'))
def home():
    global postSession
    global postDepart
    postSession = ""
    postDepart=""
    status = None
    post = ""
    app.jinja_env.globals.update(zip=zip)
    current = datetime.now()
    depts = db.Vacancies.find()
    departments, totals, vac = ([], [], [])

    for i in depts:
        departments.append(i['department'])
    departments = list(set(departments)).copy()

    for i in departments:
        totals.append(db.Vacancies.find({'department':i,'deadline':{'$gte': current}}).count())
    
    if request.method == 'POST':
        department = request.form.get('department')
        post = db.Vacancies.find({'department':department})
    else:
        post = db.Vacancies.find()

    

    for i in post:
        position = i['post']
        department=i['department']
        minimum_requirements = i['minimum requirements']
        responsibilities = i['responsibilities']
        deadline = i['deadline']
        post_id=i['_id']
        apply_url = url_for('test', token = position,depart=department, _external = False)
        description = i['post description']
        
        current = datetime.now()

        if current < deadline:
            status = "Active Vacancy"
            vac.append((position, minimum_requirements, responsibilities, apply_url, description,post_id,department))
        else:
            status = "Expired Vacancy"
    
    print(departments)
    print(totals)


   
    return render_template('index2.html', post=vac,depts=departments, totals=totals )

@app.route('/humanResourceHome')
@login_required
def humanResourceHome():
    global postSession
    postSession = ""
    global postDepart
    postDepart =""
    status = None
    pos = db.Vacancies.find().count()
    posts = db.Vacancies.find() #query : vacancies
    active = 0
    expired = 0
    archived = 0

    for i in posts:
        if i['deadline'] < datetime.now():
            expired += 1
        else:
            active += 1 
    

    applicants = db.applicants.find().count()  #query : applicants
  
    




    posting = db.Vacancies.find()
    vac = []
    
    for i in posting:
        position = i['post']
        department=i['department']
        minimum_requirements = i['minimum requirements']
        responsibilities = i['responsibilities']
        deadline = i['deadline']
        total= db.applicants.find({"post":position,"department":department}).count()
        description = i['post description']
        department=i['department']
        current = datetime.now()

        if current < deadline:
            status = "Active Vacancy"
        else:
            status = "Expired Vacancy"

        vac.append((position, minimum_requirements, responsibilities, deadline, status,department, total, description ))

    return render_template('hr.html', post=vac,active=active, expired=expired, archived=archived, applicants=applicants,posts=pos,username= username)



@app.route('/manageposts')
@login_required
def manageposts():
    global postSession
    postSession = ""
    global postDepart
    postDepart = ""
    status = None
    
    posting = db.Vacancies.find()
    vac = []
    
    for i in posting:
        position = i['post']
        department=i['department']
        minimum_requirements = i['minimum requirements']
        responsibilities = i['responsibilities']
        deadline = i['deadline']
        total= db.applicants.find({"post":position,"department":department}).count()
        add_url = url_for('temporary', token = position,depart =department, _external = False)
        edit_url = url_for('edit', token = position,depart= department, _external = False)
        fullList_url = url_for('fullList', token = position,depart= department, _external = False)
        adjudicator_url = url_for('adjudicator', token = position,depart= department, _external = False)
        interview_url=url_for('interview', token = position,depart= department, _external = False)
        description = i['post description']
        
        current = datetime.now()

        if current < deadline:
            status = "Active Vacancy"
        else:
            status = "Expired Vacancy"

        vac.append((position, minimum_requirements, responsibilities, deadline, status, add_url, edit_url, fullList_url,adjudicator_url,interview_url, description,total,department ))


    return render_template('manageposts.html', post=vac)




@app.route('/addVacancy', methods=('GET', 'POST'))
@login_required
def addVacancy():

    department=db.Department.find()

    if request.method == 'POST':
        post = request.form.get('post')
        description = request.form.get('post description')
        department = request.form.get('department')
        requirements = (request.form.get('requirement')).split("\r\n")
        responsibilities = (request.form.get('responsibilities')).split("\r\n")

        dateOfDeadline = request.form.get('deadline')

        deadlineDate = dateOfDeadline.split("-")

        c = []

        for i in deadlineDate:
            c.append(int(i))

        deadline = datetime(c[0], c[1], c[2], 11, 59, 59)
        db.Vacancies.insert({"post":post, "post description":description,  "department":department, "deadline":deadline, "minimum requirements":requirements, "responsibilities":responsibilities})
        flash('New Vacancy Successfully Added','success')
        return redirect(url_for('humanResourceHome'))
    return render_template('addvacancy.html',depart=department)


@app.route('/department', methods=('GET', 'POST'))
@login_required
def department():
    depart = db.Department.find()

    return render_template('department.html',depart=depart)

@app.route('/adjudication', methods=('GET', 'POST'))
@login_required
def adjudication():

    adj = db.Adjudicator.find({"post":postSession,"department":postDepart})
    fil=db.Field.find({"post":postSession,"department":postDepart})

    return render_template('adjudication.html',adj=adj,post=postSession,depart=postDepart,field=fil)

@app.route('/addadjudication', methods=('GET', 'POST'))
@login_required
def addadjudication():

    if request.method == 'POST':
        for i in range(1, int(request.form.get('numberOfAdjudicator')) + 1):

            db.Adjudicator.insert({"department":postDepart, "post":postSession, "fullname":request.form.get('fullname{}'.format(i)),"position":request.form.get('position{}'.format(i)),"email":request.form.get('email{}'.format(i)) })

        return redirect(url_for('adjudication'))
        
        
    return render_template('addadjudicator.html')

@app.route('/addfield', methods=('GET', 'POST'))
@login_required
def addfield():

    if request.method == 'POST':
        field=[]
        for i in range(1, int(request.form.get('numberOfField')) + 1):

            db.Field.insert({"department":postDepart, "post":postSession, "field":request.form.get('field{}'.format(i))})
            db.Adjudicator.update_many({"department":postDepart, "post":postSession},{"$set":{request.form.get('field{}'.format(i)):""}})
            field.append(request.form.get('field{}'.format(i)))
        return redirect(url_for('adjudication'))
        
        
    return render_template('addfield.html')

@app.route('/interviews', methods=('GET', 'POST'))
@login_required
def interviews():
    app.jinja_env.globals.update(zip=zip)

    vaccancies = list()
    applicants = db.applicants.find({"post":postSession,"department":postDepart,"status":"shortlist"})
    
    adjudicators = db.Adjudicator.find({"post":postSession,"department":postDepart})
    
    # for applicant in applicants:
        
    #     details["applicant"]= applicant["name"]
        
    
    for adjudicator in adjudicators:
        details = dict()
        details["fullname"] = adjudicator["fullname"]
        details["fields"] = db.Field.find({"post":postSession,"department":postDepart})
        vaccancies.append(details)
            # print(details)
    print(vaccancies)

            

    fields = db.Field.find({"post":postSession,"department":postDepart})

    print(adjudicators)

    return render_template('interview.html',applicants=applicants ,adju=adjudicators,field=fields ,vaccancies=vaccancies)

@app.route('/deldepart/<value>')
def deldepartment(value):
    db.Department.delete_one({"department":value})
    

    return redirect(url_for('department'))



@app.route('/adddepartment', methods=('GET', 'POST'))
def adddepartment():
    if request.method == 'POST':
        department = request.form.get('department')
  
        db.Department.insert({"department":department})
        flash('New Department Successfully Added','success')
        return redirect(url_for('department'))
    

    return render_template('adddepartment.html')



@app.route('/shortlist', methods=('GET', 'POST'))
def shortlist():
    global nameSession
    nameSession = ""

    app.jinja_env.globals.update(zip=zip)
    post = postSession
    depart =postDepart
   
    query = db.applicants.find({"post":post,"department":depart, "$or": [{"status":"new"}, {"status":"reserved"}]})

    applicants, x, accepted, aApplicants, aIDs, ids = ([], [], [], [], [], [])

    for i in query:
        applicants.append(i['name'])
        aIDs.append(i['National_id'])

    for i in range(len(applicants)):
        x.append(i)

    query = db.applicants.find({'post':post,"department":depart, 'status':'shortlist'})

    
    for i in query:
        accepted.append(i['email'])
        aApplicants.append(i['name'])
        ids.append(i['National_id'])

    if request.method == 'POST':
        for i in x:
            if request.form.get(str(i)) == 'shortlist':
                name = applicants[i]
                db.applicants.update({"name":name}, {"$set":{"status":"shortlist"}})
            if request.form.get(str(i)) == 'denied':
                name = applicants[i]
                db.applicants.update({"name":name}, {"$set":{"status":"denied"}})

        flash('New Applicants have been Shortlisted Successfully','success')

        return redirect(url_for('shortlist'))
    return render_template('shortlist.html', x=x, y=applicants, z=aIDs,  accepted=accepted, aApplicants=aApplicants, ids=ids)

@app.route('/resetPassword')
def resetPassword():
    global newpassword

    if newpassword != None:
       #Hashing new password
       newpassword = (bcrypt.hashpw(newpassword.encode('utf-8'), salt)).decode('utf-8')
       db.Credentials.update_one({"_id":dbEmail}, {"$set":{"password":newpassword}})
       newpassword = None
       return redirect(url_for('login'))
    return render_template('resetpassword.html')

@app.route('/passwordRecovery', methods = ['GET','POST'])
def passwordRecovery():
	'''verifies the email adress and sent the password '''
	email = ""
	if request.method == 'POST':
		email = request.form['email']
	token = s.dumps(email, salt = 'emailRecovery')
	return redirect(url_for('sending',token = token , _external = False))

@app.route('/sending/<token>')
def sending(token):
    '''this function sends a message to that email to get a new password, can use username which will be used to fetch the email address if it exists in the database '''

    global dbEmail
    email = s.loads(token, salt = 'emailRecovery')
    token = s.dumps(email, salt='emailToLink')
    dbEmail = email

    link = url_for('forgotPassword', token = token , _external = True)
    msg = Message('Email Verification', sender='Harare Institute Of Technology',recipients=[email])
    msg.body = "User associated with the your account has iniated a request to recover user password.\nTo complete password recover process, click the following link to enter new password \n{} \n\nFor your account protection, this link will expire after 24 hours.\n\nBest regards\nHIT\n\nhttps://www.hit.ac.zw/".format(link)
    mail.send(msg)
    return "Email has been sent to user emal address {}".format(email)

@app.route('/forgotPassword/<token>')
def forgotPassword(token):
	'''this runs from the link sent to the email address'''
	try:
		email = s.loads(token,salt='emailToLink', max_age = 3600)

	except SignatureExpired:
		return "Link Timed Out"
	return render_template('newpassword.html')

@app.route('/test/<token>/<depart>')
def test(token,depart):
    global postDepart
    global postSession
    postSession = token
    postDepart= depart
    print(token)
    print(depart)
    return redirect(url_for('apply'))

@app.route('/temporary/<token>/<depart>')
def temporary(token,depart):
    '''keeps track of all the posts clicked for application or for editing vacancy'''
    global postSession
    global postDepart
    postSession = token
    postDepart = depart
    return redirect(url_for('shortlist'))

@app.route('/edit/<token>/<depart>')
def edit(token,depart):
    '''keeps track of all the posts clicked for application or for editing vacancy'''
    global postSession
    global postDepart
    postSession = token
    postDepart= depart
    return redirect(url_for('editVacancy'))

@app.route('/fullList/<token>/<depart>')
def fullList(token,depart):
    '''keeps track of all the posts clicked for application or for editing vacancy'''
    global postSession
    global postDepart
    postDepart=depart
    postSession = token
    return redirect(url_for('applicantList'))

@app.route('/adjudicator/<token>/<depart>')
def adjudicator(token,depart):
    '''keeps track of all the posts clicked for application or for editing vacancy'''
    global postSession
    global postDepart
    postDepart=depart
    postSession = token
    return redirect(url_for('adjudication'))

@app.route('/interview/<token>/<depart>')
def interview(token,depart):
    '''keeps track of all the posts clicked for application or for editing vacancy'''
    global postSession
    global postDepart
    postDepart=depart
    postSession = token
    return redirect(url_for('interviews'))

@app.route('/cv/<token>/<idToken>/<postToken>')
def cv(token, idToken, postToken):
    global nameSession
    nameSession = token
    global idSession
    idSession = idToken
    global postSession
    postSession = postToken

    return redirect(url_for('viewCV'))

@app.route('/newPasswordEntry', methods=('GET', 'POST'))
def newPasswordEntry():

    global newpassword
    if request.method == 'POST':
        newpassword = request.form.get('newpassword2')
        return redirect(url_for('resetPassword'))
    return render_template('newpassword.html')


@app.route('/apply', methods=('GET', 'POST'))
def apply():


    if request.method == 'POST':

        name =  '''{} {}'''.format(request.form.get('firstname'),request.form.get('surname'))
        contacts = '''{} ,  {}  '''.format(request.form.get('phone1'),  request.form.get('address'))
        email = request.form.get('email')
        sex = request.form.get('sex')
        maritalStatus=request.form.get('maritalstatus')
        title = request.form.get('title')
        department=request.form.get('department')
        current = date.today()
        dateOfBirth = request.form.get('DOB')
        cd = current.strftime('%Y, %m, %d')
        currentDate = cd.split(",")
        dob = dateOfBirth.split("-")
        c = []
        d = []

        for i in currentDate:
            c.append(int(i))
        for i in dob:
            d.append(int(i))

        #dynamic entry of age
        age = int((date(c[0], c[1], c[2]) - date(d[0], d[1], d[2])).days / 365)

        #qualifications

        qualifications = []
        filing=[]
        workexperience = []
        
        files = request.files.getlist('file[]')
        for file in files:
            if file :
                
                
                filename = secure_filename(file.filename)
                filing.append(filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))


        for i in range(1, int(request.form.get('numberOfQualifications')) + 1):
            qualifications.append( "{}. ".format(str(i)) + request.form.get('qualification{}'.format(i)) +" awarding institute is "+request.form.get('awardingInstitute{}'.format(i)) + " in the year "+request.form.get('year{}'.format(i))+"." )
           
        for i in range(1, int(request.form.get('numberOfWorkExperiences')) + 1):
            workexperience.append("{}. Worked at {} as {} since {}. ".format(i, request.form.get('organisation{}'.format(i)), request.form.get('position{}'.format(i)), request.form.get('timeframe{}'.format(i)) ))

        user = db.applicants.find_one({'National_id':request.form.get('nationalid'), 'post':title})

        if user is None :
            db.applicants.insert({'name':name, 'contact details':contacts, 'sex':sex, 'age':age,'National_id':request.form.get('nationalid'), 'academic qualifications':qualifications, 'work experience':workexperience,'cv':filing, 'status':'new'
            ,'maritalstauts':maritalStatus , 'post':postSession,'department':postDepart, 'email':email})
            flash('Application For Vacancy Was Successfull')
            return redirect(url_for('home'))
        else:
            flash('Application For Vacancy Already Exists')
            return redirect(url_for('home'))
    
    return render_template('applicationform.html',title=postSession,department=postDepart)


@app.route('/applicantList')
def applicantList():
    data= []
    user = None
    count = []
    cv_url = []

    app.jinja_env.globals.update(zip=zip)
    if postSession == '':
        user = db.applicants.find({})
    else:
        user = db.applicants.find({"post":postSession,"department":postDepart})

    for i in user:
        dictionary = []
        values = []
        values = list(i.values())
        dictionary = values.copy()
        
        cv_url.append(url_for('cv', token = values[1], idToken = values[5], postToken = values[-2] , _external = False))
        
        data.append(dictionary)
        count.append(len(data))

    return render_template("list.html", table=data,post=postSession,depart=postDepart, count=count, cvs=cv_url )

@app.route('/login', methods=('GET', 'POST'))
def login():
    '''verifies entered credentials with that in the database'''
    error_message = ""

    if request.method == 'POST':
        global username
        username = request.form['username']
        password = bcrypt.hashpw(request.form['password'].encode('utf-8'), salt)
        user = db.Credentials.find_one({'username': username})

        if user != None :
            dbUsername = user['username']
            dbPassword = bytes(user['password'])

            if username != dbUsername or bcrypt.hashpw(request.form['password'].encode('utf-8'), password) != dbPassword:
                error_message = 'Invalid Credentials. Please try again.'
            else:
                session['USERNAME'] = username
                db.Credentials.update_one({"username":username}, {"$set":{"active":"True"}})
                return redirect(url_for('humanResourceHome'))
        else:
            error_message = 'Invalid Credentials. Please try again.'

    return render_template('login.html', Error_Message=error_message, System_Name="")


@app.route('/signup', methods=('GET', 'POST'))
def signup():
    '''verifies entered credentials with that in the database'''
    error_message = ""

    if request.method == 'POST':
        global username
        username = request.form['username']
        password = bcrypt.hashpw(request.form['password'].encode('utf-8'), salt)
        user = db.Credentials.find_one({'username': username})

        if user == None :
            db.Credentials.insert_one({'username': username,'password':password})
            session['USERNAME'] = username
            db.Credentials.update_one({"username":username}, {"$set":{"active":"True"}})
            return redirect(url_for('humanResourceHome'))
        else:
            error_message = 'User Already exists. Please try again.'

    return render_template('signup.html', Error_Message=error_message, System_Name="")



@app.route('/editVacancy', methods=('GET', 'POST'))
def editVacancy():

    post = postSession
    depart= postDepart
    query = db.Vacancies.find_one({"post":post,"department":depart})
    depart=db.Department.find()
    posts = []
    posts.extend((query['post'], query['post description'], query['department'], "\r\n".join(query['minimum requirements']), "\r\n".join(query['responsibilities']), (query['deadline']).date()))

    if request.method == 'POST':

        dateOfDeadline = request.form.get('deadline')

        deadlineDate = dateOfDeadline.split("-")
        c = []

        for i in deadlineDate:
            c.append(int(i))

        deadline = datetime(c[0], c[1], c[2], 11, 59, 59)
        description = request.form.get('post description')
        requirements = (request.form.get('requirement').split('\r\n'))
        responsibilities = (request.form.get('responsibilities').split('\r\n'))

        db.Vacancies.update({"post":post}, {"$set":{"minimum requirements":requirements, "responsibilities":responsibilities, "deadline":deadline}})
        flash('Vacancy Edit Successful ')
        return redirect(url_for('humanResourceHome'))

    return render_template('editvacancy.html', post=posts,depart=depart)

@app.route('/sendNotification', methods=('GET', 'POST'))
def sendNotification():
    post = postSession
    depart=postDepart
    accepted = []    # accepted applicants' emails
    aApplicants = [] # accepted applicants' list

    denied = []      # denied applicants' emails
    dApplicants = [] # denied applicants' list

    if request.method == 'POST':
        time = request.form.get('time')
        date = request.form.get('date')
        selected_date = datetime.strptime(date, "%Y-%m-%d").date()
        query = db.applicants.find({'post':post,'department':depart, 'status':'shortlist'})
        for i in query:
            accepted.append(i['email'])
            aApplicants.append(i['name'])
        query = db.applicants.find({'post':post,'department':depart, 'status':'denied'})
        for i in query:
            denied.append(i['email'])
            dApplicants.append(i['name'])

        #sending to accepted applicants
        for i, j in zip(accepted, aApplicants):
            msg = Message(emailConfig.aSubject.format(post,depart), sender='Harare Institute Of Technology',recipients=[i])
            msg.body = emailConfig.aBody.format(j, time,selected_date)
            mail.send(msg)

        #sending to denied applicants
        for i, j in zip(denied, dApplicants):
            msg = Message(emailConfig.dSubject.format(post), sender='Harare Institute Of Technology',recipients=[i])
            msg.body = emailConfig.dBody.format(j, post)
            mail.send(msg)

        db.applicants.delete_many({'post':post,'department':depart, 'status':'denied'})
        flash('Emails Sent Successfully')
    return redirect(url_for('humanResourceHome'))

@app.route('/viewCV', methods=('GET', 'POST'))
def viewCV():
     
    post = postSession
    name = nameSession
    
    nat_id = idSession
    query = db.applicants.find({"name":name, "post":post, "National_id":nat_id})
    file = ''
    for i in query:
        file = (i['curriculum vitae'])


    path = "static/CVs/"
    try:
        with open('{}{}-{}-{}.pdf'.format(path, nameSession, idSession, post), 'xb') as f:
            f.write(file)
       
    except FileExistsError:
        return redirect(url_for('static', filename='CVs/{}-{}-{}.pdf'.format(nameSession, idSession, post)))

    return redirect(url_for('static', filename='CVs/{}-{}-{}.pdf'.format(nameSession, idSession, post)))

@app.route('/CV', methods=('GET', 'POST'))
def CV():

    global nameSession
    nameSession = ""
    global idSession
    idSession = ""

    app.jinja_env.globals.update(zip=zip)

    accepted, cv_url , ids = ([], [], [])
    query = db.applicants.find({'post':postSession, 'status':'shortlist'})
    for i in query:
        accepted.append(i['name'])
        ids.append(i['National_id'])
        cv_url.append(url_for('cv', token = i['name'], idToken = i['National_id'] , _external = False))
    
    return render_template('viewcv.html', names=accepted, ids=ids, cvs=cv_url)
 

@app.route('/logout')
@login_required
def logout():
    session.clear()
    db.Credentials.update_one({"username":username}, {"$set":{"active":"False"}})
    return redirect(url_for('login'))

#Error code handling functions
#400 page 
@app.errorhandler(400)
def bad_request(e):
    return render_template('400.html'), 400

#401 page 
@app.errorhandler(401)
def unauthorized(e):
    return render_template('401.html'), 401

#403 page 
@app.errorhandler(403)
def forbidden(e):
    return render_template('403.html'), 403

#404 page
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

#408 page 
@app.errorhandler(408)
def request_timeout(e):
    return render_template('408.html'), 408

#500 page
@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500

if __name__ == "__main__":
	app.run(port=8090 , debug=True)
