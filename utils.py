class Rectangle:
    def __init__(self, x_min: int, y_min: int, x_max: int, y_max: int) -> None:
        self.x_min = x_min
        self.y_min = y_min
        self.x_max = x_max
        self.y_max = y_max

    def describe(self):
        return (self.x_min, self.y_min, self.x_max, self.y_max,)

    def centre_x(self):
        return (self.x_min + self.x_max) // 2

    def centre_y(self):
        return (self.y_min + self.y_max) // 2

    def height(self):
        return self.y_max - self.y_min

    def width(self):
        return self.x_max - self.x_min

    def __str__(self) -> str:
        return f'{self.x_min} {self.y_min} {self.x_max} {self.y_max}'
