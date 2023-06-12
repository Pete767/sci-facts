import requests

def add_sources():
    url = 'http://127.0.0.1:5000/add_sources'  # Replace with the appropriate URL of your Flask app

    response = requests.post(url)
    if response.status_code == 200:
        print("Sources added successfully")
    else:
        print("Failed to add sources")

if __name__ == '__main__':
    add_sources()