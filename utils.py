# Importing needed library
import cv2


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


def get_contour(mask):
    v = cv2.__version__.split('.')[0]

    # In OpenCV version 3 function cv2.findContours() returns three parameters:
    # modified image, found Contours and hierarchy
    # All found Contours from current frame are stored in the list
    # Each individual Contour is a Numpy array of(x, y) coordinates
    # of the boundary points of the Object
    # We are interested only in Contours

    # Checking if OpenCV version 3 is used
    if v == '3':
        _, contours, _ = cv2.findContours(
            mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_NONE)

    # In OpenCV version 4 function cv2.findContours() returns two parameters:
    # found Contours and hierarchy
    # All found Contours from current frame are stored in the list
    # Each individual Contour is a Numpy array of(x, y) coordinates
    # of the boundary points of the Object
    # We are interested only in Contours

    # Checking if OpenCV version 4 is used
    else:
        contours, _ = cv2.findContours(
            mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_NONE)

    # Finding the biggest Contour by sorting from biggest to smallest
    # contours = sorted(contours, key=cv2.contourArea, reverse=True)

    # if contours:
    return contours


def find_highway_region(image_path: str):
    """
    Detecting Object with chosen Colour Mask

    Algorithm:
    Reading RGB image --> Converting to HSV --> Implementing Mask -->
    --> Finding Contour Points --> Extracting Rectangle Coordinates
    """

    # intervalos de valores para diferentes tonalidades de rodovia ja mapeadas
    range_values = [
        ((0, 0, 92), (184, 19, 144)),
        ((103, 31, 0), (120, 70, 110)),
        ((98, 0, 83), (138, 42, 168)),
        ((94, 11, 55), (132, 46, 100)),
        ((100, 12, 68), (126, 52, 112)),
        ((84, 0, 113), (178, 43, 143)),
    ]

    # Read local image
    image_BGR = cv2.imread(image_path)

    # Converting current image to HSV
    image_HSV = cv2.cvtColor(image_BGR, cv2.COLOR_BGR2HSV)

    masks = [
        cv2.inRange(image_HSV, lowerb, upperb)
        for lowerb, upperb in range_values
    ]

    contours = []
    for mask in masks:
        contours += get_contour(mask)

    # Extracting Coordinates of the biggest Contour if any was found
    if len(contours) > 0:
        # Getting rectangle coordinates and spatial size from biggest Contour
        # Function cv2.boundingRect() is used to get an approximate rectangle
        # around the region of interest in the binary image after Contour was found
        contours = sorted(contours, key=cv2.contourArea, reverse=True)
        (x_min, y_min, box_width, box_height) = cv2.boundingRect(contours[0])
        return Rectangle(x_min, y_min, x_min + box_width, y_min + box_height)
