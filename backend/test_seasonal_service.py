import sys
import os
from datetime import datetime

# Add the app directory to sys.path to import SeasonalService
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

from app.services.seasonal_service import SeasonalService

def test_seasonal_detection():
    print("--- 1. Testing Seasonal Detection ---")
    seasons = [
        (datetime(2023, 1, 15), "dry-season"),
        (datetime(2023, 4, 15), "summer"),
        (datetime(2023, 8, 15), "monsoon"),
        (datetime(2023, 11, 15), "post-monsoon"),
    ]
    
    for dt, expected in seasons:
        detected = SeasonalService.get_current_season(dt)
        print(f"Date: {dt.date()}, Expected: {expected}, Detected: {detected}")
        assert detected == expected
    print("Seasonal detection tests passed!\n")

def test_seasonal_thresholds():
    print("--- 2. Testing Seasonal Thresholds ---")
    test_cases = [
        ("summer", "river", 25),
        ("monsoon", "river", 8),
        ("summer", "lake", 15),
        ("monsoon", "lake", 5),
        ("summer", "waterfall", 50),
    ]
    
    for season, body_type, expected in test_cases:
        threshold = SeasonalService.get_seasonal_threshold(season, body_type)
        print(f"Season: {season}, Type: {body_type}, Threshold: {threshold}%")
        assert threshold == expected
    print("Threshold tests passed!\n")

def test_classify_water_loss():
    print("--- 3. Testing Water Loss Classification ---")
    
    # Cases for Summer Lake (Threshold 15%)
    threshold_lake_summer = 15
    test_cases = [
        (-1.5, threshold_lake_summer, True, "normal"),
        (-10.0, threshold_lake_summer, True, "seasonal_variation"),
        (-18.0, threshold_lake_summer, True, "borderline"),
        (-25.0, threshold_lake_summer, True, "encroachment"),
    ]
    
    for loss, threshold, is_seasonal, expected_class in test_cases:
        result = SeasonalService.classify_water_loss(loss, threshold, is_seasonal)
        print(f"Loss: {abs(loss):.1f}%, Threshold: {threshold}%, Classification: {result['classification']}")
        assert result['classification'] == expected_class
        
    print("Classification tests passed!\n")

def test_seasonal_vs_non_seasonal():
    print("--- 4. Testing Seasonal and Non-Seasonal Bodies ---")
    # Actually the current implementation doesn't seem to use is_seasonal 
    # flag in classify_water_loss logic besides parameter passing (based on cat output)
    # But we can test it anyway to see if the logic holds for different types.
    
    # River in Monsoon (Threshold 8%)
    t_monsoon_river = SeasonalService.get_seasonal_threshold("monsoon", "river")
    # River in Summer (Threshold 25%)
    t_summer_river = SeasonalService.get_seasonal_threshold("summer", "river")
    
    loss = -20.0
    
    res_monsoon = SeasonalService.classify_water_loss(loss, t_monsoon_river, False)
    res_summer = SeasonalService.classify_water_loss(loss, t_summer_river, True)
    
    print(f"Loss of {abs(loss)}% in Monsoon (River): {res_monsoon['classification']} (is_encroachment: {res_monsoon['is_encroachment']})")
    print(f"Loss of {abs(loss)}% in Summer (River): {res_summer['classification']} (is_encroachment: {res_summer['is_encroachment']})")
    
    assert res_monsoon['is_encroachment'] == True
    assert res_summer['is_encroachment'] == False
    
    print("Seasonal vs Non-seasonal scenario tests passed!\n")

if __name__ == "__main__":
    try:
        test_seasonal_detection()
        test_seasonal_thresholds()
        test_classify_water_loss()
        test_seasonal_vs_non_seasonal()
        print("All SeasonalService tests passed successfully!")
    except Exception as e:
        print(f"Tests failed: {e}")
        sys.exit(1)
