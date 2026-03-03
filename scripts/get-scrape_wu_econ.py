import cloudscraper
from bs4 import BeautifulSoup
from datetime import datetime
from dateutil import parser as dateparser
from icalendar import Calendar, Event
import pytz
import re
import time
import logging


URL_dict = {"wu_econext": "https://www.wu.ac.at/en/economics/research/economics-research-seminar",
            "wu_econint": "https://www.wu.ac.at/en/economics/research/internal-economic-research-seminar"}
TIMEZONE = "Europe/Vienna"

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


def fetch_page_html(url):
    # Extract html from indicated url
    scraper = cloudscraper.create_scraper()
    return _get_with_retry(scraper, url)


def _left_column_parts(left_col):
    """ Extract event info strings from left column of an WU event record
    
    Return (date_str, time_str, room_str) from a table left column, or None.
    """
    # The left column cell will strat with bold text, denoted by <strong>
    strong = left_col.find("strong")
    if strong is None:
        return None
    # Transform html to text, 
    date = strong.get_text(strip=True)
    # Split text into lines, ignore if less than 3 lines (date, time, room)
    lines = [l for l in left_col.get_text("\n", strip=True).split("\n") if l]
    if len(lines) < 3:
        return None
    # Return event info
    return date, lines[1], lines[2].replace("\xa0", " ")


def parse_extevents(html):
    """Parse the external WU economics seminar page into a list of event dicts."""
    # Turn the HTML into a BeautifulSoup object for parsing
    soup = BeautifulSoup(html, "html.parser")
    # Find the main content block containing seminar records
    content = soup.find("table", class_="md-table-resp table-resp")
    if content is None:
        raise ValueError("Cannot find seminar content block on page")
    # Create empty list to hold parsed events
    events = []
    # Loop through each table row in the content block, looking for seminar records
    for row in content.find_all("tr"):
        # Each seminar record should have exactly 2 columns (date/time/room and speaker/title)
        cols = row.find_all("td")
        if len(cols) != 2:
            continue
        left, right = cols
        # Extarct date, time, and room info from the left column
        parts = _left_column_parts(left)
        if parts is None:
            logger.debug("Skipping malformed row (left column)")
            continue
        date, time_str, room = parts

        # Speaker name from first <a> tag; fall back to first text line
        a_tag = right.find("a")
        if a_tag:
            speaker = a_tag.get_text(strip=True).replace("\xa0", " ")
        else:
            text_lines = [l for l in right.get_text("\n", strip=True).split("\n") if l]
            speaker = text_lines[0].replace("\xa0", " ") if text_lines else "Unknown speaker"

        text_lines = right.get_text("\n", strip=True).split("\n")
        
        # Extarct affiliation from line starting with "(" if available
        aff_line = next((l for l in text_lines if l.strip().startswith("(")), "")
        affiliation = aff_line.strip("()").replace("\xa0", " ")
        # Extract title from line in quotes if available, otherwise use "Unknown title"
        joined = " ".join(text_lines)
        m = re.search(r'"([^"]+)"', joined)
        title = m.group(1) if m else "Unknown title"

        # Create event dict and add to list
        events.append({
            "date": date,
            "time": time_str,
            "room": room,
            "speaker": speaker,
            "affiliation": affiliation,
            "title": title,
        })

    return events


def parse_intevents(html):
    """Parse the internal WU economics seminar page into a list of event dicts."""
    # Turn the HTML into a BeautifulSoup object for parsing
    soup = BeautifulSoup(html, "html.parser")
    # Find the main content block containing seminar records
    content = soup.find("table", class_="md-table-resp table-resp")
    if content is None:
        raise ValueError("Cannot find seminar content block on page")
    # Create empty list to hold parsed events
    events = []
    # Loop through each table row in the content block, looking for seminar records
    for row in content.find_all("tr"):
        # Each seminar record should have exactly 2 columns (date/time/room and speaker/title)
        cols = row.find_all("td")
        if len(cols) != 2:
            continue
        left, right = cols
        # Extarct date, time, and room info from the left column
        parts = _left_column_parts(left)
        if parts is None:
            logger.debug("Skipping malformed row (left column)")
            continue
        date, time_str, room = parts

        text_lines = [l for l in right.get_text("\n", strip=True).split("\n") if l]
        if len(text_lines) == 0:
            # No text in right column, skip this record
            logger.debug("Skipping row with empty right column")
            continue
        elif len(text_lines) == 1:
            # Only one line of text, assume it's the speaker and title is unknown
            speaker = text_lines[0].replace("\xa0", " ")
            title = "Unknown title"
        elif len(text_lines) == 2:
            # Second line is title
            speaker = text_lines[0].replace("\xa0", " ")
            title = text_lines[1].replace("\xa0", " ")
        else:
            # Multiple speakers / titles separated by blank lines; 
            # Same pattern as for one speaker
            speaker = "; ".join(
                l.replace("\xa0", " ") for i, l in enumerate(text_lines) if i % 2 == 0
            )
            title = "; ".join(
                l.replace("\xa0", " ") for i, l in enumerate(text_lines) if i % 2 == 1
            )
        # Create event dict and add to list
        events.append({
            "date": date,
            "time": time_str,
            "room": room,
            "speaker": speaker,
            "title": title,
        })

    return events


