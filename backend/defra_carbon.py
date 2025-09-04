"""
DEFRA Carbon Emission Factors - 2024 Data
UK Department for Environment, Food and Rural Affairs

This module contains official DEFRA emission factors for calculating
carbon footprints in Turkey context with latest 2024 data.

EXPANDED WITH:
- Waste Disposal Factors (134 types)
- Turkey Hotel Stay Factor (32.1 kg CO2/room night)
"""

import json
import logging
from pathlib import Path

# Load DEFRA 2024 waste and hotel factors
try:
    waste_factors_path = Path(__file__).parent / "defra_2024_waste_factors.json"
    
    with open(waste_factors_path, 'r') as f:
        DEFRA_WASTE_FACTORS = json.load(f)
        
    # 🇹🇷 TURKEY HOTEL FACTOR - DEFRA 2024
    TURKEY_HOTEL_FACTOR = {
        "factor": 32.1,  # kg CO2 per room night
        "unit": "room night", 
        "source": "DEFRA 2024 - Turkey Hotel Stay",
        "defra_id": "29_600_4051_13_1",
        "category": "hotel_stay"
    }
        
    logging.info(f"✅ Loaded {len(DEFRA_WASTE_FACTORS)} waste factors and Turkey hotel factor ({TURKEY_HOTEL_FACTOR['factor']} kg CO2/room night)")
    
except Exception as e:
    logging.error(f"❌ Error loading DEFRA 2024 factors: {e}")
    DEFRA_WASTE_FACTORS = []
    TURKEY_HOTEL_FACTOR = {"factor": 32.1, "unit": "room night", "source": "DEFRA 2024 - Turkey Hotel Stay", "defra_id": "29_600_4051_13_1", "category": "hotel_stay"}

# DEFRA 2024 Emission Factors (kg CO2 per unit)
DEFRA_EMISSION_FACTORS = {
    # Energy Sources - UPDATED WITH DEFRA 2024 ORIGINAL EXCEL DATA
    "electricity": {
        "factor": 0.20705,  # kg CO2 per kWh - DEFRA 2024 Original from Excel
        "unit": "kWh",
        "source": "DEFRA 2024 Excel - UK electricity grid average",
        "category": "electricity"
    },
    
    # Water and Waste Water - UPDATED WITH DEFRA 2024 ORIGINAL EXCEL DATA
    "water": {
        "factor": 0.33885,    # kg CO2 per m³ - DEFRA 2024 Original (supply + treatment)
        "unit": "m³", 
        "source": "DEFRA 2024 Excel - Water supply + treatment",
        "category": "water"
    },
    
    # Natural Gas - UPDATED WITH DEFRA 2024 ORIGINAL EXCEL DATA
    "natural_gas": {
        "factor": 0.009245,  # kg CO2 per kWh - DEFRA 2024 Original (converted from GJ)
        "unit": "kWh",
        "source": "DEFRA 2024 Excel - Natural gas combustion (converted to kWh)",
        "category": "fuel"
    },
    
    # Solid Fuels - UPDATED WITH DEFRA 2024 ORIGINAL EXCEL DATA
    "coal": {
        "factor": 2399.44,   # kg CO2 per tonne - DEFRA 2024 Original
        "unit": "tonne",
        "source": "DEFRA 2024 Excel - Coal industrial combustion",
        "category": "fuel"
    },
    
    # Liquid Fuels - UPDATED WITH DEFRA 2024 ORIGINAL EXCEL DATA
    "diesel": {
        "factor": 2.562,     # kg CO2 per litre - DEFRA 2024 Original
        "unit": "litre",
        "source": "DEFRA 2024 Excel - Diesel combustion",
        "category": "fuel"
    },
    
    "gasoline": {
        "factor": 2.16,     # kg CO2 per litre (petrol)
        "unit": "litre", 
        "source": "DEFRA 2024 - Petrol/Gasoline combustion",
        "category": "fuel"
    },
    
    "lpg": {
        "factor": 1.617,     # kg CO2 per litre - DEFRA 2024 Original
        "unit": "litre",
        "source": "DEFRA 2024 Excel - LPG combustion", 
        "category": "fuel"
    },
    
    "fuel_oil": {
        "factor": 2.54,     # kg CO2 per litre (heavy fuel oil)
        "unit": "litre",
        "source": "DEFRA 2024 - Fuel oil combustion",
        "category": "fuel"
    },
    
    # Specific Refrigerant Gases - DEFRA 2024 GWP Values
    "r134a_gas": {
        "factor": 1430.0,   # kg CO2e per kg (GWP for HFC-134a)
        "unit": "kg",
        "source": "DEFRA 2024 - HFC-134a GWP",
        "category": "refrigerant"
    },
    
    "r600a_gas": {
        "factor": 3.0,      # kg CO2e per kg (GWP for Isobutane R600a)
        "unit": "kg", 
        "source": "DEFRA 2024 - R600a GWP",
        "category": "refrigerant"
    },
    
    "r410a_gas": {
        "factor": 2088.0,   # kg CO2e per kg (GWP for HFC-410A)
        "unit": "kg",
        "source": "DEFRA 2024 - HFC-410A GWP", 
        "category": "refrigerant"
    },
    
    "r32_gas": {
        "factor": 675.0,    # kg CO2e per kg (GWP for HFC-32)
        "unit": "kg",
        "source": "DEFRA 2024 - HFC-32 GWP",
        "category": "refrigerant"
    },
    
    # Fire Suppressants - DEFRA 2024
    "co2_fire": {
        "factor": 1.0,      # kg CO2 per kg (Direct CO2 emission)
        "unit": "kg",
        "source": "DEFRA 2024 - CO2 fire extinguisher direct emission",
        "category": "fire_suppressant"
    },
    
    "fm200_fire": {
        "factor": 3220.0,   # kg CO2e per kg (GWP for HFC-227ea/FM200)
        "unit": "kg",
        "source": "DEFRA 2024 - FM200/HFC-227ea GWP",
        "category": "fire_suppressant"
    }
}

