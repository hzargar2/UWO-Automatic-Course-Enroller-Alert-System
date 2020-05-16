from bs4 import BeautifulSoup
import time, os, config
from selenium import webdriver
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

        try:

            self.set_all_course_sections_df(course_name, course_number)

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

            print('Enroll in Classes clicked.')
            # class nbr field fill in
            class_nbr_field = self.browser.find_element_by_id('DERIVED_REGFRM1_CLASS_NBR')
            class_nbr_field.send_keys(class_nbr)
            # Submit class nbr search
            self.browser.find_element_by_xpath("//*[@value='Enter']").click()
            time.sleep(2)

            print('Class nbr submitted')

            # need extra step for enrollment if the course has dependant course components like a lab, tut, or lec. A
            # course can have all 3 components so need to account for the case that a course has all 3.

            if self.has_dependant_course_components():

                dependant_course_components = self.get_dependant_course_components_df(class_nbr)
                number_unique_dependant_course_components = dependant_course_components['course_component'].nunique()

                # get current page html
                html = self.browser.page_source
                soup = BeautifulSoup(html, 'lxml')

                # get tables
                tables = soup.find_all("table", {"class": "PSLEVEL1GRIDWBO"})

                # checks to see if the number of tables on page match the number of unique dependant course components.
                # If no, there is a discrepancy between the timetable and the student center course section selection.

                if len(tables) == number_unique_dependant_course_components:

                    # loops through the number of tables on page
                    for table in tables:

                        tr_tags = table.find_all('tr')

                        #get table title, tells us what component the table is for (Labratory, Tutorial, or Lecture)
                        table_title = tr_tags[0].text.strip().split()
                        course_component_of_table = table_title[1]

                        # Rename it to match the  user inputted format
                        if course_component_of_table == 'Laboratory':
                            course_component_of_table = 'LAB'
                        elif course_component_of_table == 'Tutorial':
                            course_component_of_table = 'TUT'
                        elif course_component_of_table == 'Lecture':
                            course_component_of_table = 'LEC'

                        for dependant_class_nbr_with_course_component_list in [dependant_class_nbr_with_course_component_list_1, dependant_class_nbr_with_course_component_list_2]:
                            # list is not None type and user inputted course component matches the course component
                            # of the table
                            if dependant_class_nbr_with_course_component_list is not None and dependant_class_nbr_with_course_component_list[1] == course_component_of_table:

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


            #click 'Next' button on page where we have selected all dependant course sections to go to next page
            self.browser.find_element_by_xpath("//*[@value='Next']").click()
            time.sleep(2)

            # Confirm course section(s) selection by clicking 'Next5' again.
            # Course selection then added to course enrollement worksheet.
            # Still not enrolled. Must finalize the course enrollment work sheet in the next step.

            self.browser.find_element_by_xpath("//*[@value='Next']").click()
            time.sleep(2)

            # click 'Proceed to Step 2 of 3'
            self.browser.find_element_by_xpath("//*[@value='Proceed to Step 2 of 3']").click()
            time.sleep(2)

            # click 'Finish Enrolling
            self.browser.find_element_by_xpath("//*[@value='Finish Enrolling']").click()
            time.sleep(2)

            print("SUCCESS: ENROLLED IN {0} {1} '{2}' CLASS NBR {3}".format(course_name.upper(), course_number.upper(), self.get_course_component_for_course_section(class_nbr), class_nbr))
            for dependant in [dependant_class_nbr_with_course_component_list_1,dependant_class_nbr_with_course_component_list_2]:
                if dependant is not None:
                    print("SUCCESS: ENROLLED IN {0} {1} '{2}' CLASS NBR {3}".format(course_name, course_number, dependant[1], dependant[0]))

        except:
            print('ERROR:')
            print(traceback.format_exc())

    def has_dependant_course_components(self) -> bool:

        try:

            if self.all_course_sections_df['course_component'].nunique() > 1:
                return True
            else:
                return False

        except:
            print('ERROR:')
            print(traceback.format_exc())

    def get_dependant_course_components_df(self, class_nbr: str) -> pd.DataFrame:

        # gets all the course components that are different than the current course class_nbr and componenet that is
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


'''TEST CASE'''

# scraper = CourseScraper(os.path.join(os.path.dirname(__file__), "chromedriver_mac_81.0.4044.138"), config.urls_dict['Summer'])
auto_enroller = AutoEnroller(os.path.join(os.path.dirname(__file__), "chromedriver_mac_81.0.4044.138"), config.urls_dict['Summer'], config.urls_dict['Student_Center_Login_Page'], login_credentials_DO_NOT_PUSH.login_creds['username'], login_credentials_DO_NOT_PUSH.login_creds['password'])

### DO NOT PUSH WITH LOGIN CREDENTIALS
# auto_enroller.enroll(login_credentials_DO_NOT_PUSH.login_creds['username'], login_credentials_DO_NOT_PUSH.login_creds['password'], 'PHYSICS', '1302A', '2063', ['2065','TUT'], ['2064','LAB'])

auto_enroller.enroll('COMPSCI', '1027B', '1194', ['1310','LAB'])




