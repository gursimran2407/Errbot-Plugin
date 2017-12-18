import re
import sqlite3
from errbot import botcmd, re_botcmd, BotPlugin


class College(BotPlugin):
    """Plugin for querying details related to college using SQLite3"""

    def activate(self):
        self.con = None
        try:
            self.con = sqlite3.connect('errbot_database.db',check_same_thread=False)
            self.cur = self.con.cursor()
        except sqlite3.Error as e:
            print(e)
        super(College, self).activate()

    def deactivate(self):
        self.con.close()
        super(College, self).deactivate()

    @re_botcmd(pattern=r"^(?=.*marks)(?=.*sem)\D*([1-8])\D*$", prefixed=False, flags=re.IGNORECASE)
    def marks_in_sem(self, msg, match):
        """ Returns students marks in given semester"""
        roll_no = msg.frm.nick
        sem = int(match.group(1))
        if sem is not None:
            self.cur.execute("select avg(student_marks) from\
             enrollment_table as e, course_table as c where student_roll_number = ? \
             and e.course_id=c.course_id \
             and course_semester = ? group by student_roll_number;", (roll_no,sem,))
            result = self.cur.fetchone()
            if result is not None:
                return 'Your average marks in %dth sem: %.2f%%' % (sem,result[0])
            else:
                return 'Have you even completed this semester?'
        else:
            return 'Is that semester no. correct?'

    @re_botcmd(pattern=r"attendance", prefixed=False, flags=re.IGNORECASE)
    def attendance_in_curr_sem(self, msg, match):
        """ Returns student's attendance in current semester"""
        roll_no = msg.frm.nick
        self.cur.execute("select course_name, average_attendence from student_details as s,\
         enrollment_table as e, course_table as c where s.student_roll_no = ? \
         and s.student_roll_no=e.student_roll_number and e.course_id=c.course_id \
         and c.course_semester = s.semester;", (roll_no,))
        result = self.cur.fetchall()
        if len(result)>0 and result is not None:
            yield 'Your attendance in all subjects of this semester:'
            for row in result:
                yield 'Attendance in %s: %s%%' % (row[0],row[1])
        else:
            yield 'You have not registerd to any course in this sem.'

    @re_botcmd(pattern=r"fee.*(paid|status)|status.*fee", prefixed=False, flags=re.IGNORECASE)
    def fee_status(self, msg, match):
        """ Returns the fee status"""
        roll_no = msg.frm.nick
        self.cur.execute("select fee_status from student_details where student_roll_no = ?", (roll_no,))
        result = self.cur.fetchone()
        if result is not None:
            if result[0]:
                return 'Your fee has been paid'
            else:
                return 'Your fee has not been paid'
        else:
            return 'Are you from this college?'
    
    @re_botcmd(pattern=r"^\D*(?=.*details)(?=.*teacher)\D*$", prefixed=False, flags=re.IGNORECASE)
    def teachers_detail_with_id(self, msg, match):
        """ Returns all teachers with teacher id"""
        self.cur.execute("select t_id, first_name, last_name from teacher_table")
        result = self.cur.fetchall()
        if len(result)>0 and result is not None:
            yield 'Teacher id - Name'
            for row in result:
                yield '%d  ---  %s %s' % (row[0],row[1],row[2])
        else:
            yield 'Teacher details not found in the database'

    @re_botcmd(pattern=r"^\D*teacher\D*(?:id|no|num)\D*([\d]{3})\D*$", prefixed=False, flags=re.IGNORECASE)
    def search_teacher_with_id(self, msg, match):
        """ Returns teacher details on given teacher id"""
        teacher_id = match.group(1)
        if teacher_id is not None:
            self.cur.execute("select * from teacher_table where t_id = ?",(teacher_id,))
            result = self.cur.fetchone()
            if result is not None:
                yield 'Teacher ID: %d' % (result[0])
                yield 'Name: %s %s' % (result[1],result[2])
                yield 'Phone: %d' % (result[3])
                yield 'Email id: %s' % (result[4])
            else:
                yield 'Teacher with given ID is not present in the database'
        else:
            yield 'Please provide teacher ID in correct format (3 digit number)'

    @re_botcmd(pattern=r"^my courses?$", prefixed=False, flags=re.IGNORECASE)
    def return_courses(self, msg, match):
        """ Returns all courses of particular teacher id or student id"""
        id = msg.frm.nick
        if len(id)==6:
            self.cur.execute("select course_name from student_details as s, \
             enrollment_table as e, course_table as c where s.student_roll_no = ? \
             and s.student_roll_no=e.student_roll_number and e.course_id=c.course_id \
             and c.course_semester = s.semester;", (id,))
            result = self.cur.fetchall()
            if len(result)>0 and result is not None:
                yield 'Courses of this semester:'
                for row in result:
                    yield '%s' % (row[0])
            else:
                yield 'You have not registerd to any course in this sem.'
        elif len(id)==3:
            self.cur.execute("select course_id, course_name from course_table \
             where t_id = ?",(id,)) 
            result = self.cur.fetchall()
            if len(result)>0 and result is not None:
                yield 'Courses under you:'
                for row in result:
                    yield '%d  ---  %s' % (row[0],row[1])
            else:
                yield 'No course is mentioned under you'
        else:
            yield 'You are not enrolled in this college'

    @re_botcmd(pattern=r"^(?=.*students)(?=.*course (?:id|no|num))\D*(\d{3})\D*$", prefixed=False, flags=re.IGNORECASE)
    def student_details_of_given_course(self, msg, match):
        """ Returns all students under given course id"""
        c_id = match.group(1)
        self.cur.execute("select student_roll_no, first_name, last_name from student_details as s, \
         enrollment_table as e where e.course_id = ? and s.student_roll_no = e.student_roll_number \
         order by student_roll_no", (c_id,))
        result = self.cur.fetchall()
        if len(result)>0 and result is not None:
            yield 'Student id --- Name'
            for row in result:
                yield '%d   ---   %s %s' % (row[0],row[1],row[2])
        else:
            yield 'No student found under this course in the database'

