"""
Test script to verify maintainability index and complexity metrics.
"""

import os
import tempfile
from pyastix.core.complexity import (
    calculate_complexity,
    get_complexity_rating,
    calculate_maintainability_index,
    get_maintainability_rating
)

def create_temp_file(code):
    """Create a temporary file with the given code and return its path."""
    fd, path = tempfile.mkstemp(suffix='.py')
    with os.fdopen(fd, 'w') as f:
        f.write(code)
    return path

def analyze_code_sample(name, code):
    """Analyze a code sample and print its metrics."""
    print(f"\n{name}:")
    print("-" * 60)
    print(code)
    print("-" * 60)
    
    # Calculate metrics
    complexity = calculate_complexity(code)
    complexity_rating, complexity_class = get_complexity_rating(complexity)
    
    mi_score = calculate_maintainability_index(code)
    mi_rating, mi_class = get_maintainability_rating(mi_score)
    
    # Print results
    print(f"Cyclomatic Complexity: {complexity} ({complexity_rating})")
    print(f"Maintainability Index: {mi_score:.1f} ({mi_rating})")
    
    return complexity, mi_score

def test_code_metrics():
    """Test complexity and maintainability metrics on various code samples."""
    print("Testing code metrics (Complexity and Maintainability Index):")
    
    # Simple, clean code
    simple_code = """
def add(a, b):
    return a + b
"""
    
    # Moderately complex code
    medium_code = """
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
    
    # Complex code with poor maintainability
    complex_code = """
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

    # Code with bad practices and low maintainability
    bad_code = """
def do_stuff(x, y, z, a=1, b=2, c=3, d=4, e=5, f=6, g=7, h=8, i=9):
    # This function does stuff with many parameters
    res = x+y*z/a-b**c+d*e/f+g-h*i
    if x > 0: res += x
    elif x < 0: res -= x
    else: res = res * 2
    if y > 0: 
        if z > 0: res += y*z
        elif z < 0: res += y/abs(z)
        else: res += y*2
    elif y < 0:
        if z > 0: res -= abs(y)*z
        elif z < 0: res -= abs(y)/abs(z)
        else: res -= abs(y)*2
    else:
        if z > 0: res = res + z
        elif z < 0: res = res - abs(z)
        else: res = res * 3
    for i in range(10):
        if i % 2 == 0: res += i
        elif i % 3 == 0: res += i*2
        elif i % 5 == 0: res += i*3
        else: res -= i
    try:
        tmp = x/y/z
        res += tmp
    except ZeroDivisionError:
        res -= 1
    except Exception as e:
        res += 2
    return res
"""

    # Analyze each code sample
    simple_complexity, simple_mi = analyze_code_sample("Simple Code", simple_code)
    medium_complexity, medium_mi = analyze_code_sample("Medium Code", medium_code)
    complex_complexity, complex_mi = analyze_code_sample("Complex Code", complex_code)
    bad_complexity, bad_mi = analyze_code_sample("Bad Code", bad_code)
    
    # Print summary
    print("\nSummary:")
    print("-" * 60)
    print(f"{'Code Sample':<15} | {'Complexity':<20} | {'MI Score':<20}")
    print("-" * 60)
    print(f"{'Simple':<15} | {simple_complexity:<20} | {simple_mi:<20.1f}")
    print(f"{'Medium':<15} | {medium_complexity:<20} | {medium_mi:<20.1f}")
    print(f"{'Complex':<15} | {complex_complexity:<20} | {complex_mi:<20.1f}")
    print(f"{'Bad':<15} | {bad_complexity:<20} | {bad_mi:<20.1f}")
    print("-" * 60)

if __name__ == "__main__":
    test_code_metrics() 