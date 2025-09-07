# Naukri.com Job Search & Resume Tailoring Automaton 🚀

## Overview

This project automates the tedious process of searching for relevant jobs on **Naukri.com**, analyzing their requirements against your resume, tailoring your resume specifically for high-match positions, and evaluating the effectiveness of the tailoring. It aims to streamline the job application workflow, save time, and increase the chances of landing interviews by submitting highly relevant resumes.

The core workflow involves:
1.  Scraping job listings from **Naukri.com** based on your search criteria.
2.  Extracting detailed information from each job posting.
3.  Utilizing Google's Gemini AI to analyze the job description, compare it against your **base resume**, and generate a match score.
4.  For jobs exceeding a defined match score threshold, automatically tailoring your base HTML resume using AI suggestions.
5.  Generating both HTML and PDF versions of the tailored resumes.
6.  Optionally **rescoring the tailored resume** against the job description using AI to assess the effectiveness of the tailoring.
7.  Storing all collected data, analysis results, tailoring status, and file paths in a central Excel file for review and further action.

**Disclaimer:** Web scraping, especially on dynamic sites like Naukri.com, can be fragile. Naukri's website structure changes frequently, which may break the scraping components (Phases 1 & 2) of this tool. The CSS selectors defined in the configuration may need regular updates. Use this tool responsibly and ethically, respecting Naukri.com's Terms of Service. Automation should augment, not replace, genuine engagement.

## Key Features ✨

*   **Automated Naukri.com Job Scraping:** Fetches job listings based on keywords, location, and a rich set of filters defined in a JSON configuration file.
*   **Detailed Data Extraction:** Gathers comprehensive job details, including full descriptions, company info, salary, experience requirements, and more.
*   **AI-Powered Job Analysis:** Uses Google Gemini to:
    *   Extract key responsibilities, required/preferred skills, experience levels, and qualifications from job descriptions.
    *   Score the match between the job description and your **base** resume (0-5 stars), including a detailed breakdown.
    *   Provide detailed feedback: Strengths, areas for improvement, and actionable recommendations.
*   **Automated Resume Tailoring:** For high-scoring jobs, uses AI to:
    *   Rewrite your resume summary.
    *   Adapt experience bullet points to highlight relevant achievements and keywords.
    *   Optimize the skills section based on job requirements.
*   **Iterative Condensation:** Attempts to automatically condense AI-generated content if the initial tailored PDF exceeds one page.
*   **HTML & PDF Generation:** Creates tailored resumes in both HTML and PDF formats using WeasyPrint.
*   **AI-Powered Rescoring:** Uses Google Gemini to re-evaluate the **tailored resume** against the job description, providing a new score.
*   **Tailoring Effectiveness Tracking:** Calculates the change between the original score and the tailored score, classifying the tailoring as Improved, Maintained, or Declined.
*   **Re-Tailoring Loop:** If a tailored resume's score drops below the threshold after rescoring, it can be automatically flagged to be re-processed by the tailoring phase (up to a configurable limit).
*   **Centralized Data:** Stores all scraped data, AI analysis, tailoring results, rescoring data, and file paths in a well-structured Excel spreadsheet.
*   **Configuration Driven:** Main workflow controlled by `main_workflow_naukri.py`, with user-facing search filters managed in a clean `naukri_search_config.json` file.
*   **Logging:** Comprehensive logging to both console and timestamped files for easy debugging and tracking.
*   **Workflow Control:** Ability to configure which phases of the workflow to run (e.g., skip scraping, only run analysis and tailoring).
*   **Error Handling & Retries:** Includes options to retry processing jobs that failed in previous runs for each phase.

## Project Workflow / Phases 📝

The automation process is divided into distinct phases, orchestrated by `main_workflow_naukri.py`:

**Phase 0: Configuration & Setup (`main_workflow_naukri.py`)**
*   Loads all configuration settings from the script itself and the `naukri_search_config.json` file.
*   Initializes logging to console and a file in the `logs_naukri/` directory.
*   Checks accessibility of the main Excel file (`naukri_jobs_master_list.xlsx`).
*   Loads environment variables (e.g., API key) from the `.env` file.
*   Calls the functions for the subsequent phases based on the `start_phase` and `end_phase` configuration.

