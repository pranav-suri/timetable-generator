import mysql.connector

# Establish a connection
cnx = mysql.connector.connect(user='root', password='Pranav18',
                               host='localhost',
                               database='timetable_manager')

# Create a cursor object
cursor = cnx.cursor(dictionary=True)

cursor.execute("""
    SELECT
    t.id AS teacherId,
    s.id AS subjectId, s.isLab
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
    SELECT division.id AS divisionId,subdiv.id AS subdivisionId
    FROM division
    LEFT JOIN subdivision subdiv ON division.id = subdiv.divisionId
    WHERE division.departmentId = 2
""")

subdivisions = cursor.fetchall()

#Formatting subdivisions
subdivisions_by_division = {}

# Organize the subdivisions data into the desired format
for subdivision in subdivisions:
    division_id = subdivision["divisionId"]
    subdivision_id = subdivision["subdivisionId"]
    
    # If the division is not yet in the dictionary, add it with an empty list
    if division_id not in subdivisions_by_division:
        subdivisions_by_division[division_id] = {"divisionId": division_id, "subdivisionIds": []}
    
    # Add the subdivision ID to the list of subdivision IDs for the division
    subdivisions_by_division[division_id]["subdivisionIds"].append(subdivision_id)

# Convert the dictionary values to a list
formatted_subdivisions = list(subdivisions_by_division.values())

ClassroomTypes = {
        "Lab": [],
        "notLab": [],
}

for classroom in classrooms:
    if classroom["isLab"]:
        ClassroomTypes["Lab"].append(str(classroom['id']))
    else:
        ClassroomTypes["notLab"].append(str(classroom['id']))

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


# Increase number of teacher entries to equal the number of divisions
for subjectId, teacherIds in notLabTeachersBySubject.items():
    if len(teacherIds) < numberOfDivisions:
        # Select teachers to increase the count
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
    

teaches.sort(key=lambda x: int(x["subjectId"]))

LabClasses = []
notLabClasses = []
for teach in teaches:
    Class = {
            "Subject": str(teach['subjectId']),
            "Type": "Lab" if teach["isLab"] else "Theory",
            "Teacher": str(teach["teacherId"]),
            "ClassroomType": "Lab" if teach["isLab"] else "notLab",
            "Duration": "2" if teach["isLab"] else "1",
            "Group": []
        }
    if teach["isLab"]:
        LabClasses.append(Class)
    else:
        notLabClasses.append(Class)

# Assign one subdivision to each labClass using subdivisions array
for i, c in enumerate(LabClasses):
    # Assign a division from formatted_subdivisions array to the class
    c["Group"].append(str(subdivisions[i % len(subdivisions)]["subdivisionId"]))

for i, c in enumerate(notLabClasses):
    # Assign a division from formatted_subdivisions array to the class
    result = list(map(str, formatted_subdivisions[i % len(formatted_subdivisions)]["subdivisionIds"]))
    c["Group"].extend(result)

Classes = LabClasses + notLabClasses
# Sort the classes by subjectId
Classes.sort(key=lambda x: int(x["Subject"]))

# Create a new list to store the modified classes
modified_classes = []

# Iterate through each element in the Classes list
for class_item in Classes:
    # If the class type is "Theory", add three entries with the same details but different subject names
    if class_item["Type"] == "Theory":
        for i in range(3):
            new_class_item = class_item.copy()  # Create a copy of the current entry
            new_class_item["Subject"] += f" {i+1}"  # Append to subject name
            modified_classes.append(new_class_item)
    else:
        new_class_item = class_item.copy()
        new_class_item["Subject"] += " 1"
        modified_classes.append(new_class_item)    

final = {"ClassroomTypes": ClassroomTypes, "Classes": modified_classes}

print(final)

# Close the connection
cnx.close()



