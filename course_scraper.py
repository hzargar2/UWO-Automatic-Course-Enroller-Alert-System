from bs4 import BeautifulSoup
import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import pandas as pd

pd.set_option('display.max_rows', 500)
pd.set_option('display.max_columns', 500)
pd.set_option('display.width', 1000)

class CourseScraper:

    def __init__(self, chromedriverpath, timetable_url):

        self.browser = webdriver.Chrome(chromedriverpath)
        self.browser.get(timetable_url)

    def __get_all_course_sections(self, course_name: str, course_number: str):

        try:
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

                    return course_sections

        except Exception as e:
            print(e)


    def __get_df_for_all_course_sections_with_component(self, course_name: str, course_number: str, component: str) -> pd.DataFrame:

        '''Valid component inputs are 'LEC', 'TUT', 'LAB'''

        try:

            course_sections = self.__get_all_course_sections(course_name, course_number)

            df = pd.DataFrame(columns=['course_section_number', 'course_component','class_nbr','instructor_name',
                                       'course_notes','course_status','course_session','course_start_date','course_end_date',
                                       'course_campus'])

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

                # if it is a lecture, not full, and the class nbr matches the user input then its not full and can
                # be enrolled in it

                if course_component == component:
                    df = df.append({'course_section_number':course_section_number,
                                    'course_component':course_component,
                                    'class_nbr':class_nbr,
                                    'instructor_name':instructor_name,
                                    'course_notes':course_notes,
                                    'course_status':course_status,
                                    'course_session':course_session,
                                    'course_start_date':course_start_date,
                                    'course_end_date':course_end_date,
                                    'course_campus':course_campus
                                   }, ignore_index=True)
                    return df

            return df

        except Exception as e:
            print(e)


    def course_section_exists(self, course_name: str, course_number: str, class_nbr: str):

        course_sections = self.__get_all_course_sections(course_name, course_number)

        # Iterates over every course section in all the course sections available
        if course_sections is not None:

            for course_section in course_sections:
                class_number = course_section.find_all('td')[2].text

                # If class nbr matches the user input then the course exits

                if class_number == class_nbr:
                    return True

        return False

    def lecture_is_not_full(self, course_name: str, course_number: str, class_nbr: str):

        df = self.__get_df_for_all_course_sections_with_component(course_name, course_number, 'LEC')

        for index, row in df.iterrows():
            if class_nbr == row['class_nbr'] and 'Not Full' == row['course_status']:
                return True

        return False

    def get_lab_components(self, course_name: str, course_number: str):

        df = self.__get_df_for_all_course_sections_with_component(course_name, course_number, 'LAB')
        return df

    def get_tutorial_components(self, course_name: str, course_number: str):

        df = self.__get_df_for_all_course_sections_with_component(course_name, course_number, 'TUT')
        return df

    def get_lecture_components(self, course_name: str, course_number: str):

        df = self.__get_df_for_all_course_sections_with_component(course_name, course_number, 'LEC')
        return df






# scraper = CourseScraper("/Users/hamidzargar/PycharmProjects/course_scraper/chromedriver", 'https://studentservices.uwo.ca/secure/timetables/SummerTT/ttindex.cfm')
# df = scraper.get_lecture_components('COMPSCI','1026A')
# print(df.head(10))





