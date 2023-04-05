import concurrent.futures
import datetime
import hashlib
import json
import time
import requests
from fake_useragent import UserAgent
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager

BUF_SIZE = 65536  # 64kb


def encode_file(filename):
    '''
        reads file refering to filename returns sha256 encoded string of file content
    '''
    sha = hashlib.sha256()
    with open(f'./assets/{filename}', 'rb') as f:
        while True:
            # read in chunks for optimal memory use
            data = f.read(BUF_SIZE)
            if not data:
                break
            sha.update(data)
    return sha.hexdigest()


def download_file(url):
    '''
        Downloads assets from url, hashes it to sha256 falvour.
        Saves content with hash string as filename and return hash string
    '''
    sha = hashlib.sha256()
    response = requests.get(url, timeout=300)
    sha.update(response.content)
    sha256 = sha.hexdigest()

    with open(f'./assets/{sha256}', 'wb') as f:
        f.write(response.content)

    return sha256


def driver1():
    ua = UserAgent()
    options = Options()
    options.add_argument("--headless")
    # options.add_extension("extension_0_3_1_0.crx")
    options.add_argument('--disable-gpu')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-blink-features")
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    options.add_argument(f'user-agent={ua.random}')
    # options.add_experimental_option("prefs", {'profile.managed_default_content_settings.javascript': 2})
    # options.add_experimental_option("detach", True)
    driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=options)
    return driver


def header():
    ua = UserAgent(browsers=['chrome'], use_external_data=True)
    headers = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
        'Accept-Language': 'en-US,en;q=0.9',
        'Referer': 'https://www.wolfautomation.com/',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Sec-Fetch-User': '?1',
        'Upgrade-Insecure-Requests': '1',
        'User-Agent': ua.random,
    }
    return headers


