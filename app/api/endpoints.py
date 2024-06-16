import uuid

import shapely
from fastapi import APIRouter, Depends
from geojson import Feature, FeatureCollection, Point
from redis import Redis
from shapely import Polygon
from shapely.geometry import mapping

from app.api.generate_points import generate_random_points_within_zone
from app.api.point_request import PointRequestPayload
from app.config.settings import settings

router = APIRouter()


def get_redis():
    return Redis(host=settings.REDIS_HOST, port=settings.REDIS_PORT)


@router.get("/health")
async def health_check(redis: Redis = Depends(get_redis)):
    try:
        redis.ping()
        return {"status": "healthy"}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}


@router.post("/generate_points")
async def generate_points(
    request_payload: PointRequestPayload, redis: Redis = Depends(get_redis)
):
    raw_points = generate_random_points_within_zone(
        request_payload.bottom_left, request_payload.upper_right, request_payload.n
    )
    point_mappings = [mapping(point) for point in raw_points]
    point_ids = [str(uuid.uuid4()) for point in raw_points]
    for point_id, point_mapping in zip(point_ids, point_mappings):
        redis.geoadd(f"points", (*point_mapping.get("coordinates"), point_id))

    return {"points": point_ids, "input_params": request_payload}


@router.post("/points/cluster")
async def cluster(redis: Redis = Depends(get_redis)):
    for point in redis.georadius("points", 0, 0, 22000, "m", withcoord=True):
        if redis.exists(f"clustered:{point[0].decode('utf-8')}"):
            continue

        nearest = redis.georadius(
            "points",
            point[1][1],
            point[1][0],
            22000,
            "km",
            withcoord=True,
            withdist=True,
            sort="ASC",
        )
        neighbors = []
        index = 0
        while len(neighbors) < 5:
            neighbor = nearest[index]
            if redis.exists(f"clustered:{neighbor[0].decode('utf-8')}"):
                index += 1
                continue
            else:
                neighbors.append(neighbor)
                index += 1

        cluster_id = str(uuid.uuid4())
        for idx, n in enumerate(neighbors):
            redis.set(
                f"clusters:{cluster_id}", (*n[2], f"clustered:{n[0].decode('utf-8')}")
            )

    return redis.keys("clusters:*")


@router.get("/clusters")
async def get_clusters(redis: Redis = Depends(get_redis)):
    return redis.keys("clusters:*")


@router.get("/polygons")
async def get_polygons(x1, y1, width, height, redis: Redis = Depends(get_redis)):
    zone_polygon = Polygon(
        [(x1, y1), (x1, y1 + height), (x1 + width, y1 + height), (x1 + width, y1)]
    )
    clusters = redis.keys("clusters:*")
    matching_polygons = []

    for cl_key in clusters:
        polygon_points = []
        cluster_members = redis.zrange(cl_key.decode("utf-8"), 0, -1)
        for member_id in cluster_members:
            point_id = member_id.decode("utf-8").split(":")[1]
            point = redis.geopos("points", point_id)
            polygon_points.append(point[0])

        cluster_polygon = Polygon([shapely.geometry.Point(p) for p in polygon_points])
        if cluster_polygon.intersects(zone_polygon):
            matching_polygons.append(cluster_polygon)

    features = [Feature(geometry=p) for p in matching_polygons]
    result = FeatureCollection(features)

    return result


@router.get("/points")
async def get_points_in_zone(x1, y1, width, height, redis: Redis = Depends(get_redis)):
    results = redis.execute_command(
        "GEOSEARCH",
        "points",
        "FROMLONLAT",
        x1,
        y1,
        "BYBOX",
        width,
        height,
        "m",
        "ASC",
        "WITHCOORD",
    )
    features = [
        Feature(geometry=Point((float(coord[0]), float(coord[1]))))
        for name, coord in results
    ]
    result = FeatureCollection(features)

    return result
