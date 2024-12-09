import tkinter as tk,json, math
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
    #may or may not be used
    def flatten_points(self, points=None):
        """Flatten the list of points for drawing."""
        if points is None:
            points = self.points
        return [coord for point in points for coord in point]
    
    def contains_point(self, x, y):
        """Check if the point (x, y) is inside or on the boundary of the polygon."""
        # Check if the point is on any of the polygon's edges (lines)
        for i in range(len(self.points) - 1):
            x1, y1 = self.points[i]
            x2, y2 = self.points[i + 1]
            if Line((x1, y1), (x2, y2), self.color).contains_point(x, y):
                return True  # Point is on an edge

        # Check if the point is inside the polygon using ray-casting
        inside = False
        n = len(self.points)
        x1, y1 = self.points[0]
        for i in range(n + 1):
            x2, y2 = self.points[i % n]
            if y > min(y1, y2):
                if y <= max(y1, y2):
                    if x <= max(x1, x2):
                        if y1 != y2:
                            xinters = (y - y1) * (x2 - x1) / (y2 - y1) + x1
                        if x1 == x2 or x <= xinters:
                            inside = not inside
            x1, y1 = x2, y2

        return inside
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

class Group(Shape):
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
        self.root.title("Drawing Pad")

        self.toolbar = ttk.Frame(root)
        self.toolbar.pack(side=tk.TOP, fill=tk.X)

        self.canvas = tk.Canvas(root, bg="white")
        self.canvas.pack(fill=tk.BOTH, expand=True)

        #config
        self.tolerance = 10  # Tolerance for snapping to the starting point
        self.THRESHOLD = 5  # Minimum movement in pixels to detect a drag
        
        #state
        self.color = "black"
        self.selected_shape_class = None  # Stores the shape class (e.g., Line, Rectangle), if not None, we are in drawing mode
        self.current_drawing_shape = None  # Stores the current shape instance being drawn
        self.shapes = []  # Store all shapes here for persistence
        self.drag_start = None
        self.active_shapes = []  # List of selected shapes (can include multiple shapes)
        self.groups = []  # List of persistent groups
        self.undo_stack = []
        self.redo_stack = []

        self.is_dragging = False  # Tracks whether the user is dragging shapes
        self.clicked_shape = None

        self.create_menus()
        self.create_toolbar_buttons()

        self.canvas.bind("<Button-1>", self.start_action)
        self.canvas.bind("<Motion>", self.mouse_move)    # Mouse movement for preview
        self.canvas.bind("<B1-Motion>", self.perform_action)
        self.canvas.bind("<ButtonRelease-1>", self.end_action)
        self.canvas.bind("<Button-3>", self.finish_polygon)
        self.root.bind("<Delete>", self.delete_shapes)  # Bind the "Delete" key to delete shapes
        self.root.bind("<Control-c>", self.copy_shapes)
        self.root.bind("<Control-v>", self.paste_shapes)
        self.root.bind("<Control-x>", self.cut_shapes)
        self.root.bind("<Control-z>", self.undo)  # Ctrl+Z for Undo
        self.root.bind("<Control-y>", self.redo)  # Ctrl+Y for Redo

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
        copy_button = ttk.Button(self.toolbar, text="Copy", command=self.copy_shapes)
        copy_button.pack(side=tk.LEFT)
        cut_button = ttk.Button(self.toolbar, text="Cut", command=self.cut_shapes)
        cut_button.pack(side=tk.LEFT)  
        paste_button = ttk.Button(self.toolbar, text="Paste", command=self.start_paste_mode)
        paste_button.pack(side=tk.LEFT)
        delete_button = ttk.Button(self.toolbar, text="Delete", command=self.delete_shapes)
        delete_button.pack(side=tk.LEFT)

    # is clicked other buttons while drawing polygon, stop it.
    def stop_drawing_polygon(self):
        self.selected_shape_class = None
        if self.current_drawing_shape and len(self.current_drawing_shape.points) > 1:
            self.current_drawing_shape.draw(self.canvas)
        self.current_drawing_shape = None

    def delete_shapes(self, event=None):
        self.save_state()
        """Delete the selected shapes or groups."""
        self.stop_drawing_polygon()
        if self.active_shapes:
            for shape in self.active_shapes:
                if isinstance(shape, Group):  # If it's a group, remove all shapes in it
                    self.groups.remove(shape)
                    self.shapes.remove(shape)
                else:
                    self.shapes.remove(shape)
            self.active_shapes.clear()  # Clear the active selection after deletion
        self.redraw_all()
            
    def set_select_mode(self):
        self.stop_drawing_polygon()
        self.selected_shape_class = None  # Disable drawing mode
        self.current_drawing_shape = None  # Clear current drawing shape
        self.redraw_all()

    def choose_color(self):
        color = colorchooser.askcolor()[1]
        if color:
            self.color = color

    def set_shape(self, shape_class):
        self.selected_shape_class = shape_class
        # if shape_class != Polygon:
        #     self.stop_drawing_polygon()
        self.current_drawing_shape = None  # Exit Drawing Mode if new shape is selected
        self.active_shapes = []  # Clear active shapes when switching to drawing mode
        self.redraw_all()
    def mouse_move(self, event):
        if not self.selected_shape_class or not self.current_drawing_shape:
            return

        x, y = event.x, event.y
        self.current_drawing_shape.preview(self.canvas, x, y)
    def start_action(self, event):
        self.save_state()
        ctrl_pressed = event.state & 0x4  # Check if Ctrl is pressed

        if self.selected_shape_class is None:  # Selection/Move Mode
            
            for shape in reversed(self.shapes):  # Check for shape under click
                if shape.contains_point(event.x, event.y):
                    self.clicked_shape = shape
                    break

            if ctrl_pressed:  # Multiple selection
                if self.clicked_shape:
                    #here only append inactive shape, not remove active one until we know it is a click, first q
                    self.drag_start = (event.x, event.y)
                self.redraw_all()
            # no ctrl mode, can deselect all, or  select single(if click) , or move multiple(if drag), we know when step 2
            else:  # Single selection or drag, we dont know 
                if self.clicked_shape:
                    if self.clicked_shape not in self.active_shapes:
                        self.active_shapes = [self.clicked_shape]  # Make only the clicked shape active
                    # else click shape is one of the active shapes, might move multiple/ might select single, see on step 2
                    self.drag_start = (event.x, event.y)
                # click blanck space
                else:
                    self.active_shapes = []  # Deselect all if clicking empty space
                self.redraw_all()
            self.is_dragging = False  # Reset dragging flag
        else:  # Drawing Mode
            #Polygon
            if self.selected_shape_class == Polygon:
                x, y = event.x, event.y
                # Initialize a new polygon if the current one is None
                if self.current_drawing_shape is None:
                    self.current_drawing_shape = Polygon(color=self.color)
                    self.shapes.append(self.current_drawing_shape)
                # First point of the polygon
                if not self.current_drawing_shape.points:
                    self.current_drawing_shape.add_point(x, y)
                else:
                    # Check if the click is near the initial point
                    initial_x, initial_y = self.current_drawing_shape.points[0]
                    if self.distance(x, y, initial_x, initial_y) <= self.tolerance:
                        # Snap to the initial point to close the polygon
                        self.current_drawing_shape.add_point(initial_x, initial_y)
                        self.current_drawing_shape.draw(self.canvas)
                        self.current_drawing_shape = None  # Mark polygon as finished
                    else:
                        # Add a new point
                        self.current_drawing_shape.add_point(x, y)

                # Draw the polygon after each point addition
                if self.current_drawing_shape:
                    self.current_drawing_shape.draw(self.canvas)
            #Freehand
            elif issubclass(self.selected_shape_class, IrRegularShape):
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
        ctrl_pressed = event.state & 0x4  # Check if Ctrl is pressed
        if self.active_shapes and self.selected_shape_class is None:  # Move selected shapes
            #drag_start meant clicked on shape, so no need to re-check if self.clicked_shape
            if self.drag_start:
                dx = event.x - self.drag_start[0]
                dy = event.y - self.drag_start[1]
                # is drag, not click, so we move shapes
                if abs(dx) > self.THRESHOLD or abs(dy) > self.THRESHOLD:  # Check if movement exceeds the threshold
                    self.is_dragging = True  # Set dragging flag
                    if not ctrl_pressed:  # If Ctrl is not pressed, if we move a inactive shape, we move it single, but if we move a active shape, we move multiple
                        if self.clicked_shape not in self.active_shapes:
                            self.active_shapes = [self.clicked_shape]
                        #else, we move multiple shapes
                    else:  # If Ctrl is pressed, and the click shape not active, we make it active
                        if self.clicked_shape not in self.active_shapes:
                            self.active_shapes.append(self.clicked_shape)
                    for shape in self.active_shapes:
                        shape.move(dx, dy)
                    self.drag_start = (event.x, event.y)  # Update drag start
                    self.redraw_all()
                #drag continue
                elif self.is_dragging:
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
        if not self.selected_shape_class or not self.current_drawing_shape:
            return

        # right click to finish the open polygon
        x, y = event.x, event.y
        self.current_drawing_shape.add_point(x, y)
        self.current_drawing_shape.draw(self.canvas)
        self.current_drawing_shape = None  # Start a new polygon on the next click

    def end_action(self, event):
        ctrl_pressed = event.state & 0x4  # Check if Ctrl is pressed
        if self.selected_shape_class is None and not self.is_dragging:  # Move/select mode. and If it's a click, not a drag
            if ctrl_pressed:                 
                if self.clicked_shape:
                    if self.clicked_shape not in self.active_shapes: 
                        self.active_shapes.append(self.clicked_shape)
                    elif self.clicked_shape in self.active_shapes:  
                        self.active_shapes.remove(self.clicked_shape)
                self.redraw_all()
            # no control mode, single click, only select the clicked shape
            else:
                if self.clicked_shape:
                    self.active_shapes = [self.clicked_shape]  # Make only the clicked shape active
                self.redraw_all()
        elif self.current_drawing_shape:  # Finalize drawing shapes
            if isinstance(self.current_drawing_shape, Freehand):
                self.current_drawing_shape.points.append((event.x, event.y))
                self.current_drawing_shape.draw(self.canvas)
                self.current_drawing_shape = None
            elif isinstance(self.current_drawing_shape, RegularShape):
                self.current_drawing_shape.end_point = (event.x, event.y)
                self.current_drawing_shape.draw(self.canvas)
                self.current_drawing_shape = None
        self.clicked_shape = None  # Reset clicked shape
        self.is_dragging=False

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
            elif isinstance(shape, Group):
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
        self.save_state()
        """Set the app to selection/move mode."""
        self.stop_drawing_polygon()
        self.selected_shape_class = None  # Disable drawing mode
        self.current_drawing_shape = None  # Clear current drawing shape
        if len(self.active_shapes) > 1:  # Can only group multiple shapes
            group = Group(self.active_shapes)
            self.groups.append(group)
            for shape in self.active_shapes:
                self.shapes.remove(shape)  # Remove individual shapes from canvas
            self.shapes.append(group)  # Add group to canvas
            self.active_shapes = [group]  # Make the group active
            self.redraw_all()

    def ungroup_shapes(self):
        self.save_state()
        """Set the app to selection/move mode."""
        self.stop_drawing_polygon()
        self.selected_shape_class = None  # Disable drawing mode
        self.current_drawing_shape = None  # Clear current drawing shape
        if len(self.active_shapes) == 1 and isinstance(self.active_shapes[0], Group):
            group = self.active_shapes[0]
            self.shapes.remove(group)
            for shape in group.shapes:
                self.shapes.append(shape)  # Restore individual shapes to canvas
            self.groups.remove(group)
            self.active_shapes = group.shapes  # Select individual shapes
            self.redraw_all()
    def cut_shapes(self, event=None):
        self.save_state()
        """Cut the selected shapes: copy them to memory and delete them from the canvas."""
        if self.active_shapes:
            # Copy shapes to memory
            self.copied_shapes = cp.deepcopy(self.active_shapes)
            
            # Remove the shapes from the canvas
            for shape in self.active_shapes:
                if isinstance(shape, Group) and shape in self.groups:
                    self.groups.remove(shape)  # If it's a group, remove from the groups list
                if shape in self.shapes:
                    self.shapes.remove(shape)  # Remove from the shapes list

            # Clear active selection
            self.active_shapes.clear()
            
            # Redraw the canvas to reflect the changes
            self.redraw_all()

    def copy_shapes(self, event=None):
        """Copy the selected shapes."""
        if self.active_shapes:
            self.copied_shapes = cp.deepcopy(self.active_shapes)  # Deep copy to avoid changes to original shapes

    def paste_shapes(self, event=None):
        self.save_state()
        """Paste the copied shapes at the mouse location."""
        if hasattr(self, 'copied_shapes') and self.copied_shapes:
            # Find the reference point (top-left corner of the copied shapes)
            min_x, min_y = float('inf'), float('inf')

            def get_min_coords(shape):
                """Recursively calculate the minimum x and y coordinates for a shape or group."""
                nonlocal min_x, min_y
                if isinstance(shape, IrRegularShape):
                    for x, y in shape.points:
                        min_x = min(min_x, x)
                        min_y = min(min_y, y)
                elif isinstance(shape, RegularShape):
                    min_x = min(min_x, shape.start_point[0], shape.end_point[0])
                    min_y = min(min_y, shape.start_point[1], shape.end_point[1])
                elif isinstance(shape, Group):
                    for sub_shape in shape.shapes:
                        get_min_coords(sub_shape)

            # Iterate over all copied shapes to calculate the reference point
            for shape in self.copied_shapes:
                get_min_coords(shape)

            # Get mouse position
            mouse_x, mouse_y = self.canvas.winfo_pointerx() - self.canvas.winfo_rootx(), \
                            self.canvas.winfo_pointery() - self.canvas.winfo_rooty()

            # Calculate offset to align the top-left corner with the mouse position
            dx, dy = mouse_x - min_x, mouse_y - min_y

            # Create new shapes by moving the copied shapes to the new location
            new_shapes = cp.deepcopy(self.copied_shapes)
            for shape in new_shapes:
                shape.move(dx, dy)
                self.shapes.append(shape)

            # Redraw canvas
            self.redraw_all()

    def start_paste_mode(self):
        """Activate paste mode where shapes follow the mouse until placed."""
        if hasattr(self, 'copied_shapes') and self.copied_shapes:
            self.is_pasting = True
            self.paste_preview = cp.deepcopy(self.copied_shapes)  # Temporary copy for preview
            self.canvas.bind("<Motion>", self.update_paste_preview)  # Follow mouse
            self.canvas.bind("<Button-1>", self.finalize_paste)  # Place shapes on click
    def update_paste_preview(self, event):
        """Update the dotted outline position for the paste preview."""
        if self.is_pasting and self.paste_preview:
            # Calculate the offset for preview
            min_x, min_y = float('inf'), float('inf')

            def get_min_coords(shape):
                """Recursively calculate the minimum x and y coordinates for a shape or group."""
                nonlocal min_x, min_y
                if isinstance(shape, IrRegularShape):
                    for x, y in shape.points:
                        min_x = min(min_x, x)
                        min_y = min(min_y, y)
                elif isinstance(shape, RegularShape):
                    min_x = min(min_x, shape.start_point[0], shape.end_point[0])
                    min_y = min(min_y, shape.start_point[1], shape.end_point[1])
                elif isinstance(shape, Group):
                    for sub_shape in shape.shapes:
                        get_min_coords(sub_shape)

            # Calculate reference point
            for shape in self.paste_preview:
                get_min_coords(shape)

            dx, dy = event.x - min_x, event.y - min_y

            # Move preview shapes
            for shape in self.paste_preview:
                shape.move(dx, dy)

            # Redraw canvas with preview
            self.redraw_all()
            self.draw_dotted_outline(self.paste_preview)  # Draw dotted preview
    def finalize_paste(self, event):
        self.save_state()
        """Finalize the paste operation by placing the shapes on the canvas."""
        if self.is_pasting and self.paste_preview:
            # Add the preview shapes to the main shapes list
            self.shapes.extend(self.paste_preview)
            self.paste_preview = None  # Clear the preview
            self.is_pasting = False  # Exit paste mode
            self.canvas.unbind("<Motion>")
            self.canvas.unbind("<Button-1>")
            self.redraw_all()
    def draw_dotted_outline(self, shapes):
        """Draw shapes with a dotted outline for preview."""
        for shape in shapes:
            if isinstance(shape, IrRegularShape):
                self.canvas.create_line(
                    *shape.flatten_points(),
                    fill="gray", dash=(4, 2), tags="preview"
                )
            elif isinstance(shape, RegularShape):
                x1, y1 = shape.start_point
                x2, y2 = shape.end_point
                self.canvas.create_rectangle(
                    x1, y1, x2, y2,
                    outline="gray", dash=(4, 2), tags="preview"
                )
            elif isinstance(shape, Group):
                for sub_shape in shape.shapes:
                    self.draw_dotted_outline([sub_shape])

    def save_state(self):
        """Save the current state of shapes to the undo stack."""
        self.undo_stack.append(cp.deepcopy(self.shapes))
        self.redo_stack.clear()  # Clear redo stack on a new action
    def undo(self, event=None):
        """Undo the last action."""
        if self.undo_stack:
            self.redo_stack.append(cp.deepcopy(self.shapes))  # Save current state to redo stack
            self.shapes = self.undo_stack.pop()  # Restore the previous state
            self.redraw_all()
    def redo(self, event=None):
        """Redo the last undone action."""
        if self.redo_stack:
            self.undo_stack.append(cp.deepcopy(self.shapes))  # Save current state to undo stack
            self.shapes = self.redo_stack.pop()  # Restore the state from redo stack
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

    @staticmethod
    def distance(x1, y1, x2, y2):
        return math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)

if __name__ == "__main__":
    root = tk.Tk()
    app = DrawingApp(root)
    root.mainloop()