"""Shared deterministic public-office geometry and identity safeguards."""
import math, re, hashlib, json, ipaddress
from urllib.parse import urlsplit
from common import km, is_url

PROFILE_VERSION = 1

def public_https_url(value):
    if not isinstance(value,str) or not is_url(value) or chr(92) in value:return False
    try:
        parsed=urlsplit(value);host=parsed.hostname;port=parsed.port
        if parsed.scheme!='https' or not host or parsed.username is not None or parsed.password is not None:return False
        host=host.rstrip('.').lower()
        if host in ('localhost','localhost.localdomain') or host.lower().endswith(('.local','.internal','.localhost')):return False
        try:return ipaddress.ip_address(host).is_global
        except ValueError:return '.' in host and all(re.fullmatch(r'[a-zA-Z0-9](?:[a-zA-Z0-9-]*[a-zA-Z0-9])?',x) for x in host.rstrip('.').split('.'))
    except ValueError:return False


def coordinate_distance(center, latitude, longitude, source):
    if isinstance(latitude, bool) or isinstance(longitude, bool):
        raise ValueError('Coordinates must be finite numbers')
    lat, lon = float(latitude), float(longitude)
    if not (math.isfinite(lat) and math.isfinite(lon) and -90 <= lat <= 90 and -180 <= lon <= 180):
        raise ValueError('Coordinates must be finite and within latitude/longitude ranges')
    if not public_https_url(source):
        raise ValueError('Coordinates require a public HTTPS provenance source')
    distance = km(center['latitude'], center['longitude'], lat, lon)
    if distance > center['radius_km']:
        raise ValueError('Clinic coordinate outside the configured radius')
    return distance

def candidate_hash(row):
    return hashlib.sha256(json.dumps({'schema_version': PROFILE_VERSION, 'row': row}, sort_keys=True, allow_nan=False).encode()).hexdigest()

def office_address(value):
    # Preserve all civic/unit tokens. No prefix or substring address matching.
    tokens=re.findall(r'[a-z0-9]+', str(value or '').casefold())
    aliases={'street':'st','road':'rd','avenue':'ave','boulevard':'blvd','drive':'dr','suite':'unit','ste':'unit'}
    return tuple(aliases.get(x,x) for x in tokens)

def same_office(a,b):
    norm=lambda v:re.sub(r'[^a-z0-9]','',str(v or '').casefold())
    return (bool(norm(a.get('name'))) and norm(a.get('name'))==norm(b.get('name'))
            and norm(a.get('community'))==norm(b.get('community'))
            and bool(office_address(a.get('address')))
            and office_address(a.get('address'))==office_address(b.get('address')))
