# main_workflow_naukri.py
# Phase 0: Configuration, Logging Setup, and Workflow Orchestration for Naukri.com

import os
import sys
import time
import traceback
from pathlib import Path
from datetime import datetime
import logging
import json # For loading JSON-like config parts if needed later

# --- Add Project Directory to Python Path ---
BASE_DIR = Path(__file__).resolve().parent
sys.path.append(str(BASE_DIR))
print(f"[Startup] Added project directory to sys.path: {BASE_DIR}")

# --- Attempt to Import Phase Logic (Naukri specific) ---
try:
    import phase1_list_scraper_naukri
    import phase2_detail_scraper_naukri
    import phase3_ai_analysis
    import phase4_tailoring
    import phase5_rescore
    print("[Startup] Successfully imported phase modules (Naukri versions or compatible).")
except ImportError as e:
    print(f"!!!!!! ERROR: Failed to import one or more Naukri phase scripts: {e} !!!!!")
    # ... (error messages remain the same) ...
    sys.exit(1)

# ==============================================================================
# --- Centralized Excel Column Schema ---
# ==============================================================================
 #ALL_EXPECTED_COLUMNS_NAUKRI = [
 #   # ... (your full list of columns remains unchanged here) ...
 #   'Naukri Job ID', 'Job Title', 'Job Detail Page URL', 'Company Name',
 #   'Actual Posting Company', 'Company Logo URL', 'Company Rating (AmbitionBox)',
 #  'Company Reviews Count (AmbitionBox)', 'AmbitionBox Review Link',
 #   'Experience Required', 'Location(s)', 'Job Snippet', 'Key Skills/Tags (from card)',
 #   'Posted Ago Text', 'Posted Days Ago',
 #   'Is Promoted/Sponsored', 'Salary Indication (from Card/Filters)',
 #   'Source', 'Date Added', 'Status', 'Applied Date', 'Notes',
 #   'Full Job Description HTML', 'Full Job Description Plain Text',
 #   'Salary Range (Detailed)', 'Work Mode (Detailed)', 'Industry (Detailed)',
 #   'Functional Area/Department (Detailed)', 'Role Category (Detailed)',
 #   'Employment Type (Detailed)', 'Education Requirements (Detailed)',
 #   'Key Skills (from detail page)',
 #   'Company Website (Official)', 'About Company (Detailed)',
 #   'Date Scraped Detailed', 'Scraping Issues (Phase 2)',
 #   'Extracted Responsibilities', 'Extracted Required Skills', 'Extracted Preferred Skills',
 #   'Extracted Experience Level', 'Extracted Key Qualifications', 'Extracted Company Description (from JD)',
 #   'AI Match Score (Base Resume)', 'AI Score Justification (Base Resume)',
 #   'AI Strengths (Base Resume)', 'AI Areas for Improvement (Base Resume)',
 #   'AI Actionable Recommendations (Base Resume)',
 #   'Keyword Match Score (Base Resume)', 'Achievements Score (Base Resume)',
 #   'Summary Quality Score (Base Resume)', 'Structure Score (Base Resume)',
 #   'Tools Certs Score (Base Resume)', 'Total Match Score (Base Resume)',
 #   'Generated Tailored Summary', 'Generated Tailored Bullets', 'Generated Tailored Skills List',
 #   'Tailored HTML Path', 'Tailored PDF Path', 'Tailored PDF Pages',
 #   'Tailored Resume Score (Rescore)', 'Score Change (Rescore)',
 #   'Tailoring Effectiveness Status (Rescore)', 'Retailoring Attempts'
#]

# This new list should replace the existing one in main_workflow_naukri.py


# This new list should replace the existing one in main_workflow_naukri.py

