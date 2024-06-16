import numpy as np
from shapely.geometry import Point


def _generate_random_points(zone: list[Point], n: int):
    random_x_coords = np.random.uniform(low=zone[0].x, high=zone[2].x, size=n)
    random_y_coords = np.random.uniform(low=zone[0].y, high=zone[2].y, size=n)

    points = [Point(x, y) for x, y in zip(random_x_coords, random_y_coords)]
    return points


def generate_random_points_within_zone(
    bottom_left: tuple, upper_right: tuple, n: int
) -> list[Point]:
    bottom_left = Point(*bottom_left)
    upper_right = Point(*upper_right)
    upper_left = Point(bottom_left.x, upper_right.y)
    bottom_right = Point(upper_right.x, bottom_left.y)

    zone_coordinates = [bottom_left, upper_left, upper_right, bottom_right]

    x_span = upper_right.x - bottom_left.x
    y_span = upper_right.y - bottom_left.y

    if not all([x_span > 0, y_span > 0]):
        return (
            []
        )  # Won't consider the zone 'Valid' because the rect isn't oriented as descried

    points = _generate_random_points(zone_coordinates, n)

    return points
