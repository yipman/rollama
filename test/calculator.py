def add(x, y):
    return x + y

def subtract(x, y):
    return x - y

def multiply(x, y):
    return x * y

def divide(x, y):
    if y == 0:
        raise ValueError("Cannot divide by zero")
    return x / y

class Calculator:
    def __init__(self):
        self.result = None
    
    def calculate(self, operation, x, y):
        try:
            operation_result = {
                "add": add,
                "subtract": subtract,
                "multiply": multiply,
                "divide": divide
            }[operation]
        except KeyError:
            raise ValueError("Invalid operation")
        
        try:
            self.result = operation_result(x, y)
            return "Result is {}".format(self.result)
        except Exception as e:
            raise e

def main():
    calc = Calculator()
    print(calc.calculate("add", 5, 3))
    print(calc.calculate("divide", 10, 2))

if __name__ == "__main__":
    main()