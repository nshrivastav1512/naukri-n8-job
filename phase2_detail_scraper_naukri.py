# phase2_detail_scraper_naukri.py
# Phase 2: Scrapes detailed information for individual job links from Naukri.com.

import time
import traceback
import logging
from datetime import datetime
import pandas as pd
import re 
from bs4 import BeautifulSoup
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException, ElementClickInterceptedException

# Import helpers from Phase 1
from phase1_list_scraper_naukri import setup_selenium_driver, get_random_delay, parse_posted_ago_naukri

# --- Helper Functions ---
import re # Make sure 'import re' is at the top of the file

def clean_text_for_excel(text):
    """Removes illegal characters for Excel from a string."""
    if not isinstance(text, str):
        return text
    # Excel's XML format forbids characters in the 0x00-0x1F range, except for tab (0x09), newline (0x0A), and carriage return (0x0D).
    # We will remove all characters in the 0x00-0x08, 0x0B-0x0C, and 0x0E-0x1F ranges.
    return re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f]', '', text)

def safe_get_text(element, default='N/A'):
    """Safely get text from a Selenium element, returning a default value on failure."""
    try:
        text = element.text.strip()
        return text if text else default
    except (NoSuchElementException, Exception):
        return default

def safe_get_attribute(element, attribute, default='N/A'):
    """Safely get an attribute from a Selenium element, returning a default value on failure."""
    try:
        attr = element.get_attribute(attribute) or ""
        return attr if attr else default
    except (NoSuchElementException, Exception):
        return default

def clean_html_for_text(html_content: str) -> str:
    """Uses BeautifulSoup to extract clean plain text from HTML content."""
    if not html_content or pd.isna(html_content): return ""
    try:
        # Use lxml for better parsing of potentially broken HTML
        soup = BeautifulSoup(html_content, 'lxml')
        return soup.get_text(separator=' ', strip=True)
    except Exception:
        # Fallback for any other errors
        return ""


# In phase2_detail_scraper_naukri.py