def calculate_carbon_emissions(consumption_data):
    """
    Calculate total carbon emissions using DEFRA factors
    
    Args:
        consumption_data (dict): Dictionary containing consumption values
        
    Returns:
        dict: Carbon emission calculations and breakdown
    """
    
    emissions = {}
    total_co2 = 0.0
    
    for fuel_type, consumption_value in consumption_data.items():
        if fuel_type in DEFRA_EMISSION_FACTORS and consumption_value is not None:
            factor_data = DEFRA_EMISSION_FACTORS[fuel_type]
            
            # Convert consumption to float, default to 0 if invalid
            try:
                consumption = float(consumption_value)
            except (ValueError, TypeError):
                consumption = 0.0
            
            # Special handling for coal (convert kg to tonnes)
            if fuel_type == "coal":
                consumption = consumption / 1000.0  # kg to tonnes
            
            # 🔥 CRITICAL FIX: Natural Gas Unit Conversion (m³ to kWh)
            if fuel_type == "natural_gas":
                # Convert m³ to kWh using standard conversion factor
                consumption_kwh = consumption * 10.55  # 1 m³ = 10.55 kWh (net calorific value)
                co2_emission = consumption_kwh * factor_data["factor"]
                logging.info(f"🔥 Natural Gas Conversion: {consumption} m³ → {consumption_kwh:.2f} kWh → {co2_emission:.2f} kg CO2")
            else:
                # Calculate emissions for this fuel type
                co2_emission = consumption * factor_data["factor"]
            
            emissions[fuel_type] = {
                "consumption": consumption,
                "unit": factor_data["unit"],
                "emission_factor": factor_data["factor"],
                "co2_emissions": round(co2_emission, 3),  # kg CO2
                "source": factor_data["source"],
                "category": factor_data["category"]
            }
            
            total_co2 += co2_emission
    
    # Calculate per-person emissions if accommodation count is provided
    per_person_co2 = 0.0
    accommodation_count = consumption_data.get("accommodation_count", 0)
    if accommodation_count and accommodation_count > 0:
        per_person_co2 = total_co2 / accommodation_count
    
    # 🗑️ WASTE EMISSIONS CALCULATION
    waste_emissions = {}
    waste_co2_total = 0.0
    
    # Check for waste data in consumption_data
    waste_data = consumption_data.get("waste_data", {})
    if waste_data and DEFRA_WASTE_FACTORS:
        for waste_entry in waste_data:
            waste_type = waste_entry.get("waste_type", "")
            waste_amount = float(waste_entry.get("amount", 0))
            waste_unit = waste_entry.get("unit", "kg")
            
            # 🔍 IMPROVED WASTE TYPE MATCHING FOR DEFRA 2024
            defra_factor = None
            
            # Mapping common waste types to DEFRA categories
            waste_mapping = {
                "organic waste": "Organic: food and drink waste",
                "food waste": "Organic: food and drink waste", 
                "kitchen waste": "Organic: food and drink waste",
                "paper waste": "Paper and board: mixed",
                "cardboard": "Paper and board: board",
                "plastic waste": "Plastics: average plastics",
                "glass waste": "Glass",
                "metal waste": "Metal",
                "mixed waste": "Commercial and industrial waste"
            }
            
            # Try direct mapping first
            waste_type_lower = waste_type.lower()
            defra_category = waste_mapping.get(waste_type_lower)
            
            if defra_category:
                # Find DEFRA factor for this category
                for factor in DEFRA_WASTE_FACTORS:
                    if defra_category.lower() in factor.get("level2", "").lower():
                        defra_factor = factor
                        break
            
            # Fallback: Search in all factor fields
            if not defra_factor:
                for factor in DEFRA_WASTE_FACTORS:
                    level2 = factor.get("level2", "").lower()
                    level3 = factor.get("level3", "").lower()
                    activity = factor.get("activity", "").lower()
                    
                    if (waste_type_lower in level2 or 
                        waste_type_lower in level3 or 
                        waste_type_lower in activity or
                        any(keyword in level2 + level3 + activity for keyword in waste_type_lower.split())):
                        defra_factor = factor
                        break
            
            # Apply DEFRA factor if found
            if defra_factor:
                co2_emission = waste_amount * defra_factor["ghg_factor"]
                waste_emissions[waste_type] = {
                    "amount": waste_amount,
                    "unit": waste_unit,
                    "emission_factor": defra_factor["ghg_factor"],
                    "co2_emissions": round(co2_emission, 3),
                    "defra_id": defra_factor["id"],
                    "defra_category": defra_factor.get("level2", "Unknown"),
                    "category": "waste_disposal"
                }
                waste_co2_total += co2_emission
                logging.info(f"🗑️ Waste match: {waste_type} → {defra_factor.get('level2', 'Unknown')} ({defra_factor['ghg_factor']} kg CO2 × {waste_amount} kg)")
            else:
                logging.warning(f"⚠️ No DEFRA factor found for waste type: {waste_type}")
    else:
        logging.info("ℹ️ No waste data provided for carbon calculation")
    
    # 🏨 HOTEL STAY EMISSIONS CALCULATION
    hotel_emissions = {}
    hotel_co2_total = 0.0
    
    # Check for hotel/accommodation data
    hotel_data = consumption_data.get("hotel_data", {})
    if hotel_data and TURKEY_HOTEL_FACTOR:
        for hotel_entry in hotel_data:
            country = hotel_entry.get("country", "Turkey")
            room_nights = float(hotel_entry.get("room_nights", 0))
            
            # Use Turkey hotel factor for all countries (simplified approach)
            co2_emission = room_nights * TURKEY_HOTEL_FACTOR["factor"]
            hotel_emissions[country] = {
                "room_nights": room_nights,
                "unit": TURKEY_HOTEL_FACTOR["unit"],
                "emission_factor": TURKEY_HOTEL_FACTOR["factor"],
                "co2_emissions": round(co2_emission, 3),
                "defra_id": TURKEY_HOTEL_FACTOR["defra_id"],
                "category": TURKEY_HOTEL_FACTOR["category"]
            }
            hotel_co2_total += co2_emission
    
    # Update totals with waste and hotel emissions
    total_co2 += waste_co2_total + hotel_co2_total
    
    # Recalculate per-person with new total
    if accommodation_count and accommodation_count > 0:
        per_person_co2 = total_co2 / accommodation_count
    
    return {
        "total_co2_emissions": round(total_co2, 3),  # kg CO2
        "total_co2_tonnes": round(total_co2 / 1000.0, 6),  # tonnes CO2
        "per_person_co2": round(per_person_co2, 3),  # kg CO2 per person
        "accommodation_count": accommodation_count,
        "emissions_breakdown": emissions,
        "waste_emissions": waste_emissions,  # 🗑️ NEW: Waste emissions breakdown
        "hotel_emissions": hotel_emissions,  # 🏨 NEW: Hotel emissions breakdown
        "total_waste_co2": round(waste_co2_total, 3),  # 🗑️ NEW: Total waste CO2
        "total_hotel_co2": round(hotel_co2_total, 3),  # 🏨 NEW: Total hotel CO2
        "calculation_date": "2024",
        "methodology": "DEFRA 2024 Emission Factors + Waste + Hotel",
        "units": "kg CO2 equivalent"
    }

