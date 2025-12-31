
from bs4 import BeautifulSoup
import json
import re
import calendar


def get_all_date_data(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        calendar_html = f.read()
    soup = BeautifulSoup(calendar_html, 'html.parser')
    date_data = []
    # Find all event-items that have data-date attributes
    events = soup.find_all('div', class_='event-item', attrs={"data-date": True})
    for event in events:
        # event_json = event_html_to_json(event)
        if event.get("data-date"):  # Only add if conversion was successful
            date_data.append(event.get("data-date"))
    return date_data
  
def extract_event_html(html_content, date_key): 
    """Extract event HTML for a given date_key"""
    soup = BeautifulSoup(html_content, 'html.parser')
    event = soup.find('div', {'data-date': date_key})
    if event:
        return event , str(event)
    return None
  

def event_html_to_json(event_element):
    # """Convert BeautifulSoup event element to JSON"""
    # """Extract event HTML for a given date_key"""
    # event_element = BeautifulSoup(event_html, 'html.parser')
    if not event_element:
        return None
    # Extract data-date
    date_code = event_element.get('data-date')
    # Extract date string
    date_span = event_element.find('span', class_='event-date')
    date_str = date_span.get_text().strip() if date_span else ""
    # Extract description text (everything except spans)
    descript_span = event_element.find('span', class_='event-description')
    description = descript_span.get_text().strip() if descript_span else ""
    description = re.sub(r'\r?\n\s*', ' ', description).strip()
    title_span = event_element.find('span', class_='event-title')
    title = title_span.get_text().strip() if title_span else ""         
    title = re.sub(r'\r?\n\s*', ' ', title).strip()
    # Extract links
    links = []
    link_spans = event_element.find_all('span', class_='event-links')
    for span in link_spans:
        for link in span.find_all('a'):
            link_text = link.get_text().strip()
            link_text = re.sub(r'\r?\n\s*', ' ', link_text).strip()
            link_descr_span = span.find('span', class_='event-link-descr')
            lnkDescr = link_descr_span.get_text().strip()
            lnkDescr = re.sub(r'\r?\n\s*', ' ', lnkDescr).strip() if link_descr_span else ""    
            links.append({
                "href": link.get('href', ''),
                "lnkTxt": link_text,
                "lnkDescr": lnkDescr
            })
    # Build JSON object
    event_json = {
        "dateCode": date_code if date_code else None,
        "dateStr": date_str,
        "description": description,
        "title": title,  # Now properly filtered
        "links": links
    }
    
    return event_json
  
def extract_and_remove_event(html_content, date_key):
    """Extract event as JSON, then remove from HTML"""
    soup = BeautifulSoup(html_content, 'html.parser')
    event = soup.find('div', {'data-date': date_key})
    if event:
        # Convert to JSON first
        event_json = event_html_to_json(event)
        # Then remove from HTML
        print(event)
        event.decompose()
        # print(soup)
        return event_json, str(soup)
    return None, html_content

def create_event_html_from_json(event_json):
    """Create event HTML from JSON object"""
    dateCode = event_json.get('dateCode', '')
    dateStr = event_json.get('dateStr', '')
    title = event_json.get('title', '')
    description = event_json.get('description', '')
    # Build links
    links = []
    for link in event_json.get('links', []):
        href = link.get('href', '')
        lnkTxt = link.get('lnkTxt', '')
        lnkDescr = link.get('lnkDescr', '')
        links.append(f'<a href="{href}">{lnkTxt} </a> <span class="event-link-descr"> {lnkDescr} </span>')
    links_html = ''.join([f'<span class="event-links">{link}</span>' for link in links])
    # Create HTML
    html = f'''<div class="event-item" data-date="{dateCode}">
        <span class="event-date">{dateStr}</span>
        <span class="event-title">{title}</span>
        <span class="event-description">{description}</span>
        {links_html}
    </div>'''
    return html 

def insert_or_replace_event(calendar_path, event_json):
    """
    Insert new event or replace existing one for same date
    
    Args:
        calendar_path: path to HTML calendar file
        event_json: event data in JSON format
    """
    print(json.dumps(event_json, indent=2))
    message =''
    # 1. Load calendar HTML
    with open(calendar_path, 'r', encoding='utf-8') as f:
        html_content = f.read()
    soup = BeautifulSoup(html_content, 'html.parser')
    # 2. Extract event details
    date_code = str(event_json['dateCode'])
    date_str = event_json['dateStr'] 
    title = event_json.get('title', '')
    description = event_json.get('description', '')
    links = event_json.get('links', [])
    # 3. Create event HTML
    links_html = ""
    if len(links) > 0:
        for link in links:
            href = link.get('href', '')
            text = link.get('lnkTxt', '')
            descr = link.get('lnkDescr', '')
            links_html += f'<span class="event-links"><a href="{href}">{text}</a> <span class="event-link-descr">{descr}</span></span>'
    new_event_html = f'''
    <div class="event-item" data-date="{date_code}">
        <span class="event-date">{date_str}</span>
        <span class="event-title">{title}</span>
        <span class="event-description">{description}</span>
        {links_html}
    </div>'''
    message += f"New event HTML:"
    print(f"New event HTML:\n{new_event_html}")
    # 4. Find target month (November 2025 for dateCode 20251102)
    year = int(date_code[:4])
    month = int(date_code[4:6])
    month_name = calendar.month_name[month]
    month_cell = soup.find('span', class_='month-name', string=month_name)
    message += f"Target month: {month_name} {month}/{year}\n"
    message += f"{month_cell}\n"
    print(f"Target month name: {month_name}\nMonth cell: {month_cell}")
    if not month_cell:
        message += f"Month {month_name} not found\n"
        return html_content
    # 5. Get the weekly events column for this month
    month_row = month_cell.find_parent('tr')
    weekly_cell = month_row.find('td', class_='weekly-column')
    # 6. Remove existing event for same date (if exists)
    existing_event = soup.find('div', {'data-date': date_code})
    print(f"Existing event for {date_code}: {existing_event}")
    if existing_event:
        message += f"Replacing existing event for {date_code}\n"
        existing_event.decompose()
    # 7. Insert new event in chronological order
    new_event_soup = BeautifulSoup(new_event_html, 'html.parser')
    new_event = new_event_soup.find('div', class_='event-item')
    existing_events = weekly_cell.find_all('div', class_='event-item')
    inserted = False
    for existing_event in existing_events:
        existing_date = existing_event.get('data-date', '99999999')
        if date_code < existing_date:
            existing_event.insert_before(new_event)
            inserted = True
            break
    if not inserted:
        weekly_cell.append(new_event)
    # 8. Return updated HTML (would save to file in real implementation)
    print(message)
    return str(soup)







def delete_events(calendar_path, date_codes):
    """
    Delete multiple events by their data-date codes
    Args:
        calendar_path: path to HTML calendar file
        date_codes: list of date codes (e.g., ['20251102', '20251115', '20251203'])
    Returns:
        updated HTML string
    """
    # Load calendar HTML
    with open(calendar_path, 'r', encoding='utf-8') as f:
        html_content = f.read()
    soup = BeautifulSoup(html_content, 'html.parser')
    deleted_count = 0
    # Delete each event by data-date
    for date_code in date_codes:
        event = soup.find('div', {'data-date': str(date_code)})
        if event:
            print(f"Deleting event: {date_code}")
            event.decompose()
            deleted_count += 1
        else:
            print(f"Event not found: {date_code}")
    print(f"Deleted {deleted_count} out of {len(date_codes)} events")
    return soup, str(soup)

def extract_event_json(dateCode, link_href, cal_path):
    with open(cal_path, 'r', encoding='utf-8') as f:
        calendar_html = f.read()
    event_html = extract_event_html(calendar_html, dateCode)
    # print(event_html)
    soup = BeautifulSoup(event_html, 'html.parser')
    event = soup.find('div', class_='event-item')
    ev_json = event_html_to_json(event)
    if len(ev_json["links"]) == 0:
        ev_json["links"] = [{"href": "", "lnkTxt": "", "lnkDescr": ""}]
    for link in ev_json["links"]:
        if link["href"] == "":
            link["href"] = link_href
            link["lnkTxt"] = "Notes"
    return ev_json

def insert_new_ev_in_mo(mo_soup, new_ev_soup):
    # Find the weekly-column cell where events are stored
    weekly_column = mo_soup.find('td', class_='weekly-column')
    if not weekly_column:
        print("Error: No weekly-column found in month row")
        return
    # Get the new event's data-date for comparison
    new_date = new_ev_soup.find('div', class_='event-item').get('data-date') 
    if not new_date:
        print("Error: New event has no data-date attribute")
        return
    # Find all existing event-items in this month
    existing_events = weekly_column.find_all('div', class_='event-item')
    # If no existing events, just append the new one
    if not existing_events:
        weekly_column.append(new_ev_soup)
        print(f"Inserted first event for date: {new_date}")
        return
    # Find correct position based on chronological order
    inserted = False
    for existing_event in existing_events:
        existing_date = existing_event.get('data-date', '9999-99-99')
        # Compare dates as strings (works for YYYY-MM-DD format)
        if new_date < existing_date:
            existing_event.insert_before(new_ev_soup)
            inserted = True
            print(f"Inserted event {new_date} before {existing_date}")
            break
    # If not inserted yet, append at end (latest date)
    if not inserted:
        weekly_column.append(new_ev_soup)
        print(f"Appended event {new_date} at end of month")
        
def copy_output_to_next_cell(var, name):
    from IPython import get_ipython
    import pprint
    p = pprint.pformat(var)
    get_ipython().set_next_input(f"{name} = {var} " , replace=False)