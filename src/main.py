from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
import os
import json
from dotenv import load_dotenv
import zipfile
import os
import shutil
import time

# Colors
RED = "\033[31m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
BLUE = "\033[34m"
MAGENTA = "\033[35m"
CYAN = "\033[36m"
RESET = "\033[0m"  # Reset color

# load environment variables
load_dotenv(override=True)
username = os.getenv("USERNAME")
password = os.getenv("PASSWORD")

print(f"[LOG] Loaded Env File | Username: {BLUE}{username}{RESET}, Password: {BLUE}{password}{RESET}")

# Load input file
with open(os.path.abspath(f'input/input.json')) as f:
    data = json.load(f)
    input_file = data["file"]
    input_file_type = data["type"]
    input_request = data["request"]

print(f"[LOG] Loaded Input File | File: {BLUE}{input_file}{RESET}, Type: {BLUE}{input_file_type}{RESET}, Request: {BLUE}{input_request}{RESET}")

# if makerbot_downloads folder exists, delete it
if os.path.exists(os.path.abspath(f'makerbot_downloads')):
    shutil.rmtree(os.path.abspath(f'makerbot_downloads'))

# Set download location
profile = Options()
profile.set_preference("browser.download.folderList", 2)
profile.set_preference("browser.download.manager.showWhenStarting", False)
profile.set_preference("browser.download.dir", os.path.abspath("makerbot_downloads"))
profile.set_preference("browser.helperApps.neverAsk.saveToDisk", "application/x-gzip")

driver = webdriver.Firefox(options=profile)
driver.get("https://login.makerbot.com/login")

def login(username, password):
    # wait until input#username is visible
    username_input = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, "username"))
    )
    # username = driver.find_element(By.ID,"username")
    username_input.send_keys(username)

    # wait until input#password is visible
    password_input = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, "password"))
    )
    # password = driver.find_element(By.ID,"password")
    password_input.send_keys(password)

    sign_in_btn = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "div.button.button-primary"))
    )

    sign_in_btn.click()

# Log in to Makerbot Print
login(username, password)
print(f"[LOG] {GREEN}Successfully Logged into Makerbot Print{RESET}")

try:
    printer_status = WebDriverWait(driver, 30).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "div.ellipsis.status-text"))
    )
except:
    print(f"[ERROR] {RED}Printer not found - Quitting{RESET}")
    driver.quit()
    quit()

if printer_status.text.lower() == "offline":
    printer_status_color = RED
else:
    printer_status_color = GREEN
print(f"[LOG] Printer Status: {printer_status_color}{printer_status.text}{RESET}")

if input_request == "printer-status":
    print(f"[SUCCESS] {GREEN}Printer Status: {printer_status_color}{printer_status.text}{RESET}")
    driver.quit()
    quit()

if printer_status.text.lower() == "offline":
    print(f"[ERROR] {RED}Printer is Offline - Quitting{RESET}")
    driver.quit()
    quit()

if printer_status.text.lower() != "idle":
    print(f"[ERROR] {RED}Printer is not Idle - Quitting{RESET}")
    driver.quit()
    quit()

print_btn = WebDriverWait(driver, 10).until(
    EC.presence_of_element_located((By.XPATH, "//span[@class='word' and normalize-space(text())='Print']"))
)

print_btn.click()

time.sleep(2)

iframe = WebDriverWait(driver, 10).until(
    EC.presence_of_element_located((By.XPATH, "//iframe[@class='cloudprint-iframe']"))
)
driver.switch_to.frame(iframe)

choose_printer_btn = WebDriverWait(driver, 20).until(
    EC.presence_of_element_located((By.ID, "printer-dropdown-id"))
)

choose_printer_btn.click()

# def print_makerbot_file(driver, input_file): 

