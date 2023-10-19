import pandas as pd
import re
import time

import requests
from bs4 import BeautifulSoup
import bs4

from dms2dec.dms_convert import dms2dec

import logging 
logging.basicConfig()
logger = logging.getLogger()
logger.setLevel(logging.INFO)


def find_coordinates(soup):
    """
    Given a URL of a national park, find the coordinates
    """
    try:
        lat = soup.find(class_='latitude').text
        long = soup.find(class_='longitude').text
    except:
        lat = None
        long = None

    return lat, long

############
## Checks ##
############

def lone_nat_park_check(c_dict):
    """
    Check the countries dictionary to see if there is just one national park.
    """
    if c_dict["number_of_parks"] == 1:
        check = True
    else:
        check = False

    return check


def check_next_national_park_table(soup, country, log_level=logging.INFO) -> bool:
    """
    In the provided soup object, find the next table.
    """
    logger.setLevel(log_level)
    logger.info(f"Checking to see if a table is found in webpage for {country}...")

    if soup.find_next('table', class_='wikitable') != None:
        logger.info(f"Table with National Parks found for {country}.")
        check = True
    
    else:
        logger.info(f"No National Park table found for {country}.")
        check = False

    return check


def check_next_national_park_list(soup, country, log_level=logging.INFO) -> bool:
    """
    In the provided soup object, find the next table. Return boolean
    """
    logger.setLevel(log_level)
    logger.info(f"Checking to see if an unordered list is found in webpage for {country}...")

    if soup.find_next('ul') != None:
        logger.info(f"List with National Parks found for {country}.")
        check = True
    
    else:
        logger.info(f"No National Park list found for {country}.")
        check = False

    return check


def check_country_id(soup, country, log_level=logging.INFO):
    """
    If the country is an ID, look for the next list. This is 
    to catch edge cases of African countries that redirect to 
    the National Parks in Africa page. 
    """
    logger.setLevel(log_level)
    logger.info(f"Checking to see if an ID containing '{country}' is in the webpage...")
    
    if soup.find('span', id=country) != None:
        logger.info(f'An ID for {country} was found in the webpage. This webpage may contain multiple countries. Looking for national parks only in {country}')
        check = True
    else:
        logger.info(f"An ID for {country} was not found.")
        check = False

    return check


def check_national_park_id(soup, country, log_level=logging.INFO):
    """
    In the given URL, looker for the national park ID. 
    """
    logger.setLevel(log_level)
    logger.info(f"Checking to see if an ID matches a regex pattern for 'National Park' for {country} is in the webpage...")

    if soup.find('span', id=re.compile('[Nn]ational_[Pp]arks?')) != None:
        logger.info(f"National park ID found for {country}")
        check = True
    else:
        logger.info(f"National park ID not found for {country}")
        check = False
    
    return check


def check_table(soup, country, log_level=logging.INFO):
    logger.setLevel(log_level)
    logger.info(f"Checking to see if there are tables in the webpage")

    if soup.find('table', class_="wikitable"):
        logger.info(f"A table was found for {country}")
        check = True
    else:
        logger.info(f"A table was not found for {country}")
        check = False

    return check


def check_list(soup, country, log_level=logging.INFO):
    logger.setLevel(log_level)
    logger.info(f"Checking to see if there are unordered lists in the webpage")

    main_container = soup.find(class_='mw-parser-output')

    if main_container.find('ul'):
        logger.info(f"A list was found for {country}")
        check = True
    else:
        logger.info(f"A list was not found for {country}")
        check = False

    return check


def multiple_table_check(soup, log_level=logging.INFO):
    logger.setLevel(log_level)
    if len(soup.find_all('table', class_='wikitable')) > 1:
        logger.info("There are multiple tables at this URL")
        check = True
    else:
        logger.info("There is one or less table at this URL")
        check = False

    return check

def coordinates_check(park_table_row):
    """
    In a given park table, see if coordinates are present.
    """
    if park_table_row.find('span', class_='geo-inline') != None:
        logger.info("GPS coordinates may be present in row")
        check = True
    else:
        check = False

    return check

def scrape_table_coordinates(park_table_row):
    logger.info("Attempting to scrape national park coordinates")
    lat_dms = park_table_row.find('span', class_="latitude").text
    long_dms = park_table_row.find('span', class_="longitude").text

    # Convert to decimal
    lat_dec = round(dms2dec(lat_dms), 6)
    long_dec = round(dms2dec(long_dms), 6)

    return lat_dms, long_dms, lat_dec, long_dec


##################
## Find Element ##
##################

def find_national_park_id(soup, log_level=logging.INFO):
    """
    In the given URL, looker for the national park ID. 
    """
    logger.setLevel(log_level)
    
    nat_park_id = soup.find('span', id=re.compile('[Nn]ational_[Pp]arks?'))
    
    return nat_park_id


# Get next national park 
def find_next_national_park_table(soup, log_level=logging.INFO):
    logger.setLevel(log_level)
    park_table = soup.find_next('table', class_="wikitable")
    
    return park_table


def find_header_element(park_table):
    if len(park_table.find_next('tr').find_all('td')) > 0:
        header_element = 'td'
    else:
        header_element = 'th'
    
    return header_element


