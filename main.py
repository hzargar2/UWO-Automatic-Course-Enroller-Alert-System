from course_scraper import *
import os, time, config, sys, vlc, threading, select

while True:

    timetable = input('Select which academic timetable you would like to set the alert in. (ENTER THE NUMBER!) \n'
                      'Available options: \n'
                      '1 Summer\n'
                      '2 Fall/Winter\n'
                      'Input: ')
    if timetable not in ['1', '2']:
        print('Incorrect entry. Make sure you inputted the number and not the text')
        continue
    else:
        if timetable == '1':
            timetable_url = config.timetable_urls_dict['Summer']
        elif timetable == '2':
            timetable_url = config.timetable_urls_dict['Fall/Winter']
        break

scraper = CourseScraper("/Users/hamidzargar/PycharmProjects/course_scraper/chromedriver", timetable_url)


flag = True

while flag:

    course_names = input(
        'Enter the course name(s) followed by the Class Nbr as it appears in the timetable, seperated by commas for multiple courses. Each portion of the course must be seperated by a space. (Example: COMPSCI 1026A 1625, PSYCHOL 2035B 1210):  ')

    if course_names == '':
        print('Empty course name. Try again.')
        continue


    courses = course_names.split(',')
    bools = []

    for course in courses:
        course = course.strip().split(' ')
        course_name = course[0]
        course_number = course[1]
        class_nbr = course[2]
        bools.append(scraper.course_exists(course_name, course_number, class_nbr))

    if all(bool == True for bool in bools):
        flag = False

    else:
        for index, bool in enumerate(bools):
            if bool == False:
                print('{0} not found. Make sure you have spelled the course name, course code, and class nbr correctly and you have selected the right timetable.'.format(
                        courses[index]))

p = vlc.MediaPlayer("Red Alert-SoundBible.com-108009997.mp3")

while len(courses) > 0:

    for index, course in enumerate(courses):
        course = course.strip().split(' ')
        course_name = course[0]
        course_number = course[1]
        class_nbr = course[2]

        if scraper.course_is_not_full(course_name, course_number, class_nbr):

            i = 0
            while True:
                os.system('cls' if os.name == 'nt' else 'clear')
                print("Press <Enter> to stop me alert!")

                p = vlc.MediaPlayer("Red Alert-SoundBible.com-108009997.mp3")
                p.play()
                os.system('say "the course {0} {1} with class number {2} is now available"'.format(course_name, course_number, class_nbr))

                if sys.stdin in select.select([sys.stdin], [], [], 0)[0]:
                    line = input()
                    break
                i += 1

            del courses[index]


    time.sleep(5)



