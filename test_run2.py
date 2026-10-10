from services.verification_service_code import verification_service

# Valid Python
result_valid = verification_service.verify_code('def f(): return 1', 'python')
print(f'Valid Python: {result_valid["overall_verified"]}')

# Invalid Python
result_invalid = verification_service.verify_code('def f(:', 'python')
print(f'Invalid Python: {result_invalid["overall_verified"]}')