def scrape_naukri_job_details(driver: WebDriver, job_url: str, config: dict) -> dict:
    """Navigates to a Naukri job URL and scrapes all planned detailed information."""
    selectors = config['selectors']
    wait_time = config['selenium']['wait_time_long']
    
    details = {key: pd.NA for key in config['excel_schema']['columns_list']}
    details.update({
        'Date Scraped Detailed': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'Scraping Issues (Phase 2)': '',
        '_scrape_successful': False
    })
    
    issues = []

    try:
        driver.get(job_url)
        main_container = WebDriverWait(driver, wait_time).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div.styles_jdc__content__EZJMQ"))
        )
        time.sleep(get_random_delay(config['selenium'], "short"))

        # --- Helper for extraction using either CSS or XPATH ---
        def extract_text(selector_key, by=By.CSS_SELECTOR):
            try:
                selector = selectors[selector_key]
                return safe_get_text(main_container.find_element(by, selector))
            except (NoSuchElementException, KeyError):
                issues.append(f"Selector_NotFound: {selector_key}")
                return 'N/A'

        # --- Handle "Read More" click ---
        try:
            read_more_button = driver.find_element(By.CSS_SELECTOR, selectors['details_about_company_read_more_button'])
            if read_more_button.is_displayed():
                driver.execute_script("arguments[0].click();", read_more_button)
                time.sleep(0.5)
        except (NoSuchElementException, ElementClickInterceptedException, KeyError):
            pass

        # --- Data Extraction (Using CORRECTED Keys and Methods) ---
        details['Job Title'] = extract_text('details_job_title')
        details['Company Name'] = extract_text('details_company_name')
        details['Experience Required'] = extract_text('details_experience_required')
        details['Salary Indication (from Card/Filters)'] = extract_text('details_salary')
        details['Location(s)'] = extract_text('details_locations')
        
        # --- START OF NEW CONFIG-DRIVEN SOLUTION FOR APPLY BUTTON --- Version 3
        details['Is Already Applied'] = False
        details['Apply Button Type'] = '' # Default to empty string

        try:
            # First, find the common container for the apply buttons using the selector from config
            button_container = main_container.find_element(By.CSS_SELECTOR, selectors["details_apply_button_container"])
            
            # Now, check for each state within that container in order of priority
            # 1. Check if already applied
            try:
                applied_span = button_container.find_element(By.ID, selectors["details_already_applied_by_id"])
                details['Is Already Applied'] = True
                details['Apply Button Type'] = safe_get_text(applied_span, 'Applied')
            except NoSuchElementException:
                # 2. If not applied, check for "Apply on company site"
                try:
                    company_site_button = button_container.find_element(By.ID, selectors["details_apply_on_company_site_by_id"])
                    details['Apply Button Type'] = safe_get_text(company_site_button, 'Apply on company site')
                except NoSuchElementException:
                    # 3. If neither of the above, check for the standard "Apply" button
                    try:
                        apply_button = button_container.find_element(By.ID, selectors["details_apply_button_by_id"])
                        details['Apply Button Type'] = safe_get_text(apply_button, 'Apply')
                    except NoSuchElementException:
                        # 4. If none are found, log it as an issue
                        issues.append("Info: ApplyButton_State_NotFound")
                        details['Apply Button Type'] = 'Not Found' # Explicitly state it wasn't found

        except (NoSuchElementException, KeyError):
            issues.append("CRITICAL: ApplyButton_Container_NotFound")
            details['Apply Button Type'] = 'Error - Container Missing'
        # --- END OF NEW CONFIG-DRIVEN SOLUTION ---
        
        # Use By.XPATH for the selectors we changed
        details['Posted Ago Text Detailed'] = extract_text('details_posted_ago_xpath', by=By.XPATH)
        details['Posted Days Ago (Detailed)'] = parse_posted_ago_naukri(details['Posted Ago Text Detailed'])
        details['Openings'] = extract_text('details_openings_xpath', by=By.XPATH)
        details['Applicants'] = extract_text('details_applicants_xpath', by=By.XPATH)
        
        try:
            highlight_elements = main_container.find_elements(By.CSS_SELECTOR, selectors['details_job_highlights_list'])
            details['Job Highlights'] = "\n".join([safe_get_text(el) for el in highlight_elements])
        except (NoSuchElementException, KeyError): pass

        # ... (Job Match Score logic is fine) ...
        for item in main_container.find_elements(By.CSS_SELECTOR, selectors['details_match_score_container']):
            text = item.text.lower()
            is_checked = 'check_circle' in safe_get_attribute(item.find_element(By.TAG_NAME, 'i'), 'class')
            if 'early applicant' in text: details['Match: Early Applicant'] = is_checked
            elif 'keyskills' in text: details['Match: Keyskills'] = is_checked
            elif 'location' in text: details['Match: Location'] = is_checked
            elif 'work experience' in text: details['Match: Work Experience'] = is_checked

        try:
            jd_element = main_container.find_element(By.CSS_SELECTOR, selectors['details_job_description_html'])
            details['Full Job Description HTML'] = safe_get_attribute(jd_element, 'innerHTML')
            details['Full Job Description Plain Text'] = clean_html_for_text(details['Full Job Description HTML'])
        except (NoSuchElementException, KeyError):
            issues.append("CRITICAL: JD_HTML_Not_Found")
            details['Scraping Issues (Phase 2)'] = ", ".join(issues)
            return details

        # Use By.XPATH for the selectors we changed
        details['Role (Detailed)'] = extract_text('details_role_xpath', by=By.XPATH)
        details['Industry (Detailed)'] = extract_text('details_industry_xpath', by=By.XPATH)
        details['Functional Area/Department (Detailed)'] = extract_text('details_department_xpath', by=By.XPATH)
        details['Employment Type (Detailed)'] = extract_text('details_employment_type_xpath', by=By.XPATH)
        details['Role Category (Detailed)'] = extract_text('details_role_category_xpath', by=By.XPATH)
        details['Company HQ Address'] = extract_text('details_company_hq_address_xpath', by=By.XPATH)
        
        
        # --- START OF NEW CONFIG-DRIVEN SOLUTION FOR COMPANY WEBSITE --- Version 3
        try:
            # Use the corrected XPath selector from the config dictionary
            website_selector_xpath = selectors["details_company_official_website_link_xpath"]
            
            # Search the whole driver for better reliability
            website_element = driver.find_element(By.XPATH, website_selector_xpath)
            
            website_url = safe_get_attribute(website_element, 'href')
            # If a URL is found, use it. Otherwise, mark it clearly as 'Not Listed'.
            details['Company Website (Official)'] = website_url if website_url != 'N/A' else 'Not Listed'
            
        except (NoSuchElementException, KeyError):
            # This is the expected outcome when a company doesn't list a website.
            details['Company Website (Official)'] = 'Not Listed'
            issues.append("Info: CompanyWebsite_NotFoundOnPage")
        # --- END OF NEW CONFIG-DRIVEN SOLUTION ---

        # ... (Rest of the function is mostly fine with CSS selectors) ...
        try:
            edu_container = main_container.find_element(By.CSS_SELECTOR, selectors['details_education_container'])
            details['Education Requirements (Detailed)'] = edu_container.text.replace('\n', ' ').replace('Education', '').strip()
        except (NoSuchElementException, KeyError): pass
        
        try:
            skills_container = main_container.find_element(By.CSS_SELECTOR, selectors['details_key_skills_container'])
            details['Key Skills (from detail page)'] = ", ".join([el.text for el in skills_container.find_elements(By.TAG_NAME, 'a')])
        except (NoSuchElementException, KeyError): pass

        details['About Company (Detailed)'] = extract_text('details_about_company_overview_text')
        if details['About Company (Detailed)'] == 'N/A':
            details['About Company (Detailed)'] = extract_text('details_about_company_fallback')
        
        details['Follower Count'] = extract_text('details_follower_count')
        
        def extract_list_to_string(selector_key):
            try:
                elements = main_container.find_elements(By.CSS_SELECTOR, selectors[selector_key])
                return ", ".join([safe_get_text(el, default="").strip() for el in elements if el.text.strip()])
            except (NoSuchElementException, KeyError): return "N/A"
            
        details['Company Info Tags'] = extract_list_to_string('details_company_info_tags_list')
        details['Awards & Recognitions'] = extract_list_to_string('details_awards_list')
        details['Benefits & Perks'] = extract_list_to_string('details_benefits_list')
        
        try:
            highlight_elements = main_container.find_elements(By.CSS_SELECTOR, selectors['details_key_company_highlights_list'])
            highlights = [el.text.replace('\n', ': ') for el in highlight_elements]
            details['Key Company Highlights'] = ", ".join(highlights)
        except (NoSuchElementException, KeyError): pass

        details['_scrape_successful'] = True

    except (TimeoutException, WebDriverException) as e:
        logging.error(f"Major scraping error on page {job_url}: {type(e).__name__}", exc_info=False)
        issues.append(f"CRITICAL_{type(e).__name__}")
    
    details['Scraping Issues (Phase 2)'] = ", ".join(issues) if issues else "None"
    return details


