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


def progressBar(iterable, prefix='', suffix='', decimals=1, length=100, fill='█', printEnd="\r"):
    """
    Call in a loop to create terminal progress bar
    @params:
        iterable    - Required  : iterable object (Iterable)
        prefix      - Optional  : prefix string (Str)
        suffix      - Optional  : suffix string (Str)
        decimals    - Optional  : positive number of decimals in percent complete (Int)
        length      - Optional  : character length of bar (Int)
        fill        - Optional  : bar fill character (Str)
        printEnd    - Optional  : end character (e.g. "\r", "\r\n") (Str)
    """
    total = len(iterable)
    # Progress Bar Printing Function

    def printProgressBar(iteration):
        percent = ("{0:." + str(decimals) + "f}").format(100 *
                                                         (iteration / float(total)))
        filledLength = int(length * iteration // total)
        bar = fill * filledLength + '-' * (length - filledLength)
        print(f'\r{prefix} |{bar}| {percent}% {suffix}', end=printEnd)
    # Initial Call
    printProgressBar(0)
    # Update Progress Bar
    for i, item in enumerate(iterable):
        yield item
        printProgressBar(i + 1)
    # Print New Line on Complete
    print()


def log(message):
    l = len(message)
    if l < 78:
        message += ' ' * (78 - l)
    print(message)
