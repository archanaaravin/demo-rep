from pathlib import Path
import csv
import json
import math
from datetime import datetime
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sqlalchemy import text
from app.database.database import engine

BASE_DIR = Path(__file__).resolve().parents[3]
DATASET_PATH = BASE_DIR / 'ai' / 'dataset' / 'accidents_v2.csv'
REPORTS_DIR = BASE_DIR / 'backend' / 'data'
REPORTS_PATH = REPORTS_DIR / 'reports.json'

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
    if not stats:
        raise HTTPException(status_code=404, detail='Route location data unavailable')

    from_key = _best_location_match(from_location, stats)
    to_key = _best_location_match(to_location, stats)
    if not from_key or not to_key:
        raise HTTPException(status_code=400, detail='Unable to match start or destination location from dataset')

    if from_key == to_key:
        raise HTTPException(status_code=400, detail='Start and destination locations must be different')

    start = stats[from_key]
    end = stats[to_key]
    distance = round(_haversine_km(start['avg_latitude'], start['avg_longitude'], end['avg_latitude'], end['avg_longitude']), 1)
    distance = max(distance, 1.0)
    avg_risk = round((start['avg_risk'] + end['avg_risk']) / 2, 1)
    avg_severity = round((start['avg_severity'] + end['avg_severity']) / 2, 1)
    base_risk = min(95, max(10, avg_risk * 18 + avg_severity * 8))

    def route_option(label, multiplier, speed, risk_delta, description):
        route_distance = round(distance * multiplier + 0.4, 1)
        eta = int(round((route_distance / max(1, speed)) * 60))
        risk_value = min(99, max(5, int(base_risk + risk_delta)))
        risk_label = 'Low' if risk_value < 30 else 'Medium' if risk_value < 60 else 'High'
        return {
            'title': label,
            'distance_km': route_distance,
            'eta_min': eta,
            'risk_index': f"{risk_label} ({risk_value}%)",
            'route_path': f"{from_key} → {to_key}{description}",
            'start': { 'name': from_key, 'latitude': start['avg_latitude'], 'longitude': start['avg_longitude'] },
            'end': { 'name': to_key, 'latitude': end['avg_latitude'], 'longitude': end['avg_longitude'] },
        }

    return {
        'from': from_key,
        'to': to_key,
        'distance_km': distance,
        'routes': [
            route_option('AEGIS Safest Route', 1.35, 28, -18, ' via lower-risk corridors'),
            route_option('Balanced Route', 1.15, 32, 0, ' via moderate-speed streets'),
            route_option('Direct Fast Route', 1.05, 42, 18, ' via major arterial links'),
        ]
    }

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
