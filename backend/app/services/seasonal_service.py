"""
Seasonal Service for handling seasonal variations in water bodies
Distinguishes between natural seasonal water loss and actual encroachment
"""
from datetime import datetime
from typing import Dict, Tuple


class SeasonalService:
    """Service to detect and manage seasonal variations in water bodies"""
    
    @staticmethod
    def get_current_season(date: datetime = None) -> str:
        """
        Get season for Tamil Nadu/Erode District:
        - Summer: Mar-Jun (hot, dry - LOW water, high evaporation)
        - Southwest Monsoon: Jun-Sep (wet - HIGH water)
        - Post-Monsoon: Oct-Dec (moderate water, moderate temperature)
        - Northeast Monsoon/Dry: Dec-Feb (relatively dry, cooler)
        
        Args:
            date: Optional datetime. If None, uses current date.
        
        Returns:
            Season string: "summer", "monsoon", "post-monsoon", or "dry-season"
        """
        if date is None:
            date = datetime.now()
        
        month = date.month
        
        if month in [3, 4, 5, 6]:
            return "summer"
        elif month in [7, 8, 9]:
            return "monsoon"
        elif month in [10, 11, 12]:
            return "post-monsoon"
        else:  # Jan, Feb
            return "dry-season"
    
    @staticmethod
    def get_seasonal_threshold(season: str, body_type: str) -> float:
        """
        Get water loss threshold for different seasons and water body types.
        
        Thresholds represent maximum percentage loss considered "normal"
        Loss exceeding this indicates real encroachment, not seasonal variation.
        
        Args:
            season: Season name ("summer", "monsoon", "post-monsoon", "dry-season")
            body_type: Type of water body ("river", "lake", "reservoir", "waterfall", "tank", "canal", "pond")
        
        Returns:
            Threshold percentage (0-100)
        """
        # Seasonal thresholds by body type
        # Higher threshold = more lenient (allows more loss without marking as encroached)
        thresholds = {
            "river": {
                "summer": 25,        # Rivers naturally dry up in summer
                "monsoon": 8,        # Monsoon - should stay full, strict monitoring
                "post-monsoon": 12,  # Moderate drying allowed
                "dry-season": 20     # Post-monsoon drying continues
            },
            "lake": {
                "summer": 15,        # Lakes evaporate in summer
                "monsoon": 5,        # Should be full
                "post-monsoon": 8,
                "dry-season": 12
            },
            "reservoir": {
                "summer": 10,        # Dams more controlled, less variation
                "monsoon": 5,
                "post-monsoon": 7,
                "dry-season": 8
            },
            "waterfall": {
                "summer": 50,        # Waterfalls often dry completely in summer
                "monsoon": 10,       # Should have good flow
                "post-monsoon": 20,  # Flow reduces
                "dry-season": 40     # Often dry in dry season
            },
            "tank": {
                "summer": 20,        # Agricultural tanks evaporate
                "monsoon": 8,
                "post-monsoon": 10,
                "dry-season": 15
            },
            "canal": {
                "summer": 12,        # Controlled irrigation, moderate loss
                "monsoon": 6,
                "post-monsoon": 8,
                "dry-season": 10
            },
            "pond": {
                "summer": 18,        # Ponds evaporate more than lakes
                "monsoon": 7,
                "post-monsoon": 10,
                "dry-season": 14
            }
        }
        
        # Default to lake thresholds if type not found
        type_thresholds = thresholds.get(body_type, thresholds["lake"])
        return type_thresholds.get(season, 5)  # Default 5% if season not found
    
    @staticmethod
    def get_season_name(season: str) -> str:
        """
        Get human-readable season name.
        
        Args:
            season: Season code
        
        Returns:
            Display name
        """
        names = {
            "summer": "Summer (Mar-Jun)",
            "monsoon": "Southwest Monsoon (Jul-Sep)",
            "post-monsoon": "Post-Monsoon (Oct-Dec)",
            "dry-season": "Dry Season (Jan-Feb)"
        }
        return names.get(season, season)
    
    @staticmethod
    def classify_water_loss(
        change_percent: float,
        threshold: float,
        is_seasonal: bool
    ) -> Dict:
        """
        Classify water loss as seasonal variation or potential encroachment.
        
        Args:
            change_percent: Percentage change in water area (negative = loss)
            threshold: Seasonal threshold for this type/season
            is_seasonal: Whether water body is marked as seasonal
        
        Returns:
            Classification dict with reason and severity
        """
        # Negative change = water loss
        loss_percent = abs(change_percent) if change_percent < 0 else change_percent
        
        if loss_percent <= 2:
            return {
                "classification": "normal",
                "reason": "Minimal change",
                "severity": "low",
                "is_encroachment": False,
                "confidence": "high"
            }
        elif loss_percent <= threshold:
            return {
                "classification": "seasonal_variation",
                "reason": f"Within normal seasonal range ({loss_percent:.1f}% < {threshold:.1f}%)",
                "severity": "low",
                "is_encroachment": False,
                "confidence": "high"
            }
        elif loss_percent <= threshold + 5:
            return {
                "classification": "borderline",
                "reason": f"Slightly above seasonal threshold ({loss_percent:.1f}% vs {threshold:.1f}%)",
                "severity": "medium",
                "is_encroachment": False,  # Still uncertain
                "confidence": "medium"
            }
        else:
            return {
                "classification": "encroachment",
                "reason": f"Significant loss exceeds threshold ({loss_percent:.1f}% > {threshold:.1f}%)",
                "severity": "high",
                "is_encroachment": True,
                "confidence": "high"
            }
    
    @staticmethod
    def get_monitoring_recommendation(season: str, body_type: str) -> str:
        """
        Get monitoring frequency recommendation based on season and body type.
        
        Args:
            season: Current season
            body_type: Type of water body
        
        Returns:
            Recommendation string
        """
        # More frequent monitoring in critical seasons
        if season == "monsoon":
            return "Intensive monitoring recommended (peak water season)"
        elif season == "summer":
            if body_type in ["waterfall", "seasonal_river"]:
                return "Weekly monitoring recommended (high evaporation risk)"
            else:
                return "Bi-weekly monitoring recommended"
        else:
            return "Standard monitoring (bi-weekly)"
    
    @staticmethod
    def get_historical_baseline(
        water_body_type: str,
        current_season: str,
        historical_data: list = None
    ) -> float:
        """
        Determine expected water area for this season based on historical data.
        
        Args:
            water_body_type: Type of water body
            current_season: Current season
            historical_data: Optional list of previous measurements
        
        Returns:
            Expected water area percentage (0-100)
        """
        if historical_data and len(historical_data) > 2:
            # Calculate from historical data
            season_data = [d for d in historical_data if d.get('season') == current_season]
            if season_data:
                return sum(d.get('water_percentage', 0) for d in season_data) / len(season_data)
        
        # Default baseline expectations
        baselines = {
            "river": {
                "summer": 45,
                "monsoon": 95,
                "post-monsoon": 70,
                "dry-season": 50
            },
            "lake": {
                "summer": 60,
                "monsoon": 100,
                "post-monsoon": 85,
                "dry-season": 65
            },
            "reservoir": {
                "summer": 70,
                "monsoon": 100,
                "post-monsoon": 90,
                "dry-season": 75
            },
            "waterfall": {
                "summer": 10,
                "monsoon": 100,
                "post-monsoon": 50,
                "dry-season": 5
            },
            "tank": {
                "summer": 55,
                "monsoon": 100,
                "post-monsoon": 80,
                "dry-season": 60
            }
        }
        
        type_baselines = baselines.get(water_body_type, baselines["lake"])
        return type_baselines.get(current_season, 50)