# FINAL version for main_workflow_naukri.py
ALL_EXPECTED_COLUMNS_NAUKRI = [
    # --- Phase 1: List Scraping Columns (From Job Card) ---
    'Naukri Job ID', 'Job Title', 'Job Detail Page URL', 'Company Name', 'Actual Posting Company',
    'Company Logo URL', 'Company Rating (AmbitionBox)', 'Company Reviews Count (AmbitionBox)',
    'AmbitionBox Review Link', 'Experience Required', 'Location(s)', 'Job Snippet',
    'Key Skills/Tags (from card)', 'Posted Ago Text', 'Posted Days Ago', 'Is Promoted/Sponsored',
    'Salary Indication (from Card/Filters)',

    # --- Phase 2: Detailed Page Scraping Columns ---
    'Is Already Applied',                    # NEW
    'Apply Button Type',
    'Company Website (Official)',
    'Posted Ago Text Detailed',
    'Posted Days Ago (Detailed)',
    'Openings',
    'Applicants',
    'Job Highlights',
    'Key Company Highlights',                # NEW
    'Match: Early Applicant',
    'Match: Keyskills',
    'Match: Location',
    'Match: Work Experience',
    'Full Job Description HTML',
    'Full Job Description Plain Text',
    'Role (Detailed)',
    'Industry (Detailed)',
    'Functional Area/Department (Detailed)',
    'Employment Type (Detailed)',
    'Role Category (Detailed)',
    'Education Requirements (Detailed)',
    'Key Skills (from detail page)',
    'About Company (Detailed)',
    'Company Info Tags',
    'Follower Count',
    'Company HQ Address',
    'Awards & Recognitions',
    'Benefits & Perks',
    'Date Scraped Detailed',
    'Scraping Issues (Phase 2)',

    # --- Common Columns for All Phases ---
    'Source', 'Date Added', 'Status', 'Applied Date', 'Notes',

    # --- AI & Tailoring Columns (Phases 3, 4, 5) ---
    'Extracted Responsibilities', 'Extracted Required Skills', 'Extracted Preferred Skills',
    'Extracted Experience Level', 'Extracted Key Qualifications', 'Extracted Company Description (from JD)',
    'AI Match Score (Base Resume)', 'AI Score Justification (Base Resume)',
    'AI Strengths (Base Resume)', 'AI Areas for Improvement (Base Resume)',
    'AI Actionable Recommendations (Base Resume)', 'Keyword Match Score (Base Resume)',
    'Achievements Score (Base Resume)', 'Summary Quality Score (Base Resume)',
    'Structure Score (Base Resume)', 'Tools Certs Score (Base Resume)',
    'Total Match Score (Base Resume)', 'Generated Tailored Summary', 'Generated Tailored Bullets',
    'Generated Tailored Skills List', 'Tailored HTML Path', 'Tailored PDF Path', 'Tailored PDF Pages',
    'Tailored Resume Score (Rescore)', 'Score Change (Rescore)',
    'Tailoring Effectiveness Status (Rescore)', 'Retailoring Attempts'
]


CONFIG_EXCEL_SCHEMA_NAUKRI = {
    "columns_list": ALL_EXPECTED_COLUMNS_NAUKRI,
}

# ==============================================================================
# --- Configuration ---
# ==============================================================================
print("[Config] Loading configuration settings for Naukri.com workflow...")

# --- 1. File Paths & Core Settings ---
CONFIG_PATHS_NAUKRI = {
    "base_dir": BASE_DIR,
    "excel_filepath": BASE_DIR / "naukri_jobs_master_list.xlsx",
    "resume_filepath_html": BASE_DIR / "Resume.html",
    "output_folder": BASE_DIR / "Tailored_Resumes_Naukri",
    "log_folder": BASE_DIR / "logs_naukri",
    "env_filepath": BASE_DIR / '.env',
    # NEW: Path to the user-editable JSON filter configuration
    "naukri_user_filters_json_path": BASE_DIR / "naukri_search_config.json"
}


#  ---- Add Chrome Debugger Instructions ---
# (Instructions remain the same)
# --- HOW TO START CHROME WITH REMOTE DEBUGGING ---
# Before running this script, you MUST start Chrome manually using the command line
# and specify the same debugging port as configured below (e.g., 9222).
# Ensure ALL other Chrome instances are closed first.
#
# Windows (Command Prompt - Adjust path if necessary):
# "C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222 --user-data-dir="C:\ChromeDebugProfile"
# (Using a separate user-data-dir is recommended to avoid conflicts with your main profile)
#
# macOS (Terminal):
# /Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome --remote-debugging-port=9222 --user-data-dir="$HOME/ChromeDebugProfile"
#
# Linux (Terminal - Adjust command if needed):
# google-chrome --remote-debugging-port=9222 --user-data-dir="$HOME/ChromeDebugProfile"
#
# After starting Chrome this way, navigate manually to linkedin.com and log in if needed.
# THEN run this Python script.
# --- 2. Selenium Configuration ---
CONFIG_SELENIUM_NAUKRI = {
    # ... (remains unchanged) ...
    "chromedriver_path": r"C:\AI Use and Deveopment\chromedriver-win64\chromedriver.exe",
    "debugger_port": 9222,
    "wait_time_short": 15,
    "wait_time_long": 20,
    "enable_random_delays": True,
    "delay_short_base": 1.5, "delay_short_variance": 1.0,
    "delay_medium_base": 3.0, "delay_medium_variance": 2.0,
    "delay_long_base": 5.0, "delay_long_variance": 3.0,
}

