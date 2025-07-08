#!/usr/bin/env python3
import requests
import json
import unittest
import os
import sys
from dotenv import load_dotenv
import time

# Load environment variables from frontend/.env to get the backend URL
load_dotenv("frontend/.env")

# Get the backend URL from environment variables
BACKEND_URL = os.environ.get("REACT_APP_BACKEND_URL")
if not BACKEND_URL:
    print("Error: REACT_APP_BACKEND_URL not found in environment variables")
    sys.exit(1)

# Ensure the URL ends with /api for all requests
API_URL = f"{BACKEND_URL}/api"
print(f"Using API URL: {API_URL}")

class FarmAPITest(unittest.TestCase):
    """Test suite for La Ferme des Mini-Pousses API"""
    
    @classmethod
    def setUpClass(cls):
        """Initialize test data once for all tests"""
        # Initialize sample data
        print("Setting up test class...")
        cls.init_sample_data()
        
        # Create a visitor session for testing
        cls.session_id = cls.create_visitor_session()
        
        # Get all zones for testing
        cls.zones = cls.get_all_zones()
        assert len(cls.zones) > 0, "No zones found for testing"
        
        # Store a zone ID for testing
        cls.test_zone_id = cls.zones[0]["id"]
        print(f"Using test zone ID: {cls.test_zone_id}")
    
    @classmethod
    def init_sample_data(cls):
        """Initialize sample data for testing"""
        try:
            response = requests.post(f"{API_URL}/init-sample-data")
            assert response.status_code == 200, f"Failed to initialize sample data: {response.text}"
            print("Sample data initialized successfully")
            return response.json()
        except Exception as e:
            print(f"Error initializing sample data: {e}")
            return {"message": "Error initializing sample data"}
    
    @classmethod
    def create_visitor_session(cls):
        """Create a visitor session for testing"""
        try:
            response = requests.post(f"{API_URL}/session")
            assert response.status_code == 200, f"Failed to create visitor session: {response.text}"
            session_data = response.json()
            assert "id" in session_data, "Session ID not found in response"
            print(f"Created visitor session with ID: {session_data['id']}")
            return session_data["id"]
        except Exception as e:
            print(f"Error creating visitor session: {e}")
            return "test-session-id"
    
    @classmethod
    def get_all_zones(cls):
        """Get all zones for testing"""
        try:
            response = requests.get(f"{API_URL}/zones")
            assert response.status_code == 200, f"Failed to get zones: {response.text}"
            zones = response.json()
            print(f"Found {len(zones)} zones")
            return zones
        except Exception as e:
            print(f"Error getting zones: {e}")
            return []
    
    def test_01_get_zones(self):
        """Test GET /api/zones endpoint"""
        print("\nTesting GET /api/zones...")
        try:
            response = requests.get(f"{API_URL}/zones")
            self.assertEqual(response.status_code, 200, f"Failed to get zones: {response.text}")
            zones = response.json()
            self.assertTrue(len(zones) >= 3, f"Expected at least 3 zones, got {len(zones)}")
            
            # Verify zone structure
            for zone in zones:
                self.assertIn("id", zone, "Zone ID not found")
                self.assertIn("name", zone, "Zone name not found")
                self.assertIn("description", zone, "Zone description not found")
                self.assertIn("game", zone, "Zone game not found")
            print("✅ GET /api/zones test passed")
        except Exception as e:
            print(f"❌ GET /api/zones test failed: {e}")
            raise
    
    def test_02_get_zone_by_id(self):
        """Test GET /api/zones/{zone_id} endpoint"""
        print(f"\nTesting GET /api/zones/{self.test_zone_id}...")
        try:
            response = requests.get(f"{API_URL}/zones/{self.test_zone_id}")
            self.assertEqual(response.status_code, 200, f"Failed to get zone: {response.text}")
            zone = response.json()
            self.assertEqual(zone["id"], self.test_zone_id, "Zone ID mismatch")
            
            # Test with invalid zone ID
            print("Testing with invalid zone ID...")
            response = requests.get(f"{API_URL}/zones/invalid-id")
            self.assertEqual(response.status_code, 404, "Expected 404 for invalid zone ID")
            print("✅ GET /api/zones/{zone_id} test passed")
        except Exception as e:
            print(f"❌ GET /api/zones/{self.test_zone_id} test failed: {e}")
            raise
    
    def test_03_create_update_delete_zone(self):
        """Test POST, PUT, DELETE /api/zones endpoints"""
        print("\nTesting zone CRUD operations...")
        try:
            # Create a new zone
            new_zone = {
                "name": "Test Zone",
                "description": "This is a test zone created by the test suite",
                "video_url": "https://www.youtube.com/embed/test",
                "cta_text": "Test CTA",
                "game": {
                    "type": "quiz",
                    "question": "What is this test testing?",
                    "options": ["API", "Database", "Frontend", "All of the above"],
                    "correct_answer": "API",
                    "explanation": "This test is testing the API endpoints"
                }
            }
            
            # Create zone
            print("Creating new zone...")
            response = requests.post(f"{API_URL}/zones", json=new_zone)
            self.assertEqual(response.status_code, 200, f"Failed to create zone: {response.text}")
            created_zone = response.json()
            self.assertIn("id", created_zone, "Zone ID not found in created zone")
            zone_id = created_zone["id"]
            print(f"Created zone with ID: {zone_id}")
            
            # Verify zone was created
            print("Verifying zone was created...")
            response = requests.get(f"{API_URL}/zones/{zone_id}")
            self.assertEqual(response.status_code, 200, f"Failed to get created zone: {response.text}")
            
            # Update zone
            print("Updating zone...")
            updated_zone = new_zone.copy()
            updated_zone["name"] = "Updated Test Zone"
            updated_zone["description"] = "This zone has been updated"
            
            response = requests.put(f"{API_URL}/zones/{zone_id}", json=updated_zone)
            self.assertEqual(response.status_code, 200, f"Failed to update zone: {response.text}")
            
            # Verify zone was updated
            print("Verifying zone was updated...")
            response = requests.get(f"{API_URL}/zones/{zone_id}")
            self.assertEqual(response.status_code, 200, f"Failed to get updated zone: {response.text}")
            updated_zone_response = response.json()
            self.assertEqual(updated_zone_response["name"], "Updated Test Zone", "Zone name was not updated")
            
            # Delete zone
            print("Deleting zone...")
            response = requests.delete(f"{API_URL}/zones/{zone_id}")
            self.assertEqual(response.status_code, 200, f"Failed to delete zone: {response.text}")
            
            # Verify zone was deleted
            print("Verifying zone was deleted...")
            response = requests.get(f"{API_URL}/zones/{zone_id}")
            self.assertEqual(response.status_code, 404, "Zone was not deleted")
            print("✅ Zone CRUD operations test passed")
        except Exception as e:
            print(f"❌ Zone CRUD operations test failed: {e}")
            raise
    
    def test_04_qr_code_generation(self):
        """Test GET /api/zones/{zone_id}/qr endpoint"""
        print(f"\nTesting GET /api/zones/{self.test_zone_id}/qr...")
        try:
            response = requests.get(f"{API_URL}/zones/{self.test_zone_id}/qr")
            self.assertEqual(response.status_code, 200, f"Failed to get QR code: {response.text}")
            qr_data = response.json()
            self.assertIn("qr_code", qr_data, "QR code not found in response")
            self.assertIn("zone_name", qr_data, "Zone name not found in response")
            
            # Verify QR code is a base64 string
            self.assertTrue(len(qr_data["qr_code"]) > 0, "QR code is empty")
            
            # Test with invalid zone ID
            print("Testing with invalid zone ID...")
            response = requests.get(f"{API_URL}/zones/invalid-id/qr")
            self.assertEqual(response.status_code, 404, "Expected 404 for invalid zone ID")
            print("✅ QR code generation test passed")
        except Exception as e:
            print(f"❌ QR code generation test failed: {e}")
            raise
    
    def test_05_game_answer(self):
        """Test POST /api/zones/{zone_id}/game/answer endpoint"""
        print(f"\nTesting POST /api/zones/{self.test_zone_id}/game/answer...")
        try:
            # Get the zone to find the correct answer
            print("Getting zone to find correct answer...")
            response = requests.get(f"{API_URL}/zones/{self.test_zone_id}")
            self.assertEqual(response.status_code, 200, f"Failed to get zone: {response.text}")
            zone = response.json()
            self.assertIn("game", zone, "Game not found in zone")
            
            correct_answer = zone["game"]["correct_answer"]
            wrong_answer = "Wrong Answer"
            print(f"Correct answer: {correct_answer}")
            
            # Test with correct answer
            print("Testing with correct answer...")
            response = requests.post(
                f"{API_URL}/zones/{self.test_zone_id}/game/answer", 
                data={"selected_answer": correct_answer}
            )
            self.assertEqual(response.status_code, 200, f"Failed to submit correct answer: {response.text}")
            result = response.json()
            self.assertTrue(result["is_correct"], "Correct answer was marked as incorrect")
            
            # Test with wrong answer
            print("Testing with wrong answer...")
            response = requests.post(
                f"{API_URL}/zones/{self.test_zone_id}/game/answer", 
                data={"selected_answer": wrong_answer}
            )
            self.assertEqual(response.status_code, 200, f"Failed to submit wrong answer: {response.text}")
            result = response.json()
            self.assertFalse(result["is_correct"], "Wrong answer was marked as correct")
            
            # Test with invalid zone ID
            print("Testing with invalid zone ID...")
            response = requests.post(
                f"{API_URL}/zones/invalid-id/game/answer", 
                data={"selected_answer": correct_answer}
            )
            self.assertEqual(response.status_code, 404, "Expected 404 for invalid zone ID")
            print("✅ Game answer test passed")
        except Exception as e:
            print(f"❌ Game answer test failed: {e}")
            raise
    
    def test_06_visitor_session(self):
        """Test visitor session endpoints"""
        print(f"\nTesting visitor session endpoints...")
        try:
            # Get session
            print(f"Getting session {self.session_id}...")
            response = requests.get(f"{API_URL}/session/{self.session_id}")
            self.assertEqual(response.status_code, 200, f"Failed to get session: {response.text}")
            session = response.json()
            self.assertEqual(session["id"], self.session_id, "Session ID mismatch")
            
            # Mark zone as visited
            print(f"Marking zone {self.test_zone_id} as visited...")
            response = requests.post(f"{API_URL}/session/{self.session_id}/visit/{self.test_zone_id}")
            self.assertEqual(response.status_code, 200, f"Failed to mark zone as visited: {response.text}")
            visit_result = response.json()
            self.assertIn("visited_count", visit_result, "Visited count not found in response")
            self.assertEqual(visit_result["visited_count"], 1, "Expected visited count to be 1")
            
            # Verify zone was marked as visited
            print("Verifying zone was marked as visited...")
            response = requests.get(f"{API_URL}/session/{self.session_id}")
            self.assertEqual(response.status_code, 200, f"Failed to get updated session: {response.text}")
            updated_session = response.json()
            self.assertIn(self.test_zone_id, updated_session["visited_zones"], "Zone not marked as visited")
            
            # Mark another zone as visited
            if len(self.zones) > 1:
                second_zone_id = self.zones[1]["id"]
                print(f"Marking second zone {second_zone_id} as visited...")
                response = requests.post(f"{API_URL}/session/{self.session_id}/visit/{second_zone_id}")
                self.assertEqual(response.status_code, 200, f"Failed to mark second zone as visited: {response.text}")
                
                # Verify both zones are marked as visited
                print("Verifying both zones are marked as visited...")
                response = requests.get(f"{API_URL}/session/{self.session_id}")
                self.assertEqual(response.status_code, 200, f"Failed to get updated session: {response.text}")
                updated_session = response.json()
                self.assertEqual(len(updated_session["visited_zones"]), 2, "Expected 2 visited zones")
            
            # Test with invalid session ID
            print("Testing with invalid session ID...")
            response = requests.get(f"{API_URL}/session/invalid-id")
            self.assertEqual(response.status_code, 404, "Expected 404 for invalid session ID")
            
            # Test marking zone as visited with invalid session ID
            print("Testing marking zone as visited with invalid session ID...")
            response = requests.post(f"{API_URL}/session/invalid-id/visit/{self.test_zone_id}")
            self.assertEqual(response.status_code, 404, "Expected 404 for invalid session ID")
            print("✅ Visitor session test passed")
        except Exception as e:
            print(f"❌ Visitor session test failed: {e}")
            raise

if __name__ == "__main__":
    # Run tests with better error handling
    test_suite = unittest.TestSuite()
    test_suite.addTest(FarmAPITest('test_01_get_zones'))
    test_suite.addTest(FarmAPITest('test_02_get_zone_by_id'))
    test_suite.addTest(FarmAPITest('test_03_create_update_delete_zone'))
    test_suite.addTest(FarmAPITest('test_04_qr_code_generation'))
    test_suite.addTest(FarmAPITest('test_05_game_answer'))
    test_suite.addTest(FarmAPITest('test_06_visitor_session'))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # Print summary
    print("\n=== TEST SUMMARY ===")
    print(f"Total tests: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Skipped: {len(result.skipped)}")
    
    # Exit with appropriate code
    sys.exit(len(result.failures) + len(result.errors))