def find_national_park_name_col(park_table, header_element=['th', 'td']):
    """
    Go through the table header, and see if "Name" or "National Park" is in the header. If so, get the column number
    so we can scrape the right column. 
    """
    name_col = [re.compile('[Nn]ame'), re.compile('[Nn]ational [Pp]arks?'), re.compile('Short name')]
    
    # Go through header of table to get column number of name or national park column 
    for col_num, element in enumerate(park_table.find_next('tr').find_all(header_element)):
        if any(regex.match(element.text.strip()) for regex in name_col):
            park_name_col_index = col_num
            logger.info(f"Found column containing park name in column {park_name_col_index}")
            break
        else:
            # logger.info("Could not find park name column")
            park_name_col_index = 0
    
    return park_name_col_index

        
def find_park_name_col_element(park_table):
    """
    For a given table, figure out if the park name is in a 'td' or a 'th'
    HTML element. 
    """
    # Find first row of data
    first_row_num = find_first_data_row(park_table)
    
    # In first row, determine if the column with the park name is using a th or a td element
    row = park_table.find_all('tr')[first_row_num]
    
    if len(row.find_all('th')) > 0: 
        park_name_element = 'th'
    else:
        park_name_element = 'td'

    return park_name_element

def find_next_national_park_list(soup, log_level=logging.INFO):
    """
    In the provided soup object, find the next table.
    """
    logger.setLevel(log_level)
    park_list = soup.find_next('ul')

    return park_list


def find_country_id(soup, country, log_level=logging.INFO):
    """
    If the country is an ID, look for the next list. This is 
    to catch edge cases of African countries that redirect to 
    the National Parks in Africa page. 
    """
    logger.setLevel(log_level)
    country_id = soup.find(id=country)

    return country_id


def find_invalid_or_missing_country_url(master_dict):
    problem_list = []
    for country in master_dict:
        c_dict = master_dict[country]
        c_url = c_dict['url']

        if c_url == None or 'wiki' not in c_url:
            problem_list.append(country)
    
    return problem_list


def find_invalid_or_missing_park_url(master_dict):
    problem_list = []
    for country in master_dict:
        c_dict = master_dict[country]

        # Get park url
        parks_dict = c_dict['parks']
        for park_name in parks_dict:
            park_url = parks_dict[park_name]['url']
        

            if park_url == None or 'wiki' not in park_url:
                problem_list.append(park_name)
    
    return problem_list


def find_first_data_row(table: bs4.element.Tag):
    # header_element = find_header_element(table)
    # Get length of header
    header_row_contents = table.find_all('tr')[0].find_all(['th', 'td'])

    # Len of header 
    header_row_len = len(header_row_contents)
    logger.info(f"Header row length: {header_row_len}")

    # Find first row of data
    for row_num, row in enumerate(table.find_all('tr')[1:], start=1):
        row_len = len(row.find_all(['th', 'td']))
        # logger.info(f"Row number: {row_num}    Row length: {row_len}")
        
        if header_row_len <= row_len:
            # logger.info(f"First row of data found in row {row_num}")
            first_data_row = row_num
            break

    return first_data_row


def find_lone_table(soup, log_level=logging.INFO):
    logger.setLevel(log_level)
    park_table = soup.find('table', class_='wikitable')

    return park_table


def find_unordered_list(soup, log_level=logging.INFO):
    logger.setLevel(log_level)
    main_container = soup.find(class_='mw-parser-output')
    park_list = main_container.find('ul')

    return park_list


############
## Scrape ##
############

def scrape_next_national_park_table(park_table):
    """
    For the given national park table, get the name and URL of each park.
    """
    # Find header element, park name element, and the column number where the park name is in 
    park_name_element = ['td', 'th']
    park_name_col_index = find_national_park_name_col(park_table)
    first_row_num = find_first_data_row(park_table)
    
    logger.info(f"Park name is in column {park_name_col_index}")

    # Go through the park table, get the name and url of each park 
    # Empty dictionary
    parks = {}

    # Iterate through each row
    for row in park_table.find_all('tr')[first_row_num:]:
        
        # logger.info(f"Debugging: Number of columns in row: {len(row.find_all(park_name_element))}")
        if len(row.find_all(park_name_element)) == 0:
            logger.info("Row is empty, moving to next row")
            continue

        # Check if coordinates might be in the table
        if coordinates_check(row):
            lat_dms, long_dms, lat_dec, long_dec = scrape_table_coordinates(row)
        else:
            lat_dms, long_dms, lat_dec, long_dec = None, None, None, None

        # skip header row
        nat_park_name_col = row.find_all(park_name_element)[park_name_col_index]
        
        # get park name
        park_name = nat_park_name_col.text
        
        # get park URL 
        try:
            a = nat_park_name_col.find_all('a')
            if len(a) == 0:
                continue
            # a = row.find_next('a')
            for item in a:
                if ".jpg" not in item['href'] and "cite_note" not in item['href']:
                    park_url = item['href']
                    # logger.info(f"{park_url}") # Debugging
                    break
                else:
                    park_url = None
                    continue
        except:
            logger.info(f"No valid url for national park")
            park_url = None
    
        parks[park_name] = {
            'url': park_url,
            'lat_dms': lat_dms,
            'long_dms': long_dms, 
            'lat_dec': lat_dec,
            'long_dec': long_dec
            }
    
    return parks


def scrape_next_national_park_list(park_list):
    parks = {}
    for li in park_list.find_all('li'):
        # Get park name 
        park_name = li.text
        
        # Try to get url 
        try:
            park_url = li.a['href']
        except:
            park_url = None

        parks[park_name] = {'url': park_url}
    
    return parks


