from flask import Flask, render_template, request, redirect, url_for
from flask import Response
import mysql.connector
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import io

app = Flask(__name__)

# Connect to the database
mydb = mysql.connector.connect(
    host="localhost",
    user="root",
    password="Skh@23092005",
    database="students"
)
mycursor = mydb.cursor()

def grading_system(marks):
    if marks >= 90:
        return 'A+'
    elif marks >= 80:
        return 'A'
    elif marks >= 70:
        return 'B+'
    elif marks >= 60:
        return 'B'
    elif marks >= 50:
        return 'C'
    elif marks >= 40:
        return 'D'
    else:
        return "Fail"

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/submit', methods=['POST'])
def submit():
    usn = request.form['usn']
    name = request.form['name']
    marks = float(request.form['marks'])
    attendance = int(request.form['attendance'])
    sql = "INSERT INTO students (usn, name, marks, attendance) VALUES (%s, %s, %s, %s)"
    val = (usn, name, marks, attendance)
    mycursor.execute(sql, val)
    mydb.commit()
    return redirect(url_for('view_students'))

@app.route('/delete', methods=['POST'])
def delete_students():
    sql = "DELETE FROM students"
    mycursor.execute(sql)
    mydb.commit()
    return redirect(url_for('view_students'))

@app.route('/view_students')
def view_students():
    mycursor.execute("SELECT usn, name, marks, attendance FROM students ORDER BY marks DESC")
    records = mycursor.fetchall()
    students = []
    failed_students = []
    topper = None
    low_attendance_good_marks = []
    low_attendance_low_marks = []

    total_classes = 122

    for i, row in enumerate(records):
        usn, name, marks, attendance = row
        grade = grading_system(marks)
        attendance_percentage = np.round((attendance / total_classes) * 100, 2)
        if attendance_percentage >= 75 and marks < 50:
            insight = "Good attendance but low marks."
        elif attendance_percentage < 75 and marks >= 50:
            insight = "Irregular attendance but good marks."
            low_attendance_good_marks.append(name)
        elif attendance_percentage < 75 and marks < 50:
            insight = "Irregular attendance and low marks."
            low_attendance_low_marks.append(name)
        else:
            insight = "Good attendance and good marks."

        students.append({
            'usn': usn,
            'name': name,
            'marks': marks,
            'grade': grade,
            'attendance': attendance,
            'attendance_percentage': attendance_percentage,
            'insight': insight
        })

        if grade == "Fail":
            failed_students.append(name)
        if i == 0:
            topper = {'name': name, 'usn': usn, 'marks': marks, 'grade': grade}

    return render_template(
        'students.html',
        students=students,
        topper=topper,
        failed_students=failed_students,
        low_attendance_good_marks=low_attendance_good_marks,
        low_attendance_low_marks=low_attendance_low_marks
    )

@app.route('/analysis_graph')
def analysis_graph():
    mycursor.execute("SELECT name, marks, attendance FROM students")
    records = mycursor.fetchall()
    df = pd.DataFrame(records, columns=['name', 'marks', 'attendance'])

    plt.figure(figsize=(8, 5))
    if df.empty:
        plt.text(0.5, 0.5, 'No Data Available', ha='center', va='center', fontsize=16)
        plt.axis('off')
    else:
        total_classes = 122
        df['attendance_percentage'] = np.round((df['attendance'] / total_classes) * 100, 2)
        x = np.arange(len(df['name']))
        width = 0.35
        plt.bar(x - width/2, df['marks'], width, label='Marks', color='skyblue')
        plt.bar(x + width/2, df['attendance_percentage'], width, label='Attendance %', color='orange')
        plt.xlabel('Students')
        plt.ylabel('Value')
        plt.title('Marks and Attendance Percentage')
        plt.xticks(x, df['name'], rotation=45)
        plt.legend()
        plt.tight_layout()

    img = io.BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)
    plt.close()
    return Response(img.getvalue(), mimetype='image/png')


if __name__ == '__main__':
    app.run(debug=True)