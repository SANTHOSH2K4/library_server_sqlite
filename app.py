from flask import Flask, request, jsonify, render_template, redirect
import sqlite3
from datetime import datetime
import os
import csv
from werkzeug.utils import secure_filename

UPLOAD_FOLDER = 'uploads'

stud_alert = [0, '']
book_alert = [0, '']

app = Flask(__name__, static_url_path='/static')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


def get_connection():
    conn = sqlite3.connect('kcet.db')
    conn.row_factory = sqlite3.Row
    return conn


def set_pin(uid, pin):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT roll_no FROM users WHERE roll_no = ?", (uid,))
        existing_roll_no = cursor.fetchone()
        if existing_roll_no:
            query = "UPDATE users SET pin = ? WHERE roll_no = ?"
            cursor.execute(query, (pin, uid))
            conn.commit()
            cursor.close()
            conn.close()
            return 'Pin set successfully'
        else:
            return 'Roll number not found'
    except Exception as e:
        return str(e)


def book_data_insert_by_excel(file_path):
    res = ''
    conn = sqlite3.connect('kcet.db')
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
        cursor.execute("SELECT id FROM books WHERE id = ?", (row[0],))
        existing_id = cursor.fetchone()

        if existing_id:
            res += f"Skipping insertion for ID {row[0]} as it already exists."
            print(f"Skipping insertion for ID {row[0]} as it already exists.")
        else:
            query = "INSERT INTO books(id,title,author,rating,description,isissued,issued_for,tag,issued_times,date,image,arrived_date) VALUES (?, ?, ?, ?, ?, 0, 'none', ?, 0, 'clear', ?, CURRENT_TIMESTAMP)"
            cursor.execute(query, (row[0], row[1], row[2], row[3], row[4], row[5], row[6]))
            conn.commit()
            res += f"Inserted row with ID {row[0]}"
            print(f"Inserted row with ID {row[0]}")

    cursor.close()
    conn.close()
    return res


def users_data_insert_by_excel(file_path):
    conn = get_connection()
    cursor = conn.cursor()
    res = ''

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
        cursor.execute("SELECT roll_no FROM users WHERE roll_no = ?", (row[0],))
        existing_roll_no = cursor.fetchone()

        if existing_roll_no:
            res += f"Skipping insertion for Roll No {row[0]} as it already exists."
            print(f"Skipping insertion for Roll No {row[0]} as it already exists.")
        else:
            query = "INSERT INTO users (roll_no, name, issuancelimit, tags, track, pass, email, pin, Dept, year_of_studying) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
            cursor.execute(query, (row[0], row[1], int(row[2]), '', '', row[3], row[4], 'none', row[5], row[6]))
            conn.commit()
            res += f"Inserted row with Roll No {row[0]}.\n"
            print(f"Inserted row with Roll No {row[0]}")

    cursor.close()
    conn.close()
    return res


def log_validation(uid, pas):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        query = "SELECT roll_no FROM users WHERE roll_no = ? AND pass = ?"
        cursor.execute(query, (uid, pas))
        row = cursor.fetchone()
        cursor.close()
        conn.close()
        if row:
            return 'login success'
        else:
            return 'login failed'
    except Exception as e:
        return 'login failed'