**Phase 1: Scrape Job List (`phase1_list_scraper_naukri.py`)**
*   Connects to an existing Chrome instance running with remote debugging enabled.
*   Builds a search URL for Naukri.com using the keywords, location, and filters defined in `naukri_search_config.json`.
*   Navigates to the search results page.
*   Scrapes basic information (Title, Company, Location, Link, Job ID, etc.) from job cards.
*   Handles pagination by clicking the "Next" button.
*   Adds newly found, unique jobs to the master Excel file (`naukri_jobs_master_list.xlsx`) with an initial `Status` of `New`.

**Phase 2: Scrape Job Details (`phase2_detail_scraper_naukri.py`)**
*   Connects to the Chrome instance.
*   Reads the master Excel file.
*   Filters for jobs with `Status` = `New` (or specific error statuses if retry is enabled).
*   For each eligible job, navigates to its specific Naukri.com job `Link`.
*   Scrapes detailed information, including the full job description, salary, role details, and company information.
*   Updates the corresponding row in the Excel file with the scraped details and sets the `Status` to `Ready for AI`.

**Phase 3: AI Analysis & Scoring (`phase3_ai_analysis.py`)**
*   This phase is job-board agnostic. It reads job data from the Excel file (scraped in Phase 2).
*   It sends the job description and your base resume text to the Gemini AI for analysis, scoring, and extraction of key details.
*   Updates the Excel file with the AI's analysis and sets the `Status` to `AI Analyzed`.

**Phase 4: AI Resume Tailoring & PDF Generation (`phase4_tailoring.py`)**
*   This phase is also job-board agnostic.
*   It filters for jobs that meet a minimum AI score threshold.
*   For each eligible job, it sends a detailed prompt to the Gemini AI to generate tailored content for your resume.
*   It applies these suggestions to the `Resume.html` template and saves the output as new HTML and PDF files in the `Tailored_Resumes_Naukri/` folder.

**Phase 5: Rescore Tailored Resumes (`phase5_rescore.py`)**
*   This final phase is also job-board agnostic.
*   It takes the newly tailored resume, re-scores it against the job description using the same AI process from Phase 3.
*   It updates the Excel file with the new score, allowing you to track the effectiveness of the resume tailoring.

## Technology Stack 💻

*   **Language:** Python 3.10+
*   **Web Scraping:** Selenium (with ChromeDriver)
*   **HTML Parsing:** BeautifulSoup4
*   **AI Model:** Google Gemini API
*   **Data Handling:** Pandas, NumPy
*   **Excel Interaction:** Openpyxl
*   **PDF Generation:** WeasyPrint
*   **Environment Management:** python-dotenv
*   **PDF Reading (for validation):** PyPDF2

## Prerequisites 📋

1.  **Python:** Version 3.10 or higher.
2.  **Pip:** Python package installer.
3.  **Git:** For cloning the repository.
4.  **Google Chrome:** The script uses Selenium with ChromeDriver.
5.  **ChromeDriver:** Must match your installed Chrome version.
6.  **Naukri.com Account:** You need an active Naukri.com account. The script assumes you will manually log in.
7.  **Google Gemini API Key:** Obtain one from Google AI Studio or Google Cloud Console.
8.  **WeasyPrint System Dependencies:** WeasyPrint relies on external libraries (Pango, Cairo, etc.). Refer to the official documentation for installation on your OS (Windows/macOS/Linux).

## Setup Instructions 🛠️

1.  **Clone the Repository:**
    ```bash
    git clone https://github.com/YOUR_USERNAME/YOUR_REPOSITORY_NAME.git
    cd YOUR_REPOSITORY_NAME
    ```

2.  **Create a Virtual Environment (Recommended):**
    ```bash
    python -m venv venv
    # Windows: venv\Scripts\activate
    # macOS/Linux: source venv/bin/activate
    ```