def process_excel_for_details(driver: WebDriver, config: dict):
    excel_filepath = config['paths']['excel_filepath']
    status_new = config['status']['NEW']
    status_processing = config['status']['PROCESSING_DETAILS']
    status_ready_for_ai = config['status']['READY_FOR_AI']
    status_scrape_failed = config['status']['FAILED_SCRAPE_DETAILS']
    status_invalid_link = config['status']['INVALID_LINK']
    
    cfg_phase2 = config['phase2']
    overwrite_data = cfg_phase2.get('overwrite_phase1_data', True)
    
    logging.info(f"Starting detailed scraping. Overwrite Phase 1 data: {overwrite_data}")
    
    try:
        df = pd.read_excel(excel_filepath, engine='openpyxl')
        all_expected_columns = config['excel_schema']['columns_list']
        for col in all_expected_columns:
            if col not in df.columns: df[col] = pd.NA
        df = df.reindex(columns=all_expected_columns)

        statuses_to_process = [status_new]
        if config['workflow'].get('retry_failed_phase2', True):
            statuses_to_process.append(status_scrape_failed)
        
        rows_to_process_mask = df['Status'].isin(statuses_to_process)
        rows_to_process_idx = df[rows_to_process_mask].index
        num_to_process = len(rows_to_process_idx)
        logging.info(f"Found {num_to_process} rows to process with status in {statuses_to_process}.")

        if num_to_process == 0: return True

        processed_count = 0
        for index in rows_to_process_idx:
            job_link = df.loc[index, 'Job Detail Page URL']
            if pd.isna(job_link) or not str(job_link).startswith('http'):
                df.loc[index, 'Status'] = status_invalid_link
                continue

            logging.info(f"--- Processing Row {index + 2}/{len(df)+1} | Job: '{df.loc[index, 'Job Title']}' ---")
            df.loc[index, 'Status'] = status_processing
            
            scraped_details = scrape_naukri_job_details(driver, job_link, config)
            
            if scraped_details.get('_scrape_successful'):
                for col, value in scraped_details.items():
                    if col in df.columns and not col.startswith('_'):
                        if overwrite_data or pd.isna(df.loc[index, col]):
                            df.loc[index, col] = value
                df.loc[index, 'Status'] = status_ready_for_ai
                logging.info(f"  Successfully processed. Status -> {status_ready_for_ai}")
            else:
                df.loc[index, 'Status'] = status_scrape_failed
                df.loc[index, 'Scraping Issues (Phase 2)'] = scraped_details.get('Scraping Issues (Phase 2)')
                logging.error(f"  Scraping failed. Issues: {df.loc[index, 'Scraping Issues (Phase 2)']}")

            processed_count += 1
            if processed_count % cfg_phase2['save_interval'] == 0:
                logging.info(f"Saving progress to Excel after {processed_count} rows...")
                df_copy_to_save = df.copy()
                # 1. First, handle all missing values.
                df_copy_to_save = df_copy_to_save.fillna('')
                # 2. Now, clean the object columns.
                for col in df_copy_to_save.select_dtypes(include=['object']).columns:
                    df_copy_to_save[col] = df_copy_to_save[col].astype(str).apply(clean_text_for_excel)
                df_copy_to_save.to_excel(excel_filepath, index=False, engine='openpyxl')
                # --- END OF MODIFICATION --- version 4
        
        logging.info("Finished processing all designated rows. Performing final save...")
        # 1. First, handle all missing values.
        df_final_copy = df.copy()
        df_final_copy = df_final_copy.fillna('')
        # 2. Now, clean the object columns. version 4
        for col in df_final_copy.select_dtypes(include=['object']).columns:
            df_final_copy[col] = df_final_copy[col].astype(str).apply(clean_text_for_excel)
        df_final_copy.to_excel(excel_filepath, index=False, engine='openpyxl')
        # --- END OF MODIFICATION ---
        return True
    
    except FileNotFoundError:
        logging.error(f"Excel file not found: '{excel_filepath}'.")
        return False
    except Exception as e:
        logging.critical(f"Critical error in Phase 2 processing: {e}", exc_info=True)
        return False


def run_phase2_detail_scraping(config: dict) -> bool:
    """Main function to execute Phase 2."""
    logging.info("Initiating Phase 2: Naukri Job Detail Scraping")
    driver = None
    try:
        driver = setup_selenium_driver(config)
        if not driver:
            logging.critical("Failed to setup Selenium driver for Phase 2.")
            return False
        
        return process_excel_for_details(driver, config)
    
    except WebDriverException as e:
        logging.critical(f"WebDriver error during Phase 2: {e}")
        return False
    except Exception as e:
        logging.critical(f"An unexpected critical error occurred in Phase 2: {e}", exc_info=True)
        return False
    finally:
        logging.info("Phase 2 run finished.")