def get_emission_factor(fuel_type):
    """
    Get emission factor for a specific fuel type
    
    Args:
        fuel_type (str): Type of fuel
        
    Returns:
        dict: Emission factor data or None if not found
    """
    return DEFRA_EMISSION_FACTORS.get(fuel_type)

def get_all_emission_factors():
    """
    Get all available emission factors
    
    Returns:
        dict: All DEFRA emission factors
    """
    return DEFRA_EMISSION_FACTORS

def get_waste_factors():
    """
    Get all DEFRA 2024 waste disposal factors
    
    Returns:
        list: All waste disposal factors
    """
    return DEFRA_WASTE_FACTORS

def get_hotel_factors():
    """
    Get Turkey hotel stay factor
    
    Returns:
        dict: Turkey hotel stay factor
    """
    return TURKEY_HOTEL_FACTOR

def search_waste_factor(waste_type):
    """
    Search for waste disposal factor by type
    
    Args:
        waste_type (str): Type of waste to search
        
    Returns:
        dict: Matching waste factor or None
    """
    waste_type_lower = waste_type.lower()
    
    for factor in DEFRA_WASTE_FACTORS:
        if (waste_type_lower in factor.get("level2", "").lower() or
            waste_type_lower in factor.get("level3", "").lower() or
            waste_type_lower in factor.get("activity", "").lower()):
            return factor
    
    return None

