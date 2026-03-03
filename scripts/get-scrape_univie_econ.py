import cloudscraper
from bs4 import BeautifulSoup
import base64
import re
from icalendar import Calendar
from datetime import datetime, date
import logging
import time


URL_dict = {"univie_vje": "https://econ.univie.ac.at/research/research-seminars/vje-seminar/",
            "univie_macro": "https://econ.univie.ac.at/research/research-seminars/vgse-macro-seminar/",
            "univie_micro": "https://econ.univie.ac.at/research/research-seminars/vgse-micro-seminar/",
            "univie_applied": "https://econ.univie.ac.at/research/research-seminars/applied-economics-seminar/",
            "univie_vcee": "https://econ.univie.ac.at/research/research-seminars/vcee-seminar/",
            "vies": "https://econ.univie.ac.at/research/research-seminars/vienna-international-economics-seminar/"
}

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

MAX_RETRIES = 3
RETRY_DELAY = 5  # seconds


def _get_with_retry(scraper, url, retries=MAX_RETRIES, delay=RETRY_DELAY):
    """ URL scraper with retry

    Perform an HTTP GET request using the provided ``scraper`` with retry logic.

        Parameters
        - scraper: an object providing a ``.get(url, timeout=...)`` method
            (for example a ``cloudscraper`` session).
        - url (str): the URL to fetch.
        - retries (int): total number of attempts before giving up (default
            ``MAX_RETRIES``).
        - delay (float): seconds to wait between failed attempts (default
            ``RETRY_DELAY``).

        Returns
        - str: ``response.text`` on a successful request.

        Raises
        - RuntimeError: if all attempts fail.
    """

    # Attempt numbers start at 1 to make log messages human-friendly
    for attempt in range(1, retries + 1):
        try:
            # Use a short timeout to prevent blocking
            response = scraper.get(url, timeout=20)
            # Raise for HTTP error status codes (4xx/5xx).
            response.raise_for_status()
            # On success, return the text body immediately.
            return response.text
        except Exception as exc:
            # Log the failure with attempt info and exception details.
            logger.warning(f"Attempt {attempt}/{retries} failed for {url}: {exc}")
            # If any retries left, wait before the next attempt.
            if attempt < retries:
                time.sleep(delay)
    # If retries are exhasuted, raise a RuntimeError
    raise RuntimeError(f"All {retries} attempts failed for {url}")


def fetch_full_ics(url):
    """Fetch the ICS calendar data linked from a UniVie seminar page."""
    # Create a cloudscraper session to handle potential anti-bot measures on the seminar pages
    scraper = cloudscraper.create_scraper()

    # Extract the html from the indicated URL
    html = _get_with_retry(scraper, url)
    soup = BeautifulSoup(html, "html.parser")

    # Find the first <iframe> element, which should contain the embedded Google Calendar
    iframe = soup.find("iframe")
    if iframe is None:
        raise ValueError(f"No <iframe> found on page: {url}")
    # Extract the src attribute from the iframe, which contains the Google Calendar embed URL
    src = iframe.get("src", "")
    if not src:
        raise ValueError(f"<iframe> has no src attribute on page: {url}")

    # Derive the Google Calendar ICS URL from the embed src
    # Based on src format, the calendar ID needs modification 
    if "group.calendar.google.com" in src:
        # For group calendars, the ID is directly in the src as a parameter ending with %40 (URL-encoded @)
        match = re.search(r"&src=([a-zA-Z0-9_]+)%40", src)
        if not match:
            raise ValueError(f"Cannot parse group calendar ID from src: {src}")
        calendar_id = match.group(1) + "@group.calendar.google.com"
    else:
        # For other calendars, the ID is base64-encoded in the src parameter
        match = re.search(r"&src=([a-zA-Z0-9_]+)&color", src)
        if not match:
            raise ValueError(f"Cannot parse calendar ID from src: {src}")
        ics_src = match.group(1)
        # Add padding for base64 decoding 
        padding = "=" * (-len(ics_src) % 4)
        try:
            decoded_bytes = base64.urlsafe_b64decode(ics_src + padding)
            calendar_id = decoded_bytes.decode("utf-8")
        except Exception as exc:
            raise ValueError(f"Failed to decode calendar ID '{ics_src}': {exc}")
    # Construct the public ICS URL for the calendar
    googlecal_url = (
        f"https://calendar.google.com/calendar/ical/{calendar_id}/public/basic.ics"
    )
    logger.info(f"  Fetching ICS from: {googlecal_url}")
    return _get_with_retry(scraper, googlecal_url)


