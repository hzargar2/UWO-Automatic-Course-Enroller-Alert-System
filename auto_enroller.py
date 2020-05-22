from bs4 import BeautifulSoup
import time, os, config, re
from selenium import webdriver
from selenium.common.exceptions import *
from course_scraper import *


import login_credentials_DO_NOT_PUSH

pd.set_option('display.max_rows', 500)
pd.set_option('display.max_columns', 500)
pd.set_option('display.width', 1000)


class AutoEnroller(CourseScraper):

    def __init__(self, chromedriverpath: str, timetable_url: str, student_center_login_url: str, username: str, password: str):

        super().__init__(chromedriverpath, timetable_url)

        self.student_center_login_url = student_center_login_url
        self.username = username
        self.password = password

    def enroll(self, course_name: str, course_number: str, class_nbr: str, dependant_class_nbr_with_course_component_list_1 = None, dependant_class_nbr_with_course_component_list_2 = None):

        """Enrolls in a course given its name, number. class nbr, and any of its dependant components that are required
        for enrollment (LAB, TUT, LEC)"""

        try:
            # Checks to see if the course section exists in the current dataframe. Otherwise, runs set_all_current_sections_df
            # again. Better than running the method each time which slows it down
            if not self.course_section_exists(class_nbr):
                print('Class_nbr not found in current all_course_sections_df attribute. Running set_all_course_sections_df method again.\n')
                print('Try to have set_all_course_sections_df() execute only once in the code logic to reduce computation time for each course iteration (5s vs 10s).\n ')
                self.set_all_course_sections_df(course_name, course_number)
                time.sleep(5)

            print("ATTEMPTING TO ENROLL IN ({0} {1} '{2}' CLASS NBR {3})".format(course_name.upper(), course_number.upper(), self.get_course_component_for_course_section(class_nbr), class_nbr))
            for dependant in [dependant_class_nbr_with_course_component_list_1,dependant_class_nbr_with_course_component_list_2]:
                if dependant is not None:
                    print("ATTEMPTING TO ENROLL IN ({0} {1} '{2}' CLASS NBR {3})".format(course_name.upper(), course_number.upper(), dependant[1], dependant[0]))

            # switches to student center login window
            self.switch_to_window_handle_with_url(self.student_center_login_url)

            print('Logging into student center...')
            username_field = self.browser.find_element_by_id("userid")
            passsword_field = self.browser.find_element_by_id("pwd")

            username_field.send_keys(self.username)
            passsword_field.send_keys(self.password)

            # submit button for login info
            self.browser.find_element_by_xpath("//*[@value='Sign In']").click()
            time.sleep(2)

            if 'Your User ID and/or Password are invalid.' in self.browser.page_source:
                raise Exception("FAILED: LOGIN FAILED.")


            print('Logged in.')

            # switches to correct frame to be ble to access required elements
            iframe = self.browser.find_element_by_xpath('//iframe[@name="TargetContent"]')
            self.browser.switch_to.frame(iframe)

            print('Switched iframes.')

            # 'Enroll in Classes' link button
            self.browser.find_element_by_partial_link_text('Enroll in Classes').click()
            time.sleep(2)

            print('Enroll in Classes clicked.')

            # del course if it already exists in the course enrollment worksheet or else system won't let me add it
            # self.__del_course_in_course_enrollment_worksheet(course_number, class_nbr, dependant_class_nbr_with_course_component_list_1, dependant_class_nbr_with_course_component_list_2)
            self.__del_all_courses_in_course_enrollment_worksheet()

            # class nbr field fill in
            class_nbr_field = self.browser.find_element_by_id('DERIVED_REGFRM1_CLASS_NBR')
            class_nbr_field.send_keys(class_nbr)
            # Submit class nbr search
            self.browser.find_element_by_xpath("//*[@value='Enter']").click()
            time.sleep(2)

            print('Class nbr submitted.')

            # need extra step for enrollment if the course has dependant course components like a lab, tut, or lec. A
            # course can have all 3 components so need to account for the case that a course has all 3.

            if self.has_dependant_course_components():

                self.__select_dependant_course_components(class_nbr, dependant_class_nbr_with_course_component_list_1, dependant_class_nbr_with_course_component_list_2)

                #click 'Next' button on page where we have selected all dependant course sections to go to next page
                try:
                    self.browser.find_element_by_xpath("//*[@value='Next']").click()
                    time.sleep(2)
                except NoSuchElementException as e:
                    print(e)

            # Confirm course section(s) selection by clicking 'Next' again.
            # Course selection then added to course enrollement worksheet.
            # Still not enrolled. Must finalize the course enrollment work sheet in the next step.

            try:
                self.browser.find_element_by_xpath("//*[@value='Next']").click()
                time.sleep(2)
            except NoSuchElementException as e:
                print(e)

            print('Added to course enrollment worksheet.')

            # click 'Proceed to Step 2 of 3'
            self.browser.find_element_by_xpath("//*[@value='Proceed to Step 2 of 3']").click()
            time.sleep(2)

            # raise exception if course enrollemnt times are closed or havn't begun.
            if 'You cannot enroll at this time.' in self.browser.page_source:
                raise Exception("FAILED: CANNOT ENROLL IN ({0} {1} '{2}' CLASS NBR {3}). ENROLLMENT HAS NOT BEGUN AND YOU DO NOT HAVE AN AN APPOINTMENT TO ENROLL OR ONLINE ENROLLMENT HAS BEEN CLOSED FOR THIS TERM/SESSION.")

            # click 'Finish Enrolling
            self.browser.find_element_by_xpath("//*[@value='Finish Enrolling']").click()
            time.sleep(3)

            if 'You are already enrolled in this class' in self.browser.page_source:
                raise Exception("FAILED: YOU ARE ALREADY ENROLLED IN ({0} {1} '{2}' CLASS NBR {3}). IF YOU MEANT TO SWAP LAB/TUT COMPONENTS IN A COURSE YOU ARE ALREADY ENROLLED IN, RESTART THE PROGRAM AND MAKE SURE YOU HAVE SELECTED THE SWAP OPTION WHEN ASKED.".format(course_name.upper(), course_number.upper(), self.get_course_component_for_course_section(class_nbr), class_nbr))

            if 'The enrollment limit for the combined section has been reached.' in self.browser.page_source:
                raise Exception("FAILED: COURSE ({0} {1} '{2}' CLASS NBR {3}) IS FULL. DISCREPANCY BETWEEN TIMETABLE AND STUDENT CENTER EXISTS.".format(course_name.upper(), course_number.upper(), self.get_course_component_for_course_section(class_nbr), class_nbr))

            print("SUCCESS: ENROLLED IN ({0} {1} '{2}' CLASS NBR {3})".format(course_name.upper(), course_number.upper(), self.get_course_component_for_course_section(class_nbr), class_nbr))
            for dependant in [dependant_class_nbr_with_course_component_list_1,dependant_class_nbr_with_course_component_list_2]:
                if dependant is not None:
                    print("SUCCESS: ENROLLED IN ({0} {1} '{2}' CLASS NBR {3})".format(course_name.upper(), course_number.upper(), dependant[1], dependant[0]))
            print('')

            # switches back to student center login page so switch_to_window_handle_with_url doesn't open another a new window
            # if other methods are ran. Resets the pag destination so less memory is used.
            self.browser.get(self.student_center_login_url)

        except Exception as e:
            print(e)

    def swap(self, swap_full_course_name: str, course_name: str, course_number: str, class_nbr: str,
             dependant_class_nbr_with_course_component_list_1 = None,
             dependant_class_nbr_with_course_component_list_2 = None):

        """Swaps an existing course in the timetable (swap_full_course_name) for new course given its name, number
        class nbr, and its required dependant components for enrollment (LAB, TUT, LEC)"""
        try:

            # Checks to see if the course section exists in the current dataframe. Otherwise, runs set_all_current_sections_df
            # again. Better than running the method each time which slows it down
            if not self.course_section_exists(class_nbr):
                print(
                    'Class_nbr not found in current all_course_sections_df attribute. Running set_all_course_sections_df method again.\n')
                print(
                    'Try to have set_all_course_sections_df() execute only once in the code logic to reduce computation time for each course iteration (5s vs 10s).\n ')
                self.set_all_course_sections_df(course_name, course_number)
                time.sleep(5)

            print("ATTEMPTING TO SWAP ({4}) FOR ({0} {1} '{2}' CLASS NBR {3})".format(course_name.upper(), course_number.upper(), self.get_course_component_for_course_section(class_nbr), class_nbr, swap_full_course_name.upper()))
            for dependant in [dependant_class_nbr_with_course_component_list_1,dependant_class_nbr_with_course_component_list_2]:
                if dependant is not None:
                    print("ATTEMPTING TO SWAP ({4}) FOR ({0} {1} '{2}' CLASS NBR {3})".format(course_name.upper(), course_number.upper(), dependant[1], dependant[0], swap_full_course_name.upper()))


            # switches to student center login window
            self.switch_to_window_handle_with_url(self.student_center_login_url)

            print('Logging into student center...')
            username_field = self.browser.find_element_by_id("userid")
            passsword_field = self.browser.find_element_by_id("pwd")

            username_field.send_keys(self.username)
            passsword_field.send_keys(self.password)

            # submit button for login info
            self.browser.find_element_by_xpath("//*[@value='Sign In']").click()
            time.sleep(2)

            print('Logged in.')

            # switches to correct frame to be ble to access required elements
            iframe = self.browser.find_element_by_xpath('//iframe[@name="TargetContent"]')
            self.browser.switch_to.frame(iframe)

            print('Switched iframes.')

            # 'Enroll in Classes' link button
            self.browser.find_element_by_partial_link_text('Enroll in Classes').click()
            time.sleep(2)

            print("'Enroll in Classes' clicked.")

            # 'Swap' link button
            self.browser.find_element_by_partial_link_text('Swap').click()
            time.sleep(2)

            print("'Swap' clicked.")

            # Click Swap This Class drop down menu

            self.browser.find_element_by_xpath("//select[@id='DERIVED_REGFRM1_DESCR50$225$']").click()

            html = self.browser.page_source
            soup = BeautifulSoup(html, 'lxml')

            # gets drop down menu html
            drop_down_menu = soup.find('select', {'id':'DERIVED_REGFRM1_DESCR50$225$'})
            # gets options in drop down menu html
            options = drop_down_menu.find_all('option')

            # iterates through options to see if any of the texts match the course the user wants to swap the new course with
            for option in options:

                # swap_full_course_name has the course name, number and full course title. We are only comparing the course
                # name and course number for our selection so we need to get the string portion that has only those
                # componenets. Eg: 'Biology 1002B - BIOLOGY FOR SCIENCE II' becomes 'Biology 1002B' then we convert
                # to upper case to standardize so final product is 'BIOLOGY 1002B' and we compare this with the
                # upper case of the tag's text to confirm if they are the same

                swap_course_name_and_course_number = swap_full_course_name.strip().split(' - ')
                swap_course_name_and_course_number = swap_course_name_and_course_number[0].upper()

                if swap_course_name_and_course_number in option.text.strip().upper():

                    option_tag = str(option)

                    # gets the value attributes value in the option tag by searching for whatever it is between the
                    # quotation marks, regular expresion
                    option_tag_value = re.search('value="(.*?)"', option_tag).group(1)
                    self.browser.find_element_by_xpath("//option[@value='{0}']".format(option_tag_value)).click()
                    break

            # input class_nbr of new course that user wants to add and press enter
            enter_class_nbr = self.browser.find_element_by_xpath("//input[@id='DERIVED_REGFRM1_CLASS_NBR']")
            enter_class_nbr.send_keys(class_nbr)
            self.browser.find_element_by_xpath("//input[@name='DERIVED_REGFRM1_SSR_PB_ADDTOLIST2$106$']").click()
            time.sleep(3)

            if 'You do not have a valid appointment for this session' in self.browser.page_source:
                raise Exception("FAILED: CANNOT ENROLL IN ({0} {1} '{2}' CLASS NBR {3}). ENROLLMENT HAS NOT BEGUN AND YOU DO NOT HAVE AN AN APPOINTMENT TO ENROLL OR ONLINE ENROLLMENT HAS BEEN CLOSED FOR THIS TERM/SESSION.")

            if 'Duplicate - Already enrolled' in self.browser.page_source:
                raise Exception("FAILED: ALREADY ENROLLED IN COURSE ({0} {1} '{2}' CLASS NBR {3})".format(course_name.upper(), course_number.upper(), self.get_course_component_for_course_section(class_nbr), class_nbr))

            # need extra step for enrollment if the course has dependant course components like a lab, tut, or lec. A
            # course can have all 3 components so need to account for the case that a course has all 3.

            if self.has_dependant_course_components():
                self.__select_dependant_course_components(class_nbr, dependant_class_nbr_with_course_component_list_1,
                                                          dependant_class_nbr_with_course_component_list_2)

                # total number of next clicks based on number of dependant componenets that are not None
                # click 'Next' button on page where we have selected all dependant course sections to go to next page
                try:
                    self.browser.find_element_by_xpath("//*[@value='Next']").click()
                    time.sleep(2)
                except NoSuchElementException as e:
                    print(e)

            # Confirm course section(s) selection by clicking 'Next' again.
            # Course selection then added to course enrollement worksheet.
            # Still not enrolled. Must finalize the course enrollment work sheet in the next step.

            try:
                self.browser.find_element_by_xpath("//*[@value='Next']").click()
                time.sleep(2)
            except NoSuchElementException as e:
                print(e)

            self.browser.find_element_by_xpath("//input[@value='Finish Swapping']").click()
            time.sleep(3)

            if ('The enrollment limit for the combined section has been reached.' in self.browser.page_source):
                raise Exception("FAILED: COURSE ({0} {1} '{2}' CLASS NBR {3}) IS FULL. DISCREPANCY BETWEEN TIMETABLE AND STUDENT CENTER EXISTS.".format(course_name.upper(), course_number.upper(), self.get_course_component_for_course_section(class_nbr), class_nbr))


            print("SUCCESS: SWAPPED ({4}) FOR ({0} {1} '{2}' CLASS NBR {3})".format(course_name.upper(), course_number.upper(), self.get_course_component_for_course_section(class_nbr), class_nbr, swap_full_course_name.upper()))
            for dependant in [dependant_class_nbr_with_course_component_list_1,dependant_class_nbr_with_course_component_list_2]:
                if dependant is not None:
                    print("SUCCESS: SWAPPED ({4}) FOR ({0} {1} '{2}' CLASS NBR {3})".format(course_name.upper(), course_number.upper(), dependant[1], dependant[0], swap_full_course_name.upper()))
            print('')

            # switches back to student center login page so switch_to_window_handle_with_url doesn't open another a new window
            # if other methods are ran. Resets the pag destination so less memory is used.
            self.browser.get(self.student_center_login_url)

        except Exception:
            print(e)

    def has_dependant_course_components(self) -> bool:

        """Checks to see if a given course section has any required course componets that would need to be enrolled
        in at the same time as the course"""

        try:

            if self.all_course_sections_df['course_component'].nunique() > 1:
                return True
            else:
                return False

        except:
            print('ERROR:')
            print(traceback.format_exc())

    def get_dependant_course_components_df(self, class_nbr: str) -> pd.DataFrame:

        """Gets all the dependant course components that are possible for enrollment. Need to enroll in dependant
        components at the same time as the inputted course for enrollment to succeed. Must enroll in at least
        1 course component of each type. Example. course has a lab, and lec component then must select
        at least 1 LAB and 1 LEC component for enrollment"""

        # gets all the course components that are different from the current course class_nbr and component that is
        # inputted and returns a df of the results.
        try:

            df = self.all_course_sections_df.loc[self.all_course_sections_df['class_nbr'] == class_nbr]

            if not df.empty:
                current_course_section_row = df.iloc[0]
                current_course_component = current_course_section_row['course_component']

                df = self.all_course_sections_df.loc[self.all_course_sections_df['course_component'] != current_course_component]
                return df

        except:
            print('ERROR:')
            print(traceback.format_exc())

    def __select_dependant_course_components(self, class_nbr, dependant_class_nbr_with_course_component_list_1, dependant_class_nbr_with_course_component_list_2):

        """Selects the dependant course components the user inputs from their respective pages when they laod"""

        try:

            dependant_course_components = self.get_dependant_course_components_df(class_nbr)
            number_unique_dependant_course_components = dependant_course_components['course_component'].nunique()

            # loops through the number of total tables that should be present and makes the selections, even if
            # the LEC compoenent has its own page
            for i in range(number_unique_dependant_course_components):

                # get current page html
                html = self.browser.page_source
                soup = BeautifulSoup(html, 'lxml')

                # get tables
                tables = soup.find_all("table", {"class": "PSLEVEL1GRIDWBO"})

                for table in tables:

                    tr_tags = table.find_all('tr')

                    # get table title, tells us what component the table is for (Labratory, Tutorial, or Lecture)
                    table_title = tr_tags[0].text.strip().split()
                    course_component_of_table = table_title[1]

                    # Rename it to match the  user inputted format
                    if course_component_of_table == 'Laboratory':
                        course_component_of_table = 'LAB'
                    elif course_component_of_table == 'Tutorial':
                        course_component_of_table = 'TUT'
                    else:
                        course_component_of_table = 'LEC'

                    for dependant_class_nbr_with_course_component_list in [dependant_class_nbr_with_course_component_list_1,
                                                                           dependant_class_nbr_with_course_component_list_2]:

                        # list is not None type and user inputted course component matches the course component
                        # of the table
                        if dependant_class_nbr_with_course_component_list is not None and \
                                dependant_class_nbr_with_course_component_list[1] == course_component_of_table:

                            # if we have a dependant component that is a LEC, our main class_nbr is a TUT or LAB.
                            # For this reason, the table for LEC components looks different and doesn't load any other
                            # dependant components with it. LEC component table has its own page. The table also
                            # doesn't have a title. So we need to find the LEC component, click it and press continue,
                            # after that we arrive at another page to add the other components (TUT, LABS) as usual
                            # (these have titles and proceed using else statement below

                            if course_component_of_table == 'LEC':
                                # get the course sections in the table, from 'tr' tag index 1 and on is the useful info, one before
                                # is just table structure data
                                for tr_tag in tr_tags[1:]:

                                    # if the class_nbr in the tr_tag from the table matches the user inputted class_nbr
                                    if tr_tag.text.split()[0] == dependant_class_nbr_with_course_component_list[0]:
                                        # get the circle button element which is an input tag. Since we got the element with
                                        # BeautifulSoup and we need to interact with it (can't interactg with it in BeautifulSoup),
                                        # we convert the element to a string so we can split it and then we get the id=
                                        # component of the input tag. Then use the browser object (Selenium) to click it

                                        input_tag_button = tr_tag.find('input')
                                        input_tag_button = str(input_tag_button).split()
                                        input_tag_button_id = input_tag_button[2].replace('id=', '').replace('"', '')

                                        self.browser.find_element_by_id('{0}'.format(input_tag_button_id)).click()
                                        # click 'Next' button on page where we have selected the lecture component
                                        try:
                                            self.browser.find_element_by_xpath("//*[@value='Next']").click()
                                            time.sleep(3)
                                            break

                                        except NoSuchElementException as e:
                                            print(e)


                            # if componenet is TUT or LAB, we proceed as normal
                            else:

                                # get the course sections in the table, from 'tr' tag number 4 and on is the useful info, ones before
                                # are just table structure data
                                for tr_tag in tr_tags[4:]:

                                    # if the class_nbr in the tr_tag from the table matches the user inputted class_nbr
                                    if tr_tag.text.split()[0] == dependant_class_nbr_with_course_component_list[0]:
                                        # get the circle button element which is an input tag. Since we got the element with
                                        # BeautifulSoup and we need to interact with it (can't interactg with it in BeautifulSoup),
                                        # we convert the element to a string so we can split it and then we get the id=
                                        # component of the input tag. Then use the browser object (Selenium) to click it

                                        input_tag_button = tr_tag.find('input')
                                        input_tag_button = str(input_tag_button).split()
                                        input_tag_button_id = input_tag_button[2].replace('id=', '').replace('"', '')

                                        self.browser.find_element_by_id('{0}'.format(input_tag_button_id)).click()
                                        break
        except:
            print(traceback.format_exc())

    def __del_course_in_course_enrollment_worksheet(self, course_number: str, class_nbr: str, dependant_class_nbr_with_course_component_list_1, dependant_class_nbr_with_course_component_list_2):

        """ Deletes a course from the course enrollment worksheet (planner) given its course number and class nbr"""

        try:

            # del course if it already exists in the course enrollment worksheet or else system won't let me add it
            if dependant_class_nbr_with_course_component_list_1:
                class_nbr_dependant_1 = dependant_class_nbr_with_course_component_list_1[0]
            else:
                class_nbr_dependant_1 = None

            if dependant_class_nbr_with_course_component_list_2:
                class_nbr_dependant_2 = dependant_class_nbr_with_course_component_list_2[0]
            else:
                class_nbr_dependant_2 = None

            all_class_nbrs = [class_number for class_number in [class_nbr, class_nbr_dependant_1, class_nbr_dependant_2] if class_number is not None]

            # get current page html
            html = self.browser.page_source
            soup = BeautifulSoup(html, 'lxml')

            course_enrollment_worksheet_table = soup.find("table", {"class": "PSLEVEL1GRID"})
            tr_tags = course_enrollment_worksheet_table.find_all('tr')

            #first tr tag is useless, just table column data
            tr_tags = tr_tags[1:]

            for tr in tr_tags:

                if 'Your course enrollment worksheet is empty' in tr.text:
                    break

                for class_number in all_class_nbrs:

                    if tr.find('a', {'id': "P_DELETE$0"}) and course_number.upper() in tr.text and class_number in tr.text:
                        self.browser.find_element_by_id("P_DELETE$0").click()
                        time.sleep(2)
                        break

        except NoSuchElementException:
            print(traceback.format_exc())

    def __del_all_courses_in_course_enrollment_worksheet(self):

        """Deletes all courses in the course enrollment worksheet (planner)"""

        try:

            # del all courses in course enrollment worksheet, makes catching exceptions easier as
            # get current page html
            html = self.browser.page_source
            soup = BeautifulSoup(html, 'lxml')

            course_enrollment_worksheet_table = soup.find("table", {"class": "PSLEVEL1GRID"})
            tr_tags = course_enrollment_worksheet_table.find_all('tr')

            # arrange tags backwards when deleting all of the courses in the worksheet because when a preceding tag is
            # deleted, the tag delete ids get updated and must scrape the html again to get the values, instead, if we
            # delete from bottom to up then tag ids update but maintain the same ids and therefore dont need to scrape
            # the html. Also discard the last value of the inverted list (first value of non_inverted list) because it
            # is insignificant (table structure data

            tr_tags = tr_tags[::-1]
            tr_tags = tr_tags[:-1]

            for tr in tr_tags:

                if 'Your course enrollment worksheet is empty' in tr.text:
                    break

                # gets the value attributes value in the option tag by searching for whatever it is between the
                # quotation marks, regular expresion
                elif bool(re.search('id="P_DELETE(.*?)"', str(tr))):
                    tr_tag_id = re.search('id="P_DELETE(.*?)"', str(tr)).group(1)
                    self.browser.find_element_by_xpath("//a[@id='P_DELETE{0}']".format(tr_tag_id)).click()
                    time.sleep(2)

        except NoSuchElementException:
            print(traceback.format_exc())

    def get_current_course_enrollment_df(self) -> pd.DataFrame:

        """Gets current timetabl of user and all they're currently enrolled course. Returns a pandas Dataframe
        of results"""

        print("RETRIEVING STUDENT'S CURRENT TIMETABLE...")

        # switches to student center login window
        self.switch_to_window_handle_with_url(self.student_center_login_url)

        print('Logging into student center...')
        username_field = self.browser.find_element_by_id("userid")
        passsword_field = self.browser.find_element_by_id("pwd")

        username_field.send_keys(self.username)
        passsword_field.send_keys(self.password)

        # submit button for login info
        self.browser.find_element_by_xpath("//*[@value='Sign In']").click()
        time.sleep(2)
        print('Logged in.')

        # switches to correct frame to be ble to access required elements
        iframe = self.browser.find_element_by_xpath('//iframe[@name="TargetContent"]')
        self.browser.switch_to.frame(iframe)
        print('Switched iframes.')

        # 'Enroll in Classes' link button
        self.browser.find_element_by_partial_link_text('My Weekly Schedule').click()
        time.sleep(5)
        print("'My Weekly Schedule' clicked.")

        # click List view
        self.browser.find_element_by_xpath("//input[@id='DERIVED_REGFRM1_SSR_SCHED_FORMAT$258$']").click()
        print("'List View' clicked.")
        time.sleep(4)

        html = self.browser.page_source
        soup = BeautifulSoup(html, 'lxml')

        # get full course name tags
        td_tags = soup.find_all('td', {'class':'PAGROUPDIVIDER'})

        # initialize df
        df = pd.DataFrame(columns=['full_course_name'])

        # iterate through tags to get all the full course names
        for td in td_tags:

            full_course_name = td.text.strip()
            df = df.append({'full_course_name':full_course_name}, ignore_index=True)

        # switches back to student center login page so switch_to_window_handle_with_url doesn't open another a new window
        # if other methods are ran. Resets the pag destination so less memory is used.
        print('SUCCESS: CURRENT TIMETABLE RETRIEVED.\n')
        self.browser.get(self.student_center_login_url)

        return df

    def bool_login_creds_valid(self):

        """Checks to see if login credentials inputted by user and which are the classes attributes are valid"""

        try:
            print('TESTING LOGIN CREDENTIALS FOR VALIDITY...')
            # switches to student center login window
            self.switch_to_window_handle_with_url(self.student_center_login_url)

            print('Logging into student center...')
            username_field = self.browser.find_element_by_id("userid")
            passsword_field = self.browser.find_element_by_id("pwd")

            username_field.send_keys(self.username)
            passsword_field.send_keys(self.password)

            # submit button for login info
            self.browser.find_element_by_xpath("//*[@value='Sign In']").click()
            time.sleep(2)

            # if login failed, return false
            if 'Your User ID and/or Password are invalid.' in self.browser.page_source:
                self.browser.get(self.student_center_login_url)
                return False
            # returns true if successful
            else:
                self.browser.get(self.student_center_login_url)
                return True

        except Exception as e:
            print(e)




'''TEST CASE'''

# auto_enroller = AutoEnroller(os.path.join(os.path.dirname(__file__), "chromedriver_mac_81.0.4044.138"), config.urls_dict['Summer'], config.urls_dict['Student_Center_Login_Page'], login_credentials_DO_NOT_PUSH.login_creds['username'], login_credentials_DO_NOT_PUSH.login_creds['password'])
# #auto_enroller.enroll('COMPSCI', '1027B', '1194', ['1310','LAB'])
# # # #
# # #
# #
# # auto_enroller.swap('Computer Science 1027B - COMP SCI FUNDAMENTALS II','STATS', '2244B', '1360', ['1401','LAB'])
# #
#
# print(auto_enroller.get_current_course_enrollment_df())