def multiple_table_scrape(soup):
    # Regex patterns for column names
    name_col = [re.compile('[Nn]ame'), re.compile('[Nn]ational [Pp]arks?'), re.compile('Short name')]
    
    # Empty dictionary
    parks = {}

    # Go through each table and check if its valid
    for table in soup.find_all('table', class_='wikitable'):
        # Check table header to see if a column for park name exists; if not, go to next table
        header_element = ['td', 'th']

        header = table.find_next('tr')
        header_contents = header.find_all(header_element)
        
        for content in header_contents:
            regex_check = False
            if any(regex.match(content.text.strip()) for regex in name_col):
                regex_check = True
                logger.info("Found park name column")
                break
        
        # If the regex check is True, we can go to next table
        if regex_check == False:
            continue
        
        # Get the column number of where the park name is in the table
        park_name_col_index = find_national_park_name_col(table)

        # Get the first row of data
        first_data_row = find_first_data_row(table)
                
        # Scrape park name and url
        for row in table.find_all('tr')[first_data_row:]:
            
            # Check if coordinates might be in the table
            if coordinates_check(row):
                lat_dms, long_dms, lat_dec, long_dec = scrape_table_coordinates(row)
            else:
                lat_dms, long_dms, lat_dec, long_dec = None, None, None, None
            
            col = row.find_all(['td', 'th'])[park_name_col_index]
            park_name = col.text
            # logger.info(f"Park name: {col.text}")
                
            # get park URL 
            try:
                a = col.find_all('a')
                # a = row.find_next('a')
                for item in a:
                    if ".jpg" not in item['href'] and "cite_note" not in item['href']:
                        park_url = item['href']
                        # logger.info(f"Park URL: {park_url}")
                        parks[park_name] = {
                            'url': park_url,
                            'lat_dms': lat_dms,
                            'long_dms': long_dms, 
                            'lat_dec': lat_dec,
                            'long_dec': long_dec
                            }
                        break
                    else:
                        park_url = None
                        logger.info(f"Park URL: {park_url}")
                        continue
            except:
                logger.info(f"No valid url for national park")
                park_url = None

            # parks[park_name] = {'url': park_url}

    return parks


def scrape_coordinates(master_dict):
    for country in master_dict:
        c_dict = master_dict[country]

        # if country url is invalid, continue
        if c_dict["url"] == None or 'wiki' not in c_dict['url']:
            logger.info(f"{country} does not have a valid URL. Moving to next country")
            continue
        
        # Scrape each park URL 
        for park in c_dict['parks']:
            # If coordinates for park already exists, continue 
            if 'lat_dms' in c_dict['parks'][park]:
                if c_dict['parks'][park]['lat_dms'] != None:
                    logger.info(f"{park} already has coordinates. Moving to next park.")
                    continue

            # If park url is invalid, continue
            sub_url = c_dict['parks'][park]['url']
            if sub_url == None or 'wiki' not in sub_url:
                logger.info(f'Park has invalid URL ({sub_url}). Moving to next park.')
                continue
            
            park_url = "https://en.wikipedia.org" + c_dict['parks'][park]['url']

            logger.info(f'Scraping {park_url}')
            try:
                # get coordinates - get both dms and dec
                soup = create_soup(park_url)
                lat_dms, long_dms = find_coordinates(soup)
                
                if lat_dms != None and long_dms != None:
                    logger.info(f"Coordinates for {park}: {lat_dms} {long_dms}. Converting to degree decimal.")
                    lat_dec = round(dms2dec(lat_dms),6)
                    long_dec = round(dms2dec(long_dms),6)
                    
                    # Save coordinates to dictionary
                    c_dict['parks'][park]['lat_dms'] = lat_dms
                    c_dict['parks'][park]['long_dms'] = long_dms
                    c_dict['parks'][park]['lat_dec'] = lat_dec
                    c_dict['parks'][park]['long_dec'] = long_dec

                else:
                    c_dict['parks'][park]['lat_dms'] = None
                    c_dict['parks'][park]['long_dms'] = None
                    c_dict['parks'][park]['lat_dec'] = None
                    c_dict['parks'][park]['long_dec'] = None

            except:
                logger.info(f"Invalid URL ({park_url}). Moving to next park.")
                c_dict['parks'][park]['lat_dms'] = None
                c_dict['parks'][park]['long_dms'] = None
                c_dict['parks'][park]['lat_dec'] = None
                c_dict['parks'][park]['long_dec'] = None
                continue
        
        master_dict[country] = c_dict

    return master_dict

def scrape_lone_list(park_list):
    parks = {}
    for li in park_list.find_all('li'):
        # Get park name 
        park_name = li.text
        
        # Try to get url 
        try:
            park_url = li.a['href']
        except:
            park_url = None

        parks[park_name] = {'url': park_url}

    pass


################
## Edge Cases ##
################
def scrape_edge_case_g2(soup):
    parks = {}
    
    main_container = soup.find(class_='mw-parser-output')
    
    ul = main_container.find_all('ul')[0]
    for li in ul.find_all('li'):
        park_name = li.text

        # Skip item in list if national parl is not in the name
        if "National Park" in park_name:
            logger.info(f"This item {li.text} is a national park.")
            # Try to get url 
            try:
                park_url = li.a['href']
                logger.info(f'{park_url}')
            except:
                logger.info("Could not get URL")
                park_url = None

    
            parks[park_name] = {'url': park_url}
        
        else:
            logger.info(f"This item {li.text} is not a national park.")   
            continue

    
    return parks

