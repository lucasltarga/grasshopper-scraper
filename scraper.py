from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException
import time
import re

MAX_NO_CHANGE = 4 # Maximum consecutive scrolls with no new content   
SCROLL_WAIT_TIME = 2 # Seconds to wait after each scroll
BUTTON_CLICK_DELAY = 0.3 # Delay after clicking a button

class Scraper:
    def __init__(self):
        chrome_options = webdriver.ChromeOptions()
        self.driver = webdriver.Chrome(options=chrome_options)
    
    def load_all_reviews(self, max_scroll_attempts):
        """
        Scrolls the reviews section until no new content loads or max attempts reached.
        """
        review_section_selector = "div.m6QErb.DxyBCb"

        try:
            reviews_section = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, review_section_selector))
            )
        except TimeoutException:
            print("Review section not found.")
            return

        print("Scrolling reviews section...")
        
        last_height = self.driver.execute_script("return arguments[0].scrollHeight", reviews_section)
        no_change_count = 0
        
        for attempt in range(max_scroll_attempts):
            self.driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight", reviews_section)
            print(f"Scroll attempt {attempt + 1}/{max_scroll_attempts}")
            time.sleep(SCROLL_WAIT_TIME) # Wait for new content to load
            
            # Check if new content was loaded
            new_height = self.driver.execute_script("return arguments[0].scrollHeight", reviews_section)
            
            if new_height == last_height:
                no_change_count += 1
                print(f"No new content loaded ({no_change_count}/{MAX_NO_CHANGE})")
                
                if no_change_count >= MAX_NO_CHANGE:
                    print("No new content after multiple attempts. Stopping scroll.")
                    break
            else:
                no_change_count = 0  # Reset counter when new content is found
            
            last_height = new_height

        print(f"Finished scrolling after {attempt + 1} attempts")

    def expand_long_reviews(self):
        """
        Clicks all 'Mais' buttons to expand truncated review text.
        """
        expand_selector = "button[aria-label='Ver mais']"
        
        more_buttons = []
        
        try:
            more_buttons = WebDriverWait(self.driver, 5).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, expand_selector))
            )
            print(f"Found {len(more_buttons)} 'Mais' buttons.")
        except TimeoutException:
            print("No buttons found.")

        clicked_count = 0
        for button in more_buttons:
            try:
                self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", button)
                WebDriverWait(self.driver, 2).until(EC.element_to_be_clickable(button))
                button.click()
                clicked_count += 1
                time.sleep(BUTTON_CLICK_DELAY)
            except Exception:
                continue

        print(f"Clicked {clicked_count} 'Mais' buttons")

    def extract_reviews_data(self):
        """
        Extracts the review data from the loaded page.
        """
        reviews = []
        review_blocks_selector = "div.jJc9Ad"
        
        try:
            review_blocks = WebDriverWait(self.driver, 10).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, review_blocks_selector))
            )
        except TimeoutException:
            print("No review blocks found.")
            return reviews

        for block in review_blocks:
            try:
                user_name = block.find_element(By.CSS_SELECTOR, "div.d4r55").text
            except NoSuchElementException:
                user_name = "N/A"

            try:
                rating_aria_label = block.find_element(By.CSS_SELECTOR, "span.kvMYJc[role='img']").get_attribute("aria-label")
                # Simple parsing to extract the number from the string
                rating_match = re.search(r"(\d+\.?\d*)", rating_aria_label)
                rating = float(rating_match.group(1)) if rating_match else "N/A"
            except NoSuchElementException:
                rating = "N/A"

            try:
                review_date = block.find_element(By.CSS_SELECTOR, "span.rsqaWe").text
            except NoSuchElementException:
                review_date = "N/A"

            try:
                # Extract review text
                review_text = block.find_element(By.CSS_SELECTOR, "span.wiI7pd").text
            except NoSuchElementException:
                review_text = "N/A"

            additional_info = self.extract_additional_info(block)

            reviews.append({
                "user_name": user_name,
                "rating": rating,
                "review_date": review_date,
                "review_text": review_text,
                "additional_info": additional_info 
            })

            #DEBUG
            #print(f"Extracted review by {user_name}: {rating} stars on {review_date} - {review_text[:50]}... - {additional_info}")

        print(f"Extracted {len(reviews)} reviews.")
        return reviews

    def extract_additional_info(self, block):
        """
        Extracts additional information from review block like price, food rating, service rating, etc.
        Returns a formatted string with all found information.
        """
        additional_info = []
        
        try:
            info_elements = block.find_elements(By.CSS_SELECTOR, "div.PBK6be")
            
            for element in info_elements:
                try:
                    text = element.text.strip()
                    if text:
                        # Format the text properly (handle bold labels and values)
                        lines = text.split('\n')
                        if len(lines) >= 2:
                            # Case: Label on first line, value on second
                            label = lines[0].replace(':', '').strip()
                            value = lines[1].strip()
                            additional_info.append(f"{label}: {value}")
                        else:
                            # Case: Single line with format "Label: value"
                            additional_info.append(text)
                except NoSuchElementException:
                    continue
                    
        except NoSuchElementException:
            pass
        
        return '\n'.join(additional_info)
    
    def scrape_reviews(self, url, max_scroll_attempts=1000):
        """
        Main method to orchestrate the scraping of a given Google Maps place URL.
        """
        try:
            self.driver.get(url)
            # Wait for the page to load initially
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "body"))
            )
            
            self.load_all_reviews(max_scroll_attempts)
            self.expand_long_reviews()
            reviews_data = self.extract_reviews_data()
            return reviews_data

        except Exception as e:
            print(f"An error occurred during scraping: {e}")
            return []
        
    def close_driver(self):
        """
        Closes the browser window.
        """
        self.driver.quit()