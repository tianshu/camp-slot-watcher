import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from fastapi import FastAPI, Query
from fastapi.responses import HTMLResponse
from mcp.server import Server
from mcp.server.fastmcp import FastMCP
from app.tools.slot_checker import check_camp_slot
from typing import Optional, List

app = FastAPI(title="Camp Slot Watcher", version="1.0.0")

server = Server("camp_slot_watcher")
mcp = FastMCP(server, app)


@mcp.tool("check_camp_slot")
def check_camp_slot_tool(campground_url: str, weekdays: list[str] | None = None):
    return check_camp_slot(campground_url)


@app.get("/", response_class=HTMLResponse)
def home_page():
    html = r"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Camp Slot Watcher</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; text-align: center; }
        h2 {
            font-size: 28px;
            margin-bottom: 24px;
        }
        input {
            width: 500px;
            padding: 10px 14px;
            font-size: 16px;
            border: 1px solid #ccc;
            border-radius: 8px;
            box-shadow: 0 1px 2px rgba(0,0,0,0.05);
        }
        .weekday-group {
            display: flex;
            justify-content: center;
            align-items: center;
            gap: 0px;
            margin-top: 16px;
            flex-wrap: nowrap;
        }
        .weekday-option {
            flex: 0 0 auto;           
            width: 60px;   
            text-align: center;    
            display: inline-flex;
            justify-content: center;
            align-items: center;
            background: #fff;
            border: 1px solid #d1d5db;
            border-radius: 6px;
            padding: 4px 6px;
            cursor: pointer;
            font-size: 14px;
            transition: all 0.15s ease;
        }
        .weekday-option:hover {
            background: #e0f2fe;
            border-color: #3b82f6;
        }
        .weekday-option input {
            margin-right: 8px;
        }
        .weekday:checked + label {
            background: #3b82f6;
            color: #fff;
        }
        button {
            padding: 10px 24px;
            font-size: 16px;
            margin-top: 20px;
            border: none;
            border-radius: 8px;
            background-color: #2563eb;
            color: white;
            cursor: pointer;
        }
        button:hover { background-color: #1e40af; }
        table {
            border-collapse: collapse;
            margin: 30px auto;
            width: 80%;
            background: white;
            border-radius: 8px;
            overflow: hidden;
        }
        th, td {
            border-bottom: 1px solid #e2e8f0;
            padding: 10px 14px;
            font-size: 15px;
        }
        th { background-color: #f1f5f9; }
        tr:nth-child(even) { background-color: #f9fafb; }
    </style>
</head>
<body>
    <h2>Camp Slot Watcher</h2>
    <input id="url" type="text" placeholder="Enter campground URL (e.g. https://www.recreation.gov/...)" />
    <!-- Weekday selector -->
    <div class="weekday-group">
        <label class="weekday-option"><input type="checkbox" class="weekday" value="Monday">Mon</label>
        <label class="weekday-option"><input type="checkbox" class="weekday" value="Tuesday">Tue</label>
        <label class="weekday-option"><input type="checkbox" class="weekday" value="Wednesday">Wed</label>
        <label class="weekday-option"><input type="checkbox" class="weekday" value="Thursday">Thu</label>
        <label class="weekday-option"><input type="checkbox" class="weekday" value="Friday">Fri</label>
        <label class="weekday-option"><input type="checkbox" class="weekday" value="Saturday">Sat</label>
        <label class="weekday-option"><input type="checkbox" class="weekday" value="Sunday">Sun</label>
    </div>
    <br>
    <button id="checkButton">Check Slots</button>
    <div id="output" style="margin:20px auto; width:80%; text-align:center;"></div>

    <script type="text/javascript">
    document.addEventListener("DOMContentLoaded", function () {
        console.log("✅ Script loaded, waiting for click...");
        const button = document.getElementById("checkButton");
        const output = document.getElementById("output");
        const urlInput = document.getElementById("url");

        button.addEventListener("click", async (e) => {
            e.preventDefault();
            console.log("🟢 Button clicked, running fetch...");
            const url = urlInput.value.trim();
            if (!url) {
                output.textContent = "⚠️ Please input a campground URL.";
                return;
            }

            const selected = Array.from(document.querySelectorAll(".weekday:checked")).map(cb => cb.value);
            const weekdayParam = selected.join(",");

            output.textContent = "⏳ Checking... Please wait.";
            try {
                const res = await fetch(`/check?url=${encodeURIComponent(url)}&weekdays=${encodeURIComponent(weekdayParam)}&_=${Date.now()}`);
                const data = await res.json();
                console.log("DEBUG RESPONSE:", data);

                if (!data.success) {
                    output.textContent = "❌ Error: " + (data.error || "Unknown error");
                    return;
                }

                const available = data.available_list || data.available_samples || [];
                if (available.length === 0) {
                    output.textContent = "😞 No available slots found.";
                    return;
                }

                let table = `
                    <h3>✅ Found ${available.length} Available Slots</h3>
                    <table>
                        <tr><th>Site</th><th>Date</th><th>Status</th></tr>
                `;

                for (const r of available.slice(0, 50)) {
                    const color = r.status === "Available" ? "green" : "red";
                    table += `
                        <tr>
                            <td>${r.site}</td>
                            <td>${r.date}</td>
                            <td style="color:${color}; font-weight:bold;">${r.status}</td>
                        </tr>
                    `;
                }
                table += "</table>";

                output.innerHTML = table;
            } catch (err) {
                console.error("⚠️ Error fetching data:", err);
                output.textContent = "⚠️ Error: " + err;
            }
        });
    });
    </script>
</body>
</html>
"""
    return HTMLResponse(content=html)


@app.get("/check")
def check_endpoint(url: str = Query(..., description="Campground URL to check"), 
weekdays: Optional[str] = Query(None, description="Comma-separated weekdays, e.g. Friday,Saturday")
):
    weekdays_list = [w.strip() for w in weekdays.split(",") if w.strip()] if weekdays else None
    return check_camp_slot(url, weekdays = weekdays_list)


@app.get("/status")
def status():
    return {"status": "Camp Slot Watcher is running"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.server:app", host="0.0.0.0", port=8080)
