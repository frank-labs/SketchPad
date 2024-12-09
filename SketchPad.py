import tkinter as tk
from tkinter import ttk, colorchooser, filedialog
import json


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
    def __init__(self, color):
        super().__init__(color)
        self.drawing = True  # To track if the polygon is still being drawn
        self.canvas_id = None

    def draw(self, canvas):
        if len(self.points) > 1:
            if self.canvas_id is not None:
                canvas.delete(self.canvas_id)
            self.canvas_id = canvas.create_polygon(*self.flatten_points(), outline=self.color, fill='')

    def contains_point(self, x, y):
        return any(abs(x - px) < 25 and abs(y - py) < 25 for px, py in self.points)

    def flatten_points(self):
        return [coord for point in self.points for coord in point]

    def close_polygon(self):
        if len(self.points) > 2:
            self.drawing = False
            return True
        return False


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
        x1, y1, x2, y2 = self.start_point + self.end_point
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

class PersistentGroup(Shape):
    def __init__(self, shapes):
        super().__init__(color=None)  # Groups don't have a single color
        self.shapes = shapes  # List of shapes in the group
    
    def draw(self, canvas):
        for shape in self.shapes:
            shape.draw(canvas)
    
    def contains_point(self, x, y):
        return any(shape.contains_point(x, y) for shape in self.shapes)
    
    def move(self, dx, dy):
        for shape in self.shapes:
            shape.move(dx, dy)
    
    def to_dict(self):
        data = super().to_dict()
        data['shapes'] = [shape.to_dict() for shape in self.shapes]
        return data
    
    @classmethod
    def from_dict(cls, data):
        shapes = [Shape.from_dict(shape_data) for shape_data in data['shapes']]
        return cls(shapes)


class DrawingApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Sketch Pad")

        self.toolbar = ttk.Frame(root)
        self.toolbar.pack(side=tk.TOP, fill=tk.X)

        self.canvas = tk.Canvas(root, bg="white")
        self.canvas.pack(fill=tk.BOTH, expand=True)

        self.color = "black"
        self.selected_shape_class = None  # Stores the shape class (e.g., Line, Rectangle)
        self.current_drawing_shape = None  # Stores the current shape instance being drawn
        self.shapes = []  # Store all shapes here for persistence
        # self.active_shape = None  # Holds the currently selected shape
        self.drag_start = None
        self.active_shapes = []  # List of selected shapes (can include multiple shapes)
        self.groups = []  # List of persistent groups

        self.create_menus()
        self.create_toolbar_buttons()

        self.canvas.bind("<Button-1>", self.start_action)
        self.canvas.bind("<B1-Motion>", self.perform_action)
        self.canvas.bind("<ButtonRelease-1>", self.end_action)
        self.canvas.bind("<Button-3>", self.finish_polygon)

    def create_menus(self):
        menu_bar = tk.Menu(self.root)
        self.root.config(menu=menu_bar)

        file_menu = tk.Menu(menu_bar, tearoff=0)
        menu_bar.add_cascade(label="File", menu=file_menu)

        file_menu.add_command(label="Save", command=self.save)
        file_menu.add_command(label="Load", command=self.load)

    def create_toolbar_buttons(self):
        color_button = ttk.Button(self.toolbar, text="Color", command=self.choose_color)
        color_button.pack(side=tk.LEFT)

        shapes = [
            ("Line", Line), ("Rectangle", Rectangle), ("Ellipse", Ellipse),
            ("Square", Square), ("Circle", Circle), ("Polygon", Polygon),
            ("Freehand", Freehand)
        ]

        for text, shape_class in shapes:
            button = ttk.Button(self.toolbar, text=text, command=lambda cls=shape_class: self.set_shape(cls))
            button.pack(side=tk.LEFT)
        select_button = ttk.Button(self.toolbar, text="Select/Move", command=self.set_select_mode)
        select_button.pack(side=tk.LEFT)
        group_button = ttk.Button(self.toolbar, text="Group", command=self.group_shapes)
        group_button.pack(side=tk.LEFT)

        ungroup_button = ttk.Button(self.toolbar, text="Ungroup", command=self.ungroup_shapes)
        ungroup_button.pack(side=tk.LEFT)

    def set_select_mode(self):
        self.selected_shape_class = None  # Disable drawing mode
        self.current_drawing_shape = None  # Clear current drawing shape
        self.redraw_all()

    def choose_color(self):
        color = colorchooser.askcolor()[1]
        if color:
            self.color = color

    def set_shape(self, shape_class):
        self.selected_shape_class = shape_class
        self.current_drawing_shape = None  # Exit Drawing Mode if new shape is selected
        self.active_shapes = []  # Clear active shapes when switching to drawing mode
        self.redraw_all()
        
    def start_action(self, event):
        ctrl_pressed = event.state & 0x4  # Check if Ctrl is pressed
        
        if self.selected_shape_class is None:  # Selection/Move Mode
            clicked_shape = None
            for shape in reversed(self.shapes):  # Check for shape under click
                if shape.contains_point(event.x, event.y):
                    clicked_shape = shape
                    break
            
            if ctrl_pressed:  # Multiple selection
                if clicked_shape:
                    if clicked_shape in self.active_shapes:  # Toggle selection
                        self.active_shapes.remove(clicked_shape)
                    else:
                        self.active_shapes.append(clicked_shape)
                self.redraw_all()
            else:  # Single selection
                self.active_shapes = [clicked_shape] if clicked_shape else []

                self.redraw_all()
            
            # Start dragging if a shape is clicked
            if clicked_shape:
                self.drag_start = (event.x, event.y)
        else:  # Drawing Mode
            if issubclass(self.selected_shape_class, IrRegularShape):
                if self.current_drawing_shape is None:
                    self.current_drawing_shape = self.selected_shape_class(color=self.color)
                    self.shapes.append(self.current_drawing_shape)
                self.current_drawing_shape.points.append((event.x, event.y))
                self.redraw_all()
            elif issubclass(self.selected_shape_class, RegularShape):
                self.current_drawing_shape = self.selected_shape_class(
                    start_point=(event.x, event.y),
                    end_point=(event.x, event.y),
                    color=self.color
                )
                self.shapes.append(self.current_drawing_shape)

    def perform_action(self, event):
        if self.active_shapes and self.selected_shape_class is None:  # Move selected shapes
            if self.drag_start:
                dx = event.x - self.drag_start[0]
                dy = event.y - self.drag_start[1]
                for shape in self.active_shapes:
                    shape.move(dx, dy)  
                self.drag_start = (event.x, event.y)  # Update drag start
                self.redraw_all()
        elif self.current_drawing_shape:  # Drawing Mode
            if isinstance(self.current_drawing_shape, RegularShape):
                self.current_drawing_shape.end_point = (event.x, event.y)
                self.redraw_all()
            elif isinstance(self.current_drawing_shape, Freehand):
                self.current_drawing_shape.points.append((event.x, event.y))
                self.redraw_all()

    def finish_polygon(self, event):
        if isinstance(self.current_drawing_shape, Polygon):
            if self.current_drawing_shape and self.current_drawing_shape.close_polygon():
                self.current_drawing_shape.draw(self.canvas)
                self.current_drawing_shape = None

    def end_action(self, event):
        if not self.active_shapes:  # Clicked on empty space
            self.redraw_all()
        if self.current_drawing_shape:
            if isinstance(self.current_drawing_shape, Freehand):
                self.current_drawing_shape.points.append((event.x, event.y))
                self.current_drawing_shape.draw(self.canvas)
                self.current_drawing_shape = None
            elif isinstance(self.current_drawing_shape, RegularShape):
                self.current_drawing_shape.end_point = (event.x, event.y)
                self.current_drawing_shape.draw(self.canvas)
                self.current_drawing_shape = None

    def redraw_all(self):
        # Clear the canvas
        self.canvas.delete("all")

        # Function to highlight shapes (including nested groups)
        def draw_highlighted_shape(shape):
            if isinstance(shape, IrRegularShape):
                # Highlight IrRegularShapes with a dashed outline
                self.canvas.create_polygon(
                    *shape.flatten_points(),
                    outline="red", dash=(5, 2), width=2,
                    fill=""  # Ensure no fill to only show outline
                )
            elif isinstance(shape, RegularShape):
                # Highlight RegularShapes with a dashed rectangle
                x1, y1 = shape.start_point
                x2, y2 = shape.end_point
                self.canvas.create_rectangle(
                    x1, y1, x2, y2,
                    outline="red", dash=(5, 2), width=2
                )
            elif isinstance(shape, PersistentGroup):
                # Recursively highlight all shapes within the group
                for sub_shape in shape.shapes:
                    draw_highlighted_shape(sub_shape)

        # Draw all shapes normally
        for shape in self.shapes:
            shape.draw(self.canvas)

        # Highlight active shapes (can be in a group or not)
        for shape in self.active_shapes:
            draw_highlighted_shape(shape)



    def group_shapes(self):
        """Set the app to selection/move mode."""
        self.selected_shape_class = None  # Disable drawing mode
        self.current_drawing_shape = None  # Clear current drawing shape
        if len(self.active_shapes) > 1:  # Can only group multiple shapes
            group = PersistentGroup(self.active_shapes)
            self.groups.append(group)
            for shape in self.active_shapes:
                self.shapes.remove(shape)  # Remove individual shapes from canvas
            self.shapes.append(group)  # Add group to canvas
            self.active_shapes = [group]  # Make the group active
            self.redraw_all()

    def ungroup_shapes(self):
        """Set the app to selection/move mode."""
        self.selected_shape_class = None  # Disable drawing mode
        self.current_drawing_shape = None  # Clear current drawing shape
        if len(self.active_shapes) == 1 and isinstance(self.active_shapes[0], PersistentGroup):
            group = self.active_shapes[0]
            self.shapes.remove(group)
            for shape in group.shapes:
                self.shapes.append(shape)  # Restore individual shapes to canvas
            self.groups.remove(group)
            self.active_shapes = group.shapes  # Select individual shapes
            self.redraw_all()

    def save(self):
        file_path = filedialog.asksaveasfilename(defaultextension=".json")
        if file_path:
            with open(file_path, "w") as file:
                json.dump([shape.to_dict() for shape in self.shapes], file)

    def load(self):
        file_path = filedialog.askopenfilename(defaultextension=".json")
        if file_path:
            with open(file_path, "r") as file:
                data = json.load(file)
                self.shapes = [Shape.from_dict(shape_data) for shape_data in data]
                self.redraw_all()


if __name__ == "__main__":
    root = tk.Tk()
    app = DrawingApp(root)
    root.mainloop()