def scrape_edge_case_g3(soup):
    parks = {}
    main_container = soup.find(class_='mw-parser-output')
    
    for ul in main_container.find_all('ul'):
        for li in ul.find_all('li'):
            park_name = li.text
            # Try to get url 
            try:
                park_url = li.a['href']
                logger.info(f'{park_url}')
            except:
                logger.info("Could not get URL")
                park_url = None
            
            parks[park_name] = {'url': park_url}
    
    return parks

def scrape_edge_case_g4(soup):
    parks = {}
    main_container = soup.find(class_='mw-parser-output')
    
    for ul in main_container.find_all('ul'):
        for li in ul.find_all('li'):
            park_name = li.text

            # Skip item in list if national parl is not in the name
            if "National Park" in park_name:
                logger.info(f"This item {li.text} is a national park.")
                # Try to get url 
                try:
                    park_url = li.a['href']
                    # logger.info(f'{park_url}') # Debugging
                except:
                    logger.info("Could not get URL")
                    park_url = None
                
                parks[park_name] = {'url': park_url}

            else:
                logger.info(f"This item {li.text} is not a national park.")   
                continue
    
    return parks

def scrape_edge_case_g5(soup):
    parks = {}
    main_container = soup.find(class_='mw-parser-output')
    park_table = main_container.find_next('table', class_='wikitable')

    park_name_element = ['td', 'th']
    park_name_col_index = find_national_park_name_col(park_table)
    first_row_num = find_first_data_row(park_table)
    
    logger.info(f"Park name is in column {park_name_col_index}")

    # Go through the park table, get the name and url of each park 
    # Empty dictionary
    parks = {}

    # Iterate through each row
    for row in park_table.find_all('tr')[first_row_num:]:
        
        # logger.info(f"Debugging: Number of columns in row: {len(row.find_all(park_name_element))}")
        if len(row.find_all(park_name_element)) == 0:
            logger.info("Row is empty, moving to next row")
            continue

        # skip header row
        nat_park_name_col = row.find_all(park_name_element)[park_name_col_index]
        
        # get park name
        park_name = nat_park_name_col.text
        
        # get park URL 
        try:
            a = nat_park_name_col.find_all('a')
            if len(a) == 0:
                continue
            # a = row.find_next('a')
            for item in a:
                if ".jpg" not in item['href'] and "cite_note" not in item['href']:
                    park_url = item['href']
                    # logger.info(f"{park_url}") # Debugging
                    break
                else:
                    park_url = None
                    continue
        except:
            logger.info(f"No valid url for national park")
            park_url = None
    
        parks[park_name] = {'url': park_url}
    
    return parks

def scrape_edge_case_g7(soup):
    # Empty dictionary
    parks = {}

    # HTML element for header and row contents
    header_element = ['td', 'th']

    # Get table
    park_table = soup.find('table', class_='wikitable')

    # Get header contents and length
    header = park_table.find_next('tr')
    header_contents = header.find_all(header_element)
    header_length = len(header_contents)

    # Get index for park name column
    park_name_col_index = find_national_park_name_col(park_table)
    
    # Get index for first row of data
    first_data_row = find_first_data_row(park_table)

    # iterate through rows of data
    for row in park_table.find_all('tr')[first_data_row:]:
        row_length = len(row.find_all(['td', 'th']))

        if row_length == 0:
            continue
        
        if row_length == header_length:
            park_name_index = park_name_col_index
        else:
            park_name_index = park_name_col_index - 1
            # then park name index is same as what it was in header
            # else, park name index is header_index - 1
    
        col = row.find_all(header_element)[park_name_index]
        park_name = col.text
        
        # get park URL 
        try:
            a = col.find_all('a')
            if len(a) == 0:
                continue
            # a = row.find_next('a')
            for item in a:
                if ".jpg" not in item['href'] and "cite_note" not in item['href']:
                    park_url = item['href']
                    # logger.info(f"{park_url}") # Debugging
                    break
                else:
                    park_url = None
                    continue
        except:
            logger.info(f"No valid url for national park")
            park_url = None
    
        parks[park_name] = {'url': park_url}

    return parks


####################
## Create objects ##
####################

def create_master_table(master_dict):
    headers = ['country', 'national_park_name', 'park_url', 'lat_dms', 'long_dms', 'lat_dec', 'long_dms']
    table_data = []
    for country in master_dict:
        c_dict = master_dict[country]

        parks = c_dict['parks']
        for park_name in parks:
            park_dict = parks[park_name]

            try:
                lat_dms = park_dict['lat_dms']
            except:
                lat_dms = None

            try:
                long_dms = park_dict['long_dms']
            except:
                long_dms = None

            try:
                lat_dec = park_dict['lat_dec']
            except:
                lat_dec = None

            try:
                long_dec = park_dict['long_dec']
            except:
                long_dec = None

            try:
                park_url = 'https://en.wikipedia.org' + park_dict['url']
            except:
                park_url = None

            # append data to row
            row_data = []
            row_data.append(country)
            row_data.append(park_name)
            row_data.append(park_url)
            row_data.append(lat_dms)
            row_data.append(long_dms)
            row_data.append(lat_dec)
            row_data.append(long_dec)
            table_data.append(row_data)

    df = pd.DataFrame(table_data, columns=headers)

    return df

#######################
## Completion Checks ##
#######################

# Find countries that are missing parks
def find_missing_parks(master_dict: dict):
    missing_parks_list = []
    for country in master_dict:
        c_dict = master_dict[country]
        if len(c_dict['parks']) == 0:
            missing_parks_list.append(country)
    
    return missing_parks_list

