import requests
from bs4 import BeautifulSoup
import csv

class ProductScraper:
    def __init__(self, url):
        self.url = url
        self.soup = None
        self.data = {
            "SKU": "",
            "Size": "",
            "Quantities": [],
            "Prices": [],
            "Entries": []  # List to store method, location, width, and height tuples
        }

    def fetch_page(self):
        try:
            response = requests.get(self.url)
            response.raise_for_status()  # Raise an error for bad status codes
            self.soup = BeautifulSoup(response.content, 'html.parser')
        except requests.exceptions.RequestException as e:
            print(f"Error fetching the page: {e}")
            return False
        return True

    def extract_sku(self):
        container_div = self.soup.find('div', class_='col-12 p-0 m-0 text-left')
        if container_div:
            item_id_p = container_div.find('p', class_='mx-0 px-0 mt-1 mb-4')
            if item_id_p:
                full_text = item_id_p.get_text(strip=True)
                sku_text = full_text.split("Item ID:")[1].strip()
                self.data["SKU"] = sku_text
            else:
                print("Item ID <p> tag not found.")
        else:
            print("Container div not found.")

    def extract_size(self):
        size_label = self.soup.find('h5', string="Size:")
        if size_label:
            size_text = size_label.find_next_sibling(string=True).strip()
            size_text_cleaned = size_text.replace('&quot;', '"')
            self.data["Size"] = size_text_cleaned
        else:
            print("Size label not found.")

    def extract_prices(self):
        table = self.soup.select_one('table.pricetable')
        if table:
            self.data["Quantities"] = [th.get_text(strip=True) for th in table.select('thead th')[1:]]
            self.data["Prices"] = [th.get_text(strip=True) for th in table.select('tbody th')]
        else:
            print("Price table not found.")

    def extract_locations_and_sizes(self):
        accordion_div = self.soup.find('div', id='printMethods')

        if accordion_div:
            child_divs = accordion_div.find_all('div', class_='card')

            for div in child_divs:
                buttons = div.select('button.btn.btn-link.btn-block.text-left.text-danger')
                methods = [button.get_text(strip=True).strip() for button in buttons]

                card_body = div.select_one('div.card-body')
                if card_body:
                    rows = card_body.select('table tbody tr')
                    for row in rows:
                        location = None
                        size = None
                        for td in row.find_all('td'):
                            if "Location" in td.decode_contents():
                                location = td.find('span').get_text(strip=True)
                            if "Size" in td.decode_contents():
                                size = td.find('span').get_text(strip=True)
                        if location and size:
                            width, height = size.replace("”", "").split(" X ")
                            width = width.strip()
                            height = height.strip()
                            for method in methods:
                                self.data["Entries"].append({
                                    "Method": method,
                                    "Location": location,
                                    "Width": width,
                                    "Height": height
                                })
                else:
                    print("Card body not found in one of the cards.")
        else:
            print("Print Methods accordion not found.")

    def save_to_csv(self, filename):
        with open(filename, mode='w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            # Write headers
            writer.writerow(["SKU", "Size", "Quantities", "Prices", "Method", "Location", "Width", "Height"])
            # Write data
            for entry in self.data["Entries"]:
                writer.writerow([
                    self.data["SKU"],
                    self.data["Size"],
                    ",".join(self.data["Quantities"]),
                    ",".join(self.data["Prices"]),
                    entry["Method"],
                    entry["Location"],
                    entry["Width"],
                    entry["Height"]
                ])
            print(f"Data saved to {filename}")

    def run(self):
        if self.fetch_page():
            self.extract_sku()
            self.extract_size()
            self.extract_prices()
            self.extract_locations_and_sizes()
            self.save_to_csv('product_data.csv')
            self.print_data()

    def print_data(self):
        print("Extracted Data:")
        print(f"SKU: {self.data['SKU']}")
        print(f"Size: {self.data['Size']}")
        print(f"Quantities: {', '.join(self.data['Quantities'])}")
        print(f"Prices: {', '.join(self.data['Prices'])}")
        for entry in self.data["Entries"]:
            print(f"Method: {entry['Method']}, Location: {entry['Location']}, Width: {entry['Width']}, Height: {entry['Height']}")

if __name__ == "__main__":
    url = 'https://www.arielpremium.com/product/ALB-CS24'
    scraper = ProductScraper(url)
    scraper.run()
