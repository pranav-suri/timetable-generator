import mysql.connector
import json

cnx = mysql.connector.connect(user='root', password='Pranav18',
                               host='localhost',
                               database='timetable_manager')
# Create a cursor object
cursor = cnx.cursor(dictionary=True)

ACADEMIC_YEAR_ID = 1

def getClassroomTypes(academic_year_id):
    cursor.execute(f"""
    SELECT c.id, c.classroomName, c.isLab
    FROM classroom c WHERE c.academicYearId = {academic_year_id}
            """)

    classrooms = cursor.fetchall()
    ClassroomTypes = {
            "Lab": [],
            "notLab": [],
    }
    for classroom in classrooms:
        if classroom["isLab"]:
            ClassroomTypes["Lab"].append(str(classroom['id']))
        else:
            ClassroomTypes["notLab"].append(str(classroom['id']))
    return ClassroomTypes

def classesByDepartment(department_id):
    cursor.execute(f"""SELECT s.id FROM subject s WHERE s.departmentId = {department_id} """)
    subjects = cursor.fetchall()
    subjectIds = [subject["id"] for subject in subjects]
    subjectIds = ",".join(map(str, subjectIds))
    cursor.execute(f"""
        SELECT
        t.id AS teacherId,
        s.id AS subjectId, 
        s.isLab,
        g.allowSimultaneous
        FROM teach
        INNER JOIN teacher t ON teach.TeacherId = t.id
        INNER JOIN subject s ON teach.SubjectId = s.id
        INNER JOIN `group` g ON s.GroupId = g.id
        WHERE s.id IN ({subjectIds})
    """)

    teaches = cursor.fetchall()
    
    cursor.execute(f"""
        SELECT division.id AS divisionId,subdiv.id AS subdivisionId
        FROM division
        INNER JOIN subdivision subdiv ON division.id = subdiv.divisionId
        WHERE division.departmentId = {department_id}
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

    # Dictionary of teachers for non-lab subjects
    notLabTeachersBySubject = {}
    # Dictionary of teachers for lab subjects
    labTeachersBySubject = {}
    # Dictionary of teachers for elective labs
    electiveLabTeachersBySubject = {}
    # Dictionary of teachers for elective theory
    electiveTheoryTeachersBySubject = {}
    
    # Separate the teachers into different dictionaries based on the subject and type of subject
    for teach in teaches:
        subjectId = teach["subjectId"]
        # Check if the subject is lab
        if teach["isLab"]:
            # Check if the lab subject allows simultaneous labs
            if teach["allowSimultaneous"]:
                # Add the teacher to the list of elective teachers for the subject
                if subjectId in electiveLabTeachersBySubject:
                    electiveLabTeachersBySubject[subjectId].append(teach["teacherId"])
                else:
                    electiveLabTeachersBySubject[subjectId] = [teach["teacherId"]]

            if not teach["allowSimultaneous"]:
                # Add the teacher to the list of core teachers for the subject
                if subjectId in labTeachersBySubject:
                    labTeachersBySubject[subjectId].append(teach["teacherId"])
                else:
                    labTeachersBySubject[subjectId] = [teach["teacherId"]]

        # If the subject is not a lab subject
        elif not teach["isLab"]:
            if teach["allowSimultaneous"]:
                # Add the teacher to the list of elective teachers for the subject
                if subjectId in electiveTheoryTeachersBySubject:
                    electiveTheoryTeachersBySubject[subjectId].append(teach["teacherId"])
                else:
                    electiveTheoryTeachersBySubject[subjectId] = [teach["teacherId"]]
            if not teach["allowSimultaneous"]:
                # Add the teacher to the list of core teachers for the subject
                if subjectId in notLabTeachersBySubject:
                    notLabTeachersBySubject[subjectId].append(teach["teacherId"])
                else:
                    notLabTeachersBySubject[subjectId] = [teach["teacherId"]]

    # Count number of divisions
    divisionSet = {subdivision["divisionId"] for subdivision in subdivisions}
    numberOfDivisions = len(divisionSet)

    # Increase number of teacher entries to equal the number of divisions for core notLabs
    for subjectId, teacherIds in notLabTeachersBySubject.items():
        if len(teacherIds) < numberOfDivisions:
            numOfSubjectTeachers = len(teacherIds)
            for i in range(numberOfDivisions - numOfSubjectTeachers):
                # Select teachers to increase the count
                teaches.append({
                    "teacherId": teacherIds[i % numOfSubjectTeachers],
                    "subjectId": subjectId,
                    "isLab": False,
                    "allowSimultaneous": False
                })
        elif len(teacherIds) == numberOfDivisions:
            pass
        else: 
            # Implement logic to remove teach entry based on subjectId

            print("Number of divions:", numberOfDivisions)
            print("Number of teachers for not lab subject is greater than number of divisions", subjectId, teacherIds)

    # Count number of subdivisions
    subdivisionSet = {subdivision["subdivisionId"] for subdivision in subdivisions}
    numberOfSubdivisions = len(subdivisionSet)

    # Increase number of teacher entries randomly to equal the number of subdivisions for Labs
    for subjectId, teacherIds in labTeachersBySubject.items():
        if len(teacherIds) < numberOfSubdivisions:
            numOfSubjectTeachers = len(teacherIds)
            for i in range(numberOfSubdivisions - numOfSubjectTeachers):
                # Select teachers to increase the count
                teaches.append({
                    "teacherId": teacherIds[i % numOfSubjectTeachers],
                    "subjectId": subjectId,
                    "isLab": True,
                    "allowSimultaneous": False
                })
        elif len(teacherIds) == numberOfSubdivisions:
            pass
        else: 
            # Implement logic to remove a teach entry based on subjectId

            print("Number of subdivisions: ", numberOfSubdivisions)
            print("Number of teachers for lab subject is greater than number of subdivisions", subjectId, teacherIds)
    
    teaches.sort(key=lambda x: int(x["subjectId"]))

    coreLabClasses = []
    electiveLabClasses = []
    coreTheoryClasses = []
    electiveTheoryClasses = []

    for teach in teaches:
        Class = {
                "Subject": str(teach['subjectId']),
                "Type": "Lab" if teach["isLab"] else "Theory",
                "Teacher": str(teach["teacherId"]),
                "ClassroomType": "Lab" if teach["isLab"] else "notLab",
                "Duration": "2" if teach["isLab"] else "1",
                "Group": [],
                "AllowSimultaneous": "true" if teach["allowSimultaneous"] else "false"
            }
        if teach["isLab"] and teach["allowSimultaneous"]:
            electiveLabClasses.append(Class)
        elif teach["isLab"] and not teach["allowSimultaneous"]:
            coreLabClasses.append(Class)
        elif not teach["isLab"] and teach["allowSimultaneous"]:
            electiveTheoryClasses.append(Class)
        elif not teach["isLab"] and not teach["allowSimultaneous"]:
            coreTheoryClasses.append(Class)

    # Assign one subdivision to each labClass using subdivisions array
    for i, c in enumerate(coreLabClasses):
        # Assign a subdivision from formatted_subdivisions array to the class
        c["Group"].append(str(subdivisions[i % len(subdivisions)]["subdivisionId"]))

    # Assign all subdivsions to each elective lab class
    
    # Assign all subdivisions to each theory thoery class

    for i, c in enumerate(coreTheoryClasses):
        # Assign a division from formatted_subdivisions array to the class
        result = list(map(str, formatted_subdivisions[i % len(formatted_subdivisions)]["subdivisionIds"]))
        c["Group"].extend(result)
    
    Classes = coreLabClasses + coreTheoryClasses # + electiveLabClasses + electiveTheoryClasses 
    # Sort the classes by subjectId
    Classes.sort(key=lambda x: int(x["Subject"]))
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
    
    return modified_classes


def data(department_id=2):

    classes = []
    # cursor.execute(f"""SELECT id FROM batch WHERE academicYearId = {ACADEMIC_YEAR_ID}""")
    # batches = cursor.fetchall()
    # for batch in batches:
    #     batch_id = batch["id"]
    #     cursor.execute(f"""SELECT id FROM department WHERE batchId = {batch_id}""")
    #     departments = cursor.fetchall()
    #     for department in departments:
    #         department_id = department["id"]
    #         # classes.extend(classesByDepartment(ACADEMIC_YEAR_ID, department_id))

    classes.extend(classesByDepartment(department_id))
    final = {"ClassroomTypes": getClassroomTypes(ACADEMIC_YEAR_ID), "Classes": classes}

    file = './test_files/ulaz3.json'

    # Convert and write JSON object to file
    with open(file, "w") as outfile:
        json.dump(final, outfile)
    cnx.close()
    print("data added")
    return 1

# Close the connection