def fill_in_missing_parks(missing_parks_list, master_dict):
    no_url = []
    invalid_url = []
    
    for country in missing_parks_list:
        c_dict = master_dict[country]
        c_url = c_dict['url']

        # If invalid url, write message and continue
        if c_url == None:
            no_url.append(country)
            missing_parks_list.remove(country)
            logger.info(f"{country} has no URL")
        
        elif 'wiki' not in c_url:
            invalid_url.append(country)
            missing_parks_list.remove(country)
            logger.info(f"{country} has a red link (invalid URL)")

        else: 
            logger.info(f"{country} has valid URL")
    
    return no_url, invalid_url

def total_parks(master_dict):
    """
    Sum up total number of parks in the world from master URL.
    """
    num_parks = 0
    for country in master_dict:
        c_dict = master_dict[country]
        if c_dict['number_of_parks'] != None:
            num_parks += int(c_dict['number_of_parks'])

    logger.info(f"There are {num_parks} national parks worldwide\n")

    return num_parks

def num_parks_found(master_dict):
    """
    Number of parks with coordinates scraped. Add it to country dictionary.
    """
    num_parks_total = 0

    for country in master_dict:
        c_dict = master_dict[country]
        num_parks_country = 0

        for park_name in c_dict['parks']:
            park_dict = c_dict['parks'][park_name]
            if 'lat_dms' in park_dict:
                if park_dict['lat_dms'] != None:
                    num_parks_total += 1
                    num_parks_country += 1
                else: 
                    logger.info(f"{park_name} does not have coordinates")

        c_dict['num_parks_scraped'] = num_parks_country
        master_dict[country] = c_dict

    return master_dict, num_parks_total

def num_parks_missing_country_url(master_dict: dict, missing_url_ls: list):
    total_num_parks = total_parks(master_dict)
    num_parks_missing = 0

    for country in missing_url_ls:
        c_dict = master_dict[country]

        if c_dict['number_of_parks'] != None:
            num_parks_missing += int(c_dict['number_of_parks'])
    
    pct_scraped = round(num_parks_missing/total_num_parks * 100,2)
    logger.info(f'{pct_scraped}% ({num_parks_missing}/{total_num_parks}) of parks are missing due to missing or invalid URLs for the country.')

def num_parks_missing_park_url(master_dict: dict):
    total_num_parks = total_parks(master_dict)
    num_parks_missing = len(find_invalid_or_missing_park_url(master_dict))
    
    pct_scraped = round(num_parks_missing/total_num_parks * 100,2)
    logger.info(f'{pct_scraped}% ({num_parks_missing}/{total_num_parks}) of parks are missing due to missing or invalid URLs for the national park.')

def country_completion_check(master_dict, high: float, low:float):
    # Empty lists to keep track of data quality
    incomplete_countries = []
    potentially_complete_countries = []
    too_many_scraped = []
    not_enough_scraped = []
    error_list = []

    for country in master_dict:
        c_dict = master_dict[country]
        
        # Get number of parks in the country that have coordinates
        try:
            if c_dict['number_of_parks'] != None:
                num_parks = int(c_dict['number_of_parks'])
                num_scraped = c_dict['num_parks_scraped']
                pct_scraped = round(num_scraped/num_parks * 100, 2)
                logger.info(f"{pct_scraped}% ({num_scraped}/{num_parks}) of national parks in {country} were scraped and have coordinates.")
                
                if pct_scraped != 100.0:
                    incomplete_countries.append(country)
                else:
                    if country not in potentially_complete_countries:
                        potentially_complete_countries.append(country)

                if pct_scraped > high:
                    too_many_scraped.append(country)
     
                if pct_scraped < low:
                    not_enough_scraped.append(country)

        except:
            logger.info(f"Error with calculating scrape percentage for {country}")
            error_list.append(country)
            pct_scraped = None

    return incomplete_countries, potentially_complete_countries, too_many_scraped, not_enough_scraped, error_list    


def completion_check(df, master_dict):
    num_parks = total_parks(master_dict)
    df = df[~df['lat_dms'].isna()]
    num_parks_scraped = df.shape[0]

    pct_complete = round(num_parks_scraped/num_parks * 100,2)
    logger.info(f"{pct_complete}% ({num_parks_scraped}/{num_parks}) of available parks have been scraped.")

    # Number of parks we couldn't find because of bad country URLs
    bad_urls = find_invalid_or_missing_country_url(master_dict)

    num_bad_urls = 0
    for country in bad_urls:
        c_dict = master_dict[country]
        if c_dict['number_of_parks'] != None:
            num_bad_urls += int(c_dict['number_of_parks'])

    pct_bad_urls = round(num_bad_urls/num_parks * 100,2)
    logger.info(f"{pct_bad_urls}% ({num_bad_urls}/{num_parks}) of parks are missing due to invalid country URLs.")

    # Number of parks we couldn't find because of bad park URLs
    num_bad_park_urls = len(find_invalid_or_missing_park_url(master_dict))

    pct_bad_park_urls = round(num_bad_park_urls/num_parks * 100,2)
    logger.info(f"{pct_bad_park_urls}% ({num_bad_park_urls}/{num_parks}) of parks are missing due to invalid park URLs.")


####################
## Main functions ##
####################

def create_soup(url: str):
    page = requests.get(url).text
    soup = BeautifulSoup(page, 'html.parser')

    return soup


