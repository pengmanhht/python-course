# classes, modules, and packages
class Point:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def translate(self, dx, dy):
        self.x += dx
        self.y += dy
    
    def __str__(self):
        return f"Point({self.x}, {self.y})"


if __name__ == "__main__":
    p = Point(1, 2)
    print(p)  # Output: Point(1, 2)
    p.translate(3, 4)
    print(p)  # Output: Point(4, 6)