# app/tools/slot_checker.py
from playwright.sync_api import sync_playwright
import time
import re
from datetime import datetime

DATE_RE = re.compile(r"([A-Za-z]{3} \d{1,2}, \d{4})")


def check_camp_slot_once(campground_url: str, weekdays: list[str] | None = None):
    """Load page and scrape slot availability once."""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=400)
        page = browser.new_page()

        try:
            print("Visiting:", campground_url)
            page.goto(campground_url, wait_until="load", timeout=90_000)

            # scroll down to trigger lazy content
            for _ in range(6):
                page.mouse.wheel(0, 2000)
                page.wait_for_timeout(2000)

            # optional snapshot
            html = page.content()
            print("\n\n========= PAGE HTML SNAPSHOT =========")
            print(html[:2000])
            print("======================================\n\n")

            # wait for availability buttons
            page.wait_for_selector("button.rec-availability-date", timeout=90_000)

            rows = page.locator("tr[id]")
            rows_count = rows.count()
            print(f"🔍 Found {rows_count} rows in table")

            buttons_total = page.locator("button.rec-availability-date").count()
            print(f"🔍 Found {buttons_total} total date buttons on page")

            entries = []  # list of dicts

            for i in range(rows_count):
                row = rows.nth(i)
                site_anchor = row.locator("th a")
                site_name = (site_anchor.text_content() or "").strip() if site_anchor.count() > 0 else f"Site-{i+1}"

                buttons = row.locator("button.rec-availability-date")
                btn_count = buttons.count()

                for j in range(btn_count):
                    btn = buttons.nth(j)
                    label = btn.get_attribute("aria-label") or ""

                    # typical label example: "Oct 30, 2025 - Site 001 is available"
                    m = DATE_RE.search(label)
                    date = m.group(1) if m else "Unknown"

                    status = "Available" if "available" in label.lower() else "Reserved"

                    weekday = None
                    try:
                        dt = datetime.strptime(date, "%b %d, %Y")
                        weekday = dt.strftime("%A")
                    except Exception:
                        weekday = "Unknown"
                    
                    # print(f"datetime is {date} {dt} weekday is {weekday}")


                    entries.append({
                        "site": site_name,
                        "date": date,
                        "weekday": weekday,
                        "status": status,
                        "label": label,
                    })
                
                if weekdays:
                    normalized = [w.capitalize() for w in weekdays]
                    # print(f"chosen weekdays: {normalized}")
                    entries = [e for e in entries if e["weekday"] in normalized]

            available = [e for e in entries if e["status"] == "Available"]
            unavailable = [e for e in entries if e["status"] != "Available"]

            summary = {
                "url": campground_url,
                "weekdays": weekdays,
                "total_entries": len(entries),          # total (site x date cells parsed)
                "available_slots": len(available),
                "unavailable_slots": len(unavailable),
                "has_available": len(available) > 0,
                "available_samples": available[:5],
                "success": True,
            }

            print(f"✅ Parsed entries: {len(entries)} total")
            print(f"✅ Available count: {len([e for e in entries if e['status']=='Available'])}")
            print(f"✅ Example sample: {entries[:3]}")

        except Exception as e:
            summary = {"error": str(e), "success": False}
        finally:
            browser.close()

        return summary


def check_camp_slot(campground_url: str, retries: int = 3, delay: int = 5, weekdays: list[str] | None = None):
    """Retry wrapper: rerun once-scrape a few times until we see any slots parsed."""
    last_result = None
    for attempt in range(1, retries + 1):
        result = check_camp_slot_once(campground_url, weekdays)
        result["attempt"] = attempt
        last_result = result

        # consider it a good scrape if parser produced any entries
        total = result.get("available_slots", 0) + result.get("unavailable_slots", 0)
        if result.get("success") and total > 0:
            return result

        print(f"{attempt} attempts done, retrying after {delay}s...")
        time.sleep(delay)

    # failout, ensure structured return
    if last_result is None:
        last_result = {}
    last_result.update({
        "attempt": retries,
        "success": False,
        "error": last_result.get("error", "Timeout: no slots detected after retries."),
    })
    return last_result