def modify_zip_file(zip_path, file_to_modify, modify_func):
    # Create a temporary directory
    temp_dir = "temp_zip_mod"
    os.makedirs(temp_dir, exist_ok=True)

    # Extract the file you want to modify
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extract(file_to_modify, temp_dir)

    # Apply your modifications using the provided modify_func
    file_path = os.path.join(temp_dir, file_to_modify)
    modify_func(file_path)

    # Create the past_prints folder if it doesn't exist
    past_prints_folder = os.path.abspath("past_prints")
    os.makedirs(past_prints_folder, exist_ok=True)

    # Create a new ZIP file with the modified content in the past_prints folder
    original_filename = os.path.basename(zip_path)
    processed_zip_path = os.path.join(past_prints_folder, "processed_" + original_filename)
    printing_zip_path = os.path.join(past_prints_folder, f"print_me.makerbot")

    with zipfile.ZipFile(processed_zip_path, 'w') as new_zip:
        # Copy over all files from the original ZIP except the one modified
        with zipfile.ZipFile(zip_path, 'r') as original_zip:
            for item in original_zip.infolist():
                if item.filename != file_to_modify:
                    new_zip.writestr(item, original_zip.read(item.filename))

        # Add the modified file back into the ZIP
        new_zip.write(file_path, file_to_modify)

    # Create a copy of the processed zip file with the _PRINTING suffix
    shutil.copy2(processed_zip_path, printing_zip_path)

    # Clean up temporary files and directories
    shutil.rmtree(temp_dir)

    return processed_zip_path, printing_zip_path


# Example modify function: Append some text to a file
def replace_mk13_with_mk12(file_path):
    # Read the content of the file
    with open(file_path, 'r') as file:
        content = file.read()

    # Replace "mk13" with "mk12"
    modified_content = content.replace("mk13", "mk12")

    # Write the modified content back to the file
    with open(file_path, 'w') as file:
        file.write(modified_content)

def select_printer(driver, printer_css_selector):
    choose_printer_btn = WebDriverWait(driver, 30).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, printer_css_selector))
    )

    choose_printer_btn.click()

def select_extra_options_and_upload_and_queue_makerbot_file(driver, printing_zip_path):
    file_input = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, "//input[@type='file' and @id='uploadMakerbotFile']"))
    )
    
    print(f"[LOG] Printer Connection Established")

    print(f"[LOG] Uploading File: {BLUE}{printing_zip_path}{RESET}")

    file_input.send_keys(printing_zip_path)

    WebDriverWait(driver, 99).until(
        EC.presence_of_element_located((By.XPATH, "//p[normalize-space(text()) = 'Do you want to queue a print job for the uploaded model?']"))
    )

    queue_btn = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, "//button[normalize-space(text()) = 'Queue']"))
    )

    queue_btn.click()

def print_latest_queued_print_job(driver):
    # print(f"[LOG] Print Job Queued")
    driver.get("https://cloudprint.makerbot.com/workspace")

    # # save page_source to html file
    # with open('print_job_queued.html', 'w') as f:
    #     f.write(driver.page_source)
    
    # wait for tr with attribute data-rbd-draggable-context-id="1" to appear
    dots = WebDriverWait(driver, 20).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "div#testing.dropdown-toggle"))
    )

    dots.click()

    # wait for span with text "Start Print Job" to appear
    open_print_menu_btn = WebDriverWait(driver, 20).until(
        EC.presence_of_element_located((By.XPATH, "//span[normalize-space(text()) = 'Start Print Job']"))
    )

    open_print_menu_btn.click()

    WebDriverWait(driver, 20).until(
        EC.presence_of_element_located((By.XPATH, "//div[normalize-space(text()) = 'Confirm build plate is clear']"))
    )

    start_print_btn = WebDriverWait(driver, 20).until(
        EC.presence_of_element_located((By.XPATH, "//div[normalize-space(text()) = 'START PRINT']"))
    )

    # print(f"[LOG] {GREEN}Print Job Queued{RESET}")

    start_print_btn.click()

if input_file_type == "makerbot":
    print(f"[LOG] Processing Makerbot File")
    # print(f"[LOG] Waiting 10 Seconds for Makerbot to load")
    # time.sleep(10)

    select_printer(driver, "div#online-printer_MakerBot-Replicator")

    modified_zip, printing_zip_path = modify_zip_file(os.path.abspath(f'input/{input_file}'), 'meta.json', replace_mk13_with_mk12)
    
    print(f"[LOG] Processed File")

    print(f"[LOG] Waiting for Printer Connection")

    select_extra_options_and_upload_and_queue_makerbot_file(driver, printing_zip_path)

    print(f"[LOG] Queued Print Job")

    WebDriverWait(driver, 99).until(
        EC.presence_of_element_located((By.XPATH, "//*[normalize-space(text()) = \"Your print job was added to the printer\'s queue\"]"))
    )

    print_latest_queued_print_job(driver)    

    print(f"[SUCCESS] {GREEN}Print Job Queued{RESET}")
    driver.quit()
    quit()

