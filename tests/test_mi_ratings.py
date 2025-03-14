"""
Test script to verify the updated maintainability index rating function.
"""

from pyastix.core.complexity import get_maintainability_rating

def test_mi_ratings():
    """
    Test the maintainability index rating function with various scores.
    """
    test_cases = [
        (-1, "N/A"),
        (0, "Difficult to Maintain"),
        (20, "Difficult to Maintain"),
        (39.9, "Difficult to Maintain"),
        (40, "Moderately Maintainable"),
        (50, "Moderately Maintainable"),
        (64.9, "Moderately Maintainable"),
        (65, "Maintainable"),
        (70, "Maintainable"),
        (74.9, "Maintainable"),
        (75, "Highly Maintainable"),
        (85, "Highly Maintainable"),
        (100, "Highly Maintainable"),
    ]
    
    print("Testing maintainability index ratings:")
    print("-" * 50)
    print(f"{'MI Score':<10} | {'Rating':<25} | {'CSS Class'}")
    print("-" * 50)
    
    for score, expected_rating in test_cases:
        rating, css_class = get_maintainability_rating(score)
        result = "✓" if rating == expected_rating else "✗"
        print(f"{score:<10} | {rating:<25} | {css_class}")
        if rating != expected_rating:
            print(f"  Expected: {expected_rating}, Got: {rating}")
    
    print("-" * 50)

if __name__ == "__main__":
    test_mi_ratings() 