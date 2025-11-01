from enum import Enum

class Category(str, Enum):
    Affordability = "Affordability"
    Accessibility = "Accessibility"
    Amenities = "Amenities"
    Environment  = "Environment"
    Community    = "Community"

class AmenityType(str, Enum):
    School = "School"
    SportsSG = "SportsSG"
    Hawker = "Hawker"
    Healthcare = "Healthcare"
    Supermarket = "Supermarket"