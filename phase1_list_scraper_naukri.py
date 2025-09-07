# phase1_list_scraper_naukri.py
# Phase 1: Scrapes basic job listing information from Naukri.com search results.

import time
import os
import traceback
import re
import logging
import random
from urllib.parse import quote_plus, urlencode
from datetime import datetime
import pandas as pd
import zipfile # To handle BadZipFile exception
import re 
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException,
    NoSuchElementException,
    StaleElementReferenceException,
    WebDriverException,
    ElementNotInteractableException
)

import re # Make sure 'import re' is at the top of the file

def clean_text_for_excel(text):
    """Removes illegal characters for Excel from a string."""
    if not isinstance(text, str):
        return text
    # Excel's XML format forbids characters in the 0x00-0x1F range, except for tab (0x09), newline (0x0A), and carriage return (0x0D).
    # We will remove all characters in the 0x00-0x08, 0x0B-0x0C, and 0x0E-0x1F ranges.
    return re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f]', '', text)

# --- Helper Functions ---
def get_random_delay(config_selenium, delay_type="medium"):
    """Generates a random delay based on selenium config settings."""
    if not config_selenium.get('enable_random_delays', True):
        return 0.1

    if delay_type == "short":
        base = config_selenium.get('delay_short_base', 1.0)
        variance = config_selenium.get('delay_short_variance', 0.5)
    elif delay_type == "long":
        base = config_selenium.get('delay_long_base', 3.0)
        variance = config_selenium.get('delay_long_variance', 1.5)
    else: # medium
        base = config_selenium.get('delay_medium_base', 2.0)
        variance = config_selenium.get('delay_medium_variance', 1.0)
    return base + random.uniform(0, variance)

def setup_selenium_driver(master_config: dict):
    """Connects Selenium to an existing Chrome instance using master_config."""
    config_selenium = master_config.get('selenium')
    if not config_selenium:
        logging.error("Selenium configuration ('selenium' key) not found in the master config.")
        return None

    driver_path = config_selenium.get('chromedriver_path')
    port = config_selenium.get('debugger_port')

    if not driver_path: logging.error("'chromedriver_path' not found in selenium config."); return None
    if port is None: logging.error("'debugger_port' not found in selenium config."); return None

    max_retries = 3; retry_count = 0
    logging.info(f"Attempting to connect to existing Chrome on port {port} using ChromeDriver: {driver_path}")

    if not os.path.exists(driver_path): logging.error(f"ChromeDriver not found at: {driver_path}"); return None

    service = Service(executable_path=driver_path)
    options = webdriver.ChromeOptions()
    options.add_experimental_option("debuggerAddress", f"localhost:{port}")
    options.add_argument("--log-level=3")
    # options.add_experimental_option('excludeSwitches', ['enable-logging']) # Suppress DevTools message

    while retry_count < max_retries:
        try:
            driver = webdriver.Chrome(service=service, options=options)
            logging.info("Successfully connected to Chrome debugger.")
            time.sleep(0.5) # Brief pause to ensure connection stability
            try:
                current_url = driver.current_url # Check if browser is responsive
                logging.info(f"Initial page in connected browser: {current_url}")
            except WebDriverException as url_err:
                 logging.warning(f"Connected, but encountered error getting current URL: {url_err}. Browser might be initializing or unresponsive.")
            return driver
        except WebDriverException as e:
            is_conn_err = any(msg in str(e).lower() for msg in ["failed to connect", "timed out", "cannot connect", "connection refused"])
            if is_conn_err:
                retry_count += 1
                logging.error(f"WebDriverException connecting (Attempt {retry_count}/{max_retries}): {e}")
                if retry_count >= max_retries:
                    logging.error("Max retries reached. Ensure Chrome started with debugging on correct port & other instances closed.")
                    return None
                logging.info(f"Retrying connection in {10 * retry_count} seconds...")
                time.sleep(10 * retry_count)
            else:
                logging.error(f"Non-connection WebDriverException during setup: {e}")
                return None
        except Exception as e:
            logging.error(f"Unexpected error during Selenium setup: {e}", exc_info=True)
            return None
    return None


