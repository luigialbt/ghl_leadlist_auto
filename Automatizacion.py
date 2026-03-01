import json, asyncio, os, random, glob, sys, platform, ctypes, shutil
import pandas as pd
from playwright.async_api import async_playwright
from playwright.async_api import TimeoutError as PlaywrightTimeoutError

# Centralized folder name
DOWNLOAD_FOLDER = "downloads"

# ==========================================
# FUNCTION 0: CLEAN FOLDER
# ==========================================
def clean_downloads():
    """Wipes the downloads folder clean to prevent processing old files."""
    if os.path.exists(DOWNLOAD_FOLDER):
        print(f"--- PREP: Cleaning out old '{DOWNLOAD_FOLDER}' folder... ---")
        shutil.rmtree(DOWNLOAD_FOLDER)
    os.makedirs(DOWNLOAD_FOLDER)
    print(f"--- PREP: '{DOWNLOAD_FOLDER}' is clean and ready. ---\n")

# ==========================================
# FUNCTION 1: DOWNLOAD FILES
# ==========================================
async def downloadFiles():
    """Logs into lovable, finds the list limit, downloads, and calls insertPhone."""
    with open('info.json', 'r') as f:
        data = json.load(f)
    
    user = data["lovable"]["username"]
    pw = data["lovable"]["password"]
    website = data["lovable"]["website"]

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()

        print("--- PHASE 1: DOWNLOADING FILES ---")
        print("Logging in to zip-to-win...")
        await page.goto(website) 
        await page.get_by_placeholder("Username").fill(user)
        await page.get_by_placeholder("Password").fill(pw)
        await page.click("button[type='submit']")

        await page.wait_for_selector("a[download]")
        
        try:
            # timeout=8000 means exactly 8 seconds (Playwright uses milliseconds)
            limit_text = await page.locator("span.bg-primary\\/20").inner_text(timeout=8000)
            limit = int(limit_text.strip()) 
            print(f"Limit found: {limit}")
            
        except PlaywrightTimeoutError:
            print("\n[!] CRITICAL: Limit badge did not appear within 8 seconds.")
            
            # Play a softer system sound alert
            if platform.system() == "Windows":
                import winsound
                winsound.PlaySound("SystemAsterisk", winsound.SND_ALIAS)
            else:
                # Mac/Linux fallback
                sys.stdout.write('\a')
                sys.stdout.flush()
                
            print("Terminating script immediately.")
            await browser.close()
            sys.exit(1)

        cards = await page.locator("div.group").all()
        target_cards = cards[:limit]

        print(f"Found {len(target_cards)} items. Starting sequence...")

        for i, card in enumerate(target_cards, 1):
            try:
                full_text = await card.locator("h4.text-foreground").inner_text()
                clean_name = full_text.split('-')[0].strip()
                download_path = os.path.join(DOWNLOAD_FOLDER, f"{clean_name}_lit.csv")

                delay = random.uniform(1.5, 3.5)
                await asyncio.sleep(delay)

                print(f"[{i}/{limit}] Downloading: {clean_name}...")

                async with page.expect_download() as download_info:
                    await card.locator("a[download]").click()
                
                download = await download_info.value
                await download.save_as(download_path)

                # Edit the CSV immediately after downloading
                await asyncio.sleep(0.5) 
                if insertPhone(download_path):
                    print(f"  └─ Successfully added 'phone number' to Column I.")

            except Exception as e:
                print(f"  └─ Error on row {i}: {e}")

        print("Finished downloading and editing files.\n")
        await asyncio.sleep(2)
        await browser.close()


