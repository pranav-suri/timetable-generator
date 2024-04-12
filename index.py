import mysql.connector

# Establish a connection
cnx = mysql.connector.connect(user='root', password='12345678',
                               host='localhost',
                               database='timetable_manager')

# Create a cursor object
cursor = cnx.cursor(dictionary=True)

cursor.execute("""
    SELECT
    t.id AS teacherId, t.teacherName, 
    s.id AS subjectId, s.subjectName, s.isLab
    FROM teach
    INNER JOIN teacher t ON teach.TeacherId = t.id
    INNER JOIN subject s ON teach.SubjectId = s.id
    WHERE t.academicYearId = 1
""")

teaches = cursor.fetchall()

cursor.execute("""
    SELECT c.id, c.classroomName, c.isLab
    FROM classroom c WHERE c.academicYearId = 1
               """)

classrooms = cursor.fetchall()

cursor.execute("""
    SELECT division.id AS divisionId, division.divisionName, subdiv.id AS subdivisionId, subdiv.subdivisionName
    FROM division
    LEFT JOIN subdivision subdiv ON division.id = subdiv.divisionId
    WHERE division.departmentId = 2
""")

subdivisions = cursor.fetchall()

ClassroomTypes = {
        "Lab": [],
        "notLab": [],
}

for classroom in classrooms:
    if classroom["isLab"]:
        ClassroomTypes["Lab"].append(classroom['id'])
    else:
        ClassroomTypes["notLab"].append(classroom['id'])

Classes = []

for teach in teaches:
    Classes.append({
            "Subject": teach["subjectId"],
            "Type": "Lab" if teach["isLab"] else "notLab",
            "Teacher": teach["teacherId"],
            "ClassroomType": "Lab" if teach["isLab"] else "notLab",
            "Duration": "2" if teach["isLab"] else "1",
        })


final = {"ClassroomTypes": ClassroomTypes, "Classes": Classes}
print(final)

# Close the connection
cnx.close()