def get_label_for_selected_code(options_list: list, selected_code_str: str) -> str:
    """Helper to find a label for a selected code within a filter's options list."""
    for option in options_list:
        if str(option.get("id")) == selected_code_str:
            return option.get("label", selected_code_str) # Fallback to code if label missing
    return selected_code_str # Fallback if code not in options

# --- URL Construction ---
# phase1_list_scraper_naukri.py

def construct_naukri_search_url(user_filters: dict, general_settings: dict, page_number: int = 1) -> str:
    """
    Constructs the Naukri search URL based on user_filters from naukri_search_config.json
    and general_settings, including pagination.
    """
    base_naukri_url = general_settings.get("naukri_base_search_url", "https://www.naukri.com/").rstrip('/')
    search_settings = user_filters.get("search_settings", {})
    keywords_str = search_settings.get("search_keywords", "jobs")
    location_str = search_settings.get("search_base_location_text", "")

    # --- NEW LOGIC: Build the URL Path ---

    # 1. Sanitize and join keywords for the path (e.g., "SQL Support, Data Analyst" -> "sql-support-data-analyst")
    keyword_slug_parts = [part.strip() for part in keywords_str.split(',') if part.strip()]
    keyword_path = "-".join(keyword_slug_parts).lower()
    keyword_path = re.sub(r'[^a-z0-9]+', '-', keyword_path).strip('-')
    if not keyword_path:
        keyword_path = "jobs" # Fallback if keywords are empty
    else:
        keyword_path += "-jobs"

    # 2. Sanitize and add location to the path (e.g., "pune" -> "in-pune")
    location_path = ""
    if location_str:
        location_slug = location_str.lower().strip()
        location_slug = re.sub(r'[^a-z0-9]+', '-', location_slug).strip('-')
        if location_slug:
            location_path = f"-in-{location_slug}"

    # 3. Combine keywords, location, and page number for the final path
    # Page 1: /sql-support-jobs-in-pune
    # Page 2: /sql-support-jobs-in-pune-2
    url_path = f"/{keyword_path}{location_path}"
    if page_number > 1:
        url_path += f"-{page_number}"

    # --- NEW LOGIC: Build the Query Parameters for Filters ---
    query_params = {}
    active_filter_logs_for_page_1_only = (page_number == 1)

    if active_filter_logs_for_page_1_only:
        logging.info(f"  Building URL with Keywords: '{keywords_str}' and Location: '{location_str}'")

    # Process ONLY the filter blocks (skip search_settings)
    for filter_config_key, filter_data in user_filters.items():
        if filter_config_key == "search_settings":
            continue # Already handled in the URL path

        param_key = filter_data.get("paramKey")
        selection_type = filter_data.get("selection_type")
        display_name = filter_data.get("displayName", filter_config_key)

        if not param_key:
            logging.debug(f"Missing 'paramKey' for filter block '{filter_config_key}'. Skipping.")
            continue

        selected_code_or_ids = None
        log_label = ""

        if selection_type == "single_code":
            code = str(filter_data.get("selected_code", "")).strip()
            if code:
                selected_code_or_ids = code
                log_label = get_label_for_selected_code(filter_data.get("options", []), code)

        elif selection_type == "multi_select":
            selected_ids = []
            selected_labels_for_log = []
            for option in filter_data.get("options", []):
                if option.get("selected") == 1 or str(option.get("selected", "0")) == "1" or option.get("selected") is True:
                    opt_id = str(option.get("id", "")).strip()
                    if opt_id:
                        selected_ids.append(opt_id)
                        selected_labels_for_log.append(option.get("label", opt_id))
            if selected_ids:
                selected_code_or_ids = selected_ids
                log_label = ', '.join(selected_labels_for_log)

        # If a filter was selected, add it to the query parameters
        if selected_code_or_ids:
            query_params[param_key] = selected_code_or_ids
            if active_filter_logs_for_page_1_only:
                logging.info(f"  Applying Filter '{display_name}': {log_label} ({param_key}={selected_code_or_ids})")

    # --- Assemble Final URL ---
    final_url = base_naukri_url + url_path
    if query_params:
        # doseq=True is important for multi-select filters like cityTypeGid
        encoded_params = urlencode(query_params, doseq=True)
        final_url += f"?{encoded_params}"

    if active_filter_logs_for_page_1_only:
        logging.info(f"Constructed Naukri Search URL (Page {page_number}): {final_url}")
    return final_url

