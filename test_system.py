#!/usr/bin/env python3
"""
Test script for the Event Reporting System
This script tests the core functionality of the system
"""

import requests
import json
import time
from datetime import datetime

API_BASE = "http://localhost:8000"

def test_health_check():
    """Test the health check endpoint"""
    print("🔍 Testing health check...")
    try:
        response = requests.get(f"{API_BASE}/health")
        if response.status_code == 200:
            print("✅ Health check passed")
            return True
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to server. Make sure the server is running.")
        return False

def test_colleges():
    """Test colleges endpoint"""
    print("🏫 Testing colleges endpoint...")
    try:
        response = requests.get(f"{API_BASE}/colleges")
        if response.status_code == 200:
            colleges = response.json()
            print(f"✅ Found {len(colleges)} colleges")
            for college in colleges[:3]:  # Show first 3
                print(f"   - {college['name']} ({college['code']})")
            return True
        else:
            print(f"❌ Colleges endpoint failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error testing colleges: {e}")
        return False

def test_students():
    """Test students endpoint"""
    print("👥 Testing students endpoint...")
    try:
        response = requests.get(f"{API_BASE}/students")
        if response.status_code == 200:
            students = response.json()
            print(f"✅ Found {len(students)} students")
            return True
        else:
            print(f"❌ Students endpoint failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error testing students: {e}")
        return False

def test_events():
    """Test events endpoint"""
    print("📅 Testing events endpoint...")
    try:
        response = requests.get(f"{API_BASE}/events")
        if response.status_code == 200:
            events = response.json()
            print(f"✅ Found {len(events)} events")
            for event in events[:3]:  # Show first 3
                print(f"   - {event['title']} ({event['event_type']})")
            return True
        else:
            print(f"❌ Events endpoint failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error testing events: {e}")
        return False

def test_reports():
    """Test reporting endpoints"""
    print("📊 Testing reports...")
    try:
        # Test event popularity report
        response = requests.get(f"{API_BASE}/reports/event-popularity?limit=5")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Event popularity report: {len(data)} events")
            if data:
                top_event = data[0]
                print(f"   - Top event: {top_event['event_title']} ({top_event['total_registrations']} registrations)")
        else:
            print(f"❌ Event popularity report failed: {response.status_code}")
            return False
        
        # Test top students report
        response = requests.get(f"{API_BASE}/reports/top-students?limit=5")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Top students report: {len(data)} students")
            if data:
                top_student = data[0]
                print(f"   - Top student: {top_student['student_name']} (Score: {top_student['participation_score']})")
        else:
            print(f"❌ Top students report failed: {response.status_code}")
            return False
        
        return True
    except Exception as e:
        print(f"❌ Error testing reports: {e}")
        return False

def test_web_interface():
    """Test web interface"""
    print("🌐 Testing web interface...")
    try:
        response = requests.get(f"{API_BASE}/")
        if response.status_code == 200:
            print("✅ Web interface accessible")
            return True
        else:
            print(f"❌ Web interface failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error testing web interface: {e}")
        return False

def main():
    """Main test function"""
    print("🧪 Event Reporting System - Test Suite")
    print("=" * 50)
    
    # Wait a moment for server to start
    print("⏳ Waiting for server to start...")
    time.sleep(3)
    
    tests = [
        test_health_check,
        test_colleges,
        test_students,
        test_events,
        test_reports,
        test_web_interface
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
            print()
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
            print()
    
    print("=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! System is working correctly.")
        print("\n🌐 You can now access:")
        print("   - Web Interface: http://localhost:8000")
        print("   - API Docs: http://localhost:8000/docs")
    else:
        print("⚠️  Some tests failed. Check the server logs for details.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)