# ==========================================
# FUNCTION 2: INSERT PHONE
# ==========================================
def insertPhone(file_path):
    """Inserts a completely blank row at the top of the CSV, and adds 'phone number' in Column I."""
    try:
        # Read the CSV as raw data (header=None) so the original top row isn't treated as a title
        df = pd.read_csv(file_path, header=None, dtype=str)
        df.fillna('', inplace=True) # Change any NaN values to pure blank strings
        
        # Ensure the file has at least 9 columns (0 through 8) so Column I actually exists
        while len(df.columns) < 9:
            df[len(df.columns)] = ""
            
        # Create a completely blank row matching the width of the file
        new_row = [""] * len(df.columns)
        
        # Put 'phone number' in Column I (which is index 8)
        new_row[8] = "phone number"
        
        # Turn our new row into a mini DataFrame
        top_row_df = pd.DataFrame([new_row])
        
        # Stack the new row perfectly on top of the original data
        df_final = pd.concat([top_row_df, df], ignore_index=True)
        
        # Save it back over the original file, ensuring no weird Pandas headers get added
        df_final.to_csv(file_path, index=False, header=False, na_rep='')
        return True
        
    except Exception as e:
        print(f"  └─ CSV Edit Error: {e}")
        return False


# ==========================================
# FUNCTION 3: SCRUB LITIGATOR
# ==========================================
async def scrubLitigator():
    """Logs into TCPA, uploads the edited files in order, and saves scrubbed results mimicking a fast human."""
    with open('info.json', 'r') as f:
        data = json.load(f)
    
    tcpa_user = data["tcpa"]["username"]
    tcpa_pw = data["tcpa"]["password"]
    tcpa_website_1 = data["tcpa"]["website_1"]
    tcpa_website_2 = data["tcpa"]["website_2"]

    # Grab and sort files by oldest first (download order)
    files = glob.glob(os.path.join(DOWNLOAD_FOLDER, "*_lit.csv"))
    files_to_scrub = sorted(files, key=os.path.getmtime)
    
    if not files_to_scrub:
        print("No '_lit.csv' files found to scrub.")
        return

    print("--- PHASE 2: SCRUBBING FILES ---")
    print(f"Found {len(files_to_scrub)} files. Initiating fast-human sequence...")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()

        print("Navigating to TCPA Litigator List...")
        await page.goto(tcpa_website_1) 
        
        await asyncio.sleep(random.uniform(0.8, 1.5))
        
        # Fast human typing
        await page.locator("input[name='username']").press_sequentially(
            tcpa_user, delay=random.randint(15, 40)
        )
        
        await asyncio.sleep(random.uniform(0.2, 0.5))
        
        await page.locator("input[name='password']").press_sequentially(
            tcpa_pw, delay=random.randint(15, 40)
        )
        
        await asyncio.sleep(random.uniform(0.3, 0.7))
        await page.locator("input[name='uwp_login_submit']").click(delay=random.randint(30, 80))

        await page.wait_for_load_state("networkidle")
        await asyncio.sleep(random.uniform(1.0, 1.5))

        for i, file_path in enumerate(files_to_scrub, 1):
            filename = os.path.basename(file_path)
            clean_name = filename.replace('_lit.csv', '')
            print(f"[{i}/{len(files_to_scrub)}] Uploading {filename}...")

            await page.goto(tcpa_website_2)
            await asyncio.sleep(random.uniform(0.6, 1.2))
            
            # 1. Upload file into the hidden input
            await page.locator("#compare_file").set_input_files(file_path)
            
            # Brief pause to let the file register in the browser
            await asyncio.sleep(random.uniform(0.4, 0.8))

            # 2. Click the main 'Step 3: Upload and scrub' button
            print("  └─ Clicking 'Upload and scrub'...")
            await page.locator("#scrub-form-submit-btn").click(delay=random.randint(30, 80))
            
            # Wait a fraction of a second for the modal animation to slide in
            await asyncio.sleep(random.uniform(0.5, 1.0))
            
            # 3. Click the 'Accept' button in the popup modal
            print("  └─ Clicking 'Accept' on confirmation modal...")
            await page.locator("button.modal-apply-btn").click(delay=random.randint(30, 80))
            
            try:
                print("  └─ File queued! Waiting for server to process (this can take 2-3 minutes for large lists)...")
                
                # 4. Use a strict, live-evaluated CSS selector.
                clean_link = page.locator("tbody tr:nth-child(1) td.td-clean_xls a[download]")
                
                # Bumping the timeout to 3 full minutes (180,000 ms).
                await clean_link.wait_for(state="visible", timeout=180000)
                
                print("  └─ Processing finished! Download link is ready. Fetching file...")
                
                # 5. Download the Excel file
                async with page.expect_download() as download_info:
                    await clean_link.click(delay=random.randint(30, 80))
                
                download = await download_info.value
                temp_xlsx_path = os.path.join(DOWNLOAD_FOLDER, f"{clean_name}_temp.xlsx")
                await download.save_as(temp_xlsx_path)
                
                # 6. Convert Excel to CSV (Fixed for blank columns/headers)
                final_csv_path = os.path.join(DOWNLOAD_FOLDER, f"{clean_name}.csv")
                df_scrubbed = pd.read_excel(temp_xlsx_path, header=None)
                df_scrubbed.to_csv(final_csv_path, index=False, header=False, na_rep='')
                
                # Clean up temporary Excel file
                os.remove(temp_xlsx_path)
                
                # --- NEW STEP: Delete the original *_lit.csv file ---
                os.remove(file_path)
                
                print(f"  └─ Converted and correctly formatted {clean_name}.csv")
                print(f"  └─ Deleted original unscrubbed file ({filename})")

            except PlaywrightTimeoutError:
                print(f"\n[!] CRITICAL: Server timed out or link never appeared for {filename}.")
                
                if platform.system() == "Windows":
                    import winsound
                    winsound.PlaySound("SystemAsterisk", winsound.SND_ALIAS)
                    
                    # Show the native Windows pop-up warning
                    ctypes.windll.user32.MessageBoxW(
                        0, 
                        f"Failed to process file:\n{filename}\n\nThe server took too long to reload or the link did not appear.", 
                        "TCPA Scrubber Timeout", 
                        0x10
                    )
                else:
                    sys.stdout.write('\a')
                    sys.stdout.flush()
                
                print("Terminating script immediately.")
                await browser.close()
                sys.exit(1) 
                
            except Exception as e:
                print(f"  └─ Failed during download/convert phase: {e}")
            
            # --- TEST MODE BREAK ---
            print("\n[TEST MODE] Stopping after 1 file.")
            break

