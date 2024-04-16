import json
import random
from costs import check_hard_constraints, subjects_order_cost, empty_space_groups_cost, empty_space_teachers_cost, \
    free_hour
from model import Class, Classroom, Data
import mysql.connector


def load_data(file_path, teachers_empty_space, groups_empty_space, subjects_order):
    """
    Loads and processes input data, initialises helper structures.
    :param file_path: path to file with input data
    :param teachers_empty_space: dictionary where key = name of the teacher, values = list of rows where it is in
    :param groups_empty_space: dictionary where key = group index, values = list of rows where it is in
    :param subjects_order: dictionary where key = (name of the subject, index of the group), value = [int, int, int]
    where ints represent start times (row in matrix) for types of classes P, V and L respectively. If start time is -1
    it means that that subject does not have that type of class.
    :return: Data(groups, teachers, classes, classrooms)
    """
    with open(file_path) as file:
        data = json.load(file)

    # classes: dictionary where key = index of a class, value = class
    classes = {}
    # classrooms: dictionary where key = index, value = classroom name
    classrooms = {}
    # teachers: dictionary where key = teachers' name, value = index
    teachers = {}
    # groups: dictionary where key = name of the group, value = index
    groups = {}
    class_list = []

    for cl in data['Classes']:
        new_group = cl['Group']
        new_teacher = cl['Teacher']

        # initialise for empty space of teachers
        if new_teacher not in teachers_empty_space:
            teachers_empty_space[new_teacher] = []

        new = Class(new_group, new_teacher, cl['Subject'], cl['Type'], cl['Duration'], cl['ClassroomType'])
        # add groups
        for group in new_group:
            if group not in groups:
                groups[group] = len(groups)
                # initialise for empty space of groups
                groups_empty_space[groups[group]] = []

        # add teacher
        if new_teacher not in teachers:
            teachers[new_teacher] = len(teachers)
        class_list.append(new)

    # shuffle mostly because of teachers
    random.shuffle(class_list)
    # add classrooms
    for cl in class_list:
        classes[len(classes)] = cl

    # every class is assigned a list of classrooms he can be in as indexes (later columns of matrix)
    for type in data['ClassroomTypes']:
        for name in data['ClassroomTypes'][type]:
            new = Classroom(name, type)
            classrooms[len(classrooms)] = new

    # every class has a list of groups marked by its index, same for classrooms
    for i in classes:
        cl = classes[i]

        classroom = cl.classrooms
        index_classrooms = []
        # add classrooms
        for index, c in classrooms.items():
            if c.type == classroom:
                index_classrooms.append(index)
        cl.classrooms = index_classrooms

        class_groups = cl.groups
        index_groups = []
        for name, index in groups.items():
            if name in class_groups:
                # initialise order of subjects
                if (cl.subject, index) not in subjects_order:
                    subjects_order[(cl.subject, index)] = [-1, -1, -1]
                index_groups.append(index)
        cl.groups = index_groups

    return Data(groups, teachers, classes, classrooms)


def set_up(num_of_columns, days, hours):
    """
    Sets up the timetable matrix and dictionary that stores free fields from matrix.
    :param num_of_columns: number of classrooms
    :return: matrix, free
    """
    w, h = num_of_columns, len(days)*len(hours)                                          # 5 (workdays) * 6 (work hours) = 30
    matrix = [[None for x in range(w)] for y in range(h)]
    free = []

    # initialise free dict as all the fields from matrix
    for i in range(len(matrix)):
        for j in range(len(matrix[i])):
            free.append((i, j))
    return matrix, free


def show_timetable(matrix, days, hours):
    """
    Prints timetable matrix.
    """

    # print heading for classrooms
    for i in range(len(matrix[0])):
        if i == 0:
            print('{:17s} C{:6s}'.format('', '0'), end='')
        else:
            print('C{:6s}'.format(str(i)), end='')
    print()

    d_cnt = 0
    h_cnt = 0
    for i in range(len(matrix)):
        day = days[d_cnt]
        hour = hours[h_cnt]
        print('{:10s} {:2d} ->  '.format(day, hour), end='')
        for j in range(len(matrix[i])):
            print('{:6s} '.format(str(matrix[i][j])), end='')
        print()
        h_cnt += 1
        if h_cnt == len(hours):
            h_cnt = 0
            d_cnt += 1
            print()


