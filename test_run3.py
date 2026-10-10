from services.programming_solution_service import programming_solution_service

steps = programming_solution_service.explain_concept('decorators', 'python')
print(f'Decorator steps: {len(steps)}')
print(f'Step 1: {steps[0]["explanation"] if steps else "None"}')