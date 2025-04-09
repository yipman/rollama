import os
import sys
from rollama.code_manager import CodeManager

def test_file_operations():
    code_manager = CodeManager()
    
    # Switch to test workspace
    try:
        code_manager.switch_workspace("test_workspace")
    except ValueError:
        code_manager.create_workspace("test_workspace")
    
    # Test markdown-style code blocks
    response = """
Here's a simple calculator module:

```python
// filepath: calculator.py
def add(a, b):
    return a + b

def subtract(a, b):
    return a - b
```

And here's a test file:

```python
// filepath: test_calculator.py
from calculator import add, subtract

def test_add():
    assert add(2, 3) == 5
    
def test_subtract():
    assert subtract(5, 3) == 2
```
"""
    
    # Process the response
    code_manager.execute_ai_command(response)
    
    # Verify files were created
    workspace_path = code_manager.current_workspace
    assert os.path.exists(os.path.join(str(workspace_path), "calculator.py"))
    assert os.path.exists(os.path.join(str(workspace_path), "test_calculator.py"))
    
    # Test explicit markers
    response = """
Let's create a package structure:

CREATE DIR: mypackage

CREATE FILE: mypackage/__init__.py
from .calculator import add, subtract
__version__ = "0.1.0"

EDIT FILE: calculator.py
def add(a, b):
    \"\"\"Add two numbers\"\"\"
    return a + b

def subtract(a, b):
    \"\"\"Subtract b from a\"\"\"
    return a - b

def multiply(a, b):
    \"\"\"Multiply two numbers\"\"\"
    return a * b
"""
    
    # Process the response
    code_manager.execute_ai_command(response)
    
    # Verify changes
    mypackage_path = os.path.join(str(workspace_path), "mypackage")
    init_path = os.path.join(mypackage_path, "__init__.py")
    calc_path = os.path.join(str(workspace_path), "calculator.py")
    
    assert os.path.isdir(mypackage_path)
    assert os.path.exists(init_path)
    with open(calc_path, 'r') as f:
        assert "multiply" in f.read()

if __name__ == "__main__":
    test_file_operations()
    print("All tests passed!")