"""
Test script to verify the maintainability index calculation.
"""

from pyastix.core.complexity import calculate_maintainability_index, get_maintainability_rating
import os

def main():
    """
    Test the maintainability index calculation with different code samples.
    """
    print("Testing maintainability index calculation:")
    
    # Simple, highly maintainable code
    code1 = """
def add(a, b):
    return a + b

def subtract(a, b):
    return a - b
"""
    mi1 = calculate_maintainability_index(code1)
    rating1, _ = get_maintainability_rating(mi1)
    print(f"Simple code MI: {mi1:.1f}, rating: {rating1}")
    
    # Moderately maintainable code with some complexity
    code2 = """
def process_data(data, options=None):
    if options is None:
        options = {}
    
    result = []
    for item in data:
        if isinstance(item, dict):
            if 'value' in item and item['value'] > 0:
                result.append(item['value'] * 2)
            else:
                result.append(0)
        elif isinstance(item, (int, float)):
            result.append(item * 2)
        else:
            try:
                value = float(item)
                result.append(value * 2)
            except (ValueError, TypeError):
                result.append(0)
    
    if options.get('sum', False):
        return sum(result)
    return result
"""
    mi2 = calculate_maintainability_index(code2)
    rating2, _ = get_maintainability_rating(mi2)
    print(f"Moderate code MI: {mi2:.1f}, rating: {rating2}")
    
    # Less maintainable code with high cyclomatic complexity
    code3 = """
def complex_function(data, threshold=0, options=None):
    if options is None:
        options = {'verbose': False, 'normalize': False, 'filter': True}
    
    result = []
    warnings = []
    errors = []
    
    for i, item in enumerate(data):
        try:
            if options.get('verbose'):
                print(f"Processing item {i}...")
            
            if isinstance(item, dict):
                if 'value' not in item:
                    errors.append(f"Item {i} missing 'value' key")
                    continue
                    
                value = item['value']
                if value < threshold:
                    if options.get('filter'):
                        warnings.append(f"Item {i} below threshold")
                        continue
                    else:
                        value = threshold
                        
                if 'weight' in item:
                    weight = item['weight']
                    if weight <= 0:
                        warnings.append(f"Item {i} has invalid weight")
                        weight = 1
                    value *= weight
                    
                if options.get('normalize') and 'max' in item:
                    max_val = item['max']
                    if max_val > 0:
                        value = value / max_val
                    else:
                        warnings.append(f"Item {i} has invalid max value")
                
                result.append(value)
            elif isinstance(item, (int, float)):
                if item < threshold and options.get('filter'):
                    warnings.append(f"Item {i} below threshold")
                    continue
                result.append(item)
            else:
                errors.append(f"Item {i} has invalid type")
        except Exception as e:
            errors.append(f"Error processing item {i}: {str(e)}")
    
    if options.get('verbose'):
        if warnings:
            print(f"Warnings: {len(warnings)}")
            for w in warnings:
                print(f"- {w}")
        if errors:
            print(f"Errors: {len(errors)}")
            for e in errors:
                print(f"- {e}")
    
    if not result:
        return 0
    
    if options.get('sum', False):
        return sum(result)
    return result
"""
    mi3 = calculate_maintainability_index(code3)
    rating3, _ = get_maintainability_rating(mi3)
    print(f"Complex code MI: {mi3:.1f}, rating: {rating3}")
    
    # Test on a real file
    current_file = os.path.abspath(__file__)
    print(f"\nTesting maintainability index on {current_file}")
    
    with open(current_file, 'r') as f:
        file_code = f.read()
    
    mi_file = calculate_maintainability_index(file_code)
    rating_file, _ = get_maintainability_rating(mi_file)
    print(f"This file's MI: {mi_file:.1f}, rating: {rating_file}")

if __name__ == "__main__":
    main() 