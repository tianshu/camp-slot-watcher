# Camp Slot Watcher

A FastAPI + Playwright server that checks available camping slots from recreation.gov.

## How to Run

```bash
pip install -r requirements.txt
uvicorn app.server:app --reload --port 8080
```

## Then visit:
http://127.0.0.1:8080
to open the web interface.


## Project Structure
```bash
camp-slot-watcher/
 ├── app/
 │   ├── server.py
 │   └── tools/
 │       └── slot_checker.py
 ├── requirements.txt
 └── README.md
 ```