# ==========================================
# FUNCTION 4: UPLOAD TO GHL
# ==========================================
async def uploadGHL():
    """Navigates to GHL, logs in, handles 2FA, and searches for sub-accounts based on file names."""
    with open('info.json', 'r') as f:
        data = json.load(f)
    
    ghl_user = data["ghl"]["username"]
    ghl_pw = data["ghl"]["password"]
    ghl_website = data["ghl"]["website"]

    # Grab only the final, scrubbed CSV files (ignoring the _lit ones)
    files_to_upload = glob.glob(os.path.join(DOWNLOAD_FOLDER, "*.csv"))
    files_to_upload = [f for f in files_to_upload if not f.endswith("_lit.csv")]

    if not files_to_upload:
        print("No scrubbed files found to upload to GHL.")
        return

    print("--- PHASE 3: UPLOADING TO GHL ---")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()

        print("Navigating to GHL...")
        await page.goto(ghl_website)
        
        # --- LOGIN SEQUENCE ---
        print("  └─ Entering credentials...")
        await asyncio.sleep(random.uniform(1.0, 2.0))
        await page.locator("#email").fill(ghl_user)
        await asyncio.sleep(random.uniform(0.3, 0.7))
        await page.locator("#password").fill(ghl_pw)
        await asyncio.sleep(random.uniform(0.3, 0.7))
        print("  └─ Clicking 'Iniciar sesión'...")
        await page.locator("button[type='submit']").click(delay=random.randint(30, 80))
        
        switcher_btn = page.locator("span.hl_switcher-loc-name", has_text="Click here to switch")

        # --- 2FA / OTP CHECK ---
        print("  └─ Checking if 2FA/OTP validation is required...")
        try:
            otp_input = page.locator("input.otp-input").first
            await otp_input.wait_for(state="visible", timeout=8000)
            
            print("  [!] 2FA screen detected! Waiting for manual 6-digit OTP input (7-minute timeout)...")
            await otp_input.click()
            
            for minute in range(7):
                if await switcher_btn.is_visible():
                    break
                print(f"      -> Action required: Enter OTP in browser. ({minute+1}/7 minutes)")
                if platform.system() == "Windows":
                    import winsound
                    winsound.PlaySound("SystemAsterisk", winsound.SND_ALIAS | winsound.SND_ASYNC)
                for _ in range(30):
                    if await switcher_btn.is_visible():
                        break 
                    await asyncio.sleep(2)
                    
            if not await switcher_btn.is_visible():
                print("  [!] CRITICAL: 7-minute timeout reached. Terminating.")
                await browser.close()
                sys.exit(1)
        except PlaywrightTimeoutError:
            print("  └─ No 2FA requested. Proceeding...")

        # --- SUB-ACCOUNT SEARCH & SWITCH LOOP ---
        for i, file_path in enumerate(files_to_upload, 1):
            filename = os.path.basename(file_path)
            # Remove '.csv' to get the exact sub-account name
            sub_account_name = filename.replace('.csv', '').strip()
            
            print(f"\n[{i}/{len(files_to_upload)}] Processing sub-account: '{sub_account_name}'")

            # 1. Click Switcher
            print("  └─ Waiting for dashboard and clicking location switcher...")
            await switcher_btn.wait_for(state="visible", timeout=30000)
            await switcher_btn.click(delay=random.randint(30, 80))

            # 2. Type in the Search Bar
            search_input = page.locator("input[name='search'][placeholder='Search for a sub-account']")
            await search_input.wait_for(state="visible", timeout=10000)
            print(f"  └─ Searching for '{sub_account_name}'...")
            await search_input.fill(sub_account_name)
            
            # Brief pause to let GHL's live-search results populate
            await asyncio.sleep(2.5)

            # 3. Check Results for Case-Insensitive Match
            results_locator = page.locator("span.hl_location-title")
            result_count = await results_locator.count()
            
            matched = False
            for j in range(result_count):
                text = await results_locator.nth(j).inner_text()
                
                # Convert both to lowercase to ignore capitalization differences
                if text.strip().lower() == sub_account_name.lower():
                    print(f"  └─ Match found! Clicking '{text}'...")
                    await results_locator.nth(j).click(delay=random.randint(30, 80))
                    matched = True
                    break # Stop looking, we found it!
            
            # 4. Handle No Match (Manual Intervention)
            if not matched:
                print(f"  [!] No exact match found for '{sub_account_name}'.")
                print("  [!] Waiting up to 3 minutes for you to manually select the account...")
                
                if platform.system() == "Windows":
                    import winsound
                    # Using "SystemHand" for a slightly more urgent/error-style sound
                    winsound.PlaySound("SystemHand", winsound.SND_ALIAS | winsound.SND_ASYNC)
                
                try:
                    # If you click a result manually, the search box disappears. We wait for that.
                    await search_input.wait_for(state="hidden", timeout=180000) # 180,000 ms = 3 mins
                    print("  └─ Dropdown closed! Assuming manual selection was successful.")
                except PlaywrightTimeoutError:
                    print("  [!] 3 minutes passed. Search box never closed. Moving to next file...")
                    # Press Escape to close the dropdown and skip this file if you ignored it
                    await page.keyboard.press("Escape")
                    await asyncio.sleep(1)
                    continue 

            # --- 5. NAVIGATE TO CONTACTS & START IMPORT ---
            print("  └─ Navigating to Contacts...")
            
            contacts_link = page.locator("#sb_contacts")
            await contacts_link.wait_for(state="visible", timeout=30000)
            await contacts_link.click(delay=random.randint(30, 80))

            # We completely removed the networkidle wait here.
            # Now we just wait purely for the button to exist and be visible.
            print("  └─ Waiting for the 'Import' button to render...")
            import_btn = page.locator("button#import-btn").first
            
            # Wait up to 30 seconds specifically for this button to appear on the screen
            await import_btn.wait_for(state="visible", timeout=30000)
            
            # Tiny pause to ensure Vue.js has finished attaching the click event listener
            await asyncio.sleep(1.0) 
            
            print("  └─ Clicking the 'Import' button...")
            await import_btn.click(delay=random.randint(30, 80))
            
            print("  └─ Waiting for the 'Next' button...")
            next_btn = page.locator("#next-import-button-1").first
            await next_btn.wait_for(state="visible", timeout=10000)
            
            # Tiny pause for the modal animation
            await asyncio.sleep(0.5)
            await next_btn.click(delay=random.randint(30, 80))
            
            print("  └─ Ready for file upload!")
            await asyncio.sleep(2)
            
            # --- 6. UPLOAD FILE & MAP FIELDS ---
            print(f"  └─ Uploading file: {filename}...")
            
            # Target the hidden file input directly
            await page.locator("input.n-upload-file-input").set_input_files(file_path)
            
            # Brief pause to let the frontend register the file
            await asyncio.sleep(random.uniform(0.5, 1.0))

            print("  └─ Clicking 'Next' to proceed to mapping...")
            # Grab the visible 'Next' button
            upload_next_btn = page.locator("button", has_text="Next").locator("visible=true").last
            await upload_next_btn.wait_for(state="visible", timeout=15000)
            await upload_next_btn.click(delay=random.randint(30, 80))

            print("  └─ Waiting for mapping screen to render...")
            
            # Dictionary matching the Playwright index (0-based) to the Field Name
            fields_to_map = {
                0: "First Name",
                1: "Last Name",
                2: "Street Address",
                4: "City",
                5: "State"
            }
            
            # Grab all the dropdown inputs on the screen
            mapping_inputs = page.locator("input.n-base-selection-input")
            
            # Wait purely for the first dropdown to appear instead of relying on the page load
            await mapping_inputs.first.wait_for(state="visible", timeout=30000)
            await asyncio.sleep(1.0) # Let the rest of the dropdowns fully render
            
            print("  └─ Mapping specific fields...")

            # Loop through only our specifically defined indexes
            for index, field_name in fields_to_map.items():
                print(f"      -> Mapping dropdown {index + 1} to '{field_name}'")
                
                # 1. Click the specific dropdown box to open the menu and focus it
                await mapping_inputs.nth(index).click(delay=random.randint(30, 80))
                await asyncio.sleep(random.uniform(0.4, 0.7)) 
                
                # 2. Type the field name using the keyboard to filter the virtual list!
                print(f"         Filtering for '{field_name}'...")
                await page.keyboard.type(field_name, delay=random.randint(30, 60))
                await asyncio.sleep(random.uniform(0.4, 0.7)) # Give the UI a moment to filter
                
                # 3. Click the specific text now that it is forced to the top of the visible list
                dropdown_menu = page.locator(".n-base-select-menu")
                
                # Using force=True just in case the scrollbar slightly overlaps the text
                await dropdown_menu.get_by_text(field_name, exact=True).first.click(delay=random.randint(30, 80), force=True)
                
                await asyncio.sleep(random.uniform(0.2, 0.5))

            # --- 7. ADVANCED OPTIONS: ADD TAGS ---
            print("  └─ Configuring Advanced Options...")
            
            # Wait for the specific checkbox container to be fully attached and visible
            checkbox_container = page.locator("#do-not-import-data")
            await checkbox_container.wait_for(state="visible", timeout=15000)

            print("  └─ Checking the 'Don't import data' checkbox...")
            await checkbox_container.click(delay=random.randint(30, 80), force=True)
            
            # Wait for the checkmark to actually register in the software
            try:
                await page.locator('#do-not-import-data[aria-checked="true"]').wait_for(state="attached", timeout=3000)
                print("  └─ Checkbox successfully checked!")
            except Exception:
                print("  └─ Warning: Checkbox state didn't update visually, but click was sent.")

            print("  └─ Clicking 'Next' to finalize mapping...")
            mapping_next_btn = page.locator("button", has_text="Next").locator("visible=true").last
            await mapping_next_btn.click(delay=random.randint(30, 80))

            # --- NEW CHECKBOX CLICK ---
            print("  └─ Checking the 3rd advanced options checkbox...")
            
            # Target the visible checkbox boxes and select the 3rd one (index 2)
            advanced_checkbox = page.locator(".n-checkbox-box").locator("visible=true").nth(2)
            await advanced_checkbox.click(delay=random.randint(30, 80), force=True)
            await asyncio.sleep(random.uniform(0.5, 1.0))

            print("  └─ Clicking the tag dropdown...")
            # Target the tag selection box wrapper
            tag_dropdown = page.locator(".n-base-selection-tags").first
            await tag_dropdown.click(delay=random.randint(30, 80), force=True)
            await asyncio.sleep(random.uniform(0.4, 0.8))
            
            print("  └─ Typing tag 'lovable'...")
            # Target the input that appears using its exact placeholder text
            tag_input = page.locator('input[placeholder="Search / create tags"]')
            await tag_input.wait_for(state="visible", timeout=5000)
            
            # Use press_sequentially to mimic human typing and trigger the dropdown list
            await tag_input.press_sequentially("lovable", delay=random.randint(30, 60))
            
            # Wait a moment for GHL to search or generate the 'lovable' tag option
            await asyncio.sleep(random.uniform(0.8, 1.2)) 

            print("  └─ Selecting the tag from the list...")
            # Target the dropdown item containing the text
            tag_option = page.locator(".item.tags").filter(has_text="lovable").first
            await tag_option.wait_for(state="visible", timeout=5000)
            await tag_option.click(delay=random.randint(30, 80), force=True)
            print("  └─ Tag added successfully!")

            print("  └─ Checking the final checkbox at the bottom...")
            # Target the very last visible checkbox box on the screen
            final_checkbox = page.locator(".n-checkbox-box").locator("visible=true").last
            await final_checkbox.click(delay=random.randint(30, 80), force=True)
            await asyncio.sleep(random.uniform(0.5, 1.0))

            # --- 8. FINAL SUBMIT: START BULK IMPORT ---
            print("  🚀 Clicking 'Start Bulk Import'...")
            
            # Target by the specific ID provided in your HTML
            submit_button = page.locator("#next-import-button-4")
            
            # Ensure it's ready to be clicked
            await submit_button.wait_for(state="visible", timeout=10000)
            
            # Final click to launch the process
            await submit_button.click(delay=random.randint(100, 200))
            
            print("  ✅ Import process started successfully!")
            
            # Wait a few seconds for the 'Success' toast or page redirection
            await asyncio.sleep(5.0)

            # --- TEST MODE BREAK ---
            print("\n[TEST MODE] Stopping after 1 file.")
            break

        # await browser.close()

# ==========================================
# MAIN ORCHESTRATOR
# ==========================================
if __name__ == "__main__":
    async def main():
        # Wipe the folder clean before we start
        #clean_downloads()

        # Execute Phase 1 (Download + Insert Phone)
        #await downloadFiles()
        
        # Execute Phase 2 (Upload + Scrub)
        #await scrubLitigator()

        # Execute Phase 3 (Upload)
        await uploadGHL()

    # Run the entire sequence
    asyncio.run(main())