# --- Data Extraction from Job Card ---
def parse_posted_ago_naukri(text: str) -> int:
    """Parses Naukri 'Posted Ago' text into days."""
    if not isinstance(text, str): return -1
    text_lower = text.lower().strip()
    days = -1
    if "just now" in text_lower or "today" in text_lower: days = 0
    elif "yesterday" in text_lower: days = 1
    else:
        match = re.search(r'(\d+)\s+(day|week|month|year)s?\s+ago', text_lower)
        if match:
            num, unit = int(match.group(1)), match.group(2)
            if unit == 'day': days = num
            elif unit == 'week': days = num * 7
            elif unit == 'month': days = num * 30 
            elif unit == 'year': days = num * 365
            elif "3+ weeks ago" in text_lower: days = 25
    return days

def extract_job_data_from_naukri_card(card_element: webdriver.remote.webelement.WebElement, config_selectors: dict, verbose: bool) -> dict | None:
    """Extracts data from a single Naukri job card element, mapping to ALL_EXPECTED_COLUMNS_NAUKRI."""
    if verbose: logging.debug("Processing card...")
    # Initialize with keys matching ALL_EXPECTED_COLUMNS_NAUKRI for Phase 1
    data = {
        'Naukri Job ID': 'N/A', 'Job Title': 'N/A', 'Job Detail Page URL': 'N/A',
        'Company Name': 'N/A', 'Actual Posting Company': '', 'Company Logo URL': 'N/A',
        'Company Rating (AmbitionBox)': pd.NA, 'Company Reviews Count (AmbitionBox)': pd.NA,
        'AmbitionBox Review Link': 'N/A', 'Experience Required': 'N/A', 'Location(s)': 'N/A',
        'Job Snippet': 'N/A', 'Key Skills/Tags (from card)': [], # Initialize as list
        'Posted Ago Text': 'N/A', 'Posted Days Ago': -1, 'Is Promoted/Sponsored': False,
        'Salary Indication (from Card/Filters)': 'N/A',
        'Source': 'Naukri.com Job Search'
        # Other columns like Date Added, Status will be added by add_jobs_to_excel
    }

    try:
        data['Naukri Job ID'] = card_element.get_attribute(config_selectors.get('job_card_data_job_id_attr', 'data-job-id')) or 'N/A'

        title_link_el = card_element.find_element(By.CSS_SELECTOR, config_selectors['job_card_title_link'])
        data['Job Title'] = title_link_el.get_attribute('title').strip() or title_link_el.text.strip()
        data['Job Detail Page URL'] = title_link_el.get_attribute('href')
        if not data['Job Detail Page URL'] or not data['Job Title'] or data['Job Title'] == 'N/A':
            logging.warning(f"Card skipped (Job ID: {data['Naukri Job ID']}): Missing Link or Title.")
            return None

        try:
            company_el = card_element.find_element(By.CSS_SELECTOR, config_selectors['job_card_company_name_link'])
            data['Company Name'] = company_el.get_attribute('title').strip() or company_el.text.strip()
            try:
                recruiter_el = card_element.find_element(By.CSS_SELECTOR, config_selectors['job_card_recruiter_name_link'])
                data['Actual Posting Company'] = recruiter_el.text.strip().replace("Posted by ","").replace("Posted by","").strip()
            except NoSuchElementException:
                data['Actual Posting Company'] = data['Company Name']
        except NoSuchElementException: pass

        try: data['Company Logo URL'] = card_element.find_element(By.CSS_SELECTOR, config_selectors['job_card_company_logo']).get_attribute('src')
        except NoSuchElementException: pass
        
        try:
            rating_el = card_element.find_element(By.CSS_SELECTOR, config_selectors['job_card_company_rating'])
            data['Company Rating (AmbitionBox)'] = pd.to_numeric(rating_el.text.strip(), errors='coerce')
            review_link_el = card_element.find_element(By.CSS_SELECTOR, config_selectors['job_card_ambitionbox_link'])
            data['AmbitionBox Review Link'] = review_link_el.get_attribute('href')
            try:
                reviews_count_el = card_element.find_element(By.CSS_SELECTOR, config_selectors['job_card_company_reviews_count'])
                reviews_text = reviews_count_el.text.strip()
                match = re.search(r'([\d,]+)', reviews_text)
                if match: data['Company Reviews Count (AmbitionBox)'] = int(match.group(1).replace(',', ''))
            except NoSuchElementException: pass
        except NoSuchElementException: pass

        try:
            exp_el = card_element.find_element(By.CSS_SELECTOR, config_selectors['job_card_experience'])
            data['Experience Required'] = exp_el.get_attribute('title').strip() or exp_el.text.strip()
        except NoSuchElementException: pass
        
        try:
            sal_el = card_element.find_element(By.CSS_SELECTOR, config_selectors['job_card_salary_on_card'])
            data['Salary Indication (from Card/Filters)'] = sal_el.get_attribute('title').strip() or sal_el.text.strip()
        except NoSuchElementException: data['Salary Indication (from Card/Filters)'] = "Not disclosed" # Naukri often shows this

        try:
            loc_el = card_element.find_element(By.CSS_SELECTOR, config_selectors['job_card_location'])
            data['Location(s)'] = loc_el.get_attribute('title').strip() or loc_el.text.strip()
        except NoSuchElementException: pass
        
        try: data['Job Snippet'] = card_element.find_element(By.CSS_SELECTOR, config_selectors['job_card_job_snippet']).text.strip()
        except NoSuchElementException: pass

        try:
            tag_elements = card_element.find_elements(By.CSS_SELECTOR, config_selectors['job_card_tags_list_items'])
            data['Key Skills/Tags (from card)'] = [tag.text.strip() for tag in tag_elements if tag.text.strip()]
        except NoSuchElementException: pass
        
        try:
            posted_el = card_element.find_element(By.CSS_SELECTOR, config_selectors['job_card_posted_ago'])
            data['Posted Ago Text'] = posted_el.text.strip()
            data['Posted Days Ago'] = parse_posted_ago_naukri(data['Posted Ago Text'])
        except NoSuchElementException: pass

        # Is Promoted Check
        try:
            # A more reliable check might be looking for a specific wrapper unique to promoted jobs
            promoted_wrapper_selector = config_selectors.get("promoted_job_card_wrapper", "div.srp-job-promotion") # Example
            card_element.find_element(By.CSS_SELECTOR, promoted_wrapper_selector)
            data['Is Promoted/Sponsored'] = True
            # If promoted, some selectors might be different. Add specific re-extraction if needed.
            # Example:
            # data['Job Title'] = card_element.find_element(By.CSS_SELECTOR, config_selectors['promoted_job_title']).text.strip()
        except NoSuchElementException:
            data['Is Promoted/Sponsored'] = False


        if verbose: logging.debug(f"  Extracted: {data['Naukri Job ID']} - {data['Job Title']}")
        return data

    except Exception as e:
        job_id_for_log = data.get('Naukri Job ID', card_element.get_attribute(config_selectors.get('job_card_data_job_id_attr', 'data-job-id')))
        logging.error(f"Error processing card (Job ID: {job_id_for_log}): {e}", exc_info=verbose)
        return None


