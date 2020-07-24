from flask import Flask ,render_template , flash , redirect , url_for, session, request, logging

import pymysql
from passlib.hash import pbkdf2_sha256
from data import Articles
from functools import wraps

app = Flask(__name__)
app.debug=True


db = pymysql.connect(host='localhost', 
                        port=3306, 
                        user='root', 
                        passwd='1234', 
                        db='myflaskapp')


#init mysql 
# mysql = MySQL(app)
# cur  = mysql.connection.cursor()
# result  = cur.execute("SELECT * FROM users;")

# users  = cur.fetchall()
# print(users)
# print(result)

def is_logged_out(f):
    @wraps(f)
    def wrap(*args , **kwargs):
        if 'is_logged' in session:
        # if is session['is_logged']:
            return redirect(url_for('articles'))
        else:
            return f(*args ,**kwargs)
    return wrap
def is_admin(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if session['username'] == 'ADMIN':
            return redirect('/admin')
        else :
            return f(*args, **kwargs) # 그대로 실행되는 코드 
    return wrap

def is_admined(f):
    @wraps(f)
    def wrap(*args,**kwargs):
        if session['username'] !="ADMIN":
            return redirect('/')
        else:
            return f(*args,**kwargs)
    return wrap

@app.route('/register',methods=['GET' ,'POST'])
@is_logged_out
def register():
    if request.method == 'POST':

        # data = request.body.get('author')
        name = request.form.get('name')
        email = request.form.get('email')
        password = pbkdf2_sha256.hash(request.form.get('password'))
        re_password = request.form.get('re_password')
        username = request.form.get('username')
        # name = form.name.data

        cursor = db.cursor()
        sql = 'SELECT username FROM users WHERE username = %s'
        cursor.execute(sql,[username])
        username_one = cursor.fetchone()

        if  username_one :
            return redirect(url_for('register'))
        else:

            if(pbkdf2_sha256.verify(re_password,password )):
                print(pbkdf2_sha256.verify(re_password,password ))
            
                sql = '''
                    INSERT INTO users (name , email , username , password) 
                    VALUES (%s ,%s, %s, %s )
                '''
                cursor.execute(sql , (name,email,username,password ))
                db.commit()
            

                # cursor = db.cursor()
                # cursor.execute('SELECT * FROM users;')
                # users = cursor.fetchall()
            
                return redirect(url_for('login'))

            else:
                return redirect(url_for('register'))

        db.close()
    else:
        return render_template('register.html')


@app.route('/login',methods=['GET', 'POST'])
@is_logged_out
def login():
    if request.method == 'POST':
        id = request.form['username']
        pw = request.form.get('password')
        print([id])

        sql='SELECT * FROM users WHERE username = %s'
        cursor  = db.cursor()
        cursor.execute(sql, [id])
        users = cursor.fetchone()
        print(users)

        if users ==None:
            return redirect(url_for('login'))
        else:
            if pbkdf2_sha256.verify(pw,users[4] ):
                session['is_logged'] = True
                session['username'] = users[3]
                print(session)
                return redirect('/')
            else:
                return redirect(url_for('login'))
        
    else:
        return render_template('login.html')

def is_logged_in(f):
    @wraps(f)
    def _wraper(*args, **kwargs):
        if 'is_logged' in session:#아래와 같은말임
        # if session['is_logged']:#위와 같은 말임
            return f(*args, **kwargs)
        else:
            flash('UnAuthorized, Please login', 'dnager')
            return redirect(url_for('login'))
    return _wraper

@app.route('/admin', methods=['GET','POST'])
@is_logged_in
@is_admined
def admin():
    cursor = db.cursor()
    sql = 'SELECT * FROM users'
    cursor.execute(sql)
    admin_user = cursor.fetchall()
    return render_template('admin.html', data = admin_user)

@app.route('/user/<string:id>', methods=['GET', 'POST'])
@is_logged_in
@is_admined
def change_level(id):
    if request.method =='POST':
        cursor=db.cursor()
        sql = 'UPDATE `users` SET `auth`=%s WHERE  `id`=%s;'
        # 
        auth = request.form['auth']
        cursor.execute(sql ,[auth,id])
        return redirect('/')
    else:
        cursor=db.cursor()
        sql = "SELECT * FROM users WHERE id=%s"
        cursor.execute(sql,[id])
        user = cursor.fetchone()
        return render_template('change_level.html', users=user)

@app.route('/')
@is_logged_in
@is_admin

def index():
    print("Success")
    # session['test'] = "Hokyoung Kim"
    # session_data = session
    # print(session_data)
    # # return "TEST"
    return render_template('home.html')

@app.route('/logout')
@is_logged_in
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/about')
@is_logged_in
def about():
    print("Success")
    # return "TEST"
    # return redirect(url_for('about'))
    return render_template('about.html')

@app.route('/articles')
@is_logged_in
def articles():
    # data = Articles()
    # print(len(articles))
    cursor = db.cursor()
    sql='SELECT * FROM topic;'
    cursor.execute(sql)
    data = cursor.fetchall()
    print(data)
    return render_template('articles.html',articles=data)
    # return "GET Success"


@app.route('/article/<int:id>')
@is_logged_in
def     article(id):
    print(type(id))
    articles= Articles()[id-1]
    cursor = db.cursor()
    sql = 'SELECT * FROM topic WHERE id=%s;'
    cursor.execute(sql,[id])
    topic = cursor.fetchone()
    print(topic)
    # print(articles)
    return render_template('article.html',data =topic)
    # return "Success"

@app.route('/add_articles',methods=['GET','POST'])
@is_logged_in
def add_articles():
    if request.method == 'POST':
        # print(request.form['title'])
        title = request.form['title']
        body = request.form['body']
        author = request.form['author']
        cursor = db.cursor()
        sql = '''
            INSERT INTO topic (title, body , author)
            VALUES (%s ,%s ,%s)
        '''
        cursor.execute(sql,(title, body , author))
        db.commit()
        
        return redirect("/articles")
    else:
        return render_template('add_articles.html')

    db.close()

@app.route('/article/<string:id>/edit_article',methods=['GET', 'POST'])
@is_logged_in
def edit_article(id):
    if request.method =="POST":
        title = request.form['title']
        body = request.form['body']
        author = request.form['author']
        cur = db.cursor()
        sql = '''
            UPDATE `topic` SET `title`=%s,`body`=%s, `author`=%s  WHERE  `id`= %s;
        '''
        cur.execute(sql , (title,body,author, id ))
        db.commit()
        return redirect(url_for('articles'))
    else:
        print(id)
        cur = db.cursor()
        sql = 'SELECT * FROM topic WHERE id=%s'
        cur.execute(sql , [id])
        topic = cur.fetchone()
        return render_template('edit_article.html', data= topic)
    db.close()

@app.route('/delete/<string:id>',methods = ['POST'])
@is_logged_in
def delete(id):
   cursur = db.cursor()
   sql = 'DELETE FROM `topic` WHERE  `id`=%s;'
   cursur.execute(sql,[id])
   db.commit()
   return redirect(url_for('articles'))


if __name__ =='__main__':
    # app.run(host='0.0.0.0', port='8080')
    app.secret_key = 'hokyoung123456789'# ssession 실행시 필요한 설정이다
    app.run() # 서버 실행
    