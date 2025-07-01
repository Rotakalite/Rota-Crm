"""
DEFRA Carbon Emission Factors - 2024 Data
UK Department for Environment, Food and Rural Affairs

This module contains official DEFRA emission factors for calculating
carbon footprints in Turkey context with latest 2024 data.
"""

# DEFRA 2024 Emission Factors (kg CO2 per unit)
DEFRA_EMISSION_FACTORS = {
    # Energy Sources
    "electricity": {
        "factor": 0.19338,  # kg CO2 per kWh (Turkey grid average 2024)
        "unit": "kWh",
        "source": "DEFRA 2024 - Turkey electricity grid",
        "category": "electricity"
    },
    
    # Water and Waste Water
    "water": {
        "factor": 0.344,    # kg CO2 per m³ (supply + waste water treatment)
        "unit": "m³", 
        "source": "DEFRA 2024 - Water supply and treatment",
        "category": "water"
    },
    
    # Natural Gas
    "natural_gas": {
        "factor": 0.18316,  # kg CO2 per kWh (net CV basis)
        "unit": "kWh",
        "source": "DEFRA 2024 - Natural gas combustion",
        "category": "fuel"
    },
    
    # Solid Fuels
    "coal": {
        "factor": 2240.0,   # kg CO2 per tonne (industrial coal average)
        "unit": "tonne",
        "source": "DEFRA 2024 - Coal combustion",
        "category": "fuel"
    },
    
    # Liquid Fuels - DEFRA Additional Types
    "diesel": {
        "factor": 2.51,     # kg CO2 per litre
        "unit": "litre",
        "source": "DEFRA 2024 - Diesel combustion",
        "category": "fuel"
    },
    
    "gasoline": {
        "factor": 2.16,     # kg CO2 per litre (petrol)
        "unit": "litre", 
        "source": "DEFRA 2024 - Petrol/Gasoline combustion",
        "category": "fuel"
    },
    
    "lpg": {
        "factor": 1.51,     # kg CO2 per litre
        "unit": "litre",
        "source": "DEFRA 2024 - LPG combustion", 
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
    
    return {
        "total_co2_emissions": round(total_co2, 3),  # kg CO2
        "total_co2_tonnes": round(total_co2 / 1000.0, 6),  # tonnes CO2
        "per_person_co2": round(per_person_co2, 3),  # kg CO2 per person
        "accommodation_count": accommodation_count,
        "emissions_breakdown": emissions,
        "calculation_date": "2024",
        "methodology": "DEFRA 2024 Emission Factors",
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

# Carbon reduction targets and benchmarks
CARBON_BENCHMARKS = {
    "hotel_industry_average": {
        "co2_per_room_night": 45.0,  # kg CO2 per room per night
        "source": "Hotel industry average Turkey 2024"
    },
    "sustainable_target": {
        "co2_per_room_night": 30.0,  # kg CO2 per room per night
        "source": "Sustainable tourism target"
    },
    "excellent_performance": {
        "co2_per_room_night": 20.0,  # kg CO2 per room per night
        "source": "Green hotel excellence level"
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