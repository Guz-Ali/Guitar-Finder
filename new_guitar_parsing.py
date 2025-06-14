import json
import os

BASE_SITE_URL = "https://www.guitarcenter.com"

def load_json_file(file_path):
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"{file_path} not found.")
    
    with open(file_path, 'r', encoding='utf-8') as file:
        return json.load(file)

def calculate_price_drop(original_price, price):
    try:
        if original_price and price and original_price > price:
            return round(original_price - price, 2)
    except:
        pass
    return 0

def parse_new_guitars(data):
    guitars = []

    # Support both list and dict with "results" key
    results = data if isinstance(data, list) else data.get("results", [])

    for result in results:
        for item in result.get("hits", []):
            original_price = item.get("listPrice") or 0
            price = item.get("price") or 0
            
            slug = item.get("seoUrl")
            full_url = f"{BASE_SITE_URL}{slug}" if slug else None

            retail_only = item.get("retailOnly", False)
            if retail_only:
                local_pickup_available = True
                shipping_available = False
            else:
                local_pickup_available = False
                shipping_available = True
            
            guitar_info = {
                "title": item.get("displayName"),
                "brand": item.get("brand"),
                "price": price,
                "original_price": original_price,
                "price_drop": calculate_price_drop(original_price, price),
                "condition": item.get("condition", {}).get("lvl0"),
                "location": None,
                "slug": slug,
                "url": full_url,
                "shipping_available": shipping_available,
                "local_pickup_available": local_pickup_available,
                "store": "Guitar Center"
            }
            guitars.append(guitar_info)
    
    return guitars

if __name__ == "__main__":
    try:
        all_guitars = []
        json_files = sorted(f for f in os.listdir('.') if f.startswith("new_guitars") and f.endswith(".json"))
        
        for file_name in json_files:
            data = load_json_file(file_name)
            parsed = parse_new_guitars(data)
            all_guitars.extend(parsed)
        
        with open("new_guitars_combined.json", "w", encoding="utf-8") as out_file:
            json.dump(all_guitars, out_file, indent=2, ensure_ascii=False)
        
        print(f"✅ Parsed and combined {len(all_guitars)} new guitars into new_guitars_combined.json")
    
    except Exception as e:
        print(f"❌ Error: {e}")
