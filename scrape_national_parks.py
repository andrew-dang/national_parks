from national_parks import * 

import logging 
logging.basicConfig()
logger = logging.getLogger()
logger.setLevel(logging.INFO)

if __name__ == "__main__":
    url = "https://en.wikipedia.org/wiki/List_of_national_parks"
    master_dict, df, check_dict = main(url)

