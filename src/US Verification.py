# Global Food Production Impact Calculator
# Calculates percentage decrease in global production when US production declines

def calculate_global_production_impact():
    """
    Calculate the percentage decrease in global food production 
    when US production declines by a specified percentage.
    
    Given:
    - US production: 1.4 × 10^15 calories/year
    - Global production: 0.65 × 10^16 calories/year
    - US production decline: 29%
    
    Returns:
    - Percentage decrease in global production
    """
    
    # Initial production values (in calories per year)
    us_production_initial = 1.4e15  # 1.4 × 10^15 calories
    global_production_initial = 0.65e16  # 0.65 × 10^16 = 6.5 × 10^15 calories
    
    # US production decline percentage
    us_decline_percent = 29  # 29%
    
    # Calculate US production after decline
    us_decline_factor = us_decline_percent / 100
    us_production_after = us_production_initial * (1 - us_decline_factor)
    
    # Calculate absolute decline in US production
    us_production_decline_absolute = us_production_initial - us_production_after
    
    # Calculate new global production
    # (Original global production minus the absolute decline in US production)
    global_production_after = global_production_initial - us_production_decline_absolute
    
    # Calculate percentage decrease in global production
    global_production_decline_absolute = global_production_initial - global_production_after
    global_decline_percent = (global_production_decline_absolute / global_production_initial) * 100
    
    # Verify US share of global production
    us_share_of_global = (us_production_initial / global_production_initial) * 100
    
    # Display results
    print("=== Food Production Impact Analysis ===\n")
    
    print(f"Initial US production: {us_production_initial:.2e} calories/year")
    print(f"Initial global production: {global_production_initial:.2e} calories/year")
    print(f"US share of global production: {us_share_of_global:.1f}%\n")
    
    print(f"US production decline: {us_decline_percent}%")
    print(f"US production after decline: {us_production_after:.2e} calories/year")
    print(f"Absolute decline in US production: {us_production_decline_absolute:.2e} calories/year\n")
    
    print(f"New global production: {global_production_after:.2e} calories/year")
    print(f"Global production decrease: {global_decline_percent:.2f}%\n")
    
    # Verification calculation using proportion method
    print("=== Verification using proportion method ===")
    expected_global_decline = us_share_of_global * (us_decline_percent / 100) * 100
    print(f"Expected global decline: {us_share_of_global:.1f}% × {us_decline_percent}% = {expected_global_decline:.2f}%")
    print(f"Calculated global decline: {global_decline_percent:.2f}%")
    print(f"Match: {'✓' if abs(expected_global_decline - global_decline_percent) < 0.01 else '✗'}")
    
    return global_decline_percent

# Run the calculation
if __name__ == "__main__":
    result = calculate_global_production_impact()
    print(f"\n=== Final Answer ===")
    print(f"Global food production decreases by {result:.2f}%")
    