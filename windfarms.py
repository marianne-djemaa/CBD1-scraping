#!/usr/bin/python
# coding: utf-8
# marianne

# from __future__ import unicode_literals
# import time
import io
import os
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, ElementClickInterceptedException, TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from w3lib.html import replace_entities
import json

def find_countries(webdriver, url):
    country2code = {}
    webdriver.get(url)
    # time.sleep(3)
    # countries = webdriver.find_elements_by_tag_name('option')
    countries = WebDriverWait(driver, 9).until(EC.presence_of_all_elements_located((By.TAG_NAME, 'option')))
    for item in countries:
        country_name = clean_up_str(item.text)
        code = item.get_attribute('value')
        country2code[country_name] = code
    return country2code

def make_country_url(default_project_code):
    return "http://www.4coffshore.com/windfarms/windfarms.aspx?windfarmId="+default_project_code

# def wait_to_click(x, t):
#     try:
#         x.click()
#     except ElementClickInterceptedException:
#         time.sleep(t)
#         if t < 4:
#             wait_to_click(x, t*2)
#         wait_to_click(x, t)

def get_projects(driver, current_page_number): #est appele avec un driver ou la page est deja ouverte
    project2link = {}
    # time.sleep(9)
    # html_projects_table = driver.find_element_by_id("ctl00_Body_Main_Content_ucSubscriberTools_WindfarmIndex2_GridView2")

    html_projects_table = WebDriverWait(driver, 9).until(EC.presence_of_element_located((By.ID, "ctl00_Body_Main_Content_ucSubscriberTools_WindfarmIndex2_GridView2")))
    html_projects_links = html_projects_table.find_elements_by_class_name("linkWF")
    for project in html_projects_links:
        project_name = clean_up_str(project.text)
        project_url = project.get_attribute('href')
        project2link[project_name] = project_url
    try:
        page_links_list = driver.find_element_by_class_name("gvwfsPager")
        next_page_number = current_page_number + 1
        # next_page_link = page_links_list.find_element_by_link_text(str(next_page_number))
        # # time.sleep(1)
        next_page_link = WebDriverWait(driver, 17).until(EC.element_to_be_clickable((By.LINK_TEXT, str(next_page_number))))
        next_page_link.click()
        # wait_to_click(next_page_link, 1)
        # time.sleep(3)
        # print json.dumps(project2link)
        project2link.update(get_projects(driver, next_page_number))
    except (NoSuchElementException, TimeoutException):
        print "...done retrieving project addresses for this country"
    return project2link

def clean_up_str(s):
    s = replace_entities(s)
    split_s = s.split("<em>")
    s = "".join(split_s)
    split_s = s.split("</em>")
    s = "".join(split_s)
    split_s = s.split("<br>")
    s = "\n".join(split_s)
    return s.strip()

def get_role(raw_role):
    try:
        role = clean_up_str(raw_role.text)
        if role == "":
            role = raw_role.get_attribute('innerHTML')
        # project2details[category].append([role, {}])
    except NoSuchElementException:
        role = ""
    return clean_up_str(role)

def get_org_name(raw_org_info):
    org_name = clean_up_str(raw_org_info.text)
    if org_name == "":
        try:
            org_name = raw_org_info.find_element_by_css_selector("a").get_attribute('innerHTML')
        except NoSuchElementException:
            org_name = raw_org_info.get_attribute('innerHTML')
    return clean_up_str(org_name)

def get_org_url(raw_org_info, raw_job_description):#TODO compléter
    try:
        org_url = raw_org_info.find_element_by_tag_name("a").get_attribute("href")
    except NoSuchElementException:
        try:
            org_url = raw_job_description.find_element_by_tag_name("a").get_attribute("href")
        except NoSuchElementException:
            org_url = ""
    return org_url

def get_job_description(raw_job_description):
    try:
        job_description = raw_job_description.text
        if job_description == "":
            try:
                job_description =  raw_job_description.find_element_by_tag_name("a").get_attribute('innerHTML')
            except NoSuchElementException:
                job_description =  raw_job_description.find_element_by_tag_name("span").get_attribute('innerHTML')
    except NoSuchElementException:
        job_description = ""
    return clean_up_str(job_description)

# if $value is not the empty string, add it to dictionary d with key $key
def add_if_not_empty(key, value, d, category = "", role = ""):
    if value != "":
        d[key] = value
    else:
        print category, ">", role, ">", key, "couldn't be found"


