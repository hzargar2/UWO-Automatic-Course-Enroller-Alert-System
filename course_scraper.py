from bs4 import BeautifulSoup
import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

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

                if course_name.lower() in course.text.split(' ')[0].lower() and course_number.lower() in course.text.split(' ')[1].lower():
                    course_sections_table = courses_in_search[index].find_next('tbody')

                    # Gets all tr tags in the table (course slots), then slices and gets every other because every other
                    # 'tr' tag is table data, not useful.

                    course_sections = course_sections_table.find_all('tr')[::2]

                    return course_sections

        except Exception as e:
            print(e)

    def course_is_not_full(self, course_name: str, course_number: str, class_nbr: str):

        course_sections = self.__get_all_course_sections(course_name, course_number)

        # Iterates over every course section in all the course sections available

        for course_section in course_sections:
            course_component = course_section.find_all('td')[1].text
            class_number = course_section.find_all('td')[2].text
            course_status = course_section.find_all('td')[14].text.strip()

            # if it is a lecture, not full, and the class nbr matches the user input then its not full and can
            # be enrolled in it

            if course_component == 'LEC' and course_status == 'Not Full' and class_number == class_nbr:
                return True

        return False

    def course_exists(self, course_name: str, course_number: str, class_nbr: str):

        course_sections = self.__get_all_course_sections(course_name, course_number)

        # Iterates over every course section in all the course sections available

        for course_section in course_sections:
            class_number = course_section.find_all('td')[2].text

            # If class nbr matches the user input then the course exits

            if class_number == class_nbr:
                return True

        return False

    def course_lab_components(self, course_name: str, course_number: str):

        course_sections = self.__get_all_course_sections(course_name, course_number)

        # Iterates over every course section in all the course sections available

        for course_section in course_sections:
            course_component = course_section.find_all('td')[1].text

            # if its a LAB section then it returns true

            if course_component == 'LAB':
                return True

        return False

    def course_tutorial_components(self, course_name: str, course_number: str):

        course_sections = self.__get_all_course_sections(course_name, course_number)

        # Iterates over every course section in all the course sections available

        for course_section in course_sections:
            course_component = course_section.find_all('td')[1].text

            #if its a tutorial section then it returns true
            if course_component == 'TUT':
                return True

        return False



# scraper = CourseScraper("/Users/hamidzargar/PycharmProjects/course_scraper/chromedriver", 'https://studentservices.uwo.ca/secure/timetables/SummerTT/ttindex.cfm')
# print(scraper.course_is_not_full('COMPSCI', '1026A'))



