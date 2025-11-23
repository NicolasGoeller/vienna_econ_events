import cloudscraper
from bs4 import BeautifulSoup
from datetime import datetime
from dateutil import parser as dateparser
from icalendar import Calendar, Event
import pytz


URL = "https://www.wu.ac.at/en/economics/research/internal-economic-research-seminar"
TIMEZONE = "Europe/Vienna"


def fetch_page_html(url):
    # Extract html from indicated url
    scraper = cloudscraper.create_scraper()
    return scraper.get(url).text


def parse_events(html):
    soup = BeautifulSoup(html, "html.parser")

    # Main content block where seminars are listed
    content = soup.find("table", class_="md-table-resp table-resp")
    if content is None:
        raise ValueError("Cannot find seminar content block on page")

    events = []

    # Each seminar is in a <tr> inside a table
    rows = content.find_all("tr")
    row = rows[5]
    for row in rows:
        cols = row.find_all("td")
        if len(cols) != 2:
            continue  # skip malformed rows

        left = cols[0]
        right = cols[1]

        # Left column: date, time, room
        date = left.find("strong").get_text(strip=True)

        lines = left.get_text("\n", strip=True).split("\n")
        if len(lines) < 3:
            continue

        # Example:
        # lines = ["October 15, 2025", "4.30-6.00 pm", "room D4.0.039"]
        time = lines[1]
        room = lines[2]

        # Right column: speaker, affiliation, title
        #speaker = right.find("a").get_text(strip=True)

        text_lines = right.get_text("\n", strip=True).split("\n")
        if len(text_lines) == 2:
            speaker = text_lines[0]
            title = text_lines[1]
        else:
            speaker = text_lines[0] + "; " + text_lines[2]
            title = text_lines[1] + "; " + text_lines[3]
            
        # Example:
        # ["Fabian Kindermann", "(University of Regensburg)", "", "\"Negotiating Parenthood...\""]

        # Extract title (in quotes)
        #join_text = " ".join(text_lines)
        #m = re.search(r"\"([^\"]+)\"", join_text)
        #title = m.group(1) if m else "Unknown title"

        events.append({
            "date": date,
            "time": time,
            "room": room,
            "speaker": speaker,
            "title": title
        })

    return(events)


def parse_datetime(date_str, time_range_str):
    """
    Convert 'October 15, 2025' and '4.30-6.00 pm'
    into timezone-aware datetime objects.
    """
    date = dateparser.parse(date_str)

    # Convert "4.30-6.00 pm" → "4:30 pm" and "6:00 pm"
    tr = time_range_str.replace(".", ":").lower()

    # Extract AM/PM once (applies to both)
    ampm = "am" if "am" in tr else "pm" if "pm" in tr else ""

    start_str, end_str = tr.replace("am", "").replace("pm", "").split("-")

    start_str = start_str.strip() + " " + ampm
    end_str = end_str.strip() + " " + ampm

    start_time = dateparser.parse(start_str)
    end_time = dateparser.parse(end_str)

    tz = pytz.timezone(TIMEZONE)
    dt_start = tz.localize(datetime(date.year, date.month, date.day,
                                    start_time.hour, start_time.minute))
    dt_end = tz.localize(datetime(date.year, date.month, date.day,
                                  end_time.hour, end_time.minute))

    return dt_start, dt_end


def build_ics(events, filename="../public/ics/wu_econint_seminars.ics"):
        
    cal = Calendar()
    cal.add("prodid", "-//WU Economics Internal Seminar Calendar//")
    cal.add("version", "2.0")

    for ev in events:
        dt_start, dt_end = parse_datetime(ev["date"], ev["time"])

        event = Event()
        event.add("summary", f"{ev['speaker']}: {ev['title']}")
        event.add("dtstart", dt_start)
        event.add("dtend", dt_end)
        event.add("location", ev["room"])
        event.add("description",
                  f"Speaker: {ev['speaker']}\nTitle: {ev['title']}")
        cal.add_component(event)

    if len(cal.subcomponents) == 0:
        print("No events found, file not created")
    else:
        with open(filename, "wb") as f: f.write(cal.to_ical())

    print(f"Created ICS file: {filename}")
    
#html = fetch_page_html(URL)
#events = parse_events(html)
#print(f"Found {len(events)} seminars")
#build_ics(events)

def main():
    html = fetch_page_html(URL)
    events = parse_events(html)
    print(f"Found {len(events)} seminars")
    build_ics(events)


if __name__ == "__main__":
    main()
    