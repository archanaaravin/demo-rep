from pathlib import Path
import csv
import json
import math
import os
from datetime import datetime
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import urlopen
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sqlalchemy import text
from app.database.database import engine

BASE_DIR = Path(__file__).resolve().parents[3]
DATASET_PATH = BASE_DIR / 'ai' / 'dataset' / 'accidents_v2.csv'
REPORTS_DIR = BASE_DIR / 'backend' / 'data'
REPORTS_PATH = REPORTS_DIR / 'reports.json'
MAPBOX_ACCESS_TOKEN = os.getenv('MAPBOX_ACCESS_TOKEN')

class ReportCreate(BaseModel):
    id: int | None = None
    loc: str
    type: str
    severity: str
    desc: str
    photos: list[str] = []
    time: str | None = None


def _to_float(value):
    if value is None:
        return None
    try:
        return float(value)
    except (ValueError, TypeError):
        return None


def _to_int(value):
    if value is None:
        return None
    try:
        return int(float(value))
    except (ValueError, TypeError):
        return None

router = APIRouter(
    prefix='/accidents',
    tags=['Accidents']
)

@router.get('/')
def get_accidents(limit: int = 100):
    with engine.connect() as connection:
        result = connection.execute(
            text('SELECT * FROM accidents LIMIT :limit'),
            {'limit': limit}
        )

        accidents = []
        for row in result:
            accidents.append(dict(row._mapping))

        return accidents

