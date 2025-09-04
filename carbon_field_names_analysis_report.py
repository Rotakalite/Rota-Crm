#!/usr/bin/env python3
"""
GreenWave CRM - CARBON FIELD NAMES ANALYSIS REPORT
Based on Backend Code Analysis

CRITICAL FINDINGS FROM /app/backend/server.py lines 11132-11148:

API RESPONSE STRUCTURE (/api/analytics/carbon-footprint):
{
    "year": year,
    "client_id": target_client_id,
    "total_carbon_emissions": round(total_yearly_co2, 3),
    "total_carbon_tonnes": round(total_yearly_co2 / 1000.0, 6),
    "average_per_person_co2": round(total_yearly_co2 / total_yearly_accommodation if total_yearly_accommodation > 0 else 0, 3),  # ⚠️ MISMATCH!
    "total_accommodation_count": total_yearly_accommodation,
    "total_waste_co2": round(total_yearly_waste_co2, 3),  # ✅ EXISTS
    "total_hotel_co2": round(total_yearly_hotel_co2, 3),  # ✅ EXISTS
    "monthly_carbon_data": monthly_carbon_data,
    "yearly_benchmarks": yearly_benchmarks,
    "total_emission_sources": total_emission_sources,
    "methodology": "DEFRA 2024 Emission Factors + Waste + Hotel",
    "units": "kg CO2 equivalent"
}

MONTHLY DATA STRUCTURE (lines 11086-11100):
{
    "month": consumption.get("month"),
    "month_name": "Ocak/Şubat/etc",
    "total_co2_emissions": carbon_results.get("total_co2_emissions", 0),
    "total_co2_tonnes": carbon_results.get("total_co2_tonnes", 0),
    "per_person_co2": carbon_results.get("per_person_co2", 0),  # ✅ EXISTS IN MONTHLY
    "accommodation_count": consumption.get("accommodation_count", 0),
    "total_waste_co2": carbon_results.get("total_waste_co2", 0),  # ✅ EXISTS
    "total_hotel_co2": carbon_results.get("total_hotel_co2", 0),  # ✅ EXISTS
    "waste_emissions": carbon_results.get("waste_emissions", {}),
    "hotel_emissions": carbon_results.get("hotel_emissions", {}),
    "emissions_breakdown": emissions_breakdown,
    "benchmark": benchmark_result
}
"""