def get_country_names(soup):
    """
    Scrapes the main URL to get the list of country names that have national parks. 
    """
    country_names_list = []

    for table in soup.find_all('table', class_ = 'wikitable'):
        for row in table.find_all('tr'):
            try:
                for i, col in enumerate(row.find_all('td')):
                    # Country name is in the first column of a table in this page
                    if i == 0 and col.text not in country_names_list:
                        country_names_list.append(col.text)
            except:
                print('Could not find country in the main URL')
    
    return country_names_list


def create_master_dict(soup, country_names: list):
    """
    Create a dictionary where each country in the main URL is a key. The value 
    for each country will contain information such as the National Park URL for 
    each country, the name of each national park in that country, and the 
    corresponding URL for that national park
    """

    master_dict = {}
    url_list = []

    for table in soup.find_all('table', class_ = 'wikitable'): 
        for row in table.find_all('tr'):
            country_dict = {}
            for i, col in enumerate(row.find_all('td')):
                if i == 0 and col.text in country_names:
                    country = col.text
                    a = col.find_next('a')
                    url = a['href']
                    url_list.append(url)
                    country_dict['url'] = url
                        
                # Get the number of parks
                if i == 2:
                    num_parks = col.text
                    # Replace empty string with None
                    if num_parks == '':
                        num_parks = str(0)
                    country_dict['number_of_parks'] = num_parks
                
                if country not in master_dict:
                        master_dict[country] = country_dict
    
    return master_dict 

def create_summary_df(master_dict: dict) -> pd.DataFrame:
    headers = ['country', 'number_of_parks_listed', 'number_of_parks_scraped']
    table_data = []
    
    for country in master_dict:
        row_data = []
        c_dict = master_dict[country]

        number_of_parks = c_dict['number_of_parks']
        num_scraped = c_dict['num_parks_scraped']
        
        row_data.append(country)
        row_data.append(number_of_parks)
        row_data.append(num_scraped)
        table_data.append(row_data)
        
    df = pd.DataFrame(table_data, columns=headers)
    
    # Clean country names
    clean_country_name_lambda = lambda x: clean_country_name(x)
    df["country"] = df["country"].apply(clean_country_name_lambda)
    
    return df