@router.get('/csv')
def get_accidents_csv(limit: int = 100):
    if not DATASET_PATH.exists():
        raise HTTPException(status_code=404, detail='Dataset file not found')

    accidents = []
    with DATASET_PATH.open(newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for idx, row in enumerate(reader):
            if idx >= limit:
                break
            accidents.append(row)

    return accidents

@router.get('/history')
def get_accident_history(limit: int = 30):
    if not DATASET_PATH.exists():
        raise HTTPException(status_code=404, detail='Dataset file not found')

    history = []
    with DATASET_PATH.open(newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for idx, row in enumerate(reader):
            if idx >= limit:
                break

            risk = (row.get('AccidentRisk') or 'Unknown').strip() or 'Unknown'
            severity = (row.get('AccidentSeverity') or 'Unknown').strip() or 'Unknown'
            road_name = (row.get('RoadName') or row.get('AreaName') or 'Unknown').strip()
            time_of_day = (row.get('TimeOfDay') or '').strip()
            month = (row.get('Month') or '').strip()
            day = (row.get('Day') or '').strip()
            year = (row.get('Year') or '').strip()
            date_label = f"{day}/{month}/{year}" if day and month and year else ''
            event_time = f"{time_of_day} · {date_label}" if date_label else time_of_day

            details = []
            if row.get('Weather'):
                details.append(f"Weather: {row['Weather']}")
            if row.get('RoadCondition'):
                details.append(f"Road: {row['RoadCondition']}")
            if row.get('TrafficDensity'):
                details.append(f"Traffic: {row['TrafficDensity']}")
            if (row.get('Hotspot') or '').strip().lower() == 'yes':
                details.append('Hotspot reported')

            history.append({
                'id': row.get('AccidentID'),
                'loc': road_name,
                'type': f"{severity} incident",
                'risk': risk,
                'severity': severity,
                'desc': ', '.join(details) if details else 'No additional description available.',
                'photos': [],
                'time': event_time,
            })

    return history

@router.get('/summary')
def get_accident_summary():
    if not DATASET_PATH.exists():
        raise HTTPException(status_code=404, detail='Dataset file not found')

    summary = {
        'total_records': 0,
        'total_accidents': 0,
        'risk_counts': {},
        'severity_counts': {},
        'hotspot_count': 0,
    }

    with DATASET_PATH.open(newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            summary['total_records'] += 1
            summary['total_accidents'] += 1
            risk = (row.get('AccidentRisk') or 'Unknown').strip() or 'Unknown'
            summary['risk_counts'][risk] = summary['risk_counts'].get(risk, 0) + 1
            severity = (row.get('AccidentSeverity') or 'Unknown').strip() or 'Unknown'
            summary['severity_counts'][severity] = summary['severity_counts'].get(severity, 0) + 1
            if (row.get('Hotspot') or '').strip().lower() == 'yes':
                summary['hotspot_count'] += 1

    summary['report_count'] = _load_saved_report_count()
    return summary


def _ensure_reports_file():
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    if not REPORTS_PATH.exists():
        REPORTS_PATH.write_text('[]', encoding='utf-8')
    return REPORTS_PATH


def _load_saved_reports():
    if not REPORTS_PATH.exists():
        return []
    try:
        with REPORTS_PATH.open('r', encoding='utf-8') as f:
            data = json.load(f)
            return data if isinstance(data, list) else []
    except Exception:
        return []


def _load_saved_report_count():
    return len(_load_saved_reports())


def _save_report(report_data: dict):
    _ensure_reports_file()
    reports = _load_saved_reports()
    reports.insert(0, report_data)
    with REPORTS_PATH.open('w', encoding='utf-8') as f:
        json.dump(reports, f, ensure_ascii=False, indent=2)
    return report_data


@router.get('/reports')
def get_saved_reports(limit: int = 50):
    reports = _load_saved_reports()
    return reports[:limit]


@router.post('/report')
def create_report(report: ReportCreate):
    now = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')
    report_dict = report.dict()
    report_dict['id'] = report_dict.get('id') or int(datetime.utcnow().timestamp() * 1000)
    report_dict['time'] = report_dict.get('time') or now
    report_dict['saved_at'] = now
    saved = _save_report(report_dict)
    return {'status': 'ok', 'report': saved, 'report_count': _load_saved_report_count()}


@router.get('/analytics/monthly')
def get_monthly_accidents():
    if not DATASET_PATH.exists():
        raise HTTPException(status_code=404, detail='Dataset file not found')

    counts = {str(month): 0 for month in range(1, 13)}
    with DATASET_PATH.open(newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            month = (row.get('Month') or '').strip()
            if month and month.isdigit() and month in counts:
                counts[month] += 1

    month_names = [
        {'label': 'Jan', 'count': counts['1']},
        {'label': 'Feb', 'count': counts['2']},
        {'label': 'Mar', 'count': counts['3']},
        {'label': 'Apr', 'count': counts['4']},
        {'label': 'May', 'count': counts['5']},
        {'label': 'Jun', 'count': counts['6']},
        {'label': 'Jul', 'count': counts['7']},
        {'label': 'Aug', 'count': counts['8']},
        {'label': 'Sep', 'count': counts['9']},
        {'label': 'Oct', 'count': counts['10']},
        {'label': 'Nov', 'count': counts['11']},
        {'label': 'Dec', 'count': counts['12']},
    ]
    return month_names

@router.get('/analytics/severity')
def get_severity_counts():
    if not DATASET_PATH.exists():
        raise HTTPException(status_code=404, detail='Dataset file not found')

    counts = {}
    with DATASET_PATH.open(newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            severity = (row.get('AccidentSeverity') or 'Unknown').strip() or 'Unknown'
            counts[severity] = counts.get(severity, 0) + 1

    return counts

@router.get('/analytics/timeofday')
def get_time_of_day_counts():
    if not DATASET_PATH.exists():
        raise HTTPException(status_code=404, detail='Dataset file not found')

    counts = {}
    with DATASET_PATH.open(newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            time_of_day = (row.get('TimeOfDay') or '').strip() or 'Unknown'
            counts[time_of_day] = counts.get(time_of_day, 0) + 1

    sorted_counts = sorted(counts.items(), key=lambda item: item[1], reverse=True)
    return [{ 'time': key, 'count': value } for key, value in sorted_counts]

def _normalize_location_name(row):
    return (row.get('RoadName') or row.get('AreaName') or '').strip()


def _load_location_stats():
    if not DATASET_PATH.exists():
        return {}

    stats = {}
    with DATASET_PATH.open(newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            location = _normalize_location_name(row)
            if not location:
                continue

            entry = stats.setdefault(location, {
                'name': location,
                'count': 0,
                'latitude_sum': 0.0,
                'longitude_sum': 0.0,
                'risk_score': 0.0,
                'risk_count': 0,
                'severity_values': [],
            })

            entry['count'] += 1
            try:
                entry['latitude_sum'] += float(row.get('Latitude') or 0)
                entry['longitude_sum'] += float(row.get('Longitude') or 0)
            except (ValueError, TypeError):
                pass

            risk = (row.get('AccidentRisk') or '').strip()
            if risk:
                entry['risk_score'] += {'Low': 1, 'Medium': 2, 'High': 3}.get(risk, 2)
                entry['risk_count'] += 1

            severity = (row.get('AccidentSeverity') or '').strip()
            if severity:
                entry['severity_values'].append(severity)

    for entry in stats.values():
        entry['avg_latitude'] = entry['latitude_sum'] / max(1, entry['count'])
        entry['avg_longitude'] = entry['longitude_sum'] / max(1, entry['count'])
        entry['avg_risk'] = entry['risk_score'] / max(1, entry['risk_count'])
        severity_weights = {'Minor': 1, 'Major': 3, 'Fatal': 5, 'Low': 1, 'Medium': 2, 'High': 3}
        weighted = [severity_weights.get(s, 2) for s in entry['severity_values']]
        entry['avg_severity'] = sum(weighted) / max(1, len(weighted))

    return stats


def _haversine_km(lat1, lon1, lat2, lon2):
    r = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return r * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def _best_location_match(location, stats):
    if not location:
        return None
    key = location.strip().lower()
    exact = {name.lower(): name for name in stats.keys()}
    if key in exact:
        return exact[key]

    candidates = [name for name in stats.keys() if key in name.lower()]
    if candidates:
        return sorted(candidates, key=lambda name: (name.lower().find(key), len(name)))[0]

    return None


def _mapbox_request(url):
    if not MAPBOX_ACCESS_TOKEN:
        raise HTTPException(status_code=503, detail='Mapbox routing is not configured')

    try:
        with urlopen(url, timeout=15) as response:
            return json.load(response)
    except HTTPError as error:
        try:
            detail = json.load(error).get('message', 'Mapbox request failed')
        except Exception:
            detail = 'Mapbox request failed'
        raise HTTPException(status_code=502, detail=detail) from error
    except (URLError, TimeoutError) as error:
        raise HTTPException(status_code=502, detail='Unable to reach Mapbox routing service') from error


def _geocode_location(location):
    query = urlencode({
        'q': location,
        'limit': 1,
        'proximity': '80.2707,13.0827',
        'access_token': MAPBOX_ACCESS_TOKEN,
    })
    data = _mapbox_request(f'https://api.mapbox.com/search/geocode/v6/forward?{query}')
    features = data.get('features') or []
    if not features:
        raise HTTPException(status_code=400, detail=f'Location not found: {location}')

    feature = features[0]
    coordinates = (feature.get('geometry') or {}).get('coordinates') or []
    if len(coordinates) < 2:
        raise HTTPException(status_code=400, detail=f'Location not found: {location}')

    properties = feature.get('properties') or {}
    return {
        'name': properties.get('full_address') or feature.get('place_formatted') or feature.get('name') or location,
        'latitude': coordinates[1],
        'longitude': coordinates[0],
    }


def _route_hazards(coordinates, stats):
    if not coordinates:
        return []

    hazards = []
    for entry in stats.values():
        latitude = entry.get('avg_latitude')
        longitude = entry.get('avg_longitude')
        if not latitude or not longitude:
            continue

        nearest_km = min(
            _haversine_km(latitude, longitude, point[1], point[0])
            for point in coordinates[::max(1, len(coordinates) // 120)]
        )
        if nearest_km <= 0.75 and entry.get('avg_risk', 0) >= 2:
            risk = 'High' if entry['avg_risk'] >= 2.5 else 'Medium'
            hazards.append({
                'name': entry['name'],
                'latitude': latitude,
                'longitude': longitude,
                'risk': risk,
                'distance_from_route_km': round(nearest_km, 2),
            })

    return sorted(hazards, key=lambda item: (item['risk'] != 'High', item['distance_from_route_km']))[:8]


@router.get('/locations')
def get_location_suggestions(query: str = '', limit: int = 50):
    stats = _load_location_stats()
    names = sorted(stats.keys())
    if query:
        query_lower = query.lower().strip()
        names = [name for name in names if query_lower in name.lower()]
    return names[:limit]


@router.get('/route')
def get_route_options(from_location: str, to_location: str):
    stats = _load_location_stats()
    start = _geocode_location(from_location)
    end = _geocode_location(to_location)
    if start['latitude'] == end['latitude'] and start['longitude'] == end['longitude']:
        raise HTTPException(status_code=400, detail='Start and destination locations must be different')

    coordinates = f"{start['longitude']},{start['latitude']};{end['longitude']},{end['latitude']}"
    query = urlencode({
        'alternatives': 'true',
        'steps': 'true',
        'geometries': 'geojson',
        'overview': 'full',
        'access_token': MAPBOX_ACCESS_TOKEN,
    })
    data = _mapbox_request(f'https://api.mapbox.com/directions/v5/mapbox/driving-traffic/{coordinates}?{query}')
    directions_routes = data.get('routes') or []
    if not directions_routes:
        raise HTTPException(status_code=400, detail='No drivable route found between these locations')

    titles = ['AEGIS Safest Route', 'Balanced Route', 'Direct Fast Route']
    routes = []
    for index, route in enumerate(directions_routes[:3]):
        geometry = (route.get('geometry') or {}).get('coordinates') or []
        hazards = _route_hazards(geometry, stats)
        high_risk_count = sum(hazard['risk'] == 'High' for hazard in hazards)
        medium_risk_count = len(hazards) - high_risk_count
        safety_score = max(5, min(100, 96 - high_risk_count * 10 - medium_risk_count * 4))
        risk_label = 'Low' if safety_score >= 80 else 'Medium' if safety_score >= 55 else 'High'
        steps = [
            {
                'instruction': step.get('maneuver', {}).get('instruction') or step.get('name') or 'Continue',
                'distance_m': round(step.get('distance', 0)),
                'duration_s': round(step.get('duration', 0)),
            }
            for leg in route.get('legs') or []
            for step in leg.get('steps') or []
        ]
        routes.append({
            'title': titles[index] if index < len(titles) else f'Route {index + 1}',
            'distance_km': round(route.get('distance', 0) / 1000, 1),
            'eta_min': max(1, round(route.get('duration', 0) / 60)),
            'risk_index': f'{risk_label} ({100 - safety_score}% exposure)',
            'safety_score': safety_score,
            'route_path': f"{start['name']} → {end['name']}",
            'start': start,
            'end': end,
            'geometry': {'type': 'LineString', 'coordinates': geometry},
            'steps': steps,
            'hazards': hazards,
        })

    while len(routes) < 3:
        duplicate = dict(routes[-1])
        duplicate['title'] = titles[len(routes)]
        routes.append(duplicate)

    return {'from': start, 'to': end, 'routes': routes}

@router.get('/analytics/accuracy')
def get_model_accuracy(limit: int = 200):
    if not DATASET_PATH.exists():
        raise HTTPException(status_code=404, detail='Dataset file not found')

    import ai.predictor as predictor

    rows = []
    with DATASET_PATH.open(newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for idx, row in enumerate(reader):
            if idx >= limit:
                break
            rows.append(row)

    if not rows:
        return {'accuracy': 0.0, 'trend': [0,0,0,0,0,0,0,0]}

    weekly = []
    segment = max(1, len(rows) // 8)
    total_correct = 0
    for price_index in range(8):
        start = price_index * segment
        end = start + segment if price_index < 7 else len(rows)
        chunk = rows[start:end]
        correct = 0
        for row in chunk:
            try:
                prediction = predictor.predict_accident(
                    weather=row.get('Weather'),
                    traffic=row.get('TrafficDensity'),
                    road=row.get('RoadType'),
                    speed=_to_float(row.get('SpeedLimit')),
                    time=row.get('TimeOfDay'),
                    road_type=row.get('RoadType'),
                    road_condition=row.get('RoadCondition'),
                    traffic_density=row.get('TrafficDensity'),
                    average_traffic_speed=_to_float(row.get('AverageTrafficSpeed')),
                    temperature=_to_float(row.get('Temperature')),
                    lanes=_to_int(row.get('NumberOfLanes')),
                )
            except Exception:
                continue
            actual = (row.get('AccidentRisk') or '').strip()
            if actual and prediction == actual:
                correct += 1
        weekly.append(round((correct / max(1, len(chunk))) * 100, 1))
        total_correct += correct

    avg_accuracy = round((total_correct / max(1, len(rows))) * 100, 1)
    return {
        'accuracy': avg_accuracy,
        'trend': weekly,
    }


@router.get('/hotspots')
def get_accident_hotspots(limit: int = 10):
    if not DATASET_PATH.exists():
        raise HTTPException(status_code=404, detail='Dataset file not found')

    hotspots = {}
    with DATASET_PATH.open(newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            road_name = (row.get('RoadName') or 'Unknown').strip()
            if not road_name:
                road_name = 'Unknown'
            entry = hotspots.setdefault(road_name, {
                'road_name': road_name,
                'total_accidents': 0,
                'road_type': (row.get('RoadType') or 'Unknown').strip(),
                'latitude_sum': 0.0,
                'longitude_sum': 0.0,
                'count': 0,
            })
            entry['total_accidents'] += 1
            try:
                entry['latitude_sum'] += float(row.get('Latitude') or 0)
            except ValueError:
                pass
            try:
                entry['longitude_sum'] += float(row.get('Longitude') or 0)
            except ValueError:
                pass
            entry['count'] += 1

    hotspot_list = []
    for entry in hotspots.values():
        count = entry['count'] or 1
        hotspot_list.append({
            'road_name': entry['road_name'],
            'total_accidents': entry['total_accidents'],
            'road_type': entry['road_type'],
            'avg_latitude': entry['latitude_sum'] / count,
            'avg_longitude': entry['longitude_sum'] / count,
        })

    hotspot_list.sort(key=lambda item: item['total_accidents'], reverse=True)
    return hotspot_list[:limit]
