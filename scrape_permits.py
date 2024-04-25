from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium import webdriver
import requests
import io
import pandas as pd

def scraper_v1():
    url = "https://planning.lacity.org/project-review/environmental-review/published-documents"

    options = webdriver.ChromeOptions()
    driver = webdriver.Chrome()
    driver.get(url)
    i=0
    j=1
    link_urls=[]
    year = []
    while j<=3:
        try:

            for i in range(2, 100, 2):
                page = driver.find_element(by=By.XPATH, value=f"/html/body/div[2]/div[2]/div[2]/div/div[2]/div/div/div/div[1]/div[3]/div/div[1]/table/tbody/tr[{i}]/td[2]/table/tbody/tr[1]/td[2]/a")
                driver.implicitly_wait(20)
                link_urls.append(page.get_attribute("href"))
                year.append(2024-j)
        except:
            j+=1
            new_url = f"/html/body/div[2]/div[2]/div[2]/div/div[2]/div/div/div/div[1]/div[1]/div[1]/select/option[{j}]"
            year = driver.find_element(by=By.XPATH, value=new_url)
            driver.implicitly_wait(20)
            year.click()
            continue

############# extractinf text from pdf ###############

def scraper_ceqa():
    pid = pd.read_csv("CEQA Documents-2500Power.csv")
    pid = pid["SCH Number"].unique()
    options = webdriver.ChromeOptions()
    driver = webdriver.Chrome()
    out = pd.DataFrame()
    for i in pid:
        url = f"https://ceqanet.opr.ca.gov/Project/{i}"
        driver.get(url)
        download_csv = """/html/body/div/div/main/a[1]"""
        file = driver.find_element(by=By.XPATH, value=download_csv)
        driver.implicitly_wait(10)
        response = requests.get(file.get_attribute("href"), stream=True)
        out = pd.concat([out, pd.read_csv(io.StringIO(response.content.decode('unicode_escape')))])


        


   

