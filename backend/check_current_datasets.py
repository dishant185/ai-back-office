import urllib.request, json

def check():
    with urllib.request.urlopen('http://127.0.0.1:8000/api/v1/uploads/list') as r:
        data = json.loads(r.read())
        print(f"Total uploads in uploads/list: {len(data)}")
        for i, item in enumerate(data):
            print(f"{i}: {item.get('upload_id')} | {item.get('filename')}")

if __name__ == "__main__":
    check()