3.  **Install Python Dependencies:**
    *   (Ensure a `requirements.txt` file exists with all necessary packages.)
    ```bash
    pip install -r requirements.txt
    ```

4.  **Setup ChromeDriver:**
    *   Download the ChromeDriver that matches your Chrome version.
    *   Place the executable in your system's PATH or update its location in the `CONFIG_SELENIUM_NAUKRI` dictionary in `main_workflow_naukri.py`.

5.  **Setup WeasyPrint Dependencies (OS Specific):**
    *   Follow the official WeasyPrint installation guide for your operating system. This is crucial for PDF generation.

6.  **Create `.env` File:**
    *   In the root directory, create a file named `.env`.
    *   Add your Google Gemini API key:
        ```dotenv
        GEMINI_API_KEY=YOUR_ACTUAL_API_KEY_HERE
        ```

7.  **Prepare `Resume.html`:**
    *   Ensure you have a well-structured HTML file named `Resume.html` in the root directory. This is your base resume template.

8.  **Configure Your Job Search:**
    *   Open the `naukri_search_config.json` file.
    *   Set your desired `search_keywords` and `search_base_location_text`.
    *   Go through the other filters (freshness, experience, salary, etc.) and set the `selected_code` or `selected` values according to the provided options to refine your search.

## Configuration Details ⚙️

Configuration is split between two main files:

*   **`naukri_search_config.json` (User-Facing Filters):**
    *   This is where you define **WHAT** to search for.
    *   It contains sections for keywords, location, experience, salary, company type, and many other filters that Naukri.com provides.
    *   Simply edit the `selected_code` or `selected` values in this file to control the job search.

*   **`main_workflow_naukri.py` (Core Workflow & System Config):**
    *   This file controls **HOW** the script runs.
    *   `CONFIG_PATHS_NAUKRI`: Defines file and folder locations.
    *   `CONFIG_SELENIUM_NAUKRI`: Settings for Selenium, including the debugger port.
    *   `CONFIG_WORKFLOW_NAUKRI`: Controls which phases to run (e.g., `start_phase`, `end_phase`) and retry logic.
    *   `CONFIG_PHASE1_GENERAL_SETTINGS_NAUKRI`: Behavioral settings like page limits.
    *   `CONFIG_AI_NAUKRI`: Settings for the Gemini API.
    *   `CONFIG_PHASE4_NAUKRI`: Thresholds and attempt limits for resume tailoring.
    *   `CONFIG_NAUKRI_SELECTORS`: **Crucial but fragile.** Contains CSS selectors for scraping. **This may need updates if Naukri.com changes its website layout.**

## Running the Workflow ▶️

1.  **Start Chrome with Remote Debugging:**
    *   **IMPORTANT:** Close *all* other instances of Google Chrome.
    *   Run Chrome from your command line with the remote debugging flag (port must match the one in the config, e.g., 9222).
        *   **Windows:** `"C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222 --user-data-dir="C:\ChromeDebugProfile"`
        *   **macOS:** `/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome --remote-debugging-port=9222 --user-data-dir="$HOME/ChromeDebugProfile"`

2.  **Log in to Naukri.com:**
    *   In the newly opened Chrome window, navigate to `https://www.naukri.com` and log in. Keep this window open.

3.  **Run the Python Script:**
    *   Open a *separate* terminal.
    *   Navigate to the project directory and activate your virtual environment.
    *   Execute the main workflow script:
        ```bash
        python main_workflow_naukri.py
        ```

4.  **Monitor:**
    *   Watch the console output for progress.
    *   Check the log file in `logs_naukri/`.

## Project File Structure 📁

```markdown
YOUR_REPOSITORY_NAME/
├── .env
├── main_workflow_naukri.py
├── phase1_list_scraper_naukri.py
├── phase2_detail_scraper_naukri.py
├── phase3_ai_analysis.py
├── phase4_tailoring.py
├── phase5_rescore.py
├── naukri_search_config.json
├── Resume.html
├── naukri_jobs_master_list.xlsx
├── requirements.txt
├── logs_naukri/
│   └── log_naukri_YYYYMMDD_HHMMSS_... .log
└── Tailored_Resumes_Naukri/
    ├── Company_JobTitle_ID.html
    └── Company_JobTitle_ID.pdf
```

