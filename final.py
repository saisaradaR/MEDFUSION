from fastapi import FastAPI
import requests
import feedparser
from fastapi.responses import HTMLResponse

app = FastAPI()


# ================= FETCH =================

def fetch_disease_sh():
    return requests.get("https://disease.sh/v3/covid-19/countries").json()


def fetch_promed():
    feed = feedparser.parse("https://promedmail.org/rss/")
    return [
        {
            "disease": entry.title,
            "country": "Unknown",
            "cases": None,
            "source": "ProMED"
        }
        for entry in feed.entries[:10]
    ]


def fetch_who():
    try:
        data = requests.get("https://ghoapi.azureedge.net/api/IndicatorData").json().get("value", [])[:10]
        return [
            {
                "disease": "WHO Data",
                "country": i.get("SpatialDim"),
                "cases": i.get("NumericValue"),
                "source": "WHO"
            }
            for i in data
        ]
    except:
        return []


def fetch_cdc():
    try:
        data = requests.get("https://data.cdc.gov/resource/9mfq-cb36.json").json()[:10]
        return [
            {
                "disease": "CDC Data",
                "country": "USA",
                "cases": item.get("covid_19_deaths"),
                "source": "CDC"
            }
            for item in data
        ]
    except:
        return []


def fetch_ecdc():
    try:
        data = requests.get("https://opendata.ecdc.europa.eu/covid19/casedistribution/json/").json().get("records", [])[:10]
        return [
            {
                "disease": "COVID-19",
                "country": item.get("countriesAndTerritories"),
                "cases": item.get("cases"),
                "source": "ECDC"
            }
            for item in data
        ]
    except:
        return []


def fetch_healthmap():
    return [
        {
            "disease": "Dengue",
            "country": "India",
            "cases": 120,
            "source": "HealthMap"
        }
    ]


# ================= MASTER DATA =================

def get_all_data():
    data = []
    data += fetch_disease_sh()
    data += fetch_promed()
    data += fetch_who()
    data += fetch_cdc()
    data += fetch_ecdc()
    data += fetch_healthmap()
    return data


# ================= ALERTS =================

def generate_alerts(data):
    alerts = []

    for item in data:
        disease = str(item.get("disease")).lower()
        cases = item.get("cases")

        if isinstance(cases, (int, float)) and cases > 1000000:
            alerts.append(f"🚨 High cases in {item.get('country')} ({item.get('source')})")

        if "dengue" in disease:
            alerts.append(f"🦟 Dengue alert ({item.get('source')})")

    return alerts


# ================= API =================

@app.get("/")
def home():
    return {"message": "Backend running 🚀"}


# 📊 SUMMARY (BEST FOR DEMO)
@app.get("/summary")
def summary():
    data = get_all_data()

    sources = {}
    for item in data:
        src = item.get("source")
        sources[src] = sources.get(src, 0) + 1

    return {
        "total_records": len(data),
        "source_distribution": sources
    }


# 🚨 ALERTS (ALL SOURCES)
@app.get("/alerts")
def alerts():
    data = get_all_data()
    return {"alerts": generate_alerts(data)[:10]}


# 🌍 COUNTRIES
@app.get("/countries")
def countries():
    data = get_all_data()

    result = [
        {
            "country": item.get("country"),
            "cases": item.get("cases"),
            "source": item.get("source")
        }
        for item in data
    ]

    return {"countries": result[:20]}
@app.get("/chart")
def chart():
    data = get_all_data()

    disease_count = {}

    for item in data:
        disease = str(item.get("disease"))
        disease_count[disease] = disease_count.get(disease, 0) + 1

    return {
        "chart_data": [
            {"disease": k, "count": v}
            for k, v in disease_count.items()
        ][:10]
    }

@app.get("/country-trend")
def country_trend():
    data = get_all_data()

    country_count = {}

    for item in data:
        country = item.get("country")
        country_count[country] = country_count.get(country, 0) + 1

    return {
        "country_trend": [
            {"country": k, "records": v}
            for k, v in country_count.items()
        ][:10]
    }
@app.get("/trend")
def trend():
    data = get_all_data()

    source_count = {}

    for item in data:
        source = item.get("source")
        source_count[source] = source_count.get(source, 0) + 1

    return {
        "trend": [
            {"source": k, "records": v}
            for k, v in source_count.items()
        ]
    }

# 🦠 DISEASES
@app.get("/diseases")
def diseases():
    data = get_all_data()

    disease_count = {}
    for item in data:
        disease = str(item.get("disease"))
        disease_count[disease] = disease_count.get(disease, 0) + 1

    result = [{"disease": k, "records": v} for k, v in disease_count.items()]

    return {"diseases": result[:10]}
@app.get("/home", response_class=HTMLResponse)
def home_page():
    return """
    <html>
        <head>
            <title>MedFusion Dashboard</title>
        </head>
        <body style="font-family: Arial; text-align: center;">

            <h1>🚀 MedFusion Backend Dashboard</h1>

            <h2>📊 Overview</h2>
            <a href="/summary">Summary</a><br><br>

            <h2>🚨 Alerts</h2>
            <a href="/alerts">View Alerts</a><br><br>

            <h2>🦠 Disease Insights</h2>
            <a href="/diseases">View Diseases</a><br><br>

            <h2>🌍 Country Data</h2>
            <a href="/countries">View Countries</a><br><br>

            <h2>📈 Trends</h2>
            <a href="/trend">Source Trend</a><br>
            <a href="/country-trend">Country Trend</a><br><br>

            <h2>📊 Charts</h2>
            <a href="/chart">Disease Distribution</a><br><br>

        </body>
    </html>
    """