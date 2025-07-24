from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

import pandas as pd
import time
from pathlib import Path

def init_driver(headless=False):
    """
    Initializes and returns a Chrome web driver

    Args:
        headless (bool): If True, executes in headless mode (without visible windows)

    Returns:
        webdriver.Chrome: Selenium instance ready for use
    """
    chrome_options=Options()

    if headless:
        chrome_options.add_argument('--headless-new')
    
    #Stability and performance configurations
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")

    #Ethic configuration of user-agent
    chrome_options.add_argument(
        "user-agent=Mozilla/5.0 (X11; Linux x86_64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/138.0.7204.100 Safari/537.36"
    )

    #Reduce innecesary logs of Selenium/Chrome
    chrome_options.add_argument("--log-level=3")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-logging"])

    # Initialize of the webdriver with webdriver-manager
    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=chrome_options
    )
    return driver

def scrape_page(driver, delay=2):
    """
    Scrapes data of players

    Args:
        driver: Instance of Selenium
        delay: Delay in seconds between pages

    Returns:
        list: List of dictionarys with data of players
    """
    base_url='https://sofifa.com/'

    driver.get(base_url)
    time.sleep(3)

    #Wait user's selection to continue
    while True:
        confirmation=input('Selection completed? (y/n): ')
        if confirmation=='y':
            break
    #Apply choices
    try:
        apply=WebDriverWait(driver,10).until(
            EC.element_to_be_clickable((By.CLASS_NAME, 'full-width'))
        )
        apply.click()
        time.sleep(2)
    except Exception as e:
        print(f'Error applying selections: {str(e)}')
    
    #Start scrapping page by page
    #Find table headers
    table_headers=WebDriverWait(driver,10).until(
        EC.presence_of_element_located((By.CLASS_NAME,'persist-header'))
    )
    headers=table_headers.find_elements(by=By.TAG_NAME, value='th')
    header_list=[]
    for i, header in enumerate(headers):
        if i!=0 and i!=len(headers)-1:
            header_list.append(header.text)

    #Start scrapping rows
    table_rows_list=[]
    flag=True
    pages=1
    while flag:
        try:
            print(f'Starting to scrape page: {pages}')
            table_body=WebDriverWait(driver,10).until(
                EC.presence_of_element_located((By.TAG_NAME,'tbody'))
            )
            table_rows=table_body.find_elements(by=By.TAG_NAME, value='tr')
            for table_row in table_rows:
                row_columns=table_row.find_elements(by=By.TAG_NAME, value='td')
                row_columns_list=[]
                for i, row_column in enumerate(row_columns):
                    if i!=0 and i!=len(row_columns)-1:
                        row_columns_list.append(row_column.text)
                table_rows_list.append(row_columns_list)
                print(f'Page: {pages} - Row: {len(table_rows_list)}: Completed...')
        except Exception as e:
            print(f'Error scrapping rows: {e}')
        try:
            pagination=WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, 'pagination'))
            )
            driver.execute_script('arguments[0].scrollIntoView({block:"center"});', pagination)
            time.sleep(2)
            buttons=pagination.find_elements(by=By.CLASS_NAME, value='button')
            for button in buttons:
                print(button.text)
                if 'Next' in button.text:
                    flag=True
                    button.click()
                    pages+=1
                else: flag=False
        except Exception as e:
            print(f'Error in [Next] button: {e}')
    print(f'Total scrapped pages: {pages}')
    file_name='./data/raw/FC25_Player_Ratings.csv'
    file_path=Path(file_name)
    if file_path.exists():
        previous_df=pd.read_csv(file_name)
    else:
        previous_df=pd.DataFrame(columns=header_list)
    df=pd.DataFrame(table_rows_list, columns=header_list)
    df_final=pd.concat([previous_df,df], ignore_index=True)
    df_final.to_csv(file_name, index=False)
    driver.quit()

scrape_page(init_driver())

