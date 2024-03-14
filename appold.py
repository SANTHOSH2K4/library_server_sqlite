from flask import Flask, request, jsonify,render_template,redirect
import mysql.connector
from datetime import datetime
import os
import csv
from werkzeug.utils import secure_filename

UPLOAD_FOLDER = 'uploads'

stud_alert=[0,'']
book_alert=[0,'']

app = Flask(__name__, static_url_path='/static')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


config = {
    'user': 'root',
    'password': 'root',
    'host': 'localhost',
    'database': 'kcet'
}

def set_pin(uid,pin):
    try:
        conn = mysql.connector.connect(**config)
        cursor = conn.cursor()
        cursor.execute("SELECT roll_no FROM users WHERE roll_no = %s", (uid,))
        existing_roll_no = cursor.fetchone()
        if existing_roll_no:
            query=f"update users set pin='{pin}' where roll_no='{uid}'"
            cursor.execute(query)
            conn.commit()
            cursor.close()
            conn.close()
            return 'pin set successfully'
        else:
            return 'roll number not found'
    except Exception as e:
        return e

def book_data_insert_by_excel(file_path):
    res=''
    conn = mysql.connector.connect(**config)
    cursor = conn.cursor()

    def read_csv_file(file_path):
        data = []
        with open(file_path, 'r') as file:
            csv_reader = csv.reader(file)
            # Skip header if present
            next(csv_reader, None)
            for row in csv_reader:
                data.append(row)
        return data

    csv_data = read_csv_file(file_path)

    for row in csv_data:
        cursor.execute("SELECT id FROM books WHERE id = %s", (row[0],))
        existing_id = cursor.fetchone()

        if existing_id:
            res+=f"Skipping insertion for ID {row[0]} as it already exists."
            print(f"Skipping insertion for ID {row[0]} as it already exists.")
        else:
            query = f"INSERT INTO books(id,title,author,rating,description,isissued,issued_for,tag,issued_times,date,image,arrived_date) VALUES (%s, %s, %s, %s, %s, 0, 'none', %s, 0, 'clear', %s,CURRENT_TIMESTAMP)"
            cursor.execute(query, (row[0], row[1], row[2], row[3], row[4], row[5],row[6]))
            conn.commit()
            res+=f"Inserted row with ID {row[0]}"
            print(f"Inserted row with ID {row[0]}")

    cursor.close()
    conn.close()
    return res

def users_data_insert_by_excel(file_path):
    conn = mysql.connector.connect(**config)
    cursor = conn.cursor()
    res=''
    def read_csv_file(file_path):
        data = []
        with open(file_path, 'r') as file:
            csv_reader = csv.reader(file)
            # Skip header if present
            next(csv_reader, None)
            for row in csv_reader:
                data.append(row)
        return data

    csv_data = read_csv_file(file_path)

    for row in csv_data:
        cursor.execute("SELECT roll_no FROM users WHERE roll_no = %s", (row[0],))
        existing_roll_no = cursor.fetchone()

        if existing_roll_no:
            res+=f"Skipping insertion for Roll No {row[0]} as it already exists."
            print(f"Skipping insertion for Roll No {row[0]} as it already exists.")
        else:
            query = f"INSERT INTO users (roll_no, name, issuancelimit, tags, track, pass, email, pin,Dept,year_of_studying) VALUES ('{row[0]}', '{row[1]}', {int(row[2])}, '', '', '{row[3]}', '{row[4]}', 'none', '{row[5]}', '{row[6]}')"
            cursor.execute(query)
            conn.commit()
            res+='Inserted row with Roll No {row[0]}.\n'
            print(f"Inserted row with Roll No {row[0]}")

    cursor.close()
    conn.close()
    return res 

def log_validation(uid,pas):
    conn = mysql.connector.connect(**config)
    cursor = conn.cursor()
    try:
        query=f"select roll_no from users where roll_no='{uid}' and pass='{pas}'"
        cursor.execute(query)
        rows=cursor.fetchall()
        cursor.close()
        conn.close()
        if(rows[0][0] == uid):
            return 'login success'
        else:
            return 'login failed'
    except Exception as e:
        return 'login failed'

