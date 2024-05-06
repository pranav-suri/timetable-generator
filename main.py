from flask import Flask
import index
import scheduler
import mysql.connector


app = Flask(__name__)
cnx = mysql.connector.connect(user='root', password='',
                               host='localhost',
                               database='timetable_manager')
# Create a cursor object
cursor = cnx.cursor(dictionary=True)

@app.route("/generate/department/<department_id>/<academic_year_id>")
def home(department_id, academic_year_id):
    no_of_classrooms = 2
    count = 0
    while True:
        try:
            if count == 5:
                return "failed"
            successful = index.data(int(department_id), int(academic_year_id), cursor, no_of_classrooms)
            if successful:
                scheduler.main(department_id, academic_year_id)
                break
        except:
            no_of_classrooms += 1
            count += 1
    return "successful"

if __name__ == "__main__":
    app.run()
