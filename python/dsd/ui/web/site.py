import pymongo
from flask import Flask, request, session, g, redirect, url_for, abort, render_template, flash
from flask import render_template

app = Flask(__name__)
app.secret_key='123edft654edfgY^%R#$%^&**&^'

@app.route("/")
def index():
    if 'Is_Login' in session:
        if session['Is_Login'] == '1':
            if session['User_Type'] == 'Admin':
                return render_template('main_page.html')
            if session['User_Type'] == 'Common':
                return render_template('jupyter_page.html')
    return render_template('welcome_page.html')

@app.route("/login", methods=['GET','POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form.get('Username')
        password = request.form.get('Password')
        login_result = check_login(username,password)
        if login_result[0]:
            session['Is_Login'] = '1'
            session['User_Type'] = login_result[2]
            return redirect(url_for('index'))
        else:
            session['Is_Login'] = '0'
            error = login_result[1]
    return render_template('login.html',error=error)

@app.route("/manage_user", methods=['GET','POST'])#TBC
def manage_user():    
    if 'Is_Login' in session:
        if session['Is_Login'] == '1':
            if session['User_Type'] == 'Admin':
                if request.method == 'GET':
                    return render_template('manage_user.html')
                if request.method == 'POST':                    
                    client = pymongo.MongoClient()
                    db = client.db_dsd
                    collection = db.users
                    if request.form.get('Action') == 'Add_User':
                        username = request.form.get('Username')
                        password = request.form.get('Password')
                        max_container_count = request.form.get('Max_Container_Count')
                        max_disk_space = request.form.get('Max_Disk_Space')
                        user_type = request.form.get('User_Type')
                        db.users.save({'Username':username,'Password':encrypt_password(password),'User_Type':user_type,'Max_Container_Count':max_container_count,'Max_Disk_Space':max_disk_space})
                    
                    if request.form.get('Action') == 'Delete_User':
                        
    return render_template('welcome_page.html')

def check_login(username,password):
    client = pymongo.MongoClient()
    db = client.db_dsd
    collection = db.users
    cursor = collection.find({'Username':username})
    if cursor.count() == 0:
        return [False,'No such user!']
    if encrypt_password(password) == cursor[0]['Password']:
        return [True,'login succeed!',cursor[0]['User_Type']]
    return [False,'Password mismatch!']

def encrypt_password(password):#TBC
    return password



@app.route('/logout')
def logout():
    session.pop('Is_Login', None)
    session.pop('User_Type', None)
    flash('You were logged out')
    return redirect(url_for('index'))

if __name__ == "__main__":
    #app.debug = True
    app.run(host='0.0.0.0')