def write_solution_to_file(matrix, data, filled, filepath, groups_empty_space, teachers_empty_space, subjects_order, days, hours):
    """
    Writes statistics and schedule to file.
    """
    f = open('solution_files/sol_' + filepath, 'w')

    f.write('-------------------------- STATISTICS --------------------------\n')
    cost_hard = check_hard_constraints(matrix, data)
    if cost_hard == 0:
        f.write('\nHard constraints satisfied: 100.00 %\n')
    else:
        f.write('Hard constraints NOT satisfied, cost: {}\n'.format(cost_hard))
    f.write('Soft constraints satisfied: {:.02f} %\n\n'.format(subjects_order_cost(subjects_order)))

    empty_groups, max_empty_group, average_empty_groups = empty_space_groups_cost(groups_empty_space, days, hours)
    f.write('TOTAL empty space for all GROUPS and all days: {}\n'.format(empty_groups))
    f.write('MAX empty space for GROUP in day: {}\n'.format(max_empty_group))
    f.write('AVERAGE empty space for GROUPS per week: {:.02f}\n\n'.format(average_empty_groups))

    empty_teachers, max_empty_teacher, average_empty_teachers = empty_space_teachers_cost(teachers_empty_space, days, hours)
    f.write('TOTAL empty space for all TEACHERS and all days: {}\n'.format(empty_teachers))
    f.write('MAX empty space for TEACHER in day: {}\n'.format(max_empty_teacher))
    f.write('AVERAGE empty space for TEACHERS per week: {:.02f}\n\n'.format(average_empty_teachers))

    f_hour = free_hour(matrix, days, hours)
    if f_hour != -1:
        f.write('Free term -> {}\n'.format(f_hour))
    else:
        f.write('NO hours without classes.\n')

    groups_dict = {}
    for group_name, group_index in data.groups.items():
        if group_index not in groups_dict:
            groups_dict[group_index] = group_name

    f.write('\n--------------------------- SCHEDULE ---------------------------')
    for class_index, times in filled.items():
        c = data.classes[class_index]
        groups = ' '
        for g in c.groups:
            groups += groups_dict[g] + ', '
        f.write('\n\nClass {}\n'.format(class_index))
        f.write('Teacher: {} \nSubject: {} \nGroups:{} \nType: {} \nDuration: {} hour(s)'
                .format(c.teacher, c.subject, groups[:len(groups) - 2], c.type, c.duration))
        room = str(data.classrooms[times[0][1]])
        f.write('\nClassroom: {:2s}\nTime: {}'.format(room[:room.rfind('-')], days[times[0][0] // len(hours)]))
        for time in times:
            f.write(' {}'.format(hours[time[0] % len(hours)]))
    f.close()

def insert_into_database(matrix, data, filled, filepath, groups_empty_space, teachers_empty_space, subjects_order, days, hours):
    ACADEMIC_YEAR_ID = 1
    # insert into database logic below
    # Establish a connection
    cnx = mysql.connector.connect(user='root', password='Pranav18',
                                host='localhost',
                                database='timetable_manager')

    # Create a cursor object
    cursor = cnx.cursor(dictionary=True)
    cursor.execute("DELETE FROM slotDatas")

    groups_dict = {}
    for group_name, group_index in data.groups.items():
        if group_index not in groups_dict:
            groups_dict[group_index] = group_name
    
    for class_index, times in filled.items():
        c = data.classes[class_index]
        group_ids = []
        for g in c.groups:
            group_ids.append(int(groups_dict[g]))
        
        # room is of the the type 'room_number - room_type' eg. "501 - notLab". We need to remove the room_type to get the room number
        room = str(data.classrooms[times[0][1]])
        teacher_id = c.teacher
        subject_id = c.subject.split(' ')[0] 
        classroom_id = room[:room.rfind('-')] # removing room_type from end
        day_number = days[times[0][0] // len(hours)]
        hour_numbers = [hours[time[0] % len(hours)] for time in times]
        print(f"Day: {day_number}\t Hours: {hour_numbers}\t Teacher: {teacher_id}\t Subject: {subject_id}\t Classroom: {classroom_id}\t Groups: {group_ids}")

        for hour in hour_numbers:
            cursor.execute(f"""SELECT id, day, number, AcademicYearId FROM Slot WHERE AcademicYearId = {ACADEMIC_YEAR_ID} AND day = {day_number} AND number = {hour}""")
            slot_id = cursor.fetchall()[0]["id"]
            cursor.execute(f"""
                INSERT INTO SlotDatas (SlotId, TeacherId, SubjectId )
                VALUES ({slot_id}, {teacher_id}, {subject_id})
            """)
            cursor.execute(f"""
                SELECT id FROM SlotDatas 
                WHERE slotId = {slot_id} AND TeacherId = {teacher_id} AND SubjectId = {subject_id}
            """)
            slotdata_id = cursor.fetchall()[0]["id"]
            cursor.execute(f"""
                INSERT INTO SlotDataClasses (SlotDataId, ClassroomId)
                VALUES ({slotdata_id}, {classroom_id})
            """)
            for group_id in group_ids:
                cursor.execute(f"""
                    INSERT INTO SlotDataSubdivisions (SlotDataId, SubdivisionId)
                    VALUES ({slotdata_id}, {group_id})
                """)
            cnx.commit()


def show_statistics(matrix, data, subjects_order, groups_empty_space, teachers_empty_space, days, hours):
    """
    Prints statistics.
    """
    cost_hard = check_hard_constraints(matrix, data)
    if cost_hard == 0:
        print('Hard constraints satisfied: 100.00 %')
    else:
        print('Hard constraints NOT satisfied, cost: {}'.format(cost_hard))
    print('Soft constraints satisfied: {:.02f} %\n'.format(subjects_order_cost(subjects_order)))

    empty_groups, max_empty_group, average_empty_groups = empty_space_groups_cost(groups_empty_space, days, hours)
    print('TOTAL empty space for all GROUPS and all days: ', empty_groups)
    print('MAX empty space for GROUP in day: ', max_empty_group)
    print('AVERAGE empty space for GROUPS per week: {:.02f}\n'.format(average_empty_groups))

    empty_teachers, max_empty_teacher, average_empty_teachers = empty_space_teachers_cost(teachers_empty_space, days, hours)
    print('TOTAL empty space for all TEACHERS and all days: ', empty_teachers)
    print('MAX empty space for TEACHER in day: ', max_empty_teacher)
    print('AVERAGE empty space for TEACHERS per week: {:.02f}\n'.format(average_empty_teachers))

    f_hour = free_hour(matrix, days, hours)
    if f_hour != -1:
        print('Free term ->', f_hour)
    else:
        print('NO hours without classes.')
