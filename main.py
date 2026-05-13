import requests
from bs4 import BeautifulSoup
import json
import re

def clean_price(price_text):
    if not price_text:
        return 0
    # Obdrži samo številke
    numeric_price = ''.join(filter(str.isdigit, price_text))
    return int(numeric_price) if numeric_price else 0

def clean_area(area_text):
    if not area_text:
        return 0.0
    
    # 1. Zamenjamo vejico s piko za decimalna števila
    area_text = area_text.replace(',', '.')
    
    # 2. Poiščemo samo številke in decimalno piko
    # Ta regex najde nize kot so "71.30"
    match = re.search(r"[-+]?\d*\.\d+|\d+", area_text)
    
    if match:
        return float(match.group())
    return 0.0

def scrape_abc_nepremicnine(limit=5, buy=True, type="flat"):
    base_url = "https://abc-nepremicnine.si"
    
    # 1. Map Property Types
    types_map = {
        "flat": "/stanovanje.v1",
        "house": "/hisa.v2",
        "business": "/poslovni-prostor.v3",
        "land": "/zemljisce.v5"
    }
    vrsta = types_map.get(type, "")

    # 3. Construct URL
    # Format: /nepremicnine/[prodaja/oddaja][tip]/[lokacija]
    action = 'prodaja.k1' if buy else 'oddaja.k2'
    url = f"{base_url}/Oglasi/{action}{vrsta}"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        listings = soup.find_all('div', class_='holder')
        data = []

        for item in listings[:limit]:
            # --- Title (Status: Prodamo/Oddamo) ---
            tag = item.find('ul', class_='more-info') if item.find('ul', class_='more-info') else None
            tag_title = tag.find_all('li')[0].find('span', class_="qty") if tag and tag.find_all('li') else None
            title = tag_title.get_text(strip=True) if tag else "N/A"

            # --- Features (Area and Other details) ---
            features_arr = []
            features_tag = tag.find_all('li', class_="info-label")[2:] if tag and tag.find_all('li') else []
            for f in features_tag:
                if f.find('span', class_="qty"):
                    features_arr.append(f.get_text(strip=True))
            print(features_arr)

            # --- Price ---
            price_tag = tag.find('span', class_='oglasCena').strong if tag else None
            price = clean_price(price_tag.get_text(strip=True) if price_tag else "N/A")

            # --- Location & Description ---
            loc_tag = item.find('div', class_='prop-title')
            location_str = loc_tag.h1.get_text(strip=True) if loc_tag else "N/A"

            area_tag = tag.find_all('li')[1].find('span', class_="qty") if tag and tag.find_all('li') else None
            area = clean_area(area_tag.get_text(strip=True) if area_tag else "N/A")

            land_desc = loc_tag.h3.get_text(strip=True) if loc_tag and loc_tag.h3 else "N/A"

            # --- Image ---
            img_tag = item.find("div", class_="overlay")['style'][22:-2] if item.find("div", class_="overlay") and 'style' in item.find("div", class_="overlay").attrs else ""
            img_src = "https:" + img_tag if img_tag else ""

            # --- Link ---
            link = item.find('div', class_="overlayw").a['href'] if item.find('div', class_="overlayw") and item.find('div', class_="overlayw").a else ""



            data.append({
                "site": "abc-nepremicnine",
                "status": title,
                "type": land_desc,
                "price": price,
                "location": location_str,
                "area": area,
                "features": features_arr,
                "link": base_url + link if link else "",
                "image": img_src
            })

        return data

    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    # Example: Buy a flat in Ljubljana
    results = scrape_abc_nepremicnine(limit=3, buy=True, type="flat")
    print(json.dumps(results, indent=4, ensure_ascii=False))