# --- Main Scraping Logic ---
def search_and_scrape_naukri_jobs(driver: webdriver.Chrome, config: dict, existing_job_urls_master: set) -> tuple[list, int, int]:
    """Searches jobs on Naukri, handles pagination, scrapes results, skipping known duplicates."""
    user_filters = config['user_filters']
    general_settings = config['phase1_general_settings']
    config_selenium = config['selenium']
    config_selectors = config['selectors']

    scrape_all = general_settings['scrape_all_pages']
    max_pages_cfg = general_settings['max_pages_to_scrape']
    total_jobs_limit_cfg = general_settings.get('total_jobs_limit') or float('inf')
    minimum_unique_jobs_target_cfg = general_settings.get('minimum_unique_jobs_target', 0)
    jobs_per_page_limit_cfg = general_settings.get('jobs_per_page_limit', 0)

    # This list will now ONLY contain jobs that are new in this session AND not in the master Excel file.
    all_newly_scraped_jobs = []
    
    # MODIFICATION 2: We no longer need a separate session-level set. We will use the master set.
    # processed_job_ids_this_session = set() # This line is removed.

    scraped_duplicates_count = 0
    current_page_number = 1
    consecutive_empty_card_pages = 0
    
    search_url_page1 = construct_naukri_search_url(user_filters, general_settings, page_number=1)

    try:
        logging.info(f"Navigating to initial search URL (Page 1): {search_url_page1}")
        driver.get(search_url_page1)
        time.sleep(get_random_delay(config_selenium, "long"))

        while True:
            # --- MODIFICATION 3: The main stopping condition is now based on the count of TRULY NEW jobs. ---
            if len(all_newly_scraped_jobs) >= minimum_unique_jobs_target_cfg:
                logging.info(f"Minimum unique jobs target ({minimum_unique_jobs_target_cfg}) met. Stopping pagination.")
                break
            # --- END MODIFICATION 3 ---
            
            if current_page_number > max_pages_cfg: logging.info(f"Max pages limit ({max_pages_cfg}) reached."); break
            if len(all_newly_scraped_jobs) >= total_jobs_limit_cfg: logging.info(f"Total jobs limit ({total_jobs_limit_cfg}) reached."); break
            if not scrape_all and current_page_number > 1: logging.info("Scrape_all_pages False. Stopping after page 1."); break
            
            # ... (rest of the navigation and page loading logic remains the same) ...
            if current_page_number > 1:
                current_url = construct_naukri_search_url(user_filters, general_settings, page_number=current_page_number)
                logging.info(f"Navigating to Page {current_page_number}: {current_url}")
                driver.get(current_url)
                time.sleep(get_random_delay(config_selenium, "long"))
            
            logging.info(f"--- Processing Page {current_page_number} ---")
            
            # ... (scrolling and waiting logic remains the same) ...
            last_height = driver.execute_script("return document.body.scrollHeight")
            for _ in range(3):
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(get_random_delay(config_selenium, "short"))
                new_height = driver.execute_script("return document.body.scrollHeight")
                if new_height == last_height: break
                last_height = new_height
            time.sleep(get_random_delay(config_selenium, "medium"))

            try:
                WebDriverWait(driver, config_selenium['wait_time_long']).until(
                    EC.presence_of_all_elements_located((By.CSS_SELECTOR, config_selectors['job_card_wrapper']))
                )
                job_card_elements = driver.find_elements(By.CSS_SELECTOR, config_selectors['job_card_wrapper'])
                logging.info(f"Found {len(job_card_elements)} job card elements on page {current_page_number}.")
                if not job_card_elements:
                    consecutive_empty_card_pages += 1
                    logging.warning(f"No job cards found on page {current_page_number}. Consecutive empty pages: {consecutive_empty_card_pages}")
                    if consecutive_empty_card_pages >= 2: logging.info("Two consecutive pages with no job cards. Assuming end of results."); break
                    current_page_number += 1; continue
                else:
                    consecutive_empty_card_pages = 0
            except TimeoutException:
                logging.warning(f"Timeout waiting for job cards on page {current_page_number}.")
                break 

            page_extracted_count = 0
            for i, card_el in enumerate(job_card_elements):
                if jobs_per_page_limit_cfg > 0 and page_extracted_count >= jobs_per_page_limit_cfg:
                    logging.info(f"Jobs per page limit ({jobs_per_page_limit_cfg}) reached for page {current_page_number}.")
                    break
                if len(all_newly_scraped_jobs) >= total_jobs_limit_cfg: break

                job_data = extract_job_data_from_naukri_card(card_el, config_selectors, general_settings['verbose_card_extraction'])
                if job_data:
                    # --- MODIFICATION 4: The core logic change. Check against the MASTER set of URLs. ---
                    job_url = job_data.get('Job Detail Page URL')
                    if job_url and job_url not in existing_job_urls_master:
                        all_newly_scraped_jobs.append(job_data)
                        # Add the new URL to the master set to avoid duplicates from later pages in the SAME session.
                        existing_job_urls_master.add(job_url)
                        page_extracted_count += 1
                    # --- END MODIFICATION 4 ---
                    elif job_url:
                        scraped_duplicates_count += 1
            
            logging.info(f"Extracted {page_extracted_count} new unique jobs from page {current_page_number}.")
            
            # This old check is no longer needed here as it's now the main loop condition.
            # if len(all_scraped_jobs_data_session) >= minimum_unique_jobs_target_cfg: ... # REMOVED
            
            current_page_number += 1
        
    except WebDriverException as e:
        logging.critical(f"WebDriverException during Naukri scraping: {e}", exc_info=True)
        if "disconnected" in str(e) or "target crashed" in str(e): raise
    except Exception as e:
        logging.error(f"Unexpected error during Naukri job search/scraping: {e}", exc_info=True)
    
    for job_data_dict in all_newly_scraped_jobs:
        if 'Key Skills/Tags (from card)' in job_data_dict and isinstance(job_data_dict['Key Skills/Tags (from card)'], list):
            job_data_dict['Key Skills/Tags (from card)'] = ", ".join(job_data_dict['Key Skills/Tags (from card)'])

    logging.info(f"Finished scraping Naukri. Found {len(all_newly_scraped_jobs)} new unique jobs in this session.")
    return all_newly_scraped_jobs, scraped_duplicates_count

