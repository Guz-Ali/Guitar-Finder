import json
import os
import re
from new_guitar_parsing import parse_new_guitars  # ✅ reused parser

BASE_SITE_URL = "https://www.guitarcenter.com"

def load_json_file(file_path):
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"{file_path} not found.")
    
    with open(file_path, 'r', encoding='utf-8') as file:
        return json.load(file)

def parse_used_guitars_old(data):
    guitars = []
    
    for result in data.get("results", []):
        for item in result.get("hits", []):
            shipping_info = item.get("shipping", {})
            slug = item.get("slug")
            free_shipping = shipping_info.get("free_shipping", 1)  # Default to free shipping if not specified
            shipping_message = shipping_info.get("shipping_message", "")
            shipping_price = 0

            # Check if shipping is free or if there's a shipping cost mentioned
            if free_shipping == 0 and shipping_message:
                # Extract shipping cost from the message, e.g., "$40.00 Shipping"
                match = re.search(r"(\$\d+(\.\d{1,2})?)", shipping_message)
                if match:
                    shipping_price = float(match.group(1).replace('$', '').replace(',', ''))

            # If the guitar is not from Sweetwater (Guitar Center or other), apply a flat $30 shipping fee
            if not slug:  # Assuming slug is used for Sweetwater
                shipping_price = 30  # Flat $30 shipping for other stores

            guitar_info = {
                "title": item.get("title"),
                "brand": item.get("brand"),
                "price": item.get("price"),
                "original_price": item.get("original_price"),
                "price_drop": item.get("price_drop"),
                "condition": item.get("condition"),
                "location": item.get("location"),
                "slug": slug,
                "url": f"https://www.guitarcenter.com/{slug}" if slug else None,  # ✅ Add this
                "shipping_available": bool(shipping_info.get("shipping_available")),
                "local_pickup_available": bool(shipping_info.get("local_pickup_available")),
                "store": "Sweetwater" if slug else "Guitar Center",  # Use Guitar Center for other stores
                "shipping_price": shipping_price  # Add shipping price info
            }
            guitars.append(guitar_info)
    
    return guitars

if __name__ == "__main__":
    try:
        combined_guitars = []

        # Traditional used guitar files, excluding "other" and "combined"
        old_files = sorted(
            f for f in os.listdir('.') 
            if f.startswith("used_guitars") 
            and f.endswith(".json") 
            and "other" not in f 
            and "combined" not in f
        )

        for file_name in old_files:
            data = load_json_file(file_name)
            if isinstance(data, dict) and "results" in data and isinstance(data["results"], list):
                parsed = parse_used_guitars_old(data)
                combined_guitars.extend(parsed)
            else:
                print(f"⚠️ Skipping {file_name}, doesn't look like old used_guitar format.")
        
        # ✅ Define new-format used guitar files
        new_format_files = sorted(f for f in os.listdir('.') if f.startswith("used_guitars_other") and f.endswith(".json"))

        for file_name in new_format_files:
            data = load_json_file(file_name)
            parsed = parse_new_guitars(data)  # returns a list
            if isinstance(parsed, list):
                combined_guitars.extend(parsed)
            else:
                print(f"⚠️ Skipping {file_name}, unexpected format: {type(parsed)}")
        
        # Save all combined data
        with open("used_guitars_combined.json", "w", encoding="utf-8") as out_file:
            json.dump(combined_guitars, out_file, indent=2, ensure_ascii=False)
        
        print(f"✅ Parsed and combined {len(combined_guitars)} used guitars into used_guitars_combined.json")
    
    except Exception as e:
        print(f"❌ Error: {e}")
