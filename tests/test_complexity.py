"""
Test script to verify the new radon-based complexity calculations.
"""

from pyastix.core.complexity import calculate_complexity, get_complexity_rating, extract_function_complexities
import os

def test_calculate_complexity():
    """
    Test the calculate_complexity function with a sample code string.
    """
    # Simple function with low complexity
    code1 = """
def simple_function(a, b):
    return a + b
"""
    complexity1 = calculate_complexity(code1)
    rating1, _ = get_complexity_rating(complexity1)
    print(f"Simple function complexity: {complexity1}, rating: {rating1}")
    
    # Function with medium complexity
    code2 = """
def medium_function(a, b, c):
    if a > b:
        if b > c:
            return a
        else:
            return b
    elif a < c:
        for i in range(c):
            if i == b:
                return i
    return c
"""
    complexity2 = calculate_complexity(code2)
    rating2, _ = get_complexity_rating(complexity2)
    print(f"Medium function complexity: {complexity2}, rating: {rating2}")
    
    # Function with high complexity
    code3 = """
def complex_function(data, threshold, options):
    result = 0
    if options.get('verbose'):
        print("Processing...")
    
    for item in data:
        if item > threshold and options.get('filter'):
            if 'key1' in item and 'key2' in item:
                if item['key1'] > item['key2']:
                    result += item['key1']
                else:
                    result += item['key2']
            elif 'key3' in item:
                result += item['key3']
                for subitem in item.get('subitems', []):
                    if subitem > threshold / 2:
                        result += subitem
                    elif subitem > threshold / 4:
                        result += subitem / 2
                    else:
                        continue
            else:
                result += item
        elif item > threshold * 2:
            result += item * 2
        else:
            result += item
    
    return result
"""
    complexity3 = calculate_complexity(code3)
    rating3, _ = get_complexity_rating(complexity3)
    print(f"Complex function complexity: {complexity3}, rating: {rating3}")

def test_extract_function_complexities():
    """
    Test the extract_function_complexities function on a Python file.
    """
    # Use this script file for testing
    current_file = os.path.abspath(__file__)
    print(f"Testing complexity extraction on {current_file}")
    
    complexities = extract_function_complexities(current_file)
    print(f"Found {len(complexities)} functions/methods")
    
    for (start, end), complexity in complexities.items():
        rating, _ = get_complexity_rating(complexity)
        print(f"Function at lines {start}-{end}: complexity={complexity}, rating={rating}")

if __name__ == "__main__":
    print("Testing calculate_complexity function:")
    test_calculate_complexity()
    print("\nTesting extract_function_complexities function:")
    test_extract_function_complexities() 