def get_project_details(webdriver, project_url, country_name, project_name, filename):
    project2details = {}
    driver.get(project_url)
    # time.sleep(9)
    # supply_chain_url = driver.find_element_by_id("ctl00_Body_Page_SubMenu_hypSupplychain").get_attribute("href")
    supply_chain_url = WebDriverWait(driver, 9).until(EC.presence_of_element_located((By.ID, "ctl00_Body_Page_SubMenu_hypSupplychain"))).get_attribute("href")
    driver.get(supply_chain_url)
    # time.sleep(9)
    # details_raw = driver.find_element_by_id("multiOpenAccordion")
    details_raw = WebDriverWait(driver, 9).until(EC.presence_of_element_located((By.ID, "multiOpenAccordion")))
    categories = details_raw.find_elements_by_tag_name("h3")
    details_as_list = details_raw.find_elements_by_css_selector("table.table.table-striped")
    for i in range(0, len(categories)):
        category = clean_up_str(categories[i].text.split(" (")[0])
        project2details[category] = []
        roles = details_as_list[i].find_elements_by_css_selector("span.gvshRole")
        orgs = details_as_list[i].find_elements_by_css_selector("div.gvshOrg")
        descriptions = details_as_list[i].find_elements_by_css_selector("div.gvshDesc")
        for j in range(0, len(roles)):
            role = get_role(roles[j])
            if role == "":
                print "some role name couldn't be retrieved. Jumping to next role/organization pair"
                continue
            org_info_dict = {}
            org_name = get_org_name(orgs[j])
            add_if_not_empty("org_name", org_name, org_info_dict, category, role)
            org_url = get_org_url(orgs[j], descriptions[j])
            add_if_not_empty("url", org_url, org_info_dict, category, role)
            job_description = get_job_description(descriptions[j])
            add_if_not_empty("job_description", job_description, org_info_dict, category, role)
            project2details[category].append([role, org_info_dict])
            append_line_to_file(",".join([country_name, project_name, category, role, "|".join(org_info_dict.values())]), filename)
    return project2details

def write_dict_to_file(d, filename):
    if not os.path.exists(filename):
        os.makedirs(os.path.dirname(filename))
    with io.open(filename, mode="w", encoding="utf-8") as f: # could be used to start again where script failed
        f.write(json.dumps(d, indent=1))#, encoding="utf-8")) #dict2json(d))

def append_dict_to_file(d, filename):
    if not os.path.exists(os.path.dirname(filename)):
        os.makedirs(os.path.dirname(filename))
    with io.open(filename, mode="a", encoding="utf8") as f: # could be used to start again where script failed
        f.write(json.dumps(d, indent=1, ensure_ascii=False)) #ensure_ascii=False, encoding="utf8")) #dict2json(d))

def append_line_to_file(l, filename):
    if not os.path.exists(os.path.dirname(filename)):
        os.makedirs(os.path.dirname(filename))
    with io.open(filename, mode="a", encoding="utf8") as f: # could be used to start again where script failed
        f.write(l+'\n') #ensure_ascii=False, encoding="utf8")) #dict2json(d))

def clear_file(filename):
    if os.path.exists(filename):
        open(filename, 'w').close()


if __name__ == '__main__':
    start_url = "http://www.4coffshore.com/windfarms/windfarms.aspx?windfarmId=AL01"
    driver = webdriver.Firefox()
    # driver.implicitly_wait(10) #uncomment if script keeps failing
    json_results = 'out/all_windfarms.json'
    csv_results = 'out/all_windfarms.csv'
    clear_file(json_results)
    clear_file(csv_results)
    print "Retrieving all country URLs..."
    country2code = find_countries(driver, start_url)
    print "...done"
    # write_dict_to_file(country2code, 'country2code.json') # could be used to start again where script failed
    # country2code = {"France" : "FR34"} #test
    # country2code = {"Lithuania" : "LT01"} #test
    total_country_count = len(country2code.keys())
    country_number = 0
    total_project_count = 0
    for (country_name, default_project_code) in country2code.iteritems():
        country_number += 1
        project2link = {}
        project2details = {}
        print "Retrieving project list for country:", country_name, "(country", country_number, "out of", total_country_count, "countries)"
        driver.get(make_country_url(default_project_code))
        try:
            project2link = get_projects(driver, 1)
            # append_dict_to_file(project2link, 'project2link.json') # could be used to start again where script failed
        except (NoSuchElementException, TimeoutException):
            print "WARNING: this information is not available; proceeding to next country"
            continue
        # write_dict_to_file(project2link, )
        country_project_count = len(project2link.keys())
        total_project_count += country_project_count
        project_number = 0
        for (project_name, project_url) in project2link.iteritems():
            project_number += 1
            print "Starting to scrape project", project_name, '('+project_url+")", "\n\tproject", project_number, "out of", country_project_count, "projects for country", country_name
            # print project_name,":",project_url        #test
            project2details = get_project_details(driver, project_url, country_name, project_name, csv_results)
            print "...done"
            append_dict_to_file({'country' : country_name, 'project' : project_name, 'supply chain': project2details}, json_results) # writing to final file takes place inside loop so that if the script fails, everything already scraped is saved
            # break #testC:
        # break #test
    print "Total number of countries scraped:", total_country_count
    print "Total number of projects scraped:", total_project_count

