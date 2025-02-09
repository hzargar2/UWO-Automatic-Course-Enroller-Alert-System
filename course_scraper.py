from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
import pandas as pd
import time, os, config, traceback


class CourseScraper:

    def __init__(self, chromedriverpath, timetable_url):

        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("disable-gpu")

        self.browser = webdriver.Chrome(chromedriverpath, options=chrome_options)
        self.timetable_url = timetable_url

        self.all_course_sections_df = pd.DataFrame()

    def set_all_course_sections_df(self, course_name: str, course_number: str):

        """scrapes timetable for the course and stores all its sections in a pandas Dataframe object"""

        try:

            # Initializes empty dataframe on each method call if dataframe is not empty to make sure each
            # course gets a fresh empty df

            if not self.all_course_sections_df.empty:
                self.all_course_sections_df = pd.DataFrame()

            # switch to the timetable window. Otherwise, makes a new window if it doesn't exist
            self.switch_to_window_handle_with_url(self.timetable_url)


            # Course number field in search section is filled

            self.browser.find_element_by_id("inputCatalognbr").clear()
            course_number_field = self.browser.find_element_by_id("inputCatalognbr")
            course_number_field.send_keys(course_number)

            WebDriverWait(self.browser, 20).until(EC.presence_of_element_located((By.XPATH, "//*[text()[contains(., 'Submit')]]"))).click()
            time.sleep(2)

            # gets page html

            html = self.browser.page_source
            soup = BeautifulSoup(html, 'lxml')

            # Course names are displayed in h4 tags

            courses_in_search = soup.find_all('h4')

            # iterates over course names found in search since each course name has it own table

            for index, course in enumerate(courses_in_search):

                # if user inputted course name and course number is in the h4 tag, it gets the appropriate table for
                # that course

                if course_name.upper() == course.text.split(' ')[0].upper() and course_number.upper() == \
                        course.text.split(' ')[1].upper():
                    course_sections_table = courses_in_search[index].find_next('tbody')

                    # Gets all tr tags in the table (course slots), then slices and gets every other because every other
                    # 'tr' tag is table data, not useful.

                    course_sections = course_sections_table.find_all('tr')[::2]

                    # Different df structure depending on if its the summer timetable or the fall/winter timetable
                    if self.timetable_url == config.urls_dict['Fall/Winter']:
                        self.__add_fall_winter_course_sections_to_df(course_sections)

                    # Different df structure depending on if its the summer timetable or the fall/winter timetable
                    elif self.timetable_url == config.urls_dict['Summer']:
                        self.__add_summer_course_sections_to_df(course_sections)

        except:
            print('ERROR:')
            print(traceback.format_exc())

    def __get_atttibutes_for_summer_course_section(self, course_section):

        '''Summer and fall/winter timetable have a different table structure and as a result, a different number
        of course section attributes. Therefore, there are different indices for certain values'''

        try:

            course_section_number = course_section.find_all('td')[0].text.strip()
            course_component = course_section.find_all('td')[1].text.strip()
            class_nbr = course_section.find_all('td')[2].text.strip()
            course_location = course_section.find_all('td')[11].text.strip()
            instructor_name = course_section.find_all('td')[12].text.strip()
            course_notes = course_section.find_all('td')[13].text.strip()
            course_status = course_section.find_all('td')[14].text.strip()
            course_session = course_section.find_all('td')[15].text.strip()
            course_start_date = course_section.find_all('td')[16].text.strip()
            course_end_date = course_section.find_all('td')[17].text.strip()
            course_campus = course_section.find_all('td')[18].text.strip()
            course_delivery_type = course_section.find_all('td')[19].text.strip()

            return course_section_number, course_component, class_nbr, course_location, instructor_name, course_notes, \
                   course_status, course_session, course_start_date, course_end_date, course_campus, course_delivery_type

        except:
            print('ERROR:')
            print(traceback.format_exc())

    def __get_attributes_for_fall_winter_course_section(self, course_section):

        '''Summer and fall/winter timetable have a different table structure and as a result, a different number
        of course section attributes. Therefore, there are different indices for certain values'''

        try:
            course_section_number = course_section.find_all('td')[0].text.strip()
            course_component = course_section.find_all('td')[1].text.strip()
            class_nbr = course_section.find_all('td')[2].text.strip()
            course_start_time = course_section.find_all('td')[9].text.strip()
            course_end_time = course_section.find_all('td')[10].text.strip()
            course_location = course_section.find_all('td')[11].text.strip()
            instructor_name = course_section.find_all('td')[12].text.strip()
            course_notes = course_section.find_all('td')[13].text.strip()
            course_status = course_section.find_all('td')[14].text.strip()
            course_campus = course_section.find_all('td')[15].text.strip()
            course_delivery_type = course_section.find_all('td')[16].text.strip()

            return course_section_number, course_component, class_nbr, course_start_time, course_end_time, course_location, \
                   instructor_name, course_notes, course_status, course_campus, course_delivery_type

        except:
            print('ERROR:')
            print(traceback.format_exc())

    def __add_fall_winter_course_sections_to_df(self, course_sections):

        '''Initializes df with the correct coloumns for the timetable since summer and fall/winter timetable structure
        is different and adds all the course sections to the self.all_course_sections_df pandas Dataframe object'''

        try:

            self.all_course_sections_df = pd.DataFrame(
                columns=['course_section_number', 'course_component', 'class_nbr', 'course_start_time',
                         'course_end_time', 'course_location', 'instructor_name', 'course_notes',
                         'course_status', 'course_campus', 'course_delivery_type'])

            # Iterates over every course section in all the course sections available
            for index, course_section in enumerate(course_sections):
                course_section_number, course_component, class_nbr, course_start_time, course_end_time, course_location, \
                instructor_name, course_notes, course_status, course_campus, course_delivery_type = self.__get_attributes_for_fall_winter_course_section(
                    course_section)

                self.all_course_sections_df = self.all_course_sections_df.append(
                    {'course_section_number': course_section_number,
                     'course_component': course_component,
                     'class_nbr': class_nbr,
                     'course_start_time': course_start_time,
                     'course_end_time': course_end_time,
                     'course_location': course_location,
                     'instructor_name': instructor_name,
                     'course_notes': course_notes,
                     'course_status': course_status,
                     'course_campus': course_campus,
                     'course_delivery_type':course_delivery_type
                     }, ignore_index=True)

        except:
            print('ERROR:')
            print(traceback.format_exc())

    def __add_summer_course_sections_to_df(self, course_sections):

        '''Initializes df with the coorrect coloumns for the timetable since summer and fall/winter timetable structure
        is different and adds all the course sections to the self.all_course_sections_df pandas Dataframe object'''

        try:

            self.all_course_sections_df = pd.DataFrame(
                columns=['course_section_number', 'course_component', 'class_nbr', 'instructor_name',
                         'course_notes', 'course_status', 'course_session', 'course_start_date',
                         'course_end_date', 'course_campus', 'course_delivery_type'])

            # Iterates over every course section in all the course sections available
            for index, course_section in enumerate(course_sections):
                course_section_number, course_component, class_nbr, course_location, instructor_name, course_notes, \
                course_status, course_session, course_start_date, course_end_date, course_campus, course_delivery_type = self.__get_atttibutes_for_summer_course_section(
                    course_section)

                self.all_course_sections_df = self.all_course_sections_df.append(
                    {'course_section_number': course_section_number,
                     'course_component': course_component,
                     'class_nbr': class_nbr,
                     'course_location': course_location,
                     'instructor_name': instructor_name,
                     'course_notes': course_notes,
                     'course_status': course_status,
                     'course_session': course_session,
                     'course_start_date': course_start_date,
                     'course_end_date': course_end_date,
                     'course_campus': course_campus,
                     'course_delivery_type': course_delivery_type
                     }, ignore_index=True)

        except:
            print('ERROR:')
            print(traceback.format_exc())

    def get_all_course_sections_df(self) -> pd.DataFrame:

        """Retreives pandas Dataframe containing info for all the course sections"""

        return self.all_course_sections_df

    def get_course_sections_by_component_df(self, component: str) -> pd.DataFrame:

        """Valid component inputs are 'LEC', 'TUT', 'LAB'"""

        try:

            df = self.all_course_sections_df.loc[self.all_course_sections_df['course_component'] == component]
            return df

        except:
            print('ERROR:')
            print(traceback.format_exc())

    def get_course_component_for_course_section(self, class_nbr) -> str:

        """Gets the type of course compoenent for a given class nbr"""

        try:
            # Iterates over every course section in all the course sections available
            for index, row in self.all_course_sections_df.iterrows():
                if row['class_nbr'] == class_nbr:
                    return row['course_component']

        except:
            print('ERROR:')
            print(traceback.format_exc())

    def get_course_location_for_course_section(self, class_nbr) -> str:

        """Gets the location of the course section given its class nbr"""

        try:
            # Iterates over every course section in all the course sections available
            for index, row in self.all_course_sections_df.iterrows():
                if row['class_nbr'] == class_nbr:
                    return row['course_location']

        except:
            print('ERROR:')
            print(traceback.format_exc())

    def get_course_sections_not_full_df(self) -> pd.DataFrame:

        """ Gets all the course sections for the course that are not"""

        try:

            df = self.all_course_sections_df.loc[self.all_course_sections_df['course_status'] == 'Not Full']
            return df

        except:
            print('ERROR:')
            print(traceback.format_exc())

    def course_section_is_full(self, class_nbr: str) -> bool:

        """Checks if course section with class_nbr is full or not"""

        try:

            for i, row in self.all_course_sections_df.iterrows():
                if row['class_nbr'] == class_nbr and row['course_status'] == 'Not Full':
                    return False
                elif row['class_nbr'] == class_nbr and row['course_status'] == 'Full':
                    return True

        except:
            print('ERROR:')
            print(traceback.format_exc())

    def course_section_exists(self, class_nbr: str) -> bool:

        """Checks whether course section with a specific class nbr exists or not"""

        try:
            # Iterates over every course section in all the course sections available
            for index, row in self.all_course_sections_df.iterrows():
                if row['class_nbr'] == class_nbr:
                    return True
            # course section doesn't exist in current df
            return False

        except:
            print('ERROR:')
            print(traceback.format_exc())

    def course_section_is_distance_studies(self, class_nbr: str) -> bool:

        """Checks whether the course is a distance studies course"""

        try:
            # Iterates over every course section in all the course sections available
            for index, row in self.all_course_sections_df.iterrows():
                if row['class_nbr'] == class_nbr and 'Distance Studies' in row['course_delivery_type']:
                    return True

                elif row['class_nbr'] == class_nbr and 'Distance Studies' not in row['course_delivery_type']:
                    return False

        except:
            print('ERROR:')
            print(traceback.format_exc())

    def switch_to_window_handle_with_url(self, url: str):

        """Switches the window with the inputted url, if it doesn't exist, it opens a window and loads
        that a new page using that url and switches to it"""

        try:
            # loops through all windows to see if any of the window urls match the url, if true, then method returns
            # because it has already switched to it prior to doing the check so we don't need to do anything else

            for window_handle in self.browser.window_handles:

                self.browser.switch_to.window(window_handle)

                if url == self.browser.current_url:
                    return

            # if not, the iterator above has stopped at the last window and has switched to it. Therefore, when we open
            # a new window with our desired url, it opens to the right of the last window. Therefore, this new window
            # now becomes the new last window in the window handles list since it is the most rightward window.
            # We can easily switch to this lat window with the -1 index.

            self.browser.execute_script("window.open('{0}')".format(url))
            time.sleep(2)
            self.browser.switch_to.window(self.browser.window_handles[-1])

        except:
            print('ERROR:')
            print(traceback.format_exc())



# scraper = CourseScraper(os.path.join(os.path.dirname(__file__), "chromedriver_mac_81.0.4044.138"), config.urls_dict['Summer'])
#
# print(scraper.window_handle_exists(config.urls_dict['Summer']))
