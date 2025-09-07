import json

def lambda_handler(event,context):
    name = event.get('name' , 'World')
    birthDateInYear = event.get('birthDateInYear' , 'Limitless age')
    greeting = f"Hello , {name}!"
    myage= f"your age is , {birthDateInYear}!"
    return {
        'statusCode' : 200,
        'body' : json.dumps(greeting + myage)
        
    }


if __name__ == "__main__":
    print(lambda_handler({"name": "Mustafa" , "birthDateInYear": "23"}, None))
    print(lambda_handler({}, None))