# --- 3. Phase 1: GENERAL Scraping Configuration (Naukri) ---
# This dictionary now holds settings for HOW Phase 1 behaves,
# not WHAT specific job filters to apply (those come from naukri_search_config.json).
CONFIG_PHASE1_GENERAL_SETTINGS_NAUKRI = {
    "naukri_base_search_url": "https://www.naukri.com/", # Base URL to start building search query
    "scrape_all_pages": True,
    "max_pages_to_scrape": 5,
    "save_after_each_page": False,
    "verbose_card_extraction": False,
    "jobs_per_page_limit": 0,
    "total_jobs_limit": 60,
    "minimum_unique_jobs_target": 30,
}

# --- 4. Phase 2: Job Detail Scraping Configuration (Naukri) ---
CONFIG_PHASE2_NAUKRI = {
    # ... (remains unchanged) ...
    "save_interval": 5,
     "overwrite_phase1_data": False # NEW: Set to True to always use detailed page data. False to keep Phase 1 data if it exists.
}

# --- 5. AI (Gemini) Configuration ---
CONFIG_AI_NAUKRI = {
    # ... (remains unchanged, uses resume_html_filepath from CONFIG_PATHS_NAUKRI) ...
    "api_key_name": "GEMINI_API_KEY",
    "extraction_model_name": "gemini-2.0-flash",
    "analysis_model_name": "gemini-2.0-flash",
    "tailoring_model_name": "gemini-2.0-flash",
    "api_delay_seconds": 5,
    "safety_settings": {
        "HARM_CATEGORY_HARASSMENT": "BLOCK_NONE",
        "HARM_CATEGORY_HATE_SPEECH": "BLOCK_NONE",
        "HARM_CATEGORY_SEXUALLY_EXPLICIT": "BLOCK_NONE",
        "HARM_CATEGORY_DANGEROUS_CONTENT": "BLOCK_NONE",
    },
    "generation_config_json": {
        "temperature": 0.6, "top_p": 1, "top_k": 1,
        "max_output_tokens": 8192, "response_mime_type": "application/json",
    },
    "generation_config_text": {
        "temperature": 0.7, "top_p": 1, "top_k": 1,
        "max_output_tokens": 8192,
    },
    "resume_html_filepath": CONFIG_PATHS_NAUKRI["resume_filepath_html"],
}

# --- 6. Phase 4 & 5: Tailoring Configuration (Naukri) ---
CONFIG_PHASE4_NAUKRI = {
    # ... (remains unchanged, uses html_template_filepath from CONFIG_PATHS_NAUKRI) ...
    "score_threshold": 2.5,
    "max_tailoring_attempts": 3,
    "max_retailoring_attempts": 2,
    "save_interval": 3,
    "html_template_filepath": CONFIG_PATHS_NAUKRI["resume_filepath_html"],
}

# --- 7. Status Flags ---
CONFIG_STATUS_NAUKRI = {
    # ... (remains unchanged) ...
    "NEW": "New", "PROCESSING_DETAILS": "Processing Details", "READY_FOR_AI": "Ready for AI",
    "PROCESSING_AI": "Processing AI Analysis", "AI_ANALYZED": "AI Analyzed",
    "SKIPPED_LOW_SCORE": "Skipped - Low AI Score", "TAILORING": "Tailoring Resume",
    "SUCCESS": "Tailored Resume Created", "NEEDS_EDIT": "Tailored Needs Manual Edit",
    "RESCORING": "Rescoring Tailored Resume", "IMPROVED": "Rescored - Improved",
    "MAINTAINED": "Rescored - Maintained", "DECLINED": "Rescored - Declined",
    "NEEDS_RETAILORING": "Needs Re-Tailoring",
    "FAILED_SCRAPE_LIST": "Error - Scrape Job List", "FAILED_SCRAPE_DETAILS": "Error - Scrape Job Details",
    "FAILED_AI_EXTRACTION": "Error - AI Extraction", "FAILED_AI_ANALYSIS": "Error - AI Analysis",
    "FAILED_TAILORING": "Error - AI Tailoring", "FAILED_HTML_EDIT": "Error - HTML Edit",
    "FAILED_PDF_GEN": "Error - PDF Generation", "FAILED_RESCORING": "Error - Rescoring Failed",
    "FAILED_FILE_ACCESS": "Error - File Access", "FAILED_API_CONFIG": "Error - API Config/Auth",
    "FAILED_WEBDRIVER": "Error - WebDriver Connection", "INVALID_LINK": "Error - Invalid Job Link",
    "MISSING_DATA": "Error - Missing Input Data",
    "Error - Max Retailoring": "Error - Max Re-Tailoring Attempts",
    "Error - Score Comparison": "Error - Score Comparison Failed",
    "Error - Missing Tailored HTML": "Error - Tailored HTML Missing for Rescore",
    "UNKNOWN_ERROR": "Error - Unknown",
}