**Important:** Add `.env`, `logs_naukri/`, `Tailored_Resumes_Naukri/`, `*.xlsx`, and `venv/` to your `.gitignore` file.

## Output Explanation 📊📄

*   **`naukri_jobs_master_list.xlsx`:** The central data store. See the Excel Column Details section below.
*   **`logs_naukri/` Folder:** Contains detailed log files for each run.
*   **`Tailored_Resumes_Naukri/` Folder:** Contains the output of Phase 4 (tailored HTML and PDF files).

## Excel Column Details

This section details the columns found in the `naukri_jobs_master_list.xlsx` output file.

| Column Name | Source / Purpose |
|---|---|
| **--- Phase 1: List Scraping Columns (From Job Card) ---** | |
| Naukri Job ID | Naukri's unique identifier for the job posting. |
| Job Title | The job title as listed on the job card. |
| Job Detail Page URL | Direct URL to the Naukri job posting page. |
| Company Name | The hiring company's name from the job card. |
| Actual Posting Company | The name of the recruiter or actual company posting. |
| Company Logo URL | URL for the company's logo image. |
| Company Rating (AmbitionBox) | Company rating sourced from AmbitionBox. |
| Company Reviews Count (AmbitionBox) | Number of company reviews on AmbitionBox. |
| AmbitionBox Review Link | Link to the company's AmbitionBox page. |
| Experience Required | Required experience range (e.g., "2-7 Yrs"). |
| Location(s) | Job location(s) listed on the card. |
| Job Snippet | A short description or snippet of the job. |
| Key Skills/Tags (from card) | Skills listed on the job search card. |
| Posted Ago Text | Raw text of when the job was posted (e.g., "3 Days Ago"). |
| Posted Days Ago | Calculated number of days since posting. |
| Is Promoted/Sponsored | Flag if the job is a promoted listing. |
| Salary Indication (from Card/Filters) | Salary range indicated on the card, if available. |
| **--- Phase 2: Detailed Page Scraping Columns ---** | |
| Is Already Applied | Flag indicating if you've already applied on Naukri. |
| Apply Button Type | Type of apply button (e.g., "Apply", "Apply on Company Site"). |
| Company Website (Official) | The official website of the company. |
| Posted Ago Text Detailed | More precise posting time from the detail page. |
| Posted Days Ago (Detailed) | Calculated days from the detailed posting text. |
| Openings | Number of open positions for the job. |
| Applicants | Number of applicants for the job. |
| Job Highlights | Key highlights or selling points of the job. |
| Key Company Highlights | Key highlights about the company. |
| Match: Early Applicant | Naukri's match score indicator. |
| Match: Keyskills | Naukri's match score indicator. |
| Match: Location | Naukri's match score indicator. |
| Match: Work Experience | Naukri's match score indicator. |
| Full Job Description HTML | Raw HTML of the full job description. |
| Full Job Description Plain Text | Plain text version of the job description for AI analysis. |
| Role (Detailed) | The specific role for the position. |
| Industry (Detailed) | The company's industry type. |
| Functional Area/Department (Detailed) | The department or functional area for the role. |
| Employment Type (Detailed) | Type of employment (e.g., "Full Time, Permanent"). |
| Role Category (Detailed) | The category of the role. |
| Education Requirements (Detailed) | Required educational qualifications. |
| Key Skills (from detail page) | Detailed list of key skills from the job page. |
| About Company (Detailed) | The "About" section for the company. |
| Company Info Tags | Tags associated with the company (e.g., "MNC"). |
| Follower Count | Number of followers the company has on Naukri. |
| Company HQ Address | The headquarter address of the company. |
| Awards & Recognitions | Any listed awards or recognitions. |
| Benefits & Perks | Listed employee benefits and perks. |
| Date Scraped Detailed | Timestamp when the detailed scraping was completed. |
| Scraping Issues (Phase 2) | Any non-critical issues during Phase 2 scraping. |
| **--- Common Columns for All Phases ---** | |
| Source | Source of the job listing (e.g., "Naukri.com"). |
| Date Added | Timestamp when the job was first added to the Excel file. |
| Status | Tracks the job's progress through the workflow. |
| Applied Date | Placeholder for you to manually enter application date. |
| Notes | Placeholder for your notes or for error messages. |
| **--- AI & Tailoring Columns (Phases 3, 4, 5) ---** | |
| Extracted Responsibilities | Key responsibilities extracted by AI. |
| Extracted Required Skills | Required skills extracted by AI. |
| Extracted Preferred Skills | Preferred skills extracted by AI. |
| Extracted Experience Level | Experience level extracted by AI. |
| Extracted Key Qualifications | Key qualifications extracted by AI. |
| Extracted Company Description (from JD) | Company description extracted by AI from the JD. |
| AI Match Score (Base Resume) | AI's score of your base resume against the JD. |
| AI Score Justification (Base Resume) | AI's reasoning for the score. |
| AI Strengths (Base Resume) | Strengths of your base resume identified by AI. |
| AI Areas for Improvement (Base Resume) | Improvement areas identified by AI. |
| AI Actionable Recommendations (Base Resume) | Tailoring recommendations from AI. |
| Keyword Match Score (Base Resume) | Component score for keyword alignment. |
| Achievements Score (Base Resume) | Component score for quantifiable achievements. |
| Summary Quality Score (Base Resume) | Component score for resume summary. |
| Structure Score (Base Resume) | Component score for resume structure. |
| Tools Certs Score (Base Resume) | Component score for tools and certifications. |
| Total Match Score (Base Resume) | Sum of component scores, used for tailoring threshold. |
| Generated Tailored Summary | The tailored summary text generated by AI. |
| Generated Tailored Bullets | The tailored bullet points generated by AI. |
| Generated Tailored Skills List | The tailored skills list generated by AI. |
| Tailored HTML Path | File path to the generated tailored HTML resume. |
| Tailored PDF Path | File path to the generated tailored PDF resume. |
| Tailored PDF Pages | Page count of the generated PDF. |
| Tailored Resume Score (Rescore) | The new score of the tailored resume after rescoring. |
| Score Change (Rescore) | The difference between the new and original scores. |
| Tailoring Effectiveness Status (Rescore) | Categorizes the result (e.g., "Improved", "Maintained"). |
| Retailoring Attempts | Counter for re-tailoring attempts. |

