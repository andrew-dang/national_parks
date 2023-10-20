## About the Data
The purpose of this dataset is to aid with the mapping of the national parks (as defined by the International Union for Conservation of Nature) of the world. 

This dataset contains three files. The first file, `national_parks.csv` contains information about national parks. For each national park in this file, you may find the name and coordinates of the national park, and the country that the national park can be found in. 

The second file, `missing_coordinates.csv` contains the name and URL for the parks that are missing coordinates.

The third file, `summary_table.csv` contains the number of parks listed and the number of parks scraped for each country.  

## Dataset Source
The data was scraped from Wikipedia using Python.

## Methodology
The data was scraped from Wikipedia using Python. The BeautifulSoup library was used to parse the HTML of each webpage. 

The scraping process began by scraping a [Wikipedia](https://en.wikipedia.org/wiki/List_of_national_parks#Notes) page (we will call this the main page moving forward) that contains several tables that listed the number of national parks for each country. Each country in these tables contained a URL for that country. By scraping the tables in the main page, we aimed to get the **name of each country**, the **number of national parks** in that country, and the **URL for that country**. 

Once we had the URL for each country, we scraped its contents. By scraping the country URL, we aimed to get the **name and URL of each national park** found in that country. The country URLs did not have a consistent structure across all countries, and required many if-then statements to account for these differences when looking for the data we were interested in. However, in most cases, the names and URL of the national parks were organized either in a single table or unordered lists, or several tables or unordered lists. In many cases, a table or unordered list could be found directly after an HTML header containing the text “National Park”. By using BeautifulSoup to look for specific HTML tags, attributes, and elements in each country’s webpage, we were able to get the name and URL of the national parks for most countries. Additional code was written to collect national park names and URLs for countries that did not conform to this structure. 

After obtaining the URL of each national park, we scraped its contents to get the **latitude and longitude of the national park**. The values for these coordinates were listed in degrees minutes seconds on the webpages. These coordinates were converted to degrees decimal using the `dms2dec` library. The geographic coordinates of each national park can be found in both degrees minute seconds and degrees decimal in the `national_parks.csv` file. 

The scraped data was organized in a nested dictionary, where each country name was a key. The value for each key was another dictionary. This inner dictionary stored the URL for a country, the number of parks listed on the main [Wikipedia](https://en.wikipedia.org/wiki/List_of_national_parks#Notes) page for this country, the number of parks were able to find coordinates for in this country, and finally, yet another dictionary that stored the names and URL for each national park found in this country. 

The scraped results were ultimately converted and organized into a Pandas DataFrame and then exported as a CSV file (saved as `national_parks.csv`). Each record contained a country name, a national park name, a national park URL, and the longitude and latitude in both degrees minute seconds and degrees decimal. The records were built by looping through each national park in each country within the scraped results dictionary and appending the relevant data to a list with each iteration. Many of the park names and country names had additional text which were removed to clean the dataset. A similar process was done to create the `missing_coordinates.csv` and `summary_table.csv` files. 


## Limitations
The main [Wikipedia](https://en.wikipedia.org/wiki/List_of_national_parks#Notes) page lists a total of 3,257 national parks worldwide. This dataset was able to find coordinates for 2,836 national parks. 90 national parks are missing coordinates due to missing country URLs, 333 national parks are missing coordinates due to missing national park URLs, and another 37 national parks are missing coordinates due to the coordinates not being present in the national park URL. 

If the country did not have a URL in the main [Wikipedia](https://en.wikipedia.org/wiki/List_of_national_parks#Notes) page, then it was not possible to get the name and coordinates of the national parks of that country. Likewise, if the national park itself did not have a URL, then the coordinates would not be scraped. Occasionally, the coordinates were present in a table within the country URL. In this scenario, the coordinates for the national park were scraped. The absence of a national park URL does not always mean the absence of geographic coordinates. In most cases however, not having a national park URL meant that we scraped a lower number of national parks for a country than what was listed on the main [Wikipedia](https://en.wikipedia.org/wiki/List_of_national_parks#Notes) page.

Upon investigation, it appeared that some country webpages had parks that were designated as a national park using their own national definition rather than the IUCN definition. On other occasions, some web pages listed decommissioned national parks. The scraper did not account for these scenarios. There were other webpages that listed other protected areas such as conservation areas that did not have the national park designation. While an attempt was made to filter out the non-national parks, it was not always successful and a handful of non-national parks may be present in the dataset. The scenarios described above resulted in some countries having more national parks scraped than what was listed on the [Wikipedia](https://en.wikipedia.org/wiki/List_of_national_parks#Notes) page. 