def issue_book(uid,bid):
    conn = mysql.connector.connect(**config)
    cursor = conn.cursor()
    if conn.is_connected():
        userfound=0
        try:
            query=f"select roll_no from users where roll_no='{uid}'"
            cursor.execute(query)
            rows=cursor.fetchall()
            print(rows)
            if(rows[0][0] == uid):
                userfound=1
            else:
                userfound=0
        except Exception as e:
            print(e)
            userfound=0
        if(userfound==0):
            return 'User not found!'
        
        bookfound=0
        try:
            
            query=f"select id from books where id='{bid}'"
            cursor.execute(query)
            rows=cursor.fetchall()
            
            print(rows)
            if(rows[0][0] == bid):
                bookfound=1
            else:
                bookfound=0
        except Exception as e:
            bookfound=0
            
        if(bookfound==0):
            return 'Book not found!'

        current_date = datetime.now().strftime("%d-%m-%y")

        query = f"SELECT * FROM books where id='{bid}'"
        cursor.execute(query)
        rows = cursor.fetchall()

        tag_lib=rows[0][7].split(',')        


        print(rows[0])
        isissued=rows[0][5]
        print('isissued',isissued)
        issued_times=rows[0][8]
        print('issued times',issued_times)

        query = f"SELECT title FROM books where id='{bid}'"
        cursor.execute(query)
        bname = cursor.fetchall()
        print('\nbook_name',bname,'\n')

        query=f"select *from users where roll_no ='{uid}'"
        cursor.execute(query)
        rows=cursor.fetchall()



        tag_li=rows[0][3].split(',')
        track=rows[0][4]
        track+=f'{bname[0][0]}/{current_date},'
        print('track',track)
        for i in tag_lib:
            tag_li.append(i)
        print('tag_li',tag_li)
        tags=','.join(tag_li)

        issuance_limit=rows[0][2]
        print('issuance_limits',issuance_limit)
        if(issuance_limit==0):
            return "you have reached the issuance_limit!"
        else:
            if(isissued==1):
                return "This book is already issued!"
            elif(isissued==0):
                issued_times+=1
                print(issued_times)
                current_date = datetime.now().strftime("%d-%m-%y")
                print(current_date)
                query2=f"update books set isissued=1,issued_for='{uid}',issued_times={issued_times},date='{current_date}' where id='{bid}'"
                cursor.execute(query2)
                conn.commit()

                issuance_limit=issuance_limit-1

                

                query=f"update users set issuancelimit={issuance_limit},tags='{tags}',track='{track}' where roll_no='{uid}'"
                cursor.execute(query)
                conn.commit()

                query = f"SELECT * FROM books where id='{bid}'"
                cursor.execute(query)
                rows = cursor.fetchall()
                print(rows[0])

                conn.commit()

                return 'success'

@app.route('/setpin', methods=['POST'])
def pin_set():
    data=request.get_json()
    roll_no=data.get('roll_no','')
    pin=data.get('pin','')
    res=set_pin(roll_no,pin)
    return jsonify({'setpin_res':res})

@app.route('/getpin',methods=['POST'])
def pin_get():
    data=request.get_json()
    roll_no=data.get('roll_no','')
    conn = mysql.connector.connect(**config)
    cursor = conn.cursor()
    query=f"select roll_no,pin from users where roll_no='{roll_no}'"
    cursor.execute(query)
    res=cursor.fetchone()
    cursor.close()
    conn.close()
    st=''
    if res:
        st=res[1]
        
    elif not res:
        st='User not found!'
    return jsonify({'getpin_res':st})

@app.route('/get5latestarrivedbooks')
def get5latarr():
    conn = mysql.connector.connect(**config)
    cursor = conn.cursor()
    query="select *from books order by arrived_date desc limit 5"
    cursor.execute(query)
    rows=cursor.fetchall()
    print(rows)
    return rows

@app.route('/login', methods=['POST'])
def process_message():
    data = request.get_json()
    roll_no = data.get('roll_no', '')
    pas = data.get('password', '')
    res=log_validation(roll_no,pas)
    if(res=='login failed'):
        return jsonify({'log_res': res})
    else:
        conn = mysql.connector.connect(**config)
        cursor = conn.cursor()
        query=f"select email,Dept,year_of_studying,name from users where roll_no='{roll_no}'"
        cursor.execute(query)
        rows=cursor.fetchall()
        email=rows[0][0]
        dept=rows[0][1]
        year=rows[0][2]
        name=rows[0][3]
        return jsonify({'log_res': res,'roll_no':roll_no,'email':email,'dept':dept,'Year':year,'name':name})

@app.route('/issue_book',methods=['POST'])
def issuebook():
    data = request.get_json()
    roll=data.get('roll_no','')
    bid=data.get('bid','')
    res = issue_book(roll,bid)
    return jsonify({'issue_res':res})

@app.route('/')
def home():
        return 'HELLO LIBRARY'

