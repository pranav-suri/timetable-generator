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
        ClassroomTypes["Lab"].append(str(classroom['id']))
    else:
        ClassroomTypes["notLab"].append(str(classroom['id']))

# Below algorithm assummes we are talking about a departmnent
# There will be more complex in case of multiple departments and electives

# Count number of divisions
divisionSet = {subdivision["divisionId"] for subdivision in subdivisions}
numberOfDivisions = len(divisionSet)

# Count number of teacher of a subject (notLab)
notLabTeachersBySubject = {}
for teach in teaches:
    subjectId = teach["subjectId"]
    # Check if the subject is non-lab
    if not teach["isLab"]:
        # Increment the count for the subject
        if subjectId in notLabTeachersBySubject:
            notLabTeachersBySubject[subjectId].append(teach["teacherId"])
        else:
            notLabTeachersBySubject[subjectId] = [teach["teacherId"]]

# Increase number of teacher entries randomly to equal the number of divisions
for subjectId, teacherIds in notLabTeachersBySubject.items():
    if len(teacherIds) < numberOfDivisions:
        # Randomly select teachers to increase the count
        numOfSubjectTeachers = len(teacherIds)
        for i in range(numberOfDivisions - numOfSubjectTeachers):
            teaches.append({
                "teacherId": teacherIds[i % numOfSubjectTeachers],
                "subjectId": subjectId,
                "isLab": False
            })

# Count number of subdivisions
subdivisionSet = {subdivision["subdivisionId"] for subdivision in subdivisions}
numberOfSubdivisions = len(subdivisionSet)

# Count number of teacher of a subject (Lab)
labTeachersBySubject = {}
for teach in teaches:
    subjectId = teach["subjectId"]
    # Check if the subject is lab
    if teach["isLab"]:
        # Increment the count for the subject
        if subjectId in labTeachersBySubject:
            labTeachersBySubject[subjectId].append(teach["teacherId"])
        else:
            labTeachersBySubject[subjectId] = [teach["teacherId"]]

# Increase number of teacher entries randomly to equal the number of subdivisions
for subjectId, teacherIds in labTeachersBySubject.items():
    if len(teacherIds) < numberOfSubdivisions:
        # Randomly select teachers to increase the count
        numOfSubjectTeachers = len(teacherIds)
        for i in range(numberOfSubdivisions - numOfSubjectTeachers):
            teaches.append({
                "teacherId": teacherIds[i % numOfSubjectTeachers],
                "subjectId": subjectId,
                "isLab": True
            })

Classes = []
for teach in teaches:
    Classes.append({
            "Subject": str(teach['subjectId']),
            "Type": "Lab" if teach["isLab"] else "Theory",
            "Teacher": str(teach["teacherId"]),
            "ClassroomType": "Lab" if teach["isLab"] else "notLab",
            "Duration": "2" if teach["isLab"] else "1",
            "Group": []
        })
# Sort the classes by subjectId
Classes.sort(key=lambda x: int(x["Subject"]))

# TODO: Add the groups to the classes


final = {"ClassroomTypes": ClassroomTypes, "Classes": Classes}
print(final)

# Close the connection
cnx.close()
