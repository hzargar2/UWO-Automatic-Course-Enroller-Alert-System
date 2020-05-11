from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import pandas as pd
import time


class CourseScraper:

    def __init__(self, chromedriverpath, timetable_url):

        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("disable-gpu")

        self.browser = webdriver.Chrome(chromedriverpath, options=chrome_options)
        self.timetable_url = timetable_url
        self.all_course_sections_df = pd.DataFrame(
            columns=['course_section_number', 'course_component', 'class_nbr', 'instructor_name',
                     'course_notes', 'course_status', 'course_session', 'course_start_date', 'course_end_date',
                     'course_campus'])

    def get_timetable_page(self):
        self.browser.get(self.timetable_url)

    def set_all_course_sections_df(self, course_name: str, course_number: str):

        try:

            # Initializes empty dataframe on each method call if dataframe is not empty

            if not self.all_course_sections_df.empty:
                self.all_course_sections_df = pd.DataFrame(
                    columns=['course_section_number', 'course_component', 'class_nbr', 'instructor_name',
                             'course_notes', 'course_status', 'course_session', 'course_start_date', 'course_end_date',
                             'course_campus'])

            # Course number field in search section is filled

            self.browser.find_element_by_id("inputCatalognbr").clear()
            course_number_field = self.browser.find_element_by_id("inputCatalognbr")
            course_number_field.send_keys(course_number)

            self.browser.find_element_by_xpath("/html/body/div/div/div[2]/form/fieldset/div[5]/div/button[2]").click()

            # gets page html

            html = self.browser.page_source
            soup = BeautifulSoup(html, 'lxml')

            # Course names are displayed in h4 tags

            courses_in_search = soup.find_all('h4')

            # iterates over course names found in search since each course name has it own table

            for index, course in enumerate(courses_in_search):

                # if user inputted course name and course number is in the h4 tag, it gets the appropriate table for
                # that course

                if course_name.lower() == course.text.split(' ')[0].lower() and course_number.lower() == course.text.split(' ')[1].lower():
                    course_sections_table = courses_in_search[index].find_next('tbody')

                    # Gets all tr tags in the table (course slots), then slices and gets every other because every other
                    # 'tr' tag is table data, not useful.

                    course_sections = course_sections_table.find_all('tr')[::2]

                    # Iterates over every course section in all the course sections available

                    for index, course_section in enumerate(course_sections):
                        course_section_number = course_section.find_all('td')[0].text.strip()
                        course_component = course_section.find_all('td')[1].text.strip()
                        class_nbr = course_section.find_all('td')[2].text.strip()
                        instructor_name = course_section.find_all('td')[12].text.strip()
                        course_notes = course_section.find_all('td')[13].text.strip()
                        course_status = course_section.find_all('td')[14].text.strip()
                        course_session = course_section.find_all('td')[15].text.strip()
                        course_start_date = course_section.find_all('td')[16].text.strip()
                        course_end_date = course_section.find_all('td')[17].text.strip()
                        course_campus = course_section.find_all('td')[18].text.strip()

                        self.all_course_sections_df = self.all_course_sections_df.append({'course_section_number': course_section_number,
                                        'course_component': course_component,
                                        'class_nbr': class_nbr,
                                        'instructor_name': instructor_name,
                                        'course_notes': course_notes,
                                        'course_status': course_status,
                                        'course_session': course_session,
                                        'course_start_date': course_start_date,
                                        'course_end_date': course_end_date,
                                        'course_campus': course_campus
                                        }, ignore_index=True)

        except Exception as e:
                print(e)

    def get_all_course_sections_df(self):

        return self.all_course_sections_df

    def get_all_course_sections_with_specific_component_df(self, component: str) -> pd.DataFrame:

        '''Valid component inputs are 'LEC', 'TUT', 'LAB'''

        try:

            df = self.all_course_sections_df.loc[self.all_course_sections_df['course_component'] == component]
            return df

        except Exception as e:
            print(e)

    def get_all_course_sections_not_full_df(self) -> pd.DataFrame:

        try:

            all_course_sections_not_full_df = self.all_course_sections_df.loc[self.all_course_sections_df['course_status'] == 'Not Full']
            return all_course_sections_not_full_df

        except Exception as e:
            print(e)

    def course_section_exists(self, class_nbr: str) -> bool:

        try:
            if not self.all_course_sections_df.empty:

                # Iterates over every course section in all the course sections available
                for index, row in self.all_course_sections_df.iterrows():
                    if row['class_nbr'] == class_nbr:
                        return True

            return False

        except Exception as e:
            print(e)