# --- Excel Handling ---
# The 'add_jobs_to_excel_naukri' function in phase1_list_scraper_naukri.py

def add_jobs_to_excel_naukri(scraped_jobs_list: list, config: dict) -> tuple[bool, int, int]:
    """Adds scraped Naukri job data to Excel, handles duplicates based on URL, ensures schema."""
    excel_filepath = config['paths']['excel_filepath']
    new_status = config['status']['NEW']
    all_expected_columns = config['excel_schema']['columns_list']
    
    logging.info(f"Processing {len(scraped_jobs_list)} scraped Naukri jobs for Excel: {excel_filepath}")
    added_count = 0; 
    
    if not scraped_jobs_list and not os.path.exists(excel_filepath):
        logging.info("No jobs scraped and Excel file does not exist. Creating empty Excel.")
        try:
            pd.DataFrame(columns=all_expected_columns).to_excel(excel_filepath, index=False, engine='openpyxl')
            return True, 0, 0
        except Exception as e:
            logging.error(f"Could not create empty Excel: {e}"); return False, 0, 0
    elif not scraped_jobs_list:
        logging.info("No new jobs scraped in this batch to add to existing Excel.")
        return True, 0, 0

    try:
        new_jobs_df = pd.DataFrame(scraped_jobs_list)
        if new_jobs_df.empty: logging.info("DataFrame from scraped jobs is empty."); return True, 0, 0
            
        new_jobs_df['Date Added'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        new_jobs_df['Status'] = new_status
        
        for col in all_expected_columns:
            if col not in new_jobs_df.columns: new_jobs_df[col] = ''
        
        # --- MODIFICATION 1: Change the unique key to the URL ---
        # We now use the URL as the unique identifier because it is a stable string and avoids data type issues.
        new_jobs_df['unique_key'] = new_jobs_df['Job Detail Page URL'].astype(str)
        # --- END MODIFICATION 1 ---

    except Exception as df_err:
        logging.error(f"Error creating DataFrame from scraped Naukri jobs: {df_err}", exc_info=True)
        return False, 0, 0

    file_exists = os.path.exists(excel_filepath)
    save_needed = False
    try:
        if file_exists:
            logging.debug(f"Reading existing Naukri Excel file: {excel_filepath}")
            # --- MODIFICATION 2: Read existing URLs, not IDs ---
            # We don't need special converters for URLs as they are already strings.
            existing_df = pd.read_excel(excel_filepath, engine='openpyxl')
            
            # Ensure all expected columns exist in existing_df, fill with empty string if not
            for col in all_expected_columns:
                if col not in existing_df.columns:
                    existing_df[col] = ''
                    save_needed = True # Schema changed
            existing_df = existing_df.reindex(columns=all_expected_columns, fill_value='')
            
            # Create a set of existing URLs for comparison.
            existing_job_urls = set(existing_df['Job Detail Page URL'].dropna().astype(str))
            # --- END MODIFICATION 2 ---
        else:
            logging.info(f"Naukri Excel file not found. Will create new one: {excel_filepath}")
            existing_df = pd.DataFrame(columns=all_expected_columns)
            # --- MODIFICATION 3 (Minor): Use a more descriptive name ---
            existing_job_urls = set()
            # --- END MODIFICATION 3 ---
            save_needed = True

        # --- MODIFICATION 4: Perform the check using the URL key against the set of URLs ---
        unique_new_jobs_to_add_df = new_jobs_df[~new_jobs_df['unique_key'].isin(existing_job_urls)]
        # --- END MODIFICATION 4 ---

        skipped_duplicates = len(new_jobs_df) - len(unique_new_jobs_to_add_df)
        added_count = len(unique_new_jobs_to_add_df)
       # logging.info(f"Deduplication: {added_count} new unique Naukri jobs to add, {skipped_duplicates} duplicates skipped.") remved for now we have to modify it again.
            
        if added_count > 0:
            # Drop the temporary 'unique_key' column before saving
            new_jobs_df_clean = unique_new_jobs_to_add_df.drop(columns=['unique_key'])
            # Align columns with the master list before concat
            new_jobs_df_clean = new_jobs_df_clean.reindex(columns=all_expected_columns, fill_value='')
            df_to_save = pd.concat([existing_df, new_jobs_df_clean], ignore_index=True)
            save_needed = True
        else: # No new jobs, but existing_df might have schema changes or was just created
            df_to_save = existing_df 
        
        if save_needed:
            logging.info(f"Saving Naukri DataFrame ({len(df_to_save)} rows) to Excel...")
            df_to_save = df_to_save.fillna('')
            for col in df_to_save.select_dtypes(include=['object']).columns:
                df_to_save[col] = df_to_save[col].astype(str).apply(clean_text_for_excel)
            df_to_save.to_excel(excel_filepath, index=False, engine='openpyxl')
            logging.info(f"Successfully saved Naukri Excel file: {excel_filepath}")
        else:
            logging.info("No changes or new unique jobs, Naukri Excel file not saved in this batch.")
        
        return True, added_count, skipped_duplicates
    except PermissionError:
        logging.error(f"PERMISSION ERROR writing to Naukri Excel: {excel_filepath}. CLOSE THE FILE.")
        return False, added_count, skipped_duplicates
    except Exception as e:
        logging.error(f"Unexpected error during Naukri Excel processing: {e}", exc_info=True)
        return False, added_count, skipped_duplicates

# --- Main Function for Phase 1 (Naukri) ---
def run_phase1_job_list_scraping(config: dict) -> tuple[bool, int, int]:
    """Executes Phase 1 for Naukri: connect Selenium, scrape, add to Excel."""
    logging.info("Initiating Phase 1: Naukri Job List Scraping")
    driver = None; overall_success = False
    total_added_to_excel_session = 0; total_skipped_in_excel_session = 0

    try:
        # --- MODIFICATION 5: Read Excel file and get existing URLs BEFORE scraping starts. ---
        excel_filepath = config['paths']['excel_filepath']
        existing_job_urls = set()
        if os.path.exists(excel_filepath):
            try:
                logging.info(f"Reading existing Excel file to build duplicate check list: {excel_filepath}")
                existing_df = pd.read_excel(excel_filepath, engine='openpyxl')
                # Ensure the column exists before trying to access it
                if 'Job Detail Page URL' in existing_df.columns:
                    existing_job_urls = set(existing_df['Job Detail Page URL'].dropna().astype(str))
                logging.info(f"Found {len(existing_job_urls)} existing job URLs in the master file.")
            except Exception as e:
                logging.error(f"Could not read existing Excel file to check for duplicates. Will treat all scraped jobs as new. Error: {e}")
        # --- END MODIFICATION 5 ---

        driver = setup_selenium_driver(config)
        if not driver:
            logging.critical("Failed to setup Selenium WebDriver for Naukri. Phase 1 cannot proceed.")
            return False, 0, 0

        # MODIFICATION 6: Pass the 'existing_job_urls' set to the scraping function.
        scraped_jobs_this_session, skipped_during_scrape = search_and_scrape_naukri_jobs(driver, config, existing_job_urls)
        total_skipped_in_excel_session += skipped_during_scrape # Add the count from scraping to the total

        if isinstance(scraped_jobs_this_session, list):
            excel_success, added_now, skipped_now = add_jobs_to_excel_naukri(scraped_jobs_this_session, config)
            if excel_success:
                total_added_to_excel_session = added_now
                # The 'skipped_now' from the Excel function will be the final authority on duplicates.
                total_skipped_in_excel_session += skipped_now 
                overall_success = True 
                if not scraped_jobs_this_session:
                     logging.info("No new jobs were scraped from Naukri in this session, Excel file checked/created.")
            else:
                logging.error("Critical error during Excel update for Naukri. Phase 1 failed.")
                overall_success = False
        else:
            logging.error("Naukri scraping function did not return a list as expected.")
            overall_success = False

    except WebDriverException as e:
         logging.critical(f"WebDriverException during Phase 1 (Naukri) execution: {e}", exc_info=True)
         overall_success = False
    except Exception as e:
        logging.critical(f"An unexpected critical error occurred in Phase 1 (Naukri): {e}", exc_info=True)
        overall_success = False

    # The final log message now uses the counts from the Excel function, which are more accurate.
    # The 'skipped' count from the Excel function will show any duplicates that might have slipped through
    # or were present in the initial scraped list before being passed.
    if overall_success:
         logging.info(f"Phase 1 (Naukri) Summary: Added {total_added_to_excel_session} unique jobs to Excel. Skipped {total_skipped_in_excel_session} duplicates found during scraping.")
         logging.info("Phase 1 (Naukri) completed.")
    else:
         logging.error("Phase 1 (Naukri) finished with errors.")

    return overall_success, total_added_to_excel_session, total_skipped_in_excel_session