def issue_book(uid, bid):
    conn = get_connection()
    cursor = conn.cursor()
    if conn:
        user_found = 0
        try:
            query = "SELECT roll_no FROM users WHERE roll_no = ?"
            cursor.execute(query, (uid,))
            row = cursor.fetchone()
            if row:
                user_found = 1
            else:
                user_found = 0
        except Exception as e:
            print(e)
            user_found = 0

        if user_found == 0:
            return 'User not found!'

        book_found = 0
        try:
            query = "SELECT id FROM books WHERE id = ?"
            cursor.execute(query, (bid,))
            row = cursor.fetchone()
            if row:
                book_found = 1
            else:
                book_found = 0
        except Exception as e:
            book_found = 0

        if book_found == 0:
            return 'Book not found!'

        current_date = datetime.now().strftime("%d-%m-%y")

        query = "SELECT * FROM books where id = ?"
        cursor.execute(query, (bid,))
        row = cursor.fetchone()

        tag_lib = row[7].split(',')

        is_issued = row[5]
        issued_times = row[8]

        query = "SELECT title FROM books WHERE id = ?"
        cursor.execute(query, (bid,))
        bname = cursor.fetchone()

        query = "SELECT * FROM users WHERE roll_no = ?"
        cursor.execute(query, (uid,))
        row = cursor.fetchone()

        tag_li = row[3].split(',')
        track = row[4] + f'{bname[0]}/{current_date},'
        for i in tag_lib:
            tag_li.append(i)
        tags = ','.join(tag_li)

        issuance_limit = row[2]
        if issuance_limit == 0:
            return "You have reached the issuance limit!"
        else:
            if is_issued == 1:
                return "This book is already issued!"
            elif is_issued == 0:
                issued_times += 1
                query2 = "UPDATE books SET isissued = 1, issued_for = ?, issued_times = ?, date = ? WHERE id = ?"
                cursor.execute(query2, (uid, issued_times, current_date, bid))
                conn.commit()

                issuance_limit -= 1

                query = "UPDATE users SET issuancelimit = ?, tags = ?, track = ? WHERE roll_no = ?"
                cursor.execute(query, (issuance_limit, tags, track, uid))
                conn.commit()

                query = "SELECT * FROM books WHERE id = ?"
                cursor.execute(query, (bid,))
                row = cursor.fetchone()
                conn.commit()

                return 'Success'


@app.route('/setpin', methods=['POST'])
def pin_set():
    data = request.get_json()
    roll_no = data.get('roll_no', '')
    pin = data.get('pin', '')
    res = set_pin(roll_no, pin)
    return jsonify({'setpin_res': res})


@app.route('/getpin', methods=['POST'])
def pin_get():
    data = request.get_json()
    roll_no = data.get('roll_no', '')
    conn = get_connection()
    cursor = conn.cursor()
    query = "SELECT roll_no,pin FROM users WHERE roll_no = ?"
    cursor.execute(query, (roll_no,))
    res = cursor.fetchone()
    cursor.close()
    conn.close()
    st = ''
    if res:
        st = res[1]
    elif not res:
        st = 'User not found!'
    return jsonify({'getpin_res': st})


@app.route('/get5latestarrivedbooks')
def get5latarr():
    conn = get_connection()
    cursor = conn.cursor()
    query = "SELECT * FROM books ORDER BY arrived_date DESC LIMIT 5"
    cursor.execute(query)
    rows = cursor.fetchall()
    return jsonify(rows)


@app.route('/login', methods=['POST'])
def process_message():
    data = request.get_json()
    roll_no = data.get('roll_no', '')
    pas = data.get('password', '')
    res = log_validation(roll_no, pas)
    if res == 'login failed':
        return jsonify({'log_res': res})
    else:
        conn = get_connection()
        cursor = conn.cursor()
        query = "SELECT email,Dept,year_of_studying,name FROM users WHERE roll_no = ?"
        cursor.execute(query, (roll_no,))
        row = cursor.fetchone()
        if row:
            email, dept, year, name = row
            return jsonify({'log_res': res, 'roll_no': roll_no, 'email': email, 'dept': dept, 'Year': year, 'name': name})
        else:
            return jsonify({'log_res': 'User not found'})


@app.route('/issue_book', methods=['POST'])
def issuebook():
    data = request.get_json()
    roll = data.get('roll_no', '')
    bid = data.get('bid', '')
    res = issue_book(roll, bid)
    return jsonify({'issue_res': res})


@app.route('/')
def home():
    return 'HELLO LIBRARY'


