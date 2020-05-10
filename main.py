from course_scraper import *
import os, time, config, sys, vlc, threading, select

def get_academic_timetable_url_input() -> str:

    # Gets input from user for which timetable they want to use. Loops until 1 or 2 is selected as they are the
    # only valid answers
    while True:

        timetable = input('\nSelect which academic timetable you would like to set the alert in. (ENTER THE NUMBER!) \n\n'
                          'Available options: \n'
                          '1 Summer\n'
                          '2 Fall/Winter\n\n'
                          'Input: ')
        print('')

        if timetable not in ['1', '2']:
            print('Incorrect entry. Make sure you inputted the number and not the text')
            continue
        else:
            if timetable == '1':
                timetable_url = config.timetable_urls_dict['Summer']
                return timetable_url
            elif timetable == '2':
                timetable_url = config.timetable_urls_dict['Fall/Winter']
                return timetable_url


def initialize_scraper(timetable_url) -> CourseScraper:

    # Initialize scraper object with the timetable_url
    scraper = CourseScraper("/Users/hamidzargar/PycharmProjects/course_scraper/chromedriver", timetable_url)
    return scraper


def get_course_names_input_and_check_if_they_exist(scraper: CourseScraper) -> list:

    try:

        while True:

            # gets course names input from user
            course_names = input(
                'Enter the course name, course code, and class nbr, seperated by commas for multiple courses. Each portion of the course must be seperated by a space. (Example: COMPSCI 1026A 1625, PSYCHOL 2035A 1210)\n'
                'Input: ')
            print('')

            # if strong is empty, it asks the user to re-enter it.
            if course_names == '':
                print('ERROR: Empty course name. Try again.\n')
                continue

            # splits courses by the commas in the string, storing split values in a list
            courses = course_names.split(',')

            # empty list to store booleans of whether the course exists or not
            course_sections_exists = []

            # iterates through courses list (course names inputted by user)
            for course in courses:

                # seperates each course name entry into its course name, course number, and class nbr components and
                # stores it in a list. Then each component is individually assigned and used to initialize the scraper
                # object

                course = course.strip().split(' ')

                if len(course) == 3:

                    course_name = course[0]
                    course_number = course[1]
                    class_nbr = course[2]

                    # checks whether the course inputted by the user exists and appends the return value (boolean) to
                    # the courses_exist list
                    course_sections_exists.append(scraper.course_section_exists(course_name, course_number, class_nbr))

                elif len(course) < 3:
                    print(
                        'ERROR: COURSE COMPONENTS MISSING IN {0}. Make sure each course has 3 components. A course name, course number, and a class nbr (can be found in timetable).\n'.format(
                            course))
                else:
                    print(
                        'ERROR: TOO MANY COURSE COMPONENTS IN {0}. Make sure each course has 3 components. A course name, course number, and a class nbr (can be found in timetable).\n'.format(
                            course))

            # If all the user inputs for the course anmes haven;t been added to the list courses then atleast 1 course
            # name input was missing 1 or more components

            if len(course_sections_exists) != len(courses):
                continue

            # If all values in list are True then they all exist and it returns the courses list containing all of them
            if all(bool == True for bool in course_sections_exists):
                return courses

            # Atleast 1 of the course names inputted doesn't exists and asks the user to re-enter the course names.
            # First notifies the user which course was incorrect though.
            else:
                for index, bool in enumerate(course_sections_exists):
                    if bool == False:
                        print('ERROR: {0} NOT FOUND. Make sure you have spelled the course name, course code, and class nbr correctly and you have selected the right timetable.\n'.format(
                                courses[index].strip().upper()))

    except Exception as e:
        print(e)

def alert_if_not_full(courses: list, scraper: CourseScraper):

    if courses is not None:

        #while there are elements in courses list it checks to see if the class(es) are full or not
        while len(courses) > 0:

            # assings index to each element in list for easier reference later on
            for index, course in enumerate(courses):
                course = course.strip().split(' ')
                course_name = course[0]
                course_number = course[1]
                class_nbr = course[2]

                #if course is not full it alerts the user
                if scraper.lecture_is_not_full(course_name, course_number, class_nbr):

                    # alert loops until user acknowledges alert and presses the enter key
                    i = 0
                    while True:
                        os.system('cls' if os.name == 'nt' else 'clear')
                        print("Press <Enter> to stop the alert!")
                        print('{0} {1} with class number {2} is now available!'.format(course_name.upper(), course_number.upper(), class_nbr))

                        # plays sound, once ended, system talks
                        p = vlc.MediaPlayer("Red Alert-SoundBible.com-108009997.mp3")
                        p.play()
                        time.sleep(3)

                        os.system('say "the course {0} {1} with class number {2} is now available!"'.format(course_name, course_number, class_nbr))

                        if sys.stdin in select.select([sys.stdin], [], [], 0)[0]:
                            line = input()
                            break
                        i += 1

                    # Once alert is acknowledged, element is removed from list, reducing its length. Once length gets to
                    # 0 then there are no more elements in the list to check and the ;program terminates
                    del courses[index]

                print('The course {0} {1} {2} is full. Will re-try in 5 seconds.'.format(course_name.upper(), course_number.upper(), class_nbr))


            # checks for updates every 5 seconds so the server doesn't block the connection due to too many requests
            # 5 second delay before course_is_not_full method is onvoked again by the scraper object

            time.sleep(5)



timetable_url = get_academic_timetable_url_input()
scraper = initialize_scraper(timetable_url)
courses = get_course_names_input_and_check_if_they_exist(scraper)
alert_if_not_full(courses, scraper)





