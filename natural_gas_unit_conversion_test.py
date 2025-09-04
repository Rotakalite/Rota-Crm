#!/usr/bin/env python3
"""
GreenWave CRM - Natural Gas Unit Conversion Issue Analysis
CRITICAL BUG IDENTIFIED: Missing m³ to kWh conversion for natural gas

ISSUE ANALYSIS:
1. Database stores natural_gas in m³ (cubic meters) - server.py line 1207
2. DEFRA calculation expects kWh - defra_carbon.py line 61
3. NO CONVERSION happening between m³ and kWh
4. Result: Massive underestimation of natural gas emissions

CONVERSION FACTOR: 1 m³ natural gas ≈ 10.55 kWh (standard conversion)

EXAMPLE CALCULATION:
- Input: 2,500 m³ natural gas
- Should convert to: 2,500 × 10.55 = 26,375 kWh  
- DEFRA factor: 0.009245 kg CO2/kWh
- Correct CO2: 26,375 × 0.009245 = 243.9 kg CO2
- Current (wrong): 2,500 × 0.009245 = 23.1 kg CO2
- ERROR: 10.55x underestimation!
"""

import sys

class NaturalGasUnitConversionAnalyzer:
    def __init__(self):
        self.conversion_factor = 10.55  # kWh per m³ (standard)
        self.defra_factor = 0.009245    # kg CO2 per kWh
        
        print("🔥 GreenWave CRM - Natural Gas Unit Conversion Issue Analysis")
        print("=" * 80)
    
    def analyze_unit_conversion_issue(self):
        """Analyze the natural gas unit conversion problem"""
        
        print("🚨 CRITICAL BUG IDENTIFIED: Missing m³ to kWh conversion!")
        print()
        
        # Example calculation with typical hotel consumption
        example_m3 = 2500  # m³ per month (typical hotel)
        
        print(f"📊 EXAMPLE CALCULATION:")
        print(f"   Input: {example_m3:,} m³ natural gas per month")
        print()
        
        # Current (wrong) calculation
        current_wrong_co2 = example_m3 * self.defra_factor
        print(f"❌ CURRENT (WRONG) CALCULATION:")
        print(f"   {example_m3:,} m³ × {self.defra_factor} kg CO2/kWh = {current_wrong_co2:.1f} kg CO2")
        print(f"   🚨 Problem: Using m³ directly as kWh (NO CONVERSION)")
        print()
        
        # Correct calculation
        converted_kwh = example_m3 * self.conversion_factor
        correct_co2 = converted_kwh * self.defra_factor
        print(f"✅ CORRECT CALCULATION:")
        print(f"   Step 1: {example_m3:,} m³ × {self.conversion_factor} kWh/m³ = {converted_kwh:,} kWh")
        print(f"   Step 2: {converted_kwh:,} kWh × {self.defra_factor} kg CO2/kWh = {correct_co2:.1f} kg CO2")
        print()
        
        # Error magnitude
        error_factor = correct_co2 / current_wrong_co2
        print(f"🎯 ERROR MAGNITUDE:")
        print(f"   Current result: {current_wrong_co2:.1f} kg CO2")
        print(f"   Correct result: {correct_co2:.1f} kg CO2")
        print(f"   Underestimation: {error_factor:.1f}x smaller than it should be!")
        print()
        
        return {
            "example_m3": example_m3,
            "current_wrong_co2": current_wrong_co2,
            "correct_co2": correct_co2,
            "error_factor": error_factor,
            "conversion_factor": self.conversion_factor
        }
    
    def analyze_pie_chart_impact(self, analysis_results):
        """Analyze impact on pie chart visibility"""
        
        print("🥧 PIE CHART IMPACT ANALYSIS:")
        print()
        
        # Typical emissions for comparison
        electricity_co2 = 15000 * 0.4154  # 15,000 kWh × Turkey grid factor
        water_co2 = 8000 * 0.149          # 8,000 m³ × DEFRA water factor
        
        current_natural_gas = analysis_results["current_wrong_co2"]
        correct_natural_gas = analysis_results["correct_co2"]
        
        print(f"📊 TYPICAL MONTHLY EMISSIONS COMPARISON:")
        print(f"   Electricity: {electricity_co2:.1f} kg CO2")
        print(f"   Water: {water_co2:.1f} kg CO2")
        print(f"   Natural Gas (current wrong): {current_natural_gas:.1f} kg CO2")
        print(f"   Natural Gas (correct): {correct_natural_gas:.1f} kg CO2")
        print()
        
        # Calculate percentages
        total_wrong = electricity_co2 + water_co2 + current_natural_gas
        total_correct = electricity_co2 + water_co2 + correct_natural_gas
        
        wrong_percentage = (current_natural_gas / total_wrong) * 100
        correct_percentage = (correct_natural_gas / total_correct) * 100
        
        print(f"🎯 PIE CHART PERCENTAGES:")
        print(f"   Natural Gas (current wrong): {wrong_percentage:.1f}% of total")
        print(f"   Natural Gas (correct): {correct_percentage:.1f}% of total")
        print()
        
        if wrong_percentage < 5:
            print(f"❌ FRONTEND FILTERING: {wrong_percentage:.1f}% is too small for pie chart segment!")
            print(f"   Frontend likely filters out values < 5% or uses `values[index] > 0` threshold")
        else:
            print(f"✅ FRONTEND FILTERING: {wrong_percentage:.1f}% should be visible")
        
        if correct_percentage >= 5:
            print(f"✅ AFTER FIX: {correct_percentage:.1f}% will be clearly visible in pie chart")
        
        print()
    
    def provide_fix_recommendations(self):
        """Provide specific fix recommendations"""
        
        print("🔧 FIX RECOMMENDATIONS:")
        print()
        
        print("1️⃣ BACKEND FIX (defra_carbon.py):")
        print("   Add natural gas unit conversion in calculate_carbon_emissions function:")
        print("   ```python")
        print("   # Special handling for natural gas (convert m³ to kWh)")
        print("   if fuel_type == 'natural_gas':")
        print("       consumption = consumption * 10.55  # m³ to kWh conversion")
        print("   ```")
        print()
        
        print("2️⃣ ALTERNATIVE FIX (server.py):")
        print("   Convert before passing to DEFRA calculation:")
        print("   ```python")
        print("   consumption_data = {")
        print("       'natural_gas': consumption.get('natural_gas', 0) * 10.55,  # Convert m³ to kWh")
        print("       # ... other fields")
        print("   }") 
        print("   ```")
        print()
        
        print("3️⃣ VALIDATION:")
        print("   - Test with sample data: 2,500 m³ should produce ~244 kg CO2")
        print("   - Verify pie chart shows natural gas segment")
        print("   - Check total_emission_sources.natural_gas > 0")
        print()
        
        print("4️⃣ DOCUMENTATION UPDATE:")
        print("   - Update API documentation to clarify units")
        print("   - Add conversion factor to DEFRA module comments")
        print()
    
    def run_analysis(self):
        """Run complete analysis"""
        
        analysis_results = self.analyze_unit_conversion_issue()
        self.analyze_pie_chart_impact(analysis_results)
        self.provide_fix_recommendations()
        
        print("=" * 80)
        print("🎯 SUMMARY:")
        print("   🚨 CRITICAL: Natural gas emissions underestimated by 10.55x")
        print("   🥧 IMPACT: Pie chart segment missing due to tiny values")
        print("   🔧 FIX: Add m³ to kWh conversion (multiply by 10.55)")
        print("   ⚡ PRIORITY: HIGH - Affects carbon footprint accuracy")
        print("=" * 80)
        
        return analysis_results

def main():
    """Main analysis execution"""
    analyzer = NaturalGasUnitConversionAnalyzer()
    analyzer.run_analysis()
    sys.exit(0)

if __name__ == "__main__":
    main()