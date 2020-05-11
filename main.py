from course_scraper import *
import os, time, config, sys, vlc, threading, select, os

pd.set_option('display.max_rows', 500)
pd.set_option('display.max_columns', 500)
pd.set_option('display.width', 1000)

def get_academic_timetable_url_input() -> str:

    # Gets input from user for which timetable they want to use. Loops until 1 or 2 is selected as they are the
    # only valid answers
    while True:

        timetable = input('\nSelect which academic timetable you would like to set the alert in. (ENTER 1 or 2) \n\n'
                          'Available options: \n'
                          '1. Summer\n'
                          '2. Fall/Winter\n\n'
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

def get_courses_list_input() -> list:

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

            #empty list to store valid course inputs, course must have 3 components to be stored. course name,
            # course number, and class_nbr

            courses_list = []

            # iterates through courses list (course names inputted by user)
            for course in courses:

                # seperates each course name entry into its course name, course number, and class nbr components
                # if it's a valid enbtry
                course = course.strip().split(' ')

                # if course has 3 components (course_name, course_number, and class_nbr), we add the course (which is
                # a list of 3 elements to the course_list, creating a list of lists

                if len(course) == 3:
                    courses_list.append(course)

                elif len(course) < 3:
                    print(
                        'ERROR: COURSE COMPONENTS MISSING IN {0}. Make sure each course has 3 components. A course name, course number, and a class nbr (can be found in timetable).\n'.format(
                            course))
                else:
                    print(
                        'ERROR: TOO MANY COURSE COMPONENTS IN {0}. Make sure each course has 3 components. A course name, course number, and a class nbr (can be found in timetable).\n'.format(
                            course))

                # if the number of entries in courses_list is the same as the number of entries in courses (the
                # original user input, then all of the user's input for courses hae been added to the courses_list and
                # therefore have 3 components as required

                if len(courses_list) == len(courses):
                    return courses_list

    except Exception as e:
        print(e)


def initialize_scraper(timetable_url) -> CourseScraper:


    while True:

        chrome_version = input('\nSelect the version of your Google Chrome browser. This can be found in Help -> About Google Chrome. (Enter 1,2, or 3)\n\n'
                          'Available options: \n'
                          '1. 80.0.3987.106\n'
                          '2. 81.0.4044.138\n'
                          '3. 83.0.4103.39\n\n'
                          'Input: ')
        print('')

        my_path = os.path.dirname(__file__)

        if chrome_version not in ['1', '2', '3']:
            print('Incorrect entry. Make sure you inputted the number and not the text')
            continue

        elif chrome_version == '1':
            chrome_path = os.path.join(my_path, "chromedriver_mac_80.0.3987.106")

        elif chrome_version == '2':
            chrome_path = os.path.join(my_path, "chromedriver_mac_81.0.4044.138")
            print(chrome_path)

        elif chrome_version == '3':
            chrome_path = os.path.join(my_path, "chromedriver_mac_83.0.4103.39")


        # Initialize scraper object with the timetable_url
        course_scraper = CourseScraper(chrome_path, timetable_url)
        return course_scraper


def courses_exist(courses_list: list, course_scraper: CourseScraper) -> bool:

    try:

        while True:

            # empty list to store booleans of whether the course exists or not
            course_sections_exists = []

            for course in courses_list:
                course_name = course[0]
                course_number = course[1]
                class_nbr = course[2]

                course_scraper.set_all_course_sections_df(course_name, course_number)


                # checks whether the course inputted by the user exists and appends the return value (boolean) to
                # the courses_exist list
                course_sections_exists.append(course_scraper.course_section_exists(class_nbr))

            # If all values in list are True then they all exist and it returns the courses list containing all of them
            if all(bool == True for bool in course_sections_exists):
                return True

            # Atleast 1 of the course names inputted doesn't exists and asks the user to re-enter the course names.
            # First notifies the user which course was incorrect though.
            else:
                for index, bool in enumerate(course_sections_exists):
                    if bool == False:
                        print('ERROR: {0} NOT FOUND. Make sure you have spelled the course name, course code, and class nbr correctly and you have selected the right timetable.\n'.format(
                                courses_list[index].strip().upper()))

                return False

    except Exception as e:
        print(e)


def alert_if_not_full(courses_list: list, course_scraper: CourseScraper):

        #while there are elements in courses list it checks to see if the class(es) are full or not
        while len(courses_list) > 0:

            for index, course in enumerate(courses_list):
                course_name = course[0]
                course_number = course[1]
                class_nbr = course[2]

                course_scraper.set_all_course_sections_df(course_name, course_number)

                all_course_sections_df = course_scraper.get_all_course_sections_df()

                # assigns index to each element in list for easier reference later on
                for index, row in all_course_sections_df.iterrows():

                    #if ldcture component of course is not full it alerts the user
                    if row['class_nbr'] == class_nbr and row['course_status'] == 'Not Full':

                        # alert loops until user acknowledges alert and presses the enter key
                        while True:
                            os.system('cls' if os.name == 'nt' else 'clear')
                            print("Press <Enter> to stop the alert!")
                            print('{0} {1} with class number {2} is now available!'.format(course_name.upper(), course_number.upper(), class_nbr))

                            # plays sound, once ended, system talks
                            p = vlc.MediaPlayer("Red Alert-SoundBible.com-108009997.mp3")
                            p.play()
                            time.sleep(3)

                            os.system('say "the course {0} {1} with class number {2} is now available!"'.format(course_name.upper(), course_number.upper(), class_nbr))

                            if sys.stdin in select.select([sys.stdin], [], [], 0)[0]:
                                line = input()
                                break

                        # Once alert is acknowledged, element is removed from list, reducing its length. Once length gets to
                        # 0 then there are no more elements in the list to check and the ;program terminates
                        del courses_list[index]

                        # atleast another course must be in queue for searching after the found one is dropped
                        # for this if statment to be triggered
                        if len(courses_list) > 0:
                            print('Moving onto the next course...')

                    elif row['class_nbr'] == class_nbr and row['course_status'] == 'Full':

                        print('{0} {1} {2} is full. Will re-try in 5 seconds.'.format(course_name.upper(), course_number.upper(), class_nbr))

def main():

    timetable_url = get_academic_timetable_url_input()
    courses_list = get_courses_list_input()

    course_scraper = initialize_scraper(timetable_url)

    while True:

        if courses_exist(courses_list, course_scraper):
            alert_if_not_full(courses_list, course_scraper)
            break
        else:
            courses_list = get_courses_list_input()



if __name__ == '__main__':
    main()