else:
    print(f"[LOG] Processing STL File -> Makerbot File")

    select_printer(driver, "div#offline-printer_Replicator-5th-Gen")

    import_btn = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, "//span[normalize-space(text()) = 'Import']"))
    )

    import_btn.click()

    try:
        try:
            arrow = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//*[starts-with(@class, 'CollapsedPrintSettings_icon__')]"))
            )

            arrow.click()
        except:
            # probs already open
            pass


        # padded base
        try:
            elem = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div#quick-settings_Base-Layer"))
            )
            elem.click()
            # print("CLicked")
            time.sleep(2)
            padded_base = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//*[normalize-space(text()) = 'Padded Base']"))
            )
            padded_base.click()
            print("[LOG] Padded Base Set")
            # time.sleep(200000)
        except Exception as e:
            print("[ERROR] Failed to set padded base")
            print(e)


        # temperature
        text_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//input[@type='text' and @placeholder='Search by Setting Name']"))
        )

        text_input.send_keys("Extruder 1 Temperatur")
        text_input.send_keys(Keys.RETURN)

        open_temp_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//*[starts-with(@class, 'Collapse_collapse')]"))
        )
        open_temp_input.click()

        temp_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//input[@value='215']"))
        )
        # temp_input.clear()
        temp_input.send_keys(Keys.BACK_SPACE)
        temp_input.send_keys(Keys.BACK_SPACE)
        temp_input.send_keys(Keys.BACK_SPACE)
        temp_input.send_keys(Keys.BACK_SPACE)
        # import time
        time.sleep(1)
        temp_input.send_keys('210')
        temp_input.send_keys(Keys.RETURN)

        # arrow.click()
        print("[LOG] Temperature Set")

    except Exception as e:
        print(e)
        print("[Error] Failed to apply custom settings")
        # driver.quit()
        # quit()
        while True:
            time.sleep(1)
        pass

    file_input = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, "//input[@type='file' and @id='importFile']"))
    )

    file_input.send_keys(os.path.abspath(f'input/{input_file}'))

    # check if text exists after 10 seconds
    try:
        error = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//div[normalize-space(text()) = '.makerbot Error']"))
        )

        if error:
            print("[LOG] Makerbot Server error occured, but avoided. Uploading STL File")
            open_anyways = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//div[@class='button button-primary' and normalize-space(text()) = 'OPEN ANYWAY']"))
            )
            open_anyways.click()
        else:
            print("[LOG] Uploaded STL File Successfully")
    except:
        print("[LOG] Uploading STL File Successfully")

    export_btn = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, '[data-testid="export-button"]'))
    )

    export_btn.click()

    # time.sleep()

    file_inpit_without_extension = input_file.replace(".stl", "")
    # wait 60 seconds for makerbot file to be created in makerbot_downloads folder. if not found, quit
    start_time = time.time()
    while not os.path.exists(os.path.abspath(f'makerbot_downloads/{file_inpit_without_extension}.makerbot')):
        time.sleep(1)
        print("[LOG] Waiting for Makerbot File to be created")
        if start_time > time.time() + 60:
            print("[ERROR] Makerbot File not found")
            driver.quit()
            quit()

    print(f"[LOG] Makerbot File Created")

    # now we just have to follow the same steps as for a Makerbot file!

    driver.refresh()
    # correct printer is for some reason auto selected!

    
    iframe = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, "//iframe[@class='cloudprint-iframe']"))
    )
    driver.switch_to.frame(iframe)

    # remove .stl from input file

    modified_zip, printing_zip_path = modify_zip_file(os.path.abspath(f'makerbot_downloads/{file_inpit_without_extension}.makerbot'), 'meta.json', replace_mk13_with_mk12)
    
    print(f"[LOG] Processed File")

    # save page_source to html file
    with open('print_job_queued.html', 'w') as f:
        f.write(driver.page_source)

    # find div with data-testid="main-print-button-group" and click on it

    extra_options = WebDriverWait(driver, 20).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "[data-testid='main-print-button-group'] > div > button"))
    )

    extra_options.click()

    select_extra_options_and_upload_and_queue_makerbot_file(driver, printing_zip_path)

    print(f"[LOG] Queued Print Job")

    WebDriverWait(driver, 99).until(
        EC.presence_of_element_located((By.XPATH, "//*[normalize-space(text()) = \"Your print job was added to the printer\'s queue\"]"))
    )

    print_latest_queued_print_job(driver)    

    print(f"[SUCCESS] {GREEN}Print Job Queued{RESET}")
    
    # delete makerbot_downloads folder if exists
    if os.path.exists(os.path.abspath(f'makerbot_downloads')):
        shutil.rmtree(os.path.abspath(f'makerbot_downloads'))

    driver.quit()
    quit()











    