def search_hotel_factor(country):
    """
    Search for hotel stay factor by country (returns Turkey factor)
    
    Args:
        country (str): Country name to search
        
    Returns:
        dict: Turkey hotel factor (simplified approach)
    """
    # Always return Turkey factor (simplified approach)
    return TURKEY_HOTEL_FACTOR

def validate_consumption_data(consumption_data):
    """
    Validate consumption data format
    
    Args:
        consumption_data (dict): Consumption data to validate
        
    Returns:
        tuple: (is_valid, errors)
    """
    errors = []
    
    # Check if it's a dictionary
    if not isinstance(consumption_data, dict):
        errors.append("Consumption data must be a dictionary")
        return False, errors
    
    # Check for required fields
    required_fields = ["electricity", "water", "natural_gas", "coal"]
    for field in required_fields:
        if field not in consumption_data:
            errors.append(f"Missing required field: {field}")
    
    # Validate numeric values
    for fuel_type, value in consumption_data.items():
        if fuel_type in DEFRA_EMISSION_FACTORS:
            try:
                float_value = float(value) if value is not None else 0.0
                if float_value < 0:
                    errors.append(f"Negative value not allowed for {fuel_type}: {value}")
            except (ValueError, TypeError):
                errors.append(f"Invalid numeric value for {fuel_type}: {value}")
    
    is_valid = len(errors) == 0
    return is_valid, errors

# Carbon reduction targets and benchmarks - UPDATED TO TONNES CO2
CARBON_BENCHMARKS = {
    "hotel_industry_average": {
        "co2_per_room_night": 0.050,  # tCO2 per room per night (was 50 kg)
        "source": "Hotel industry average Turkey 2024 (updated to tonnes)"
    },
    "sustainable_target": {
        "co2_per_room_night": 0.035,  # tCO2 per room per night (was 35 kg) 
        "source": "Sustainable tourism target (updated to tonnes)"
    },
    "excellent_performance": {
        "co2_per_room_night": 0.020,  # tCO2 per room per night (was 20 kg)
        "source": "Green hotel excellence level (updated to tonnes)"
    }
}

def benchmark_performance(total_co2, accommodation_count, nights=30):
    """
    Benchmark carbon performance against industry standards
    
    Args:
        total_co2 (float): Total CO2 emissions in kg
        accommodation_count (int): Number of accommodations
        nights (int): Number of nights (default 30 for monthly)
        
    Returns:
        dict: Benchmark analysis
    """
    if accommodation_count <= 0 or nights <= 0:
        return {"error": "Invalid accommodation count or nights"}
    
    co2_per_room_night = total_co2 / (accommodation_count * nights)
    
    performance_level = "Poor"
    if co2_per_room_night <= CARBON_BENCHMARKS["excellent_performance"]["co2_per_room_night"]:
        performance_level = "Excellent"
    elif co2_per_room_night <= CARBON_BENCHMARKS["sustainable_target"]["co2_per_room_night"]:
        performance_level = "Good"
    elif co2_per_room_night <= CARBON_BENCHMARKS["hotel_industry_average"]["co2_per_room_night"]:
        performance_level = "Average"
    
    return {
        "co2_per_room_night": round(co2_per_room_night, 3),
        "performance_level": performance_level,
        "benchmarks": CARBON_BENCHMARKS,
        "total_room_nights": accommodation_count * nights
    }