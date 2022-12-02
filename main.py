import sys
import time
from datetime import datetime

import requests
from bs4 import BeautifulSoup
import csv

BASE_URL = "https://myclickdealer.co.uk"

COLUMNS = [
    "Stock#", "VRM", "Registered Date", "Make / Model", "VIN / Chassis No", "Variant", "Purchasedate", "Location"
]


def run(email: str, password: str, locations: list):
    start = time.time()
    session = requests.Session()
    payload = {
        "login": email,
        "password": password
    }
    session.post(f"{BASE_URL}/dealer_interface_login_action.php", data=payload)

    # get all available locations
    res = session.get(f"{BASE_URL}/stock_list.php")
    content = res.content
    available_locations = dict()
    try:
        soup = BeautifulSoup(content, "html5lib")
        location_select = soup.find("select", {"id": "location_select"})
        for option in location_select.find_all("option"):
            available_locations[option.get_text()] = option["value"]
    except:
        print("Couldn't get available locations.")
        return

    # get report data
    today = datetime.today()
    location_ids = [
        available_locations.get(location.upper())
        for location in locations
        if location.upper() in available_locations
    ]
    params = {
        "date_day": today.day,
        "date_month": today.month,
        "date_year": today.year,
        "stock_type": "stock",
        "costs": "net",
        "vat_type": "",
        "status": "all",
        "sale_type": "",
        "stock_plan": "",
        "supplier_id": "",
        "stock_plan_supplier_id": "",
        "buyer_id": "",
        "search_weeks": 0,
        "search_weeks_retail": 0,
        "vehicle_grading_id": 0,
        "v5": "",
        "hpi": "",
        "action": "View+Report",
        "location_id": location_ids,
    }
    res = session.get(f"{BASE_URL}/stock_list.php", params=params)
    content = res.text

    try:
        soup = BeautifulSoup(content, "html5lib")
        stock_list_table = soup.find("table", {"id": "stock_list_table"})

        # parse header
        headers = stock_list_table.find("tr")
        list_headers = []
        for header in headers.find_all("th"):
            try:
                list_headers.append(header.get_text().strip())
            except:
                list_headers.append('')

        # parse main data
        data = []
        html_data = stock_list_table.find_all("tr")[1:]
        for elements in html_data:
            row = []
            for element in elements.find_all("td"):
                try:
                    row.append(element.get_text().strip())
                except:
                    row.append('')
            if row:
                data.append(row)

        # parse footer data
        html_footer = stock_list_table.find_all("tr")[-1]
        row = []
        for element in html_footer.find_all("th"):
            try:
                row.append(element.get_text().strip())
            except:
                row.append('')
        data.append(row)

        indexes = [list_headers.index(column) for column in COLUMNS]
        rows = []
        for item in data:
            row = []
            for i in indexes:
                row.append(item[i])
            rows.append(row)

        # write results to csv
        filename = f"{today.strftime('%Y-%m-%d_%H-%M-%S')}.csv"
        with open(filename, "w") as f:
            wr = csv.writer(f)
            wr.writerow(COLUMNS)
            wr.writerows(rows)
        print(f"Success to download CSV file. Output={filename}")
    except Exception as exc:
        print(f"Failed to scrape downloaded content. exc={exc}")
    print(f"Time elapsed: {time.time() - start}")


# python main.py email password
# python main.py email password OC TA CJ
if __name__ == '__main__':
    args = sys.argv[1:]
    email = args.pop(0)
    password = args.pop(0)
    locations = args
    run(email, password, locations)