def return_book(bid):
    conn = get_connection()
    cursor = conn.cursor()
    query = "SELECT * FROM books "
    cursor.execute(query)
    rows = cursor.fetchall()
    bid_li = [row[0] for row in rows]
    if bid not in bid_li:
        return 'Book ID not found!'

    query = "SELECT * FROM books WHERE id = ?"
    cursor.execute(query, (bid,))
    row = cursor.fetchone()
    is_issued = row[5]
    if is_issued == 1:
        uid = row[6]
        query = "UPDATE books SET isissued = 0, issued_for = 'none', date = 'clear' WHERE id = ?"
        cursor.execute(query, (bid,))
        conn.commit()
        query = "SELECT * FROM users WHERE roll_no = ?"
        cursor.execute(query, (uid,))
        row = cursor.fetchone()
        issuance_limit = row[2]
        issuance_limit += 1
        query = "UPDATE users SET issuancelimit = ? WHERE roll_no = ?"
        cursor.execute(query, (issuance_limit, uid))
        conn.commit()
        cursor.close()
        conn.close()
        return 'Successfully returned'
    else:
        cursor.close()
        conn.close()
        return 'This book is not issued by anyone!'


@app.route('/admin')
def index():
    conn = get_connection()
    cursor = conn.cursor()
    query = "SELECT COUNT(*) FROM users"
    cursor.execute(query)
    total_students = cursor.fetchone()[0]

    query = "SELECT COUNT(*) FROM books"
    cursor.execute(query)
    total_books = cursor.fetchone()[0]

    query = "SELECT COUNT(*) FROM books WHERE isissued = 1"
    cursor.execute(query)
    total_books_issued = cursor.fetchone()[0]

    return render_template('index.html', total_students=total_students, total_books=total_books,
                           total_books_issued=total_books_issued)


@app.route('/book')
def book_page():
    conn = get_connection()
    cursor = conn.cursor()
    query = "SELECT * FROM books "
    cursor.execute(query)
    rows = cursor.fetchall()
    if book_alert[0] == 1:
        book_alert[0] = 0
        ret = book_alert[1]
        book_alert[1] = ''
        return render_template('book.html', show_upload_alert=True, ret=ret, res=rows)
    else:
        return render_template('book.html', show_alert=False, res=rows, show_upload_alert=False)


@app.route('/student')
def stud_page():
    conn = get_connection()
    cursor = conn.cursor()
    query = "SELECT roll_no,name,email,Dept,year_of_studying,issuancelimit,tags FROM users "
    cursor.execute(query)
    rows = cursor.fetchall()
    if stud_alert[0] == 1:
        stud_alert[0] = 0
        resp = stud_alert[1]
        stud_alert[1] = ''
        return render_template('student.html', show_alert=True, resp=resp, res=rows)
    else:
        return render_template('student.html', show_alert=False, res=rows)


@app.route('/showhistory/', methods=['POST'])
def sol():
    id = request.form['value']
    conn = get_connection()
    cursor = conn.cursor()
    query = "SELECT track FROM users WHERE roll_no = ?"
    cursor.execute(query, (id,))
    data_str = cursor.fetchone()[0]
    pairs = data_str.split(',')
    result = [(pair.split('/')[0], pair.split('/')[1]) for pair in pairs if pair]
    return render_template('history.html', res=result)


@app.route('/proc_return', methods=['POST'])
def proc_return():
    bid = request.form['bookNumberReturn']
    resp = return_book(bid)
    conn = get_connection()
    cursor = conn.cursor()
    query = "SELECT * FROM books "
    cursor.execute(query)
    rows = cursor.fetchall()
    return render_template('book.html', show_alert=True, res=rows, resp=resp)


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
            ret = users_data_insert_by_excel(file_path)
            os.remove(file_path)
            stud_alert[0] = 1
            stud_alert[1] = ret
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
            ret = book_data_insert_by_excel(file_path)
            os.remove(file_path)
            book_alert[0] = 1
            book_alert[1] = ret
            return redirect('/book')
    except Exception as e:
        return f'Error: {str(e)}'


if __name__ == '__main__':
    app.run(debug=True)