def scrap(p):
    # for p in all_cat_links:
    category = p.find("span").text
    for x in range(1, 10000):
        link2 = "https://www.wolfautomation.com" + p["href"] + f"?p={x}"
        r2 = requests.get(link2, headers=header()).text
        soup2 = BeautifulSoup(r2, "html.parser")
        try:
            if soup2.select_one(
                    ".message.info.empty").text.strip() == "We can't find products matching the selection.":
                print("a")
                break
        except:
            pass
        p_links = [[i.find("a")["href"], i.select_one(".product.name.product-item-name").text.strip()] for i in
                   soup2.select_one(".products.list.items.product-items").find_all("li")]
        for link3 in p_links:
            # r3 = requests.get(link3[0]).text
            win.get(link3[0])
            time.sleep(3)
            r3 = win.page_source
            soup3 = BeautifulSoup(r3, "html.parser")
            try:
                p_name = link3[1]
                p_manufacture = soup3.select_one(".product.attribute.manufacturer").text.strip()
                p_sku = soup3.select_one(".product.attribute.sku").text.replace("-", "").strip()
                # in_stock = soup3.select_one(".availability.only.test1").text.strip()
                desc = soup3.select_one(".product.attribute.overview").text.strip()
                desc_html = str(soup3.select_one(".product.attribute.overview")).strip()
                if desc:
                    pass
                else:
                    desc = None
                    desc_html = None
                avail_to_check = soup3.select_one("#product-addtocart-button").text.strip()
                if avail_to_check == "Add to Cart":
                    in_stock_bool = True
                    avail_to_check_bool = True
                else:
                    in_stock_bool = False
                    avail_to_check_bool = False
                price = soup3.select_one(".price-box.price-final_price").text.strip().replace("$", "")
                if price:
                    pri = [{"min_qty": 1,
                            "price": float(price),
                            "currency": "USD"}]
                else:
                    pri = [{"min_qty": 1,
                            "price_string": "Call for price",
                            "currency": "USD"}]
                quantity = soup3.select_one(".field.qty").find("input")["value"]
                key = [i.text for i in soup3.select_one("#product-attribute-specs-table").find_all("th")]
                value = [i.text for i in soup3.select_one("#product-attribute-specs-table").find_all("td")]
                attri = dict(zip(key, value))
                rem_list = ["SKU", 'Alternate Part Number', 'Part Number', 'Manufacturer', 'Availability']
                for key in rem_list:
                    try:
                        del attri[key]
                        print(key)
                    except:
                        pass
                test = {i.text.strip().split(":")[0]: i.text.strip().split(":")[1] for i in
                        soup3.select_one(".spectab").find_all("li") if ":" in i.text.strip()}
                attri_main = {**attri, **test}
                ass = []
                try:
                    for i in soup3.find(id="tab.tab1").find_all("li"):
                        href = i.find("a")["href"]
                        # download_datsheet = download_file(href)
                        # asset_hash = encode_file(download_datsheet)
                        if "datasheet" in href:
                            f = {
                                "name": i.find("a").text,
                                "source": href,
                                "type": "document/spec",
                                "media_type": "application/pdf",
                                # "sha256": asset_hash
                            }
                        else:
                            f = {
                                "name": i.find("a").text,
                                "source": href,
                                "type": "document/catalog",
                                "media_type": "application/pdf",
                                # "sha256": asset_hash
                            }
                        ass.append(f)
                except:
                    pass
                try:
                    image = soup3.find(class_="fotorama__nav-wrap fotorama__nav-wrap--horizontal").find_all("img")
                    for im in image:
                        # download_datsheet = download_file(im["src"])
                        # asset_hash = encode_file(download_datsheet)
                        f = {
                            "source": im["src"],
                            "type": "image/product",
                            "media_type": "image/jpeg",
                            # "sha256": asset_hash
                        }
                        ass.append(f)
                except:
                    pass
                try:
                    main_image = soup3.select_one(".fotorama__stage__shaft.fotorama__grab").find("img")["src"]
                    # download = download_file(main_image)
                    # image_hash = encode_file(download)
                    img = {
                        "name": p_name,
                        "source": main_image,
                        "type": "image/product",
                        "media_type": "image/jpeg",
                        # "sha256": image_hash
                    }
                except:
                    img = None
                data = {
                    "vendor_name": "Marshall Wolf Automation",
                    "name": p_name,
                    "uom": "each",
                    "sku_unit": "item",
                    "sku_quantity": int(quantity),
                    "quantity_increment": 1,
                    "estimated_lead_time": None,
                    "manufacturer": p_manufacture,
                    "mpn": p_sku,
                    "features": [],
                    "sku": p_sku,
                    "pdp_url": link3[0],
                    "category": [category],
                    "price": pri,
                    "in_stock": in_stock_bool,
                    "available_to_checkout": avail_to_check_bool,
                    "description": desc,
                    "description_html": desc_html,
                    "attributes": [{"name": key, "value": attri_main[key], "group": "Specifications"} for
                                   key, value
                                   in
                                   attri_main.items()],
                    "main_image": img,
                    "assets": ass,
                    "_scrape_metadata": {"breadcrumbs": [{
                        "name": "Home",
                        "url": "https://www.wolfautomation.com/"},
                        {"name": "All Products", "url": link1},
                        {"name": category, "url": link2.split("?")[0]}, ], "url": link3[0],
                        "date_visited": datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%f")[
                                        :-3] + "Z"}}
                print(data)
                dataset.append(data)

            except:
                pass


dataset = []
win = driver1()
link1 = "https://www.wolfautomation.com/all-products"
r1 = requests.get(link1).text
soup1 = BeautifulSoup(r1, "html.parser")
all_cat_links = [i.find("a") for i in soup1.select(".manufacturercategoryblock")]
with concurrent.futures.ThreadPoolExecutor(32) as e:
    e.map(scrap, all_cat_links)

json_object = json.dumps(dataset, indent=4)
with open("wolf.json", "w") as outfile:
    outfile.write(json_object)