def parse_datetime(date_str, time_range_str):
    """
    Convert e.g. 'October 15, 2025' and '4.30-6.00 pm'
    into a pair of timezone-aware datetime objects.
    """
    # Try parsing the date string with dateparser
    try:
        date = dateparser.parse(date_str)
    except Exception as exc:
        raise ValueError(f"Cannot parse date '{date_str}': {exc}")

    #Normalize time string: : instead of . and no am/pm
    tr = time_range_str.replace(".", ":").lower()
    ampm = "am" if "am" in tr else "pm" if "pm" in tr else ""
    core = tr.replace("am", "").replace("pm", "").strip()

    # Expect a time range separated by "-", e.g. "4:30-6:00"
    if "-" not in core:
        raise ValueError(f"Unexpected time range format (no '-'): '{time_range_str}'")
    # Split into start and end parts, stripping whitespace
    start_raw, end_raw = core.split("-", 1)

    # If start has no colon (e.g. "4"), add ":00"
    if ":" not in start_raw:
        start_raw = start_raw.strip() + ":00"
    if ":" not in end_raw:
        end_raw = end_raw.strip() + ":00"

    # Try parsing the start and end times with dateparser, adding am/pm if needed
    try:
        start_time = dateparser.parse(start_raw.strip() + " " + ampm)
        end_time = dateparser.parse(end_raw.strip() + " " + ampm)
    except Exception as exc:
        raise ValueError(f"Cannot parse times from '{time_range_str}': {exc}")
    # Raise error if dateparser returned None for either time
    if start_time is None or end_time is None:
        raise ValueError(f"dateparser returned None for times in '{time_range_str}'")

    # Combine the date with the start and end times, and localize to the specified timezone
    tz = pytz.timezone(TIMEZONE)
    dt_start = tz.localize(
        datetime(date.year, date.month, date.day, start_time.hour, start_time.minute)
    )
    dt_end = tz.localize(
        datetime(date.year, date.month, date.day, end_time.hour, end_time.minute)
    )
    return dt_start, dt_end


def build_ics(events, filename):
    """Build and write a .ics file from a list of event dicts."""
    # Basic calendar setup with PRODID and VERSION
    cal = Calendar()
    cal.add("prodid", "-//WU Economics Research Seminar Calendar//")
    cal.add("version", "2.0")
    # Loop over events list and track how many we skip due to parsing errors
    skipped = 0
    for ev in events:
        # Try to parse event times, skip if error
        try:
            dt_start, dt_end = parse_datetime(ev["date"], ev["time"])
        except ValueError as exc:
            logger.warning(f"Skipping event '{ev.get('title', '?')}': {exc}")
            skipped += 1
            continue
        # Create an iCalendar event and add basic event info
        event = Event()
        event.add("summary", f"{ev['speaker']}: {ev['title']}")
        event.add("dtstart", dt_start)
        event.add("dtend", dt_end)
        event.add("location", ev["room"])
        # Add dedicated description field with speaker, title, and affiliation (if available)
        desc_parts = [f"Speaker: {ev['speaker']}", f"Title: {ev['title']}"]
        if ev.get("affiliation"):
            desc_parts.insert(1, f"Affiliation: {ev['affiliation']}")
        event.add("description", "\n".join(desc_parts))
        # Add the event to the calendar
        cal.add_component(event)
    # Log how many events were skipped due to parsing errors
    if skipped:
        logger.warning(f"Skipped {skipped} event(s) due to parsing errors")
    # Display a warning if no events were successfully parsed, and skip writing the file
    event_count = sum(1 for _ in cal.walk("VEVENT"))
    if event_count == 0:
        logger.warning(f"No events to write — skipping file: {filename}")
        return
    # Try writing the calendar to an .ics file, logging success or any errors
    # Display the number of events included in the file for confirmation
    try:
        with open(filename, "wb") as f:
            f.write(cal.to_ical())
        logger.info(f"Created ICS file: {filename} ({event_count} event(s))")
    except OSError as exc:
        logger.error(f"Failed to write {filename}: {exc}")


def main():
    # Loop through each URL in the URL_dict, fetch and parse the seminar page, and build the corresponding .ics file
    for url_name, url in URL_dict.items():
        logger.info(f"Processing {url_name} ...")
        # Try fetching the page HTML with retry logic
        try:
            html = fetch_page_html(url)
        except Exception as exc:
            logger.error(f"Failed to fetch page for {url_name}: {exc}")
            continue
        # Try parsing the html based on URL name
        try:
            if url_name == "wu_econext":
                events = parse_extevents(html)
            elif url_name == "wu_econint":
                events = parse_intevents(html)
            else:
                logger.warning(f"Unknown URL name '{url_name}', skipping")
                continue
        except Exception as exc:
            logger.error(f"Failed to parse events for {url_name}: {exc}")
            continue
        # Log how many events were found for confirmation
        logger.info(f"Found {len(events)} seminar(s)")
        # Create the .ics file for this URL
        wu_file = f"../public/ics/{url_name}_seminars.ics"
        build_ics(events, filename=wu_file)


if __name__ == "__main__":
    main()