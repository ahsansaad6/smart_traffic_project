from fastapi import FastAPI, HTTPException
from typing import List
from pydantic import BaseModel

app = FastAPI()

# In-memory data (replace with database later)
traffic_data = {"A": 75, "B": 60, "C": 80}

class TrafficData(BaseModel):
    zone: str
    vehicle_count: int

@app.get("/traffic/", response_model=List[TrafficData])
async def get_all_traffic():
    """Gets traffic data for all zones."""
    return [TrafficData(zone=k, vehicle_count=v) for k, v in traffic_data.items()]

@app.get("/traffic/{zone}", response_model=TrafficData)
async def get_traffic(zone: str):
    """Gets traffic data for a specific zone."""
    if zone not in traffic_data:
        raise HTTPException(status_code=404, detail="Zone not found")
    return TrafficData(zone=zone, vehicle_count=traffic_data[zone])

@app.put("/traffic/{zone}", response_model=TrafficData)
async def update_traffic(zone: str, vehicle_count: int):
    """Updates traffic data for a specific zone."""
    if zone not in traffic_data:
        raise HTTPException(status_code=404, detail="Zone not found")
    traffic_data[zone] = vehicle_count
    return TrafficData(zone=zone, vehicle_count=traffic_data[zone])

@app.get("/signal/{zone}")
async def get_signal_status(zone: str):
    """Gets the signal status for a zone."""
    if zone not in traffic_data:
        raise HTTPException(status_code=404, detail="Zone not found")
    count = traffic_data[zone]
    if count > 70:
        return {"zone": zone, "signal": "Red", "duration": 45}
    else:
        return {"zone": zone, "signal": "Green", "duration": 30}

@app.get("/status")
async def get_service_status():
    """Gets the status of the Traffic Service."""
    return {"status": "Traffic Service is running"}