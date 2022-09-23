import requests
from tqdm import tqdm

for x in tqdm(range(100)):
    requests.get("http://127.0.0.1:8000/pathfind/n743000/n100000/743000/n100000")
