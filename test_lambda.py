import lambda_function

event ={'name' : 'Lab User'}
context = {}


response = lambda_function.lambda_handler(event, context)

print("test response:" , response)
assert "Lab User" in response['body'], "Unit Test Failed: Name not found in response"
print("Unit Test Passed!")