from bs4 import BeautifulSoup
import time, os, config
from selenium import webdriver
from course_scraper import *

import login_credentials_DO_NOT_PUSH


class AutoEnroller(CourseScraper):

    def __init__(self, chromedriverpath: str, student_center_login_url: str, timetable_url: str):

        super().__init__(chromedriverpath, timetable_url)

        self.student_center_login_url = student_center_login_url

    def enroll(self, username: str, password: str, course_name: str, course_number: str, class_nbr: str, dependant_course_component_and_class_nbr_list_1 = None, dependant_course_component_and_class_nbr_list_2 = None):

        try:

            self.set_all_course_sections_df(course_name, course_number)

            # switches to student center login window.
            self.switch_to_window_handle_with_url(self.student_center_login_url)

            print('Logging into student center...')
            username_field = self.browser.find_element_by_id("userid")
            passsword_field = self.browser.find_element_by_id("pwd")

            username_field.send_keys(username)
            passsword_field.send_keys(password)

            # submit button for login info
            self.browser.find_element_by_xpath("/html/body/div[3]/div[2]/div[1]/form/table[1]/tbody/tr[3]/td[2]/input").click()
            time.sleep(2)

            print('Logged in.')

            # switches to correct frame to be ble to access required elements
            iframe = self.browser.find_element_by_xpath('//iframe[@name="TargetContent"]')
            self.browser.switch_to.frame(iframe)

            print('Switched iframes.')

            # 'Enroll in Classes' link button
            self.browser.find_element_by_xpath('/html/body/form/div[5]/table/tbody/tr/td/div/table/tbody/tr[2]/td[2]/div/table/tbody/tr/td/table/tbody/tr[4]/td[2]/div/table/tbody/tr/td/table/tbody/tr[6]/td[2]/div/table/tbody/tr[2]/td/table/tbody/tr[4]/td[2]/div/table/tbody/tr[2]/td/table/tbody/tr[3]/td[2]/div/span/a').click()
            time.sleep(2)

            print('Enroll in Classes clicked.')
            # class nbr field fill in and submit
            class_nbr_field = self.browser.find_element_by_id('DERIVED_REGFRM1_CLASS_NBR')
            class_nbr_field.send_keys(class_nbr)
            self.browser.find_element_by_xpath('/html/body/form/div[5]/table/tbody/tr/td/div/table/tbody/tr[9]/td[2]/div/table/tbody/tr/td/table/tbody/tr[4]/td[2]/div/table/tbody/tr[2]/td/table/tbody/tr[2]/td[2]/div/table/tbody/tr/td/table/tbody/tr[4]/td[2]/div/table/tbody/tr/td/table/tbody/tr[2]/td[2]/div/a/span/input').click()
            time.sleep(2)

            print('Class nbr submitted')

            # get current page html
            html = self.browser.page_source
            soup = BeautifulSoup(html, 'lxml')

            # need extra step for enrollment if the course has dependant course components like a lab, tut, or lec. A
            # course can have all 3 components so need to account for the case that a course has all 3

            # if self.has_dependant_course_components():

            for dependant_course_component_and_class_nbr in [dependant_course_component_and_class_nbr_list_1, dependant_course_component_and_class_nbr_list_2]:
                if dependant_course_component_and_class_nbr is not None:

                    table = soup.find("table", {"id": "SSR_CLS_TBL_R1$scroll$0"})
                    tr_tags = table.find_all('tr')

                    #get table title, tells us what component the table is for (Labratory, Tutorial, or Lecture)
                    table_title = tr_tags[0].text.strip().split()
                    table_title_component = table_title[1]

                    if dependant_course_component_and_class_nbr

                    # get the course components in the table, from 'tr' tag number 4 and on is the useful info, ones before
                    # are just table structure data

                    for tr_tag in tr_tags[4:]:


                        print('<{0}>'.format(' '.join(tr_tag.text.split())))

        except Exception as e:
            print(e)

    def has_dependant_course_components(self):
        if self.all_course_sections_df['course_component'].nunique() > 1:
            return True
        else:
            return False

    def get_dependant_course_components(self, class_nbr: str):

        try:
            current_course_component = None

            for index, row in self.all_course_sections_df:
                if row['class_nbr'] == class_nbr:
                    current_course_component = row['course_component']
                    break

            if current_course_component is not None:
                df = self.all_course_sections_df.loc[self.all_course_sections_df['course_status'] != current_course_component]
                return df

        except Exception as e:
            print(e)


'''TEST CASE'''

# scraper = CourseScraper(os.path.join(os.path.dirname(__file__), "chromedriver_mac_81.0.4044.138"), config.urls_dict['Summer'])
auto_enroller = AutoEnroller(os.path.join(os.path.dirname(__file__), "chromedriver_mac_81.0.4044.138"), config.urls_dict['Student_Center_Login_Page'], config.urls_dict['Summer'])

### DO NOT PUSH WITH LOGIN CREDENTIALS
auto_enroller.enroll(login_credentials_DO_NOT_PUSH.login_creds['username'], login_credentials_DO_NOT_PUSH.login_creds['password'], 'COMPSCI', '1027B', '1194')




