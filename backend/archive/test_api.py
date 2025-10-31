import requests
import json

# Test script for the Keyword Management API
BASE_URL = "http://localhost:8000"

def test_api():
    print("🧪 Testing Keyword Management API\n")
    
    # Test adding keywords
    test_keywords = [
        {"word": "sailing", "category": "maritime"},
        {"word": "diving", "category": "maritime"},
        {"word": "storm", "category": "weather"},
        {"word": "anchor", "category": "maritime"},
        {"word": "emergency", "category": "safety"},
        {"word": "help", "category": "safety"},
        {"word": "reef", "category": "maritime"}
    ]
    
    print("📝 Adding test keywords...")
    keyword_ids = []
    
    for keyword in test_keywords:
        try:
            response = requests.post(f"{BASE_URL}/keywords", json=keyword)
            if response.status_code == 200:
                result = response.json()
                keyword_ids.append(result['id'])
                print(f"✅ Added: {result['word']} ({result['category']})")
            else:
                print(f"❌ Failed to add {keyword['word']}: {response.text}")
        except Exception as e:
            print(f"❌ Error adding {keyword['word']}: {e}")
    
    # Test duplicate prevention
    print("\n🔄 Testing duplicate prevention...")
    try:
        response = requests.post(f"{BASE_URL}/keywords", json={"word": "sailing", "category": "maritime"})
        if response.status_code == 400:
            print("✅ Duplicate prevention working")
        else:
            print("❌ Duplicate prevention failed")
    except Exception as e:
        print(f"❌ Error testing duplicates: {e}")
    
    # Test listing keywords
    print("\n📋 Testing keyword listing...")
    try:
        response = requests.get(f"{BASE_URL}/keywords")
        if response.status_code == 200:
            keywords = response.json()
            print(f"✅ Retrieved {len(keywords)} keywords")
            for kw in keywords[:3]:  # Show first 3
                print(f"   - {kw['word']} ({kw['category']})")
        else:
            print(f"❌ Failed to list keywords: {response.text}")
    except Exception as e:
        print(f"❌ Error listing keywords: {e}")
    
    # Test filtering by category
    print("\n🔍 Testing category filtering...")
    try:
        response = requests.get(f"{BASE_URL}/keywords?category=maritime")
        if response.status_code == 200:
            maritime_keywords = response.json()
            print(f"✅ Found {len(maritime_keywords)} maritime keywords")
        else:
            print(f"❌ Failed to filter keywords: {response.text}")
    except Exception as e:
        print(f"❌ Error filtering keywords: {e}")
    
    # Test categories endpoint
    print("\n📂 Testing categories endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/categories")
        if response.status_code == 200:
            categories = response.json()
            print(f"✅ Found categories: {categories['categories']}")
        else:
            print(f"❌ Failed to get categories: {response.text}")
    except Exception as e:
        print(f"❌ Error getting categories: {e}")
    
    # Test keyword export
    if keyword_ids:
        print("\n📤 Testing keyword export...")
        try:
            # Export first 3 keywords
            export_ids = keyword_ids[:3]
            response = requests.post(f"{BASE_URL}/keywords/export", json=export_ids)
            if response.status_code == 200:
                export_data = response.json()
                print(f"✅ Exported keywords: {export_data['keywords']}")
            else:
                print(f"❌ Failed to export keywords: {response.text}")
        except Exception as e:
            print(f"❌ Error exporting keywords: {e}")
    
    print("\n🎉 Testing complete!")

if __name__ == "__main__":
    test_api()