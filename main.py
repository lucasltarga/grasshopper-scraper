from scraper import Scraper
from file_handler import save_to_csv

def main():
    # The URL to be scraped (reviews tab of a specific place on Google Maps)
    place_url = ""
    
    scraper = Scraper()

    try:
        reviews_data = scraper.scrape_reviews(place_url)
        if reviews_data:
            print("Saving reviews data to CSV...")
            save_to_csv(reviews_data)
        else:
            print("No reviews data was collected.")
    finally:
        scraper.close_driver()

if __name__ == "__main__":
    main()