def get_park_names_and_urls(url):
    master_soup = create_soup(url)
    country_names = get_country_names(master_soup)
    master_dict = create_master_dict(master_soup, country_names)

    # Edge case where there is a "National Park" ID in a header, but there are multiple tables on the page
    edge_cases_g1 = ['Greece', 'Thailand', 'Italy', "People's Republic of China"]
    # No header, there is an unordered list, but its all protected areas - look for just 'National Park'
    edge_cases_g2 = ['Nicaragua', 'United Arab Emirates', 'Saudi Arabia', 'Oman', 'Afghanistan', 'Bhutan', 'Guyana']
    # Edge case where there is a "National Park" ID in a header, but there are multiple lists on the page
    edge_cases_g3 = ['Bahamas']
    # National park header exists, multiple lists exists, but protected areas are also in the lists
    edge_cases_g4 = ['Malaysia']
    # National park header exists, table is before header instead of after
    edge_cases_g5 = ['South Africa', 'Poland']
    # Multiple countries on the webpage, but parks are organized in table instead of list
    edge_cases_g6 = ['Estonia', 'Latvia', 'Lithuania']
    # Weird table structure - first column consists of merged cells which throws off park_name_col_index
    edge_cases_g7 = ['Vietnam']

    # DEBUG
    # counter = 0

    for country in master_dict:
        c_dict = master_dict[country]
        logger.info('----------------------------------------------------------------------------------------------------------------')
        # logger.info("DEBUGGING: New loop iteration")
        logger.info(f'Getting park names and URLs for {country}...')

        logger.info(f"URL for {country}: {c_dict['url']}")
        # if invalid url or None, continue
        if c_dict["url"] == None or 'wiki' not in c_dict['url']:
            logger.info(f"{country} does not have a valid URL. Moving to next country")
            c_dict['parks'] = {}
            continue

        # get URL
        c_url = "https://en.wikipedia.org" + c_dict['url']
        soup = create_soup(c_url)

        logger.info(f'Scraping {c_url}')

        # If there is only one park:
        if lone_nat_park_check(c_dict):
            logger.info(f"Only one park in {country}. Looking for National Park ID.")
        #   If we can find coordinates:
        #       Find park name and scrape coordinates
            
        #   Else, if we can find a header with an ID containing "National park":
            if check_national_park_id(soup, country):
                if country in edge_cases_g5:
                    logger.info(f"{country} is an edge case (Group 5). Scraping logic changing accordingly")
                    parks = scrape_edge_case_g5(soup)
                else:
                    nat_park_id = find_national_park_id(soup)
                    logger.info(f"A header with an ID containing national park has been found for {country}. Looking for the next table or list...")
        #           If there is a table directly after the National park header:
                    if check_next_national_park_table(nat_park_id):
                        if country in edge_cases_g1:
                            logger.info(f"{country} is an edge case (Group 1). Scraping logic changing accordingly")
                            parks = multiple_table_scrape(soup)
                        # Get park name and URLs from the table 
                        else:
                            park_table = find_next_national_park_table(nat_park_id)
                            logger.info(f"A national park table for {country} directly after the 'National Park' header has been found. Getting park names and URLs.")
                            parks = scrape_next_national_park_table(park_table)
        #           Else, if there is a list directly after the National park list: 
                    elif check_next_national_park_list(nat_park_id):
                        logger.info(f"No table was found. An unordered list was found instead.")
                        if country in edge_cases_g4:
                            logger.info(f"{country} is an edge case (Group 4). Scraping logic changing accordingly")
                            parks = scrape_edge_case_g4(soup)
                        elif country in edge_cases_g3:
                            logger.info(f"{country} is an edge case (Group 3). Scraping logic changing accordingly")
                            parks = scrape_edge_case_g3(soup)
            #           Get park name and URLs from the list
                        else:
                            park_list = find_next_national_park_list(nat_park_id)
                            parks = scrape_next_national_park_list(park_list)
        #       Else, there is no header with an ID containing "National park" and if we can find a table:
            else:
                logger.info(f"No header with an ID containing national park was found for {country}. Looking for any table in webpage...")
                if check_next_national_park_table(soup, country):           
                    logger.info(f"A table was found in the webpage. Checking if there are multiple tables...")
    #               If there is more than one valid table:
                    if multiple_table_check(soup):
    #                   Get park names and URLs from all the tables
                        parks = multiple_table_scrape(soup)  
    #               Else, if there is only one valid table:
                    else:
    #                   Get park names and URLs from the table
                        park_table = find_next_national_park_table(soup)
                        parks = scrape_next_national_park_table(park_table)
    #           Else, if can find the first list: - This may not be necessary, could save as None and append country to a list to get data elsewhere 
                elif check_next_national_park_list(soup, country):
                    if country in edge_cases_g2:
                        logger.info(f"{country} is an edge case (Group 2). Scraping logic changing accordingly")
                        parks = scrape_edge_case_g2(soup)
                    # Get park names and URLs from the list 
                    else:
                        park_list = find_next_national_park_list(soup)
                        parks = scrape_next_national_park_list(park_list)
                else:
                    parks = {}
        
        # Else, if the country name is an ID
        elif check_country_id(soup, country):
            logger.info(f"First elif block for {country}...")
            logger.info("More than one country. Country ID has been found.")
            country_header = find_country_id(soup, country)
            if country in edge_cases_g6:
                logger.info(f"{country} is an edge case (Group 6). Scraping logic changing accordingly")
                park_table = find_next_national_park_table(country_header)
                parks = scrape_next_national_park_table(park_table)
            elif check_next_national_park_list(country_header, country):
                    park_list = find_next_national_park_list(country_header)
                    parks = scrape_next_national_park_list(park_list)
            else:
                parks = {}
        
        # Else, if there is more than one park, if we can find a header with an ID containing "National park":
        elif check_national_park_id(soup, country):
            if country in edge_cases_g5:
                logger.info(f"{country} is an edge case (Group 5). Scraping logic changing accordingly")
                parks = scrape_edge_case_g5(soup)
            elif country in edge_cases_g7:
                logger.info(f"{country} is an edge case (Group 7). Scraping logic changing accordingly")
                parks = scrape_edge_case_g7(soup)
            else:
                logger.info(f"Second elif block for {country}...")
                nat_park_id = find_national_park_id(soup)
                logger.info(f"{country} has more than one national park. A header with an ID containing national park has been found for {country}. Looking for the next table or list.")
                # logger.info(f"DEBUGGING: Still on same loop iteration for {country}")
            #   If there is a table directly after the National park header:
                if check_next_national_park_table(nat_park_id, country):
                    if country in edge_cases_g1:
                            logger.info(f"{country} is an edge case. Scraping logic changing accordingly")
                            parks = multiple_table_scrape(soup)
            # Get park name and URLs from the table 
                    else:
                        park_table = find_next_national_park_table(nat_park_id)
                        logger.info(f'A national park table for {country} has been found. Getting park names and URLs.')
                        parks = scrape_next_national_park_table(park_table)
            #       Else, if there is a list directly after the National park list: 
                elif check_next_national_park_list(nat_park_id, country):
                        if country in edge_cases_g4:
                            logger.info(f"{country} is an edge case (Group 4). Scraping logic changing accordingly")
                            parks = scrape_edge_case_g4(soup)
                        elif country in edge_cases_g3:
                            logger.info(f"{country} is an edge case (Group 3). Scraping logic changing accordingly")
                            parks = scrape_edge_case_g3(soup)
                        # Get park names and URLs from the list 
                        else:
                            park_list = find_next_national_park_list(nat_park_id)
                            parks = scrape_next_national_park_list(park_list)
                else:
                    parks = {}
        # Else, if there is no "National park" ID:
        else:
            logger.info(f"Last else block for {country}...")
            logger.info(f"No national park ID and more than one park for {country}. Trying to find tables in webpage.") 
        #   If we can find a table:
            if check_table(soup, country):
                logger.info(f"Table found for {country}")
        #       If we can find multiple tables:
                if multiple_table_check(soup):      
                    logger.info(f"{country} has multiple tables.")
        #           Get park names and URLs from the tables
                    parks = multiple_table_scrape(soup)
        #       Else, if we only have one table:
                else:
                    logger.info(f"{country} only has one table.")
        #           Get park names and URLs from the table 
                    park_table = find_lone_table(soup)
                    parks = scrape_next_national_park_table(park_table)
        #   Else, if we can find first list:
            elif check_list(soup, country):
                if country in edge_cases_g2:
                    logger.info(f"{country} is an edge case (Group 2). Scraping logic changing accordingly")
                    parks = scrape_edge_case_g2(soup)
                else:       
                    # Get park names and URLs from the table
                    park_list = find_unordered_list(soup)
                    parks = scrape_next_national_park_list(park_list) 
        #   Else:
            else:
        #       Set the park names and URLs as blank dictionary
                logger.info("Saving a blank dictionary")
                parks = {}
        
        # Save park urls for the country
        c_dict['parks'] = parks 
        master_dict[country] = c_dict

        # Debugging
        # counter += 1
        # if counter == 10:
        #     break

    return master_dict

