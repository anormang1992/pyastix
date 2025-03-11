"""
Example Python module to test Pyastix visualization.
"""

from math import sqrt
from typing import List, Dict, Any


class Shape:
    """Base class for geometric shapes."""
    
    def __init__(self, name: str):
        self.name = name
    
    def area(self) -> float:
        """Calculate the area of the shape."""
        pass
    
    def perimeter(self) -> float:
        """Calculate the perimeter of the shape."""
        pass
    
    def describe(self) -> str:
        """Return a description of the shape."""
        return f"Shape: {self.name}"


class Rectangle(Shape):
    """Rectangle shape with width and height."""
    
    def __init__(self, width: float, height: float):
        super().__init__("Rectangle")
        self.width = width
        self.height = height
    
    def area(self) -> float:
        """
        Calculate the area of the rectangle.
        
        Returns:
            float: Width multiplied by height
        """
        return self.width * self.height
    
    def perimeter(self) -> float:
        """
        Calculate the perimeter of the rectangle.
        
        Returns:
            float: Sum of all sides (2*width + 2*height)
        """
        return 2 * (self.width + self.height)
    
    def describe(self) -> str:
        """
        Return a description of the rectangle.
        
        Returns:
            str: Description including dimensions
        """
        return f"Rectangle: width={self.width}, height={self.height}"


class Square(Rectangle):
    """Square shape, a special case of rectangle."""
    
    def __init__(self, side: float):
        super().__init__(side, side)
        self.name = "Square"
    
    def describe(self) -> str:
        """
        Return a description of the square.
        
        Returns:
            str: Description including the side length
        """
        return f"Square with side length: {self.width}"


class Circle(Shape):
    """Circle shape with a radius."""
    
    def __init__(self, radius: float):
        super().__init__("Circle")
        self.radius = radius
    
    def area(self) -> float:
        """
        Calculate the area of the circle.
        
        Returns:
            float: Pi times radius squared
        """
        return 3.14159 * (self.radius ** 2)
    
    def perimeter(self) -> float:
        """
        Calculate the circumference of the circle.
        
        Returns:
            float: 2 times Pi times radius
        """
        return 2 * 3.14159 * self.radius
    
    def describe(self) -> str:
        """
        Return a description of the circle.
        
        Returns:
            str: Description including the radius
        """
        return f"Circle with radius: {self.radius}"


def calculate_total_area(shapes: List[Shape]) -> float:
    """
    Calculate the total area of a list of shapes.
    
    Args:
        shapes (List[Shape]): List of shape objects
        
    Returns:
        float: Sum of the areas of all shapes
    """
    total = 0.0
    for shape in shapes:
        total += shape.area()
    return total


def create_shape_report(shapes: List[Shape]) -> Dict[str, Any]:
    """
    Create a report about the shapes.
    
    Args:
        shapes (List[Shape]): List of shape objects
        
    Returns:
        Dict[str, Any]: Report containing counts and measurements
    """
    report = {
        "total_count": len(shapes),
        "by_type": {},
        "total_area": calculate_total_area(shapes),
        "descriptions": []
    }
    
    for shape in shapes:
        shape_type = shape.__class__.__name__
        if shape_type not in report["by_type"]:
            report["by_type"][shape_type] = 0
        report["by_type"][shape_type] += 1
        report["descriptions"].append(shape.describe())
    
    return report


def main():
    """Main function to demonstrate shape calculations."""
    shapes = [
        Rectangle(5, 10),
        Square(7),
        Circle(4),
        Rectangle(3, 4)
    ]
    
    report = create_shape_report(shapes)
    print(f"Shape Report: {len(shapes)} shapes found")
    print(f"Total area: {report['total_area']:.2f}")
    
    for shape in shapes:
        print(f"{shape.describe()}, Area: {shape.area():.2f}, Perimeter: {shape.perimeter():.2f}")


if __name__ == "__main__":
    main() 