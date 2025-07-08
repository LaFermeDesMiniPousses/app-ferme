#!/usr/bin/env python3
import requests
import base64
import io
from PIL import Image
import json
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv("/app/frontend/.env")

BACKEND_URL = os.environ.get("REACT_APP_BACKEND_URL")
API_URL = f"{BACKEND_URL}/api"

def url_to_base64(url, max_size=(800, 600)):
    """Convert image URL to base64 string with resizing"""
    try:
        # Download image
        response = requests.get(url)
        response.raise_for_status()
        
        # Open with PIL and resize
        image = Image.open(io.BytesIO(response.content))
        
        # Convert to RGB if necessary
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        # Resize while maintaining aspect ratio
        image.thumbnail(max_size, Image.Resampling.LANCZOS)
        
        # Convert to base64
        buffer = io.BytesIO()
        image.save(buffer, format='JPEG', quality=85)
        base64_string = base64.b64encode(buffer.getvalue()).decode('utf-8')
        
        return base64_string
    except Exception as e:
        print(f"Error converting {url} to base64: {e}")
        return ""

def update_zone_with_image(zone_id, image_base64):
    """Update a zone with an image"""
    try:
        # First get the current zone data
        response = requests.get(f"{API_URL}/zones/{zone_id}")
        if response.status_code != 200:
            print(f"Failed to get zone {zone_id}: {response.text}")
            return False
            
        zone_data = response.json()
        
        # Update the image
        zone_data["image_base64"] = image_base64
        
        # Remove fields that shouldn't be in the update
        update_data = {
            "name": zone_data["name"],
            "description": zone_data["description"],
            "image_base64": image_base64,
            "video_url": zone_data.get("video_url", ""),
            "audio_base64": zone_data.get("audio_base64", ""),
            "cta_text": zone_data.get("cta_text", "Découvrir"),
            "cta_url": zone_data.get("cta_url", ""),
            "game": zone_data.get("game")
        }
        
        # Update the zone
        response = requests.put(f"{API_URL}/zones/{zone_id}", json=update_data)
        if response.status_code == 200:
            print(f"✅ Updated zone {zone_data['name']} with image")
            return True
        else:
            print(f"❌ Failed to update zone {zone_id}: {response.text}")
            return False
            
    except Exception as e:
        print(f"Error updating zone {zone_id}: {e}")
        return False

def main():
    """Main function to update all zones with images"""
    print("🌾 Updating zone images for La Ferme des Mini-Pousses...")
    
    # Get all zones
    try:
        response = requests.get(f"{API_URL}/zones")
        if response.status_code != 200:
            print(f"Failed to get zones: {response.text}")
            return
            
        zones = response.json()
        print(f"Found {len(zones)} zones")
        
        # Image mappings based on zone names
        zone_images = {
            "Poulailler": "https://images.unsplash.com/photo-1672620003939-f82a45cb5adc",
            "Wallaby": "https://images.unsplash.com/photo-1511762996499-16c647c36eee",
            "Rosie la vache avec Yukie le poulain": "https://images.unsplash.com/photo-1636014421603-97854d143a3e"
        }
        
        # Update each zone with its corresponding image
        for zone in zones:
            zone_name = zone["name"]
            if zone_name in zone_images:
                print(f"🖼️  Processing image for {zone_name}...")
                image_url = zone_images[zone_name]
                image_base64 = url_to_base64(image_url)
                
                if image_base64:
                    success = update_zone_with_image(zone["id"], image_base64)
                    if success:
                        print(f"✅ Successfully updated {zone_name}")
                    else:
                        print(f"❌ Failed to update {zone_name}")
                else:
                    print(f"❌ Failed to process image for {zone_name}")
            else:
                print(f"⚠️  No image mapping found for {zone_name}")
        
        print("\n🎉 Zone image update complete!")
        
    except Exception as e:
        print(f"Error in main function: {e}")

if __name__ == "__main__":
    main()