from bs4 import BeautifulSoup
import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

class CourseScraper:

    def __init__(self, chromedriverpath, timetable_url):

        self.browser = webdriver.Chrome(chromedriverpath)
        self.browser.get(timetable_url)

    def course_is_not_full(self, course_name: str, course_number: str, class_nbr: str):

        self.browser.find_element_by_id("inputCatalognbr").clear()
        course_number_field = self.browser.find_element_by_id("inputCatalognbr")
        course_number_field.send_keys(course_number)

        self.browser.find_element_by_xpath("/html/body/div/div/div[2]/form/fieldset/div[5]/div/button[2]").click()

        html = self.browser.page_source
        soup = BeautifulSoup(html, 'lxml')

        courses_in_search = soup.find_all('h4')

        for index, course in enumerate(courses_in_search):

            if course_name.lower() in course.text.split(' ')[0].lower() and course_number.lower() in course.text.split(' ')[1].lower():
                course_slot_table = courses_in_search[index].find_next('tbody')
                # get every other because 'tr' in between is table data, not useful
                course_slots = course_slot_table.find_all('tr')[::2]

                for course_slot in course_slots:
                    course_component = course_slot.find_all('td')[1].text
                    class_number = course_slot.find_all('td')[2].text
                    course_status = course_slot.find_all('td')[14].text.strip()

                    if course_component == 'LEC' and course_status == 'Not Full' and class_number == class_nbr:
                        return True

        return False

    def course_exists(self, course_name: str, course_number: str, class_nbr: str):

        self.browser.find_element_by_id("inputCatalognbr").clear()
        course_number_field = self.browser.find_element_by_id("inputCatalognbr")
        course_number_field.send_keys(course_number)

        self.browser.find_element_by_xpath("/html/body/div/div/div[2]/form/fieldset/div[5]/div/button[2]").click()

        html = self.browser.page_source
        soup = BeautifulSoup(html, 'lxml')

        courses_in_search = soup.find_all('h4')

        for index, course in enumerate(courses_in_search):

            if course_name.lower() in course.text.split(' ')[0].lower() and course_number.lower() in course.text.split(' ')[1].lower():
                course_slot_table = courses_in_search[index].find_next('tbody')
                # get every other because 'tr' in between is table data, not useful
                course_slots = course_slot_table.find_all('tr')[::2]

                for course_slot in course_slots:
                    class_number = course_slot.find_all('td')[2].text

                    if class_number == class_nbr:
                        return True

                # return True

        return False


# scraper = CourseScraper("/Users/hamidzargar/PycharmProjects/course_scraper/chromedriver", 'https://studentservices.uwo.ca/secure/timetables/SummerTT/ttindex.cfm')
# print(scraper.course_is_not_full('COMPSCI', '1026A'))



