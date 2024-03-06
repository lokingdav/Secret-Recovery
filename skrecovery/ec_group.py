from oblivious.ristretto import point as Point, scalar as Scalar

def random_scalar():
    return Scalar()

def export_scalar(secret: Scalar):
    return secret.hex()

def import_scalar(secret):
    if isinstance(secret, Scalar):
        return secret
    return Scalar.fromhex(secret)

def point_from_scalar(scalar: Scalar):
    return Point.base(scalar)

def hash_to_point(message) -> Point:
    return Point.hash(message)

def export_point(point: Point):
    if not isinstance(point, Point):
        raise Exception("Not a point")
    
    return point.hex()

def import_point(point):
    if isinstance(point, Point):
        return point
    
    return Point.fromhex(point)

def random_DH():
    scalar: Scalar = random_scalar()
    return scalar, point_from_scalar(scalar)