import os
from fastapi import APIRouter, HTTPException
from .image_monitor import fetch_satellite_image, detect_water_bodies, compare_images
from fastapi.responses import StreamingResponse
import numpy as np
from PIL import Image
import io
from .email_alert import send_email_alert

router = APIRouter()

# Example coordinates (can be parameterized)
MONITOR_LAT = float(os.getenv('MONITOR_LAT', '12.9716'))
MONITOR_LON = float(os.getenv('MONITOR_LON', '77.5946'))

# Store previous mask in memory (for demo)
previous_mask = None

@router.get('/monitor')
def monitor_water_body():
    global previous_mask
    image = fetch_satellite_image(MONITOR_LAT, MONITOR_LON)
    mask = detect_water_bodies(image)
    encroachment = False
    percent_loss = 0.0
    if previous_mask is not None:
        percent_loss = compare_images(previous_mask, mask)
        if percent_loss > 0.05:  # 5% loss threshold
            encroachment = True
            # Send email alert
            send_email_alert(
                subject="Water Body Encroachment Detected!",
                body=f"Encroachment detected at ({MONITOR_LAT}, {MONITOR_LON}). Water area loss: {percent_loss*100:.2f}%.",
                to_email=os.getenv('ALERT_EMAIL', 'alert@example.com')
            )
    previous_mask = mask
    # Return image and status
    buf = io.BytesIO()
    image.save(buf, format='PNG')
    buf.seek(0)
    return StreamingResponse(buf, media_type='image/png', headers={
        'X-Encroachment': str(encroachment),
        'X-Percent-Loss': str(percent_loss)
    })