def main(url):
    main_start = time.time()
    
    # Create master dict with URLs for each national park
    logger.info("GETTING COUNTRY/NATIONAL PARK NAMES AND URLS ###################################################################")
    start = time.time()
    master_dict = get_park_names_and_urls(url)
    end = time.time()
    logger.info(f"{round(end-start, 2)} seconds to get country/national park names and URLS ############################################################\n")
    
    # Country URL check
    logger.info("PERFORMING CHECK - NO COORDINATES DUE TO MISSING URL FOR COUNTRY ###############################################")
    country_missing_url = find_invalid_or_missing_country_url(master_dict)
    num_parks_missing_country_url(master_dict, country_missing_url)
    
    # Park URL check
    logger.info("PERFORMING CHECKS - NO COORDINATES DUE TO MISSING URL FOR PARK #################################################")
    park_missing_url = find_invalid_or_missing_park_url(master_dict)
    num_parks_missing_park_url(master_dict)
    
    # Get coordinates
    logger.info("SCRAPING NATIONAL PARK URLS TO GET COORDINATES #################################################################")
    start = time.time()
    scrape_coordinates(master_dict)
    end = time.time()
    logger.info(f"{round(end-start,2)} seconds to get national park coordinates ##########################################################\n")
    
    # Create df and clean names
    logger.info("CREATING MAIN DATA TABLE AND CLEANING UP PARK AND COUNTRY NAMES ################################################")
    df = create_master_table(master_dict)
    
    # Clean country and park names
    clean_park_name_lambda = lambda x: clean_park_name(x)
    df["national_park_name"] = df["national_park_name"].apply(clean_park_name_lambda)

    clean_country_name_lambda = lambda x: clean_country_name(x)
    df["country"] = df["country"].apply(clean_country_name_lambda)

    # Add num_parks_scraped to master_dict
    master_dict, num_parks_total = num_parks_found(master_dict)
    logger.info(f"{num_parks_total} parks with coordinates have been found.")
    
    # completion checks
    incomplete_countries, potentially_complete_countries, too_many_scraped, not_enough_scraped, error_list = country_completion_check(master_dict, 105, 50)
    completion_check(df, master_dict)
    
    check_dict = {
        "country_missing_url": country_missing_url,
        "park_missing_url": park_missing_url,
        "incomplete": incomplete_countries,
        "complete": potentially_complete_countries,
        "too_many_parks": too_many_scraped, 
        "not_enough_parks": not_enough_scraped,
        "error_list": error_list
    }
    
    main_end = time.time()
    logger.info(f"{round(main_end-main_start,2)} seconds to complete main function ##########################################################")

    # Write dataframes to file
    df_final = df[~df['lat_dms'].isna()]
    df_final.to_csv("final.csv", encoding='utf-8-sig', index=False)

    df_missing = df[df['lat_dms'].isna()]
    df_missing.to_csv("missing_coordinates.csv", encoding='utf-8-sig', index=False)
    
    return master_dict, df, check_dict
    
    

########################
## DataFrame Cleaning ##
########################

def clean_park_name(park_name):
    park_name = re.sub("[\[].+[\]]", "", park_name) # remove square brackets
    park_name = re.sub("[(].+[)]", "", park_name) # remove round brackets
    park_name = re.sub(r"\xa0", " ", park_name) # replace xa0 with space
    park_name = re.sub(r"\n", "", park_name) # remove new lines
    park_name = re.sub("established.+", "", park_name) # remove text about park established dates
    park_name = re.sub("gazetted.+", "", park_name) # remove text after gazetted
    park_name = re.sub(r" (—|-|–) .+", "", park_name) # remove text after the park name that is separated with a dash
    park_name = re.sub(", .+", "", park_name) # remove text after the park name that is separated by comma
    park_name = re.sub("  .+", "", park_name) # remove text separated by double spaces
    park_name = re.sub("‡|†", "", park_name) # remove dagger characters
    park_name = re.sub("\*", "", park_name) # remove asterisks
    park_name = re.sub("^Source [0-9]: ", "", park_name) # Edge case
    park_name = re.sub("Εθνικός.+", "", park_name) # Remove specific non-English characters
    park_name = re.sub("Εθνικό.+", "", park_name) # Remove specific non-English characters
    park_name = re.sub("[가-힣].+", "", park_name) # Remove Korean characters00
    park_name = re.sub("\.\s[0-9].+", " ", park_name) # Edge case, period followed by date and area (size)
    park_name = re.sub(' in .+', "", park_name) # Removing text that provides regional context about national park
    park_name = re.sub('\. Lagoon .+', "", park_name) # Special case for Uruguay
    park_name = re.sub('\. Semi-freshwater .+', "", park_name) # Special case for Uruguay
    park_name = re.sub('\. Includes .+', "", park_name) # Special case for Uruguay
    park_name = park_name.strip() # Remove leading and trailing whitespaces
    
    return park_name

def clean_country_name(country_name):
    country_name = re.sub("[\[].+[\]]", "", country_name)
    country_name = country_name.strip() # Remove leading and trailing whitespaces

    return country_name