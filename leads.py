import csv
import json
import time
import requests
import os
from pathlib import Path
from groq import Groq
 

# paths
LEADS_FILE = Path("leads.csv")
OUTPUT_DIR = Path("output")
 
# airtable settings
AT_TOKEN = os.getenv("AIRTABLE_TOKEN")  
AT_BASE  = os.getenv("AIRTABLE_BASE")
AT_TABLE = "Leads"
AT_URL   = f"https://api.airtable.com/v0/{AT_BASE}/{AT_TABLE}"
 
AT_HEADERS = {
    "Authorization": f"Bearer {AT_TOKEN}",
    "Content-Type": "application/json"
}
 
# groq api key
GROQ_KEY = os.getenv("GROQ_KEY")
 
# columns for the output csv
CSV_COLUMNS = [
    "Name", "Email", "Company Name", "Job Title",
    "Lead Score", "Industry", "Business Need",
    "Recommended Action", "Priority Tier"
]
 
# the prompt i'm sending to the AI model
# it tells the model exactly what format to return
AI_PROMPT = """
You are a B2B sales analyst helping qualify inbound leads.
 
Given the lead details below, return a JSON object with these fields:
 
{
  "lead_score": a number from 0 to 100,
  "industry": "the industry this company belongs to",
  "business_need": "a short 1-2 sentence summary of what they actually need",
  "recommended_action": "what the sales team should do next",
  "priority_tier": "High Priority, Medium Priority, or Low Priority"
}
 
How to score:
High Priority (80–100): senior decision maker, clear need, enterprise scale
Medium Priority (50–79): relevant title but less urgency or unclear budget
Low Priority (0–49): vague message, individual, or early exploration
 
Return only the JSON. Nothing else.
"""
 
 
def build_prompt(lead):
    # putting the lead data into a simple text block for the model
    return f"""
Name: {lead['Name']}
Email: {lead['Email']}
Company: {lead['Company Name']}
Job Title: {lead['Job Title']}
Message: {lead['Message from Lead']}
"""
 
 
def get_ai_analysis(client, lead):
    # call the groq api and parse the response
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        max_tokens=300,
        messages=[
            {"role": "system", "content": AI_PROMPT},
            {"role": "user",   "content": build_prompt(lead)}
        ]
    )
 
    raw = response.choices[0].message.content.strip()
 
    # sometimes the model wraps the json in code blocks, stripping that out
    if "```" in raw:
        raw = raw.replace("```json", "").replace("```", "").strip()
 
    return json.loads(raw)
 
 
def push_to_airtable(record):
    # send one record to airtable
    data = {
        "fields": {
            "Name":               record["Name"],
            "Email":              record["Email"],
            "Company Name":       record["Company Name"],
            "Job Title":          record["Job Title"],
            "Lead Score":         int(record["Lead Score"]),
            "Industry":           record["Industry"],
            "Business Need":      record["Business Need"],
            "Recommended Action": record["Recommended Action"],
            "Priority Tier":      record["Priority Tier"]
        }
    }
 
    res = requests.post(AT_URL, headers=AT_HEADERS, json=data)
 
    if res.status_code in (200, 201):
        print("   -> saved to airtable")
    else:
        print(f"   -> airtable error {res.status_code}: {res.text}")
 
 
def main():
    client = Groq(api_key=GROQ_KEY)
    OUTPUT_DIR.mkdir(exist_ok=True)
 
    # load leads from csv
    with open(LEADS_FILE, encoding="utf-8") as f:
        leads = list(csv.DictReader(f))
 
    print(f"starting... {len(leads)} leads to process\n")
 
    results = []
 
    for i, lead in enumerate(leads, 1):
        name = lead["Name"]
        print(f"[{i}/{len(leads)}] {name} — {lead['Company Name']}")
 
        try:
            analysis = get_ai_analysis(client, lead)
 
            row = {
                "Name":               name,
                "Email":              lead["Email"],
                "Company Name":       lead["Company Name"],
                "Job Title":          lead["Job Title"],
                "Lead Score":         analysis.get("lead_score", 0),
                "Industry":           analysis.get("industry", ""),
                "Business Need":      analysis.get("business_need", ""),
                "Recommended Action": analysis.get("recommended_action", ""),
                "Priority Tier":      analysis.get("priority_tier", "Low Priority")
            }
 
            tier  = row["Priority Tier"]
            score = row["Lead Score"]
            print(f"   score: {score} | {tier}")
 
            push_to_airtable(row)
            results.append(row)
 
        except Exception as e:
            print(f"   error on this lead: {e}")
            results.append({
                "Name":               name,
                "Email":              lead["Email"],
                "Company Name":       lead["Company Name"],
                "Job Title":          lead["Job Title"],
                "Lead Score":         0,
                "Industry":           "unknown",
                "Business Need":      "could not process",
                "Recommended Action": "review manually",
                "Priority Tier":      "Low Priority"
            })
 
        # small delay to avoid hitting rate limits
        time.sleep(0.3)
 
    # save results to csv
    csv_path = OUTPUT_DIR / "qualified_leads.csv"
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        writer.writerows(results)
 
    # save results to json as well
    json_path = OUTPUT_DIR / "qualified_leads.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
 
    # quick summary
    High  = sum(1 for r in results if r["Priority Tier"] == "High Priority")
    Medium = sum(1 for r in results if r["Priority Tier"] == "Medium Priority")
    Low = sum(1 for r in results if r["Priority Tier"] == "Low Priority")
 
    print(f"\ndone.")
    print(f"  High:  {High}")
    print(f"  Medium: {Medium}")
    print(f"  Low: {Low}")
    print(f"  csv  -> {csv_path}")
    print(f"  json -> {json_path}")
    print(f"  airtable -> {AT_TABLE} updated")
 
 
if __name__ == "__main__":
    main()