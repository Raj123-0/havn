from fastapi import FastAPI, UploadFile, File, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import db
import json
import engine
from pydantic import BaseModel

app = FastAPI(title="Havn API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def startup_event():
    db.init_db()

@app.get("/api/sources")
def get_sources():
    return {"sources": ["github", "spotify", "takeout", "health", "csv", "calendar"]}

@app.post("/api/ingest/{source}")
async def ingest_source(source: str, file: UploadFile = File(None), token: str = None):
    return {"status": "placeholder"}

@app.get("/api/data")
def get_data(limit: int = 100):
    conn = db.get_connection()
    # using duckdb's df export since pandas is installed
    events = conn.execute("SELECT * FROM events LIMIT ?", (limit,)).fetchdf()
    # converting timestamp to string for json serialization
    events['timestamp'] = events['timestamp'].astype(str)
    
    metrics = conn.execute("SELECT * FROM metrics LIMIT ?", (limit,)).fetchdf()
    metrics['timestamp'] = metrics['timestamp'].astype(str)
    
    return {
        "events": events.to_dict(orient="records"), 
        "metrics": metrics.to_dict(orient="records")
    }

@app.post("/api/correlate")
def correlate(source1: str, name1: str, is_metric1: bool, source2: str, name2: str, is_metric2: bool):
    conn = db.get_connection()
    df1 = engine.fetch_daily_series(conn, source1, name1, is_metric1)
    df2 = engine.fetch_daily_series(conn, source2, name2, is_metric2)
    
    if df1.empty or df2.empty:
        return {"error": "Missing data for one or both series."}
        
    return engine.analyze_correlation(df1, df2)

@app.get("/api/insights")
def get_insights():
    conn = db.get_connection()
    
    metrics = conn.execute("SELECT DISTINCT source, metric_name FROM daily_metrics").fetchall()
    events = conn.execute("SELECT DISTINCT source, type FROM daily_events").fetchall()
    
    candidates = []
    for s, n in metrics:
        candidates.append({"source": s, "name": n, "is_metric": True})
    for s, n in events:
        candidates.append({"source": s, "name": n, "is_metric": False})
        
    results = []
    for i in range(len(candidates)):
        for j in range(i+1, len(candidates)):
            c1 = candidates[i]
            c2 = candidates[j]
            
            if c1['source'] == c2['source']:
                continue 
                
            df1 = engine.fetch_daily_series(conn, c1['source'], c1['name'], c1['is_metric'])
            df2 = engine.fetch_daily_series(conn, c2['source'], c2['name'], c2['is_metric'])
            
            if len(df1) > 10 and len(df2) > 10:
                corr = engine.analyze_correlation(df1, df2)
                if "error" not in corr:
                    results.append({
                        "series1": c1,
                        "series2": c2,
                        "correlation": corr
                    })
                    
    results.sort(key=lambda x: abs(x["correlation"]["spearman"]["r"]), reverse=True)
    return {"insights": results[:10]}

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
