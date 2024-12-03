import tkinter as tk
from tkinter import ttk, colorchooser, filedialog
import copy as cp


class Shape:
    def __init__(self, color):
        self.color = color

    def draw(self, canvas):
        pass

    def contains_point(self, x, y):
        return False

    def move(self, dx, dy):
        pass

    def to_dict(self):
        return {
            'type': self.__class__.__name__,
            'color': self.color
        }

    @classmethod
    def from_dict(cls, data):
        shape_class = globals()[data['type']]
        return shape_class.from_dict(data)


class IrRegularShape(Shape):
    def __init__(self, color):
        super().__init__(color)
        self.points = []

    def move(self, dx, dy):
        self.points = [(x + dx, y + dy) for x, y in self.points]

    def to_dict(self):
        data = super().to_dict()
        data['points'] = self.points
        return data

    @classmethod
    def from_dict(cls, data):
        shape = cls(data['color'])
        shape.points = data['points']
        return shape


class RegularShape(Shape):
    def __init__(self, start_point, end_point, color):
        super().__init__(color)
        self.start_point = start_point
        self.end_point = end_point

    def move(self, dx, dy):
        self.start_point = (self.start_point[0] + dx, self.start_point[1] + dy)
        self.end_point = (self.end_point[0] + dx, self.end_point[1] + dy)

    def to_dict(self):
        data = super().to_dict()
        data['start_point'] = self.start_point
        data['end_point'] = self.end_point
        return data

    @classmethod
    def from_dict(cls, data):
        return cls(data['start_point'], data['end_point'], data['color'])


class Polygon(IrRegularShape):    
    def add_point(self, x, y):
        self.points.append((x, y))

    def draw(self, canvas):
        if len(self.points) > 1:
            canvas.delete("preview")  # Clear any preview
            #polygons are just a few lines, so we can draw it directly
            canvas.create_line(self.points, fill="black", tags="polygon", width=2)

    def preview(self, canvas, x, y):
        if len(self.points) > 0:
            canvas.delete("preview")  # Clear any previous preview
            preview_points = self.points + [(x, y)]
            canvas.create_line(preview_points, fill="gray", dash=(4, 2), tags="preview")

    def contains_point(self, x, y):
        """Check if the point (x, y) is inside or on the boundary of the polygon."""
        # Check if the point is on any of the polygon's edges (lines)
        for i in range(len(self.points) - 1):
            x1, y1 = self.points[i]
            x2, y2 = self.points[i + 1]
            if Line((x1, y1), (x2, y2), self.color).contains_point(x, y):
                return True  # Point is on an edge

class Freehand(IrRegularShape):
    def draw(self, canvas):
        if len(self.points) > 1:
            self.canvas_id = canvas.create_line(*self.flatten_points(), fill=self.color)

    def contains_point(self, x, y):
        return any(abs(x - px) < 10 and abs(y - py) < 10 for px, py in self.points)

    def flatten_points(self):
        return [coord for point in self.points for coord in point]


class Line(RegularShape):
    def draw(self, canvas):
        self.canvas_id = canvas.create_line(self.start_point[0], self.start_point[1], self.end_point[0],
                                            self.end_point[1], fill=self.color)

    def contains_point(self, x, y):
        x1, y1, x2, y2 = self.start_point + self.end_point
        if min(x1, x2) <= x <= max(x1, x2) and min(y1, y2) <= y <= max(y1, y2):
            dist = abs((y2 - y1) * x - (x2 - x1) * y + x2 * y1 - y2 * x1) / ((y2 - y1) ** 2 + (x2 - x1) ** 2) ** 0.5
            return dist < 5
        return False


class Rectangle(RegularShape):
    def draw(self, canvas):
        self.canvas_id = canvas.create_rectangle(self.start_point[0], self.start_point[1],
                                                 self.end_point[0], self.end_point[1], outline=self.color)

    def contains_point(self, x, y):
        (x1, y1), (x2, y2) = self.start_point , self.end_point
        return min(x1, x2) <= x <= max(x1, x2) and min(y1, y2) <= y <= max(y1, y2)


class Ellipse(RegularShape):
    def draw(self, canvas):
        self.canvas_id = canvas.create_oval(self.start_point[0], self.start_point[1],
                                            self.end_point[0], self.end_point[1], outline=self.color)

    def contains_point(self, x, y):
        rx = abs(self.end_point[0] - self.start_point[0]) / 2
        ry = abs(self.end_point[1] - self.start_point[1]) / 2
        cx = self.start_point[0] + rx
        cy = self.start_point[1] + ry
        if rx > 0 and ry > 0:
            return ((x - cx) ** 2) / (rx ** 2) + ((y - cy) ** 2) / (ry ** 2) <= 1
        return False


class Square(Rectangle):
    def draw(self, canvas):
        side_length = min(abs(self.end_point[0] - self.start_point[0]), abs(self.end_point[1] - self.start_point[1]))
        self.end_point = (self.start_point[0] + side_length, self.start_point[1] + side_length)
        super().draw(canvas)


class Circle(Ellipse):
    def draw(self, canvas):
        radius = min(abs(self.end_point[0] - self.start_point[0]), abs(self.end_point[1] - self.start_point[1])) // 2
        self.end_point = (self.start_point[0] + 2 * radius, self.start_point[1] + 2 * radius)
        super().draw(canvas)