## Error Handling & Troubleshooting ⚠️
*   **Selenium Connection Error:** Ensure Chrome is running with the correct `--remote-debugging-port` and that the port number matches the config.
*   **ChromeDriver Error:** Make sure your ChromeDriver version matches your Chrome browser version.
*   **Naukri.com Selector Errors:** Naukri.com has likely updated its website. Use browser developer tools to find the correct CSS selectors and update `CONFIG_NAUKRI_SELECTORS` in `main_workflow_naukri.py`.
*   **API Errors:** Check your `GEMINI_API_KEY` in the `.env` file. Check your Google Cloud Console for API limits or billing issues.
*   **WeasyPrint Errors:** This usually indicates missing system dependencies. Revisit the prerequisites and install the necessary libraries for your OS.
*   **PermissionError (Saving Excel):** Ensure `naukri_jobs_master_list.xlsx` is closed.
*   **FileNotFoundError:** Double-check all file paths in `CONFIG_PATHS_NAUKRI`. Ensure `naukri_search_config.json` exists.

## Future Enhancements / Roadmap 💡
*   **Support for Other Job Boards:** Modularize scraping logic to add support for Indeed, LinkedIn, etc.
*   **GUI for Configuration:** A simple UI (e.g., with Streamlit) could make configuration easier.
*   **Database Storage:** Replace Excel with a database like SQLite for better performance.
*   **Direct Application (Use with Caution):** Explore integrating with "Apply" functionality where possible.
*   **Cost Tracking:** Estimate Gemini API usage costs.
