import cloudscraper
from bs4 import BeautifulSoup
import base64
import re
from icalendar import Calendar
from datetime import datetime

URL_dict = {"univie_vje": "https://econ.univie.ac.at/research/research-seminars/vje-seminar/",
            "univie_macro": "https://econ.univie.ac.at/research/research-seminars/vgse-macro-seminar/",
            "univie_micro": "https://econ.univie.ac.at/research/research-seminars/vgse-micro-seminar/",
            "univie_applied": "https://econ.univie.ac.at/research/research-seminars/applied-economics-seminar/",
            "univie_vcee": "https://econ.univie.ac.at/research/research-seminars/vcee-seminar/",
            "vies": "https://econ.univie.ac.at/research/research-seminars/vienna-international-economics-seminar/"
}

def fetch_full_ics(url):

    # Fetch HTML
    scraper = cloudscraper.create_scraper()
    html = scraper.get(url).text

    # Parse HTML
    soup = BeautifulSoup(html, "html.parser")

    # Find iframe element
    iframe = soup.find("iframe")
    src = iframe.get("src")

    # Extract src code
    match = re.search(r"&src=([a-zA-Z0-9_]+)&color", src)
    if match:
        ics_src = match.group(1)
        
    # Decode src ID from base64
    padding = '=' * (-len(ics_src) % 4)
    decoded_bytes = base64.urlsafe_b64decode(ics_src + padding)
    calendar_id = decoded_bytes.decode("utf-8")

    # Create ics link for downloading
    googlecal_base = "https://calendar.google.com/calendar/ical/"
    googlecal_end = "/public/basic.ics"
    googlecal_url = googlecal_base + calendar_id + googlecal_end
    
    # Extract ics as string
    html_str = scraper.get(googlecal_url).text

    return(html_str)


def filter_ics(html_str):

    # Transform downloaded text into ical object
    full_cal = Calendar.from_ical(html_str)

    # Craete new calendar
    new_cal = Calendar()


    # Copy over required calendar-level properties
    for prop in ["VERSION", "PRODID", "CALSCALE", "METHOD",'X-WR-TIMEZONE', 'X-WR-CALDESC']:
        if full_cal.get(prop):
            new_cal.add(prop, full_cal.get(prop))

    # Get current date
    now_date = datetime.today()

    # Set target date to start of new semester - Oct 01 & Mar 01
    if now_date.month < 3:
        target_date = datetime(now_date.year-1, 10, 1).date()
    elif (now_date.month > 3) & (now_date.month < 9):
        target_date = datetime(now_date.year, 3, 1).date()
    elif now_date.month > 9:
        target_date = datetime(now_date.year, 10, 1).date()

    # Select only components that are happening after start of current semester    
    for component in full_cal.walk("VEVENT"):
        start = component.get("DTSTART").dt
        if start.date() >= target_date:
            new_cal.add_component(component)
            
    # Return filtered cal object
    return(new_cal)


def write_ics(cal, filename):
    if len(cal.subcomponents) == 0:
        print("No events found, file not created")
    else:
        with open(filename, "wb") as f: f.write(cal.to_ical())

    print(f"Created ICS file: {filename}")
    
def main():
    for URL in URL_dict:
        html_str = fetch_full_ics(URL)
        ical = filter_ics(html_str)
        print(f"Found {len(ical)} seminars")
        write_ics(ical)


if __name__ == "__main__":
    main()
    