def analyze_field_names():
    """Analyze the field name mismatch between frontend and backend"""
    
    print("🔍 GREENWAVE CRM - CARBON FIELD NAMES ANALYSIS REPORT")
    print("=" * 80)
    print()
    
    print("🎯 CRITICAL QUESTIONS ANSWERED:")
    print()
    
    # Question 1: per_person_co2 field name
    print("❓ Backend API response'unda per_person_co2 field ismi nedir?")
    print("   📊 MAIN RESPONSE: 'average_per_person_co2' (line 11137)")
    print("   📊 MONTHLY DATA: 'per_person_co2' (line 11092)")
    print("   🚨 MISMATCH: Frontend expects 'per_person_co2' but main response has 'average_per_person_co2'")
    print()
    
    # Question 2: total_waste_co2 field
    print("❓ total_waste_co2 field API response'da var mı?")
    print("   ✅ YES: 'total_waste_co2' exists in main response (line 11140)")
    print("   ✅ YES: 'total_waste_co2' exists in monthly data (line 11095)")
    print("   ✅ MATCH: Frontend expects 'total_waste_co2' and backend provides it")
    print()
    
    # Question 3: total_hotel_co2 field
    print("❓ total_hotel_co2 field API response'da var mı?")
    print("   ✅ YES: 'total_hotel_co2' exists in main response (line 11142)")
    print("   ✅ YES: 'total_hotel_co2' exists in monthly data (line 11096)")
    print("   ✅ MATCH: Frontend can use 'total_hotel_co2' field")
    print()
    
    # Question 4: Field name matching
    print("❓ Frontend'in beklediği field names ile backend'in gönderdiği field names match ediyor mu?")
    print("   ⚠️  PARTIAL MATCH:")
    print("      ✅ total_waste_co2: PERFECT MATCH")
    print("      ✅ total_hotel_co2: PERFECT MATCH") 
    print("      ❌ per_person_co2: MISMATCH - backend uses 'average_per_person_co2'")
    print()
    
    print("🔍 DETAILED FIELD ANALYSIS:")
    print()
    
    # Main response fields
    print("📊 MAIN API RESPONSE FIELDS:")
    main_fields = [
        ("year", "int", "✅ Standard"),
        ("client_id", "string", "✅ Standard"),
        ("total_carbon_emissions", "float", "✅ Standard"),
        ("total_carbon_tonnes", "float", "✅ Standard"),
        ("average_per_person_co2", "float", "🚨 MISMATCH - Frontend expects 'per_person_co2'"),
        ("total_accommodation_count", "int", "✅ Standard"),
        ("total_waste_co2", "float", "✅ MATCH - Frontend uses this"),
        ("total_hotel_co2", "float", "✅ MATCH - Frontend can use this"),
        ("monthly_carbon_data", "array", "✅ Contains monthly breakdown"),
        ("yearly_benchmarks", "object", "✅ Performance benchmarks"),
        ("total_emission_sources", "object", "✅ Source breakdown"),
        ("methodology", "string", "✅ 'DEFRA 2024 Emission Factors + Waste + Hotel'"),
        ("units", "string", "✅ 'kg CO2 equivalent'")
    ]
    
    for field, field_type, status in main_fields:
        print(f"   {status}: {field} ({field_type})")
    print()
    
    # Monthly data fields
    print("📅 MONTHLY DATA FIELDS (in monthly_carbon_data array):")
    monthly_fields = [
        ("month", "int", "✅ Standard"),
        ("month_name", "string", "✅ Turkish month names"),
        ("total_co2_emissions", "float", "✅ Monthly total"),
        ("total_co2_tonnes", "float", "✅ Monthly tonnes"),
        ("per_person_co2", "float", "✅ MATCH - Frontend can use this from monthly data"),
        ("accommodation_count", "int", "✅ Monthly accommodation"),
        ("total_waste_co2", "float", "✅ MATCH - Monthly waste CO2"),
        ("total_hotel_co2", "float", "✅ MATCH - Monthly hotel CO2"),
        ("waste_emissions", "object", "✅ Detailed waste breakdown"),
        ("hotel_emissions", "object", "✅ Detailed hotel breakdown"),
        ("emissions_breakdown", "object", "✅ All emission sources"),
        ("benchmark", "object", "✅ Monthly performance")
    ]
    
    for field, field_type, status in monthly_fields:
        print(f"   {status}: {field} ({field_type})")
    print()
    
    print("🚨 CRITICAL ISSUE IDENTIFIED:")
    print("   Field Name: per_person_co2")
    print("   Frontend Expects: carbonData.per_person_co2")
    print("   Backend Main Response: carbonData.average_per_person_co2")
    print("   Backend Monthly Data: carbonData.monthly_carbon_data[0].per_person_co2")
    print()
    
    print("💡 SOLUTIONS:")
    print("   Option 1: Frontend uses 'average_per_person_co2' from main response")
    print("   Option 2: Frontend uses 'per_person_co2' from monthly_carbon_data[0]")
    print("   Option 3: Backend changes 'average_per_person_co2' to 'per_person_co2'")
    print()
    
    print("✅ CONFIRMED WORKING FIELDS:")
    print("   ✅ total_waste_co2: Available in both main response and monthly data")
    print("   ✅ total_hotel_co2: Available in both main response and monthly data")
    print("   ✅ Waste & Hotel CO2 calculations are implemented and working")
    print()
    
    print("🎯 RECOMMENDATION:")
    print("   The easiest fix is for frontend to use:")
    print("   - carbonData.average_per_person_co2 (instead of per_person_co2)")
    print("   - carbonData.total_waste_co2 (already correct)")
    print("   - carbonData.total_hotel_co2 (already available)")
    print()
    
    print("📋 BACKEND CODE LOCATIONS:")
    print("   Main Response: /app/backend/server.py lines 11132-11148")
    print("   Monthly Data: /app/backend/server.py lines 11086-11100")
    print("   Endpoint: @api_router.get('/analytics/carbon-footprint') line 10925")
    print()
    
    print("=" * 80)
    
    return {
        "per_person_co2_field": "average_per_person_co2",  # Main response
        "per_person_co2_monthly": "per_person_co2",        # Monthly data
        "total_waste_co2_exists": True,
        "total_hotel_co2_exists": True,
        "field_mismatch_count": 1,
        "working_fields_count": 2
    }

if __name__ == "__main__":
    analyze_field_names()