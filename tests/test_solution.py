#!/usr/bin/env python3
"""
Test script for the new step-by-step solution functionality
"""
import sys
import os
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from solution_service import solution_service
from verification_service import verification_service

def test_equation_solving():
    print("Testing equation solving...")
    # Test simple linear equation
    equation = "2*x + 5 = 15"
    steps = solution_service.solve_equation_step_by_step(equation)
    print(f"Equation: {equation}")
    print(f"Number of steps: {len(steps)}")
    for i, step in enumerate(steps, 1):
        print(f"Step {step['step_number']}: {step['explanation']}")
        print(f"  Expression: {step['expression']}")
        print(f"  LaTeX: {step['expression_latex']}")
    print()

def test_differentiation():
    print("Testing differentiation...")
    # Test simple polynomial differentiation
    expression = "x^3 + 4*x^2 - 5*x + 7"
    steps = solution_service.differentiate_step_by_step(expression)
    print(f"Expression: {expression}")
    print(f"Number of steps: {len(steps)}")
    for i, step in enumerate(steps, 1):
        print(f"Step {step['step_number']}: {step['explanation']}")
        print(f"  Expression: {step['expression']}")
        print(f"  LaTeX: {step['expression_latex']}")
    print()

def test_integration():
    print("Testing integration...")
    # Test simple polynomial integration
    expression = "3*x^2 + 8*x - 5"
    steps = solution_service.integrate_step_by_step(expression)
    print(f"Expression: {expression}")
    print(f"Number of steps: {len(steps)}")
    for i, step in enumerate(steps, 1):
        print(f"Step {step['step_number']}: {step['explanation']}")
        print(f"  Expression: {step['expression']}")
        print(f"  LaTeX: {step['expression_latex']}")
    print()

def test_verification_extension():
    print("Testing extended verification...")
    # Test derivative verification
    result = verification_service.verify_calculus_operation(
        "derivative",
        "x^3 + 4*x^2 - 5*x + 7",
        "3*x^2 + 8*x - 5"
    )
    print(f"Derivative verification: {result}")

    # Test integral verification
    result = verification_service.verify_calculus_operation(
        "integral",
        "3*x^2 + 8*x - 5",
        "x^3 + 4*x^2 - 5*x"
    )
    print(f"Integral verification: {result}")
    print()

if __name__ == "__main__":
    print("Running solution service tests...\n")
    test_equation_solving()
    test_differentiation()
    test_integration()
    test_verification_extension()
    print("Tests completed!")