"""
Supplemental library functions for 3D distances stuff,
mainly for getting space objects close to a position.
"""

from sbs_utils.procedural.query import to_space_object
from sbs_utils.procedural.space_objects import broad_test

def get_space_objects_within_radius(position, radius, broad_type):
    """
    Gets all space objects whose distance to a position is less than
    or equal to the specified radius. In other words, gets all space objects
    contained in a sphere with the specified center position and radius.
    
    Which types of space objects get returned (e.g. player ships only,
    exclude terrain, etc.) can be filtered using the broad_type parameter.
    
    Args:
        position (Vec3): the center of the sphere
        radius (float): the radius of the sphere
        broad_type (int, optional): The type of objects for which to search.
            Same as in broad_test.
            * TERRAIN = 0x01,
            * NPC = 0x10,
            * PLAYER = 0x20,
            * ALL = 0xffff,
            * NPC_AND_PLAYER = 0x30,
            * DEFAULT is 0xfff0
    Returns:
        set[space object]: Set of space objects within the given radius
    """
    space_objects_within_radius = set()
    for space_object_id in broad_test_around_position(position, radius, radius, broad_type):
        space_object = to_space_object(space_object_id)
        # we can assume space_object is not None,
        # since otherwise it could not have been returned from broad_test
        if is_distance_closer_than_or_equal_to(position, space_object.pos, radius):
            space_objects_within_radius.add(space_object)
    return space_objects_within_radius

def broad_test_around_position(position, width, depth, broad_type):
    """
    Gets ids of all space objects that are within a rectangle of the
    specified width, depth, and center position.
    
    Which types of space objects get their ids returned (e.g. player ships only,
    exclude terrain, etc.) can be filtered using the broad_type parameter.
    
    Same as broad_test_around, except that a space object at the center
    of the rectangle is unnecessary.
    
    Args:
        position (Vec3): the center of the rectangle
        width (float): the width of the rectangle
        depth (float): the depth of the rectangle
        broad_type (int, optional): The type of objects for which to search.
            Same as in broad_test.
            * TERRAIN = 0x01,
            * NPC = 0x10,
            * PLAYER = 0x20,
            * ALL = 0xffff,
            * NPC_AND_PLAYER = 0x30,
            * DEFAULT is 0xfff0
    Returns:
        set[str]: Set of ids of space objects within the given rectangle
    """
    x1 = position.x - 0.5 * width
    z1 = position.z - 0.5 * depth
    x2 = position.x + 0.5 * width
    z2 = position.z + 0.5 * depth
    return broad_test(x1, z1, x2, z2, broad_type)

# avoids expensive square root operations

def is_distance_closer_than(position_1, position_2, radius):
    """
    Compares whether two positions in 3D space are closer than a given distance.
    Does not perform any square root operations.
    Args:
        position_1 (Vec3): one position
        position_2 (Vec3): another position
        radius (float): distance under which the two positions must be from each other
    Returns:
        boolean: True if the actual distance is less than the given radius, otherwise False
    """
    return get_distance_squared(position_1, position_2) < radius * radius

def is_distance_closer_than_or_equal_to(position_1, position_2, radius):
    """
    Compares whether two positions in 3D space are closer than or equal to a given distance.
    Does not perform any square root operations.
    Args:
        position_1 (Vec3): one position
        position_2 (Vec3): another position
        radius (float): distance at or under which the two positions must be from each other
    Returns:
        boolean: True if the actual distance is less than or equal to the given radius,
            otherwise False
    """
    return get_distance_squared(position_1, position_2) <= radius * radius

def is_distance_farther_than(position_1, position_2, radius):
    """
    Compares whether two positions in 3D space are farther than a given distance.
    Does not perform any square root operations.
    Args:
        position_1 (Vec3): one position
        position_2 (Vec3): another position
        radius (float): distance above which the two positions must be from each other
    Returns:
        boolean: True if the actual distance is greater than the given radius, otherwise False
    """
    return get_distance_squared(position_1, position_2) > radius * radius

def is_distance_farther_than_or_equal_to(position_1, position_2, radius):
    """
    Compares whether two positions in 3D space are farther than or equal to a given distance.
    Does not perform any square root operations.
    Args:
        position_1 (Vec3): one position
        position_2 (Vec3): another position
        radius (float): distance at or above which the two positions must be from each other
    Returns:
        boolean: True if the actual distance is greater than or equal to the given radius,
            otherwise False
    """
    return get_distance_squared(position_1, position_2) >= radius * radius

def get_distance_squared(position_1, position_2):
    """
    Gets the square of the distance between two positions in 3D space.
    Args:
        position_1 (Vec3): one position
        position_2 (Vec3): another position
    Returns:
        float: square of the distance between the two positions
    """
    dx = position_2.x - position_1.x
    dy = position_2.y - position_1.y
    dz = position_2.z - position_1.z
    return dx * dx + dy * dy + dz * dz