def filter_ics(html_str):
    """Parse and return a new Calendar containing only current-semester events."""
    # Try to extarct the full calendar from the fetched ICS data
    try:
        full_cal = Calendar.from_ical(html_str)
    except Exception as exc:
        raise ValueError(f"Failed to parse ICS data: {exc}")

    # Define new calendar object
    new_cal = Calendar()
    # Extract and copy basic properties to new calendar
    for prop in ["VERSION", "PRODID", "CALSCALE", "METHOD", "X-WR-TIMEZONE", "X-WR-CALDESC"]:
        if full_cal.get(prop):
            new_cal.add(prop, full_cal.get(prop))

    # Determine the current date and the target date for filtering events
    now_date = datetime.today()
    # Semester boundaries: Oct 1 (winter) or Mar 1 (summer)
    if now_date.month < 3:
        target_date = datetime(now_date.year - 1, 10, 1).date()
    elif 3 <= now_date.month <= 9:
        target_date = datetime(now_date.year, 3, 1).date()
    else:
        target_date = datetime(now_date.year, 10, 1).date()

    # Loop over all events in calendar and track included ones
    included = 0
    for component in full_cal.walk("VEVENT"):
        # Extract DTSTART
        dtstart = component.get("DTSTART")
        if dtstart is None:
            logger.debug("Skipping event with no DTSTART")
            continue
        # Transfrom DTSTART to datetime if necessary
        start = dtstart.dt
        if isinstance(start, datetime):
            start_date = start.date()
        elif isinstance(start, date):
            start_date = start
        else:
            logger.debug(f"Skipping event with unrecognised DTSTART type: {type(start)}")
            continue
        # Include only events where DTSTART after the start of the semester
        if start_date >= target_date:
            new_cal.add_component(component)
            included += 1

    logger.info(f"  Kept {included} event(s) from current semester onwards")
    return new_cal


def write_ics(cal, filename):
    """Write the calendar to an ICS file, skipping if empty."""
    # Count events in filtered calendar
    event_count = sum(1 for _ in cal.walk("VEVENT"))
    # Skip if zero events filtered
    if event_count == 0:
        logger.warning(f"No events found — skipping file: {filename}")
        return
    # Write the calendar to an .ics file, display number of events
    try:
        with open(filename, "wb") as f:
            f.write(cal.to_ical())
        logger.info(f"Created ICS file: {filename} ({event_count} event(s))")
    except OSError as exc:
        logger.error(f"Failed to write {filename}: {exc}")


def main():
    # Loop over each URL in the URL_dict
    for url_name, url in URL_dict.items():
        logger.info(f"Processing {url_name} ...")
        # Fetch the full ICS data from the seminar page
        try:
            html_str = fetch_full_ics(url)
        except Exception as exc:
            logger.error(f"Failed to fetch ICS for {url_name}: {exc}")
            continue
        # Filter out relevant events from the full calendar and create a new calendar object
        try:
            ical = filter_ics(html_str)
        except Exception as exc:
            logger.error(f"Failed to parse/filter ICS for {url_name}: {exc}")
            continue
        # Write the filtered calendar to an .ics file, skipping if no events
        vie_file = f"../public/ics/{url_name}_seminars.ics"
        write_ics(ical, filename=vie_file)

if __name__ == "__main__":
    main()
    
    
