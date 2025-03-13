"""
Tests for the complexity module to ensure accurate calculations.
"""

import unittest
from pathlib import Path
from ..pyastix.complexity import calculate_complexity, get_complexity_rating


class TestComplexity(unittest.TestCase):
    """
    Test cases for cyclomatic complexity calculation.
    """
    
    def test_simple_function(self):
        """
        Test complexity of a simple function with no branches.
        """
        code = """
def simple_function():
    print("Hello, world!")
    return 42
"""
        complexity = calculate_complexity(code)
        self.assertEqual(complexity, 1)  # Base complexity with no branches
    
    def test_conditionals(self):
        """
        Test complexity with if/elif/else statements.
        """
        code = """
def conditional_function(a, b):
    if a > b:
        return a
    elif a == b:
        return a + b
    else:
        return b
"""
        complexity = calculate_complexity(code)
        self.assertEqual(complexity, 3)  # Base + if + elif
    
    def test_loops(self):
        """
        Test complexity with loops.
        """
        code = """
def loop_function(items):
    result = 0
    for item in items:
        if item > 0:
            result += item
    while result > 100:
        result -= 10
    return result
"""
        complexity = calculate_complexity(code)
        self.assertEqual(complexity, 4)  # Base + for + if + while
    
    def test_complex_function(self):
        """
        Test complexity with multiple control structures and boolean operations.
        """
        code = """
def complex_function(data):
    result = []
    for item in data:
        if item and item.is_valid():
            if item.value > 10 and item.priority == "high":
                result.append(item)
            elif item.value > 5 or item.tags:
                for tag in item.tags:
                    if tag.startswith("important"):
                        result.append(item)
                        break
    
    with open("results.txt", "w") as f:
        f.write(str(result))
    
    try:
        process_results(result)
    except ValueError:
        return None
    except (KeyError, TypeError) as e:
        print(f"Error: {e}")
    
    assert len(result) > 0, "No results found"
    
    return result
"""
        complexity = calculate_complexity(code)
        # Base + for + 2 ifs + elif + for + if + with + try + 2 excepts + assert + 2 boolean ops
        self.assertEqual(complexity, 13)
    
    def test_rating(self):
        """
        Test the complexity rating function.
        """
        low_rating, low_class = get_complexity_rating(3)
        self.assertEqual(low_rating, "Low")
        self.assertEqual(low_class, "complexity-low")
        
        med_rating, med_class = get_complexity_rating(8)
        self.assertEqual(med_rating, "Medium")
        self.assertEqual(med_class, "complexity-medium")
        
        high_rating, high_class = get_complexity_rating(15)
        self.assertEqual(high_rating, "High")
        self.assertEqual(high_class, "complexity-high")
        
        very_high_rating, very_high_class = get_complexity_rating(25)
        self.assertEqual(very_high_rating, "Very High")
        self.assertEqual(very_high_class, "complexity-very-high")


if __name__ == "__main__":
    unittest.main() 