def return_book(bid):
    conn = mysql.connector.connect(**config)
    cursor = conn.cursor()
    query = f"SELECT * FROM books "
    cursor.execute(query)
    rows = cursor.fetchall()
    bid_li=[]
    for i in rows:
        bid_li.append(i[0])
    print(bid_li)

    if(bid not in bid_li):
        return 'book ID not found!'

    query = f"SELECT * FROM books where id='{bid}'"
    cursor.execute(query)
    rows = cursor.fetchall()
    print(rows[0])
    isissued=rows[0][5]
    if(isissued==1):
        uid=rows[0][6]
        query=f"update books set isissued=0,issued_for='none',date='clear' where id='{bid}'"
        cursor.execute(query)
        conn.commit()
        query=f"select *from users where roll_no ='{uid}'"
        cursor.execute(query)
        rows=cursor.fetchall()
        issuance_limit=rows[0][2]
        issuance_limit=issuance_limit+1
        query=f"update users set issuancelimit={issuance_limit} where roll_no='{uid}'"
        cursor.execute(query)
        conn.commit()
        cursor.close()
        conn.close()
        return 'successfully returned'
    else:
        cursor.close()
        conn.close()
        return 'this book is not issued by anyone!'

@app.route('/admin')
def index():
    conn = mysql.connector.connect(**config)
    cursor = conn.cursor()
    query="select count(*) from users"
    cursor.execute(query)
    res=cursor.fetchone()
    total_students=res[0]

    query="select count(*) from books"
    cursor.execute(query)
    res=cursor.fetchone()
    total_books=res[0]

    query="select count(*) from books where isissued=1"
    cursor.execute(query)
    res=cursor.fetchone()
    total_books_issued=res[0]

    return render_template('index.html',total_students=total_students,total_books=total_books,total_books_issued=total_books_issued)

@app.route('/book')
def book_page():
    conn = mysql.connector.connect(**config)
    cursor = conn.cursor()
    query = f"SELECT * FROM books "
    cursor.execute(query)
    rows = cursor.fetchall()
    print(rows)
    if(book_alert[0]==1):
        book_alert[0]=0
        ret=book_alert[1]
        book_alert[1]=''
        return render_template('book.html',show_upload_alert=True,ret=ret,res=rows)
    else:
        return render_template('book.html',show_alert=False,res=rows,show_upload_alert=False)

@app.route('/student')
def stud_page():
    conn = mysql.connector.connect(**config)
    cursor = conn.cursor()
    query = f"SELECT roll_no,name,email,Dept,year_of_studying,issuancelimit,tags FROM users "
    cursor.execute(query)
    rows = cursor.fetchall()
    if(stud_alert[0]==1):
        stud_alert[0]=0
        resp=stud_alert[1]
        stud_alert[1]=''
        return render_template('student.html',show_alert=True,resp=resp,res=rows)
    else:
        return render_template('student.html',show_alert=False,res=rows)

@app.route('/showhistory/',methods=['POST'])
def sol():
    id= request.form['value']
    conn = mysql.connector.connect(**config)
    cursor = conn.cursor()
    query=f"select track from users where roll_no='{id}'"
    cursor.execute(query)
    rows = cursor.fetchall()
    print(rows)
    data_str = rows[0][0]

    # Splitting the string into key-value pairs
    pairs = data_str.split(',')

    # Creating a list of tuples in the desired format
    result = [(pair.split('/')[0], pair.split('/')[1]) for pair in pairs if pair]


    return render_template('history.html',res=result)




@app.route('/proc_return',methods=['POST'])
def proc_return():
    print("hello from proc_return")
    bid=request.form['bookNumberReturn']
    resp=return_book(bid)
    print(resp)
    conn = mysql.connector.connect(**config)
    cursor = conn.cursor()
    query = f"SELECT * FROM books "
    cursor.execute(query)
    rows = cursor.fetchall()
    print(rows)
    
    return render_template('book.html', show_alert=True,res=rows,resp=resp)

@app.route('/studentsUpload', methods=['POST'])
def upload_file():
    try:
        file = request.files['fileInput']

        if file.filename == '':
            return redirect(request.url)

        if file:
            filename = secure_filename(file.filename)
            upload_folder = app.config['UPLOAD_FOLDER']
            if not os.path.exists(upload_folder):
                os.makedirs(upload_folder)
            file_path = os.path.join(upload_folder, filename)
            file.save(file_path)
            ret=users_data_insert_by_excel(file_path)
            os.remove(file_path)
            stud_alert[0]=1
            stud_alert[1]=ret
            return redirect('/student')
    except Exception as e:
        return f'Error: {str(e)}'
    
@app.route('/BooksUpload', methods=['POST'])
def Book_upload_file():
    try:
        file = request.files['bookInput']

        if file.filename == '':
            return redirect(request.url)

        if file:
            filename = secure_filename(file.filename)
            upload_folder = app.config['UPLOAD_FOLDER']
            if not os.path.exists(upload_folder):
                os.makedirs(upload_folder)
            file_path = os.path.join(upload_folder, filename)
            file.save(file_path)
            ret=book_data_insert_by_excel(file_path)
            os.remove(file_path)
            book_alert[0]=1
            book_alert[1]=ret
            return redirect('/book')
    except Exception as e:
        return f'Error: {str(e)}'





if __name__ == '__main__':
    app.run(debug=True)