# --- 8. Naukri.com Selectors ---
CONFIG_NAUKRI_SELECTORS = {
    # ... (remains unchanged from your previous definition, ensure it's comprehensive) ...
    # --- Phase 1: Job List Page (Naukri) ---
    "job_list_container_outer": "div.styles_job-listing-container__OCfZC",
    "job_list_container_inner": "div.styles_jlc__main__VdwtF",
    "job_card_wrapper": "div.srp-jobtuple-wrapper",
    "job_card_data_job_id_attr": "data-job-id",
    "job_card_title_link": "div.row1 > h2 > a.title",
    "job_card_company_name_link": "div.row2 > span.comp-dtls-wrap > a.comp-name",
    "job_card_company_logo": "div.row1 > span.imagewrap > img.logoImage",
    "job_card_company_rating": "div.row2 > span.comp-dtls-wrap > a.rating > span.main-2",
    "job_card_company_reviews_count": "div.row2 > span.comp-dtls-wrap > a.review",
    "job_card_ambitionbox_link": "div.row2 > span.comp-dtls-wrap > a.rating",
    "job_card_experience": "div.row3 span.expwdth",
    "job_card_location": "div.row3 span.locWdth",
    "job_card_salary_on_card": "div.row3 span.sal-wrap",
    "job_card_job_snippet": "div.row4 > span.job-desc",
    "job_card_tags_list_items": "div.row5 > ul.tags-gt > li.tag-li",
    "job_card_posted_ago": "div.row6 > span.job-post-day",
    "job_card_recruiter_name_link": "div.client-company-name > a",
    "promoted_job_card_wrapper": "div.job-container",
    "promoted_job_title": "div.jc__card div.title > span",
    "pagination_container": "div.styles_pagination__oIvXh",
    "pagination_page_link": "div.styles_pages__v1rAK > a",
    "pagination_page_link_selected": "div.styles_pages__v1rAK > a.styles_selected__j3uvq",
    "pagination_next_button": "a.styles_btn-secondary__2AsIP:not([disabled]) i.ni-icon-arrow-2.right",
    "no_results_banner_text_xpath": "//div[contains(@class, 'styles_noResultContainer__') and contains(., 'No jobs found')]", # Example using XPath
    "json_ld_script_itemlist": 'script[type="application/ld+json"]:contains("ItemList")',
    # --- Phase 2: Job Detail Page (Naukri) ---

# -- Header and Stats (These are mostly fine as CSS) --
"details_job_title": "h1.styles_jd-header-title__rZwM1",
"details_company_name": "div.styles_jd-header-comp-name__MvqAI > a",
"details_experience_required": "div.styles_jhc__exp__k_giM",
"details_salary": "div.styles_jhc__salary__jdfEC",
"details_locations": "span.styles_jhc__location__W_pVs",
 # --- START OF MODIFICATIONS/ADDITIONS --- version 3
"details_apply_button_container": "div.styles_jhc__apply-button-container__5Bqnb", # NEW: The parent container
"details_already_applied_by_id": "already-applied", # NEW: By ID is more reliable
"details_apply_on_company_site_by_id": "company-site-button", # NEW: By ID
"details_apply_button_by_id": "apply-button", # NEW: By ID
"details_already_applied": "span.styles_already-applied__4KDhw",
"details_apply_button": ".styles_jhc__apply-button-container__5Bqnb > button.apply-button",

# -- These require XPath because of :has() and :contains() --
"details_posted_ago_xpath": "//div[contains(@class, 'styles_jhc__jd-stats__KrId0')]//span[label[contains(text(), 'Posted:')]]/span",
"details_openings_xpath": "//div[contains(@class, 'styles_jhc__jd-stats__KrId0')]//span[label[contains(text(), 'Openings:')]]/span",
"details_applicants_xpath": "//div[contains(@class, 'styles_jhc__jd-stats__KrId0')]//span[label[contains(text(), 'Applicants:')]]/span",
"details_company_hq_address_xpath": "//div[contains(@class, 'styles_comp-info-detail__4xVBr')][label[contains(text(), 'Address:')]]/span",

#"details_company_official_website_link_xpath": "//div[contains(@class, 'styles_comp-info-detail__4xVBr') and label[contains(text(), 'Link:')]]/span/a", 
"details_company_official_website_link_xpath": "//div[contains(@class, 'styles_comp-info-detail__4xVBr')][label[contains(text(), 'Link:')]]/span/a",
"details_role_xpath": "//div[contains(@class, 'styles_other-details__oEN4O')]//div[label[contains(text(), 'Role:')]]",
"details_industry_xpath": "//div[contains(@class, 'styles_other-details__oEN4O')]//div[label[contains(text(), 'Industry Type:')]]",
"details_department_xpath": "//div[contains(@class, 'styles_other-details__oEN4O')]//div[label[contains(text(), 'Department:')]]",
"details_employment_type_xpath": "//div[contains(@class, 'styles_other-details__oEN4O')]//div[label[contains(text(), 'Employment Type:')]]",
"details_role_category_xpath": "//div[contains(@class, 'styles_other-details__oEN4O')]//div[label[contains(text(), 'Role Category:')]]",

# -- Job Match and Highlights (CSS is fine here) --
"details_job_highlights_list": "ul.styles_JDC__job-highlight-list__QZC12 > li",
"details_match_score_container": "div.styles_MS__details__iS7mj",

# -- Main Content (CSS is fine here) --
"details_job_description_html": "div.styles_JDC__dang-inner-html__h0K4t",
"details_education_container": "div.styles_education__KXFkO",
"details_key_skills_container": "div.styles_key-skill__GIPn_ > div:last-of-type",
"details_about_company_read_more_button": "div.overview-section span.styles_rm-link__RgrMs",
"details_about_company_overview_text": "div.overview-section .description",
"details_about_company_fallback": "section.styles_about-company__lOsvW div.styles_detail__U2rw4",
"details_company_info_tags_list": "div.styles_company-info-tags__y6RDs > div.styles_chips__AKDM0",
"details_follower_count": "span.styles_followers__DcqTi",
"details_awards_list": "div.styles_arc__item__hg_su",
"details_benefits_list": "div.styles_pbc__benefit__OLgb0",
"details_key_company_highlights_list": "div.styles_khc__common-card__rAasp",
}

# --- 9. Workflow Control (Naukri) ---
CONFIG_WORKFLOW_NAUKRI = {
    # ... (remains unchanged) ...
    "start_phase": 1,
    "end_phase": 2,
    "retry_failed_phase2": True,
    "retry_failed_phase3": True,
    "retry_failed_phase4": True,
    "retry_failed_phase5": True,
}

# ==============================================================================
# --- Function to Load User Filter Configuration ---
# ==============================================================================
def load_naukri_user_filter_config(config_paths):
    """Loads the naukri_search_config.json file."""
    filter_config_path = config_paths["naukri_user_filters_json_path"]
    # We use print() here because logging might not be configured yet.
    print(f"[Config] Attempting to load user filters from: {filter_config_path}")
    if not filter_config_path.exists():
        print(f"!!!!!! ERROR: Naukri filter configuration file not found: {filter_config_path} !!!!!")
        print("!!!!!! Please create 'naukri_search_config.json' with your desired filter settings. !!!!!")
        return None
    try:
        with open(filter_config_path, 'r', encoding='utf-8') as f:
            user_filters = json.load(f)
        print("[Config] Successfully loaded Naukri user filter configuration.")
        # Once logging is set up, this will also go to the file.
        logging.info("Successfully loaded Naukri user filter configuration.")
        return user_filters
    except json.JSONDecodeError as e:
        print(f"!!!!!! ERROR: Invalid JSON in {filter_config_path}. Please fix it. Error: {e} !!!!!")
        logging.error(f"Error decoding JSON from {filter_config_path}: {e}")
        return None
    except Exception as e:
        print(f"!!!!!! ERROR: An unexpected error occurred while loading {filter_config_path}: {e} !!!!!")
        logging.error(f"An unexpected error occurred while loading {filter_config_path}: {e}")
        return None


# ==============================================================================
# --- Master Configuration Dictionary (Naukri) ---
# ==============================================================================
# Load user filters first
USER_NAUKRI_FILTERS = load_naukri_user_filter_config(CONFIG_PATHS_NAUKRI)

if USER_NAUKRI_FILTERS is None:
    logging.critical("Could not load Naukri user filters. Halting execution.")
    sys.exit(1) # Exit if user filters can't be loaded

MASTER_CONFIG_NAUKRI = {
    "paths": CONFIG_PATHS_NAUKRI,
    "selenium": CONFIG_SELENIUM_NAUKRI,
    "workflow": CONFIG_WORKFLOW_NAUKRI,
    "user_filters": USER_NAUKRI_FILTERS, # Loaded from naukri_search_config.json
    "phase1_general_settings": CONFIG_PHASE1_GENERAL_SETTINGS_NAUKRI, # Behavioral settings
    "phase2": CONFIG_PHASE2_NAUKRI, # Keep as is, Phase 2 doesn't have complex filter inputs
    "ai": CONFIG_AI_NAUKRI,
    "phase4": CONFIG_PHASE4_NAUKRI,
    "status": CONFIG_STATUS_NAUKRI,
    "selectors": CONFIG_NAUKRI_SELECTORS,
    "excel_schema": CONFIG_EXCEL_SCHEMA_NAUKRI,
}

# ==============================================================================
# --- Logging Setup ---
# ==============================================================================
def setup_logging(config):
    """Configures logging to console and a dated file for Naukri."""
    log_folder = config['paths']['log_folder']
    # Get search term and location from the loaded user_filters
    search_keywords = config['user_filters'].get('search_settings', {}).get('search_keywords', 'UnknownSearch_Naukri')
    location_text = config['user_filters'].get('search_settings', {}).get('search_base_location_text', 'UnknownLocation_Naukri')

    search_term_safe = "".join(c if c.isalnum() else "_" for c in search_keywords.split(',')[0]) # Use first keyword
    location_safe = "".join(c if c.isalnum() else "_" for c in location_text)[:20]
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_filename = f"log_naukri_{timestamp}_{search_term_safe}_{location_safe}.log"
    log_filepath = log_folder / log_filename

    # ... (rest of logging setup remains unchanged) ...
    try:
        log_folder.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        print(f"!!!!!! ERROR: Could not create log directory: {log_folder}. Error: {e} !!!!!")
        print("Logging to console only.")
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)-8s - [%(filename)s:%(lineno)d] - %(message)s',
            handlers=[logging.StreamHandler()]
        )
        return

    logging.basicConfig(
         force=True,
        level=logging.INFO,
        format='%(asctime)s - %(levelname)-8s - [%(filename)s:%(lineno)d] - %(message)s',
        handlers=[
            logging.FileHandler(log_filepath, mode='a', encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
    logging.getLogger("weasyprint").setLevel(logging.ERROR)
    logging.getLogger("fontTools").setLevel(logging.WARNING)
    logging.getLogger("woff2").setLevel(logging.WARNING)

    logging.info("=================================================")
    logging.info(f"Logging initialized for Naukri. Log file: {log_filepath}")
    logging.info("Starting Job Automation Workflow (Naukri.com)")
    logging.info(f"Base Directory: {config['paths']['base_dir']}")
    logging.info(f"Using Excel File: {config['paths']['excel_filepath']}")
    logging.info(f"Search Keywords: '{search_keywords}'") # Updated log
    logging.info(f"Base Location: '{location_text}'")   # Updated log
    logging.info(f"Workflow Phases: {config['workflow']['start_phase']} to {config['workflow']['end_phase']}")
    logging.info("=================================================")


# ==============================================================================
# --- Excel File Accessibility Check ---
# ==============================================================================
def check_excel_accessibility(filepath: Path, config: dict):
    # ... (remains unchanged, uses config['excel_schema']['columns_list']) ...
    logging.info(f"Checking accessibility of Excel file: {filepath}")
    retry_delay = 5
    expected_columns = config['excel_schema']['columns_list']
    while True:
        try:
            if not filepath.exists():
                logging.warning(f"Excel file '{filepath.name}' not found. It will be created by Phase 1.")
                import pandas as pd
                df_template = pd.DataFrame(columns=expected_columns)
                df_template.to_excel(filepath, index=False, engine='openpyxl')
                logging.info(f"Created empty Excel file '{filepath.name}' with standard headers.")
                return True
            else:
                with open(filepath, 'a+b'):
                    pass
                logging.info(f"Excel file '{filepath.name}' is accessible.")
                return True
        except PermissionError:
            logging.error(f"PERMISSION ERROR: Cannot access Excel file: {filepath}")
            logging.error("The file might be open in Excel or another application.")
            user_input = input(f"Please CLOSE the file, then press Enter to retry, or type 'exit' to quit: ").strip().lower()
            if user_input == 'exit': logging.info("User chose to exit."); return False
            else: logging.info(f"Retrying file access in {retry_delay} seconds..."); time.sleep(retry_delay)
        except Exception as e:
            logging.critical(f"Unexpected error checking/creating Excel file: {e}", exc_info=True)
            return False

# ==============================================================================
# --- Main Workflow Orchestration (Naukri) ---
# ==============================================================================
def run_naukri_workflow(config):
    # ... (Function logic remains unchanged, it uses the passed 'config' which is MASTER_CONFIG_NAUKRI) ...
    logging.info("########## Starting Naukri Workflow ##########")
    start_phase = config['workflow']['start_phase']
    end_phase = config['workflow']['end_phase']
    max_phase = 5
    logging.info(f"Naukri workflow configured to run from Phase {start_phase} to Phase {end_phase}.")

    if not (1 <= start_phase <= end_phase <= max_phase):
        logging.error(f"Invalid phase range ({start_phase}-{end_phase}). Must be between 1 and {max_phase}.")
        return False, {}

    overall_success = True; phase_times = {}
    phases_to_run = range(start_phase, end_phase + 1)

    # Phase 1
    if 1 in phases_to_run:
        phase_start_time = time.time()
        logging.info("--- Phase 1: Scrape Job List (Naukri) ---")
        try:
            # Pass the entire MASTER_CONFIG_NAUKRI to Phase 1
            success_p1, added_p1, skipped_p1 = phase1_list_scraper_naukri.run_phase1_job_list_scraping(config)
            if not success_p1: logging.error("Phase 1 (Naukri) failed critically. Aborting."); overall_success = False
            else: logging.info(f"--- Phase 1 (Naukri) Completed (Added: {added_p1}, Skipped Duplicates: {skipped_p1}) ---")
        except Exception as e: logging.critical(f"CRITICAL Phase 1 (Naukri) error: {e}", exc_info=True); overall_success = False
        phase_times['Phase 1'] = time.time() - phase_start_time
        logging.info(f"Phase 1 (Naukri) duration: {phase_times.get('Phase 1', 0):.2f}s.")
    elif start_phase > 1: logging.info("--- Skipping Phase 1 (Naukri) (Config) ---")

    # Phase 2
    if overall_success and 2 in phases_to_run:
        phase_start_time = time.time()
        logging.info("--- Phase 2: Scrape Job Details (Naukri) ---")
        try:
            success_p2 = phase2_detail_scraper_naukri.run_phase2_detail_scraping(config)
            if not success_p2: logging.warning("Phase 2 (Naukri) encountered critical errors.")
            else: logging.info("--- Phase 2 (Naukri) Completed ---")
        except Exception as e: logging.critical(f"CRITICAL Phase 2 (Naukri) error: {e}", exc_info=True); overall_success = False
        phase_times['Phase 2'] = time.time() - phase_start_time
        logging.info(f"Phase 2 (Naukri) duration: {phase_times.get('Phase 2', 0):.2f}s.")
    elif 2 in phases_to_run: logging.warning("--- Skipping Phase 2 (Naukri) due to prior failure ---")
    elif start_phase > 2: logging.info("--- Skipping Phase 2 (Naukri) (Config) ---")

    # Phase 3
    if overall_success and 3 in phases_to_run:
        phase_start_time = time.time()
        logging.info("--- Phase 3: AI Analysis & Scoring (Naukri Data) ---")
        try:
            success_p3 = phase3_ai_analysis.run_phase3_ai_processing(config)
            if not success_p3: logging.warning("Phase 3 (Naukri Data) encountered critical errors.")
            else: logging.info("--- Phase 3 (Naukri Data) Completed ---")
        except ImportError as e:
             if 'google.generativeai' in str(e): logging.critical("CRITICAL: google-generativeai not installed.")
             else: logging.critical(f"CRITICAL ImportError P3: {e}", exc_info=True)
             overall_success = False
        except Exception as e: logging.critical(f"CRITICAL Phase 3 (Naukri Data) error: {e}", exc_info=True); overall_success = False
        phase_times['Phase 3'] = time.time() - phase_start_time
        logging.info(f"Phase 3 (Naukri Data) duration: {phase_times.get('Phase 3', 0):.2f}s.")
    elif 3 in phases_to_run: logging.warning("--- Skipping Phase 3 (Naukri Data) due to prior failure ---")
    elif start_phase > 3: logging.info("--- Skipping Phase 3 (Naukri Data) (Config) ---")

    # Phase 4
    if overall_success and 4 in phases_to_run:
        phase_start_time = time.time()
        logging.info("--- Phase 4: AI Resume Tailoring (Naukri Data) ---")
        try:
            success_p4 = phase4_tailoring.run_phase4_resume_tailoring(config)
            if not success_p4: logging.warning("Phase 4 (Naukri Data) encountered critical errors.")
            else: logging.info("--- Phase 4 (Naukri Data) Completed ---")
        except ImportError as e:
             if 'weasyprint' in str(e): logging.critical("CRITICAL: WeasyPrint not installed or missing dependencies.")
             elif 'PyPDF2' in str(e): logging.critical("CRITICAL: PyPDF2 not installed.")
             else: logging.critical(f"CRITICAL ImportError P4: {e}", exc_info=True)
             overall_success = False
        except Exception as e: logging.critical(f"CRITICAL Phase 4 (Naukri Data) error: {e}", exc_info=True); overall_success = False
        phase_times['Phase 4'] = time.time() - phase_start_time
        logging.info(f"Phase 4 (Naukri Data) duration: {phase_times.get('Phase 4', 0):.2f}s.")
    elif 4 in phases_to_run: logging.warning("--- Skipping Phase 4 (Naukri Data) due to prior failure ---")
    elif start_phase > 4: logging.info("--- Skipping Phase 4 (Naukri Data) (Config) ---")

    # Phase 5
    if overall_success and 5 in phases_to_run:
        phase_start_time = time.time()
        logging.info("--- Phase 5: Rescore Tailored Resumes (Naukri Data) ---")
        try:
            success_p5 = phase5_rescore.run_phase5_rescoring(config)
            if not success_p5: logging.warning("Phase 5 (Naukri Data) encountered critical errors.")
            else: logging.info("--- Phase 5 (Naukri Data) Completed ---")
        except Exception as e: logging.critical(f"CRITICAL Phase 5 (Naukri Data) error: {e}", exc_info=True); overall_success = False
        phase_times['Phase 5'] = time.time() - phase_start_time
        logging.info(f"Phase 5 (Naukri Data) duration: {phase_times.get('Phase 5', 0):.2f}s.")
    elif 5 in phases_to_run: logging.warning("--- Skipping Phase 5 (Naukri Data) due to prior failure ---")
    elif start_phase > 5: logging.info("--- Skipping Phase 5 (Naukri Data) (Config) ---")

    logging.info("#################################################")
    if overall_success: logging.info(f"Naukri Workflow Completed (Phases {start_phase}-{end_phase}).")
    else: logging.error("Naukri Workflow Halted or Completed with CRITICAL ERRORS.")
    logging.info("Review log file for detailed information.")
    logging.info("#################################################")
    return overall_success, phase_times

# ==============================================================================
# --- Script Execution ---
# ==============================================================================
if __name__ == "__main__":
    global_start_time = time.time()

    # Load .env first (as it's independent of other configs)
    env_file_path = CONFIG_PATHS_NAUKRI['env_filepath'] # Use the one defined early
    print(f"[Startup] Loading .env from: {env_file_path}...")
    if env_file_path.exists():
        from dotenv import load_dotenv
        load_dotenv(dotenv_path=env_file_path)
        print("[Startup] Environment variables loaded.")
    else:
        print(f"[Startup] WARNING: .env file not found at {env_file_path}. API keys might be missing.")

    # Now MASTER_CONFIG_NAUKRI is fully defined (including loaded USER_NAUKRI_FILTERS)
    setup_logging(MASTER_CONFIG_NAUKRI)

    excel_file_path = MASTER_CONFIG_NAUKRI['paths']['excel_filepath']
    if not check_excel_accessibility(excel_file_path, MASTER_CONFIG_NAUKRI):
        logging.critical("Exiting: Excel file inaccessible or user chose to exit.")
        sys.exit(1)

    workflow_status, phase_durations = run_naukri_workflow(MASTER_CONFIG_NAUKRI)

    total_runtime = time.time() - global_start_time
    logging.info(f"Total Naukri Workflow Runtime: {total_runtime:.2f} seconds.")
    logging.info(f"Phase Durations (seconds): {phase_durations}")
    logging.info("Naukri script execution finished.")
    logging.getLogger().handlers[0].flush()
    sys.exit(0 if workflow_status else 1)