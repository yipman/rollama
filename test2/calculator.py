class Calculator:
    def add(self, x, y):
        return x + y
    
    def subtract(self, x, y):
        return x - y
    
    def multiply(self, x, y):
        return x * y
    
    def divide(self, x, y):
        if y == 0:
            raise ValueError("Cannot divide by zero")
        return x / y
    
    def run(self):
        print("Simple Calculator")
        print("1. Add")
        print("2. Subtract")
        print("3. Multiply")
        print("4. Divide")
        
        choice = input("Enter choice (1-4): ")
        num1 = float(input("Enter first number: "))
        num2 = float(input("Enter second number: "))
        
        if choice == '1':
            result = self.add(num1, num2)
            print(f"{num1} + {num2} = {result}")
            
        elif choice == '2':
            result = self.subtract(num1, num2)
            print(f"{num1} - {num2} = {result}")
            
        elif choice == '3':
            result = self.multiply(num1, num2)
            print(f"{num1} * {num2} = {result}")
            
        elif choice == '4':
            result = self.divide(num1, num2)
            print(f"{num1} / {num2} = {result}")
        else:
            print("Invalid choice!")

if __name__ == "__main__":
    calc = Calculator()
    calc.run()