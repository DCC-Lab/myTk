import unittest
from math import cos, sin, sqrt


class Vector(tuple):
    def __new__(cls, *args):
        if len(args) == 2:
            return tuple.__new__(cls, args)
        else:
            return tuple.__new__(cls, tuple(*args))

    def __add__(self, rhs):
        return Vector(self[0] + rhs[0], self[1] + rhs[1])

    def __radd__(self, rhs):
        return self.__add__(rhs)

    def __sub__(self, rhs):
        return Vector(self[0] - rhs[0], self[1] - rhs[1])

    def __mul__(self, scalar):
        return Vector(self[0] * scalar, self[1] * scalar)

    def __rmul__(self, scalar):
        return self.__mul__(scalar)

    def __truediv__(self, scalr):
        return Vector(self[0] / scalar, self[1] / scalar)

    @property
    def length(self):
        return sqrt(self[0] * self[0] + self[1] * self[1])

    def dot(self, rhs):
        return self[0] * rhs[0] + self[1] * rhs[1]

    def normalized(self):
        inv_l = 1.0 / self.length()
        return Vector(self[0] * inv_l, self[1] * inv_l)


class ReferenceFrame:
    def __init__(
        self, scale: Vector, origin=None, xHat=Vector(1, 0), yHat=Vector(0, -1)
    ):
        """
        Scale is the length of the x and y unit vectors in canvas units (or in original units)
        Everything is in original units (usually canvas)
        """
        self.scale = scale
        self.xHat = xHat
        self.yHat = yHat
        self.origin = origin

    def convert_to_local(self, point):
        x_c, y_c = point - self.origin

        return x_c / self.scale[0] * self.xHat + y_c / self.scale[1] * self.yHat

    def convert_to_canvas(self, local_point):
        x_c, y_c = (local_point[0] * self.scale[0], local_point[1] * self.scale[1])

        return self.origin + self.xHat * x_c + self.yHat * y_c

    def scale_to_local(self, size):
        return (size[0] * abs(self.scale[0]), size[1] * abs(self.scale[1]))

    def scale_to_canvas(self, size):
        return (size[0] / abs(self.scale[0]), size[1] / abs(self.scale[1]))

    @property
    def unit_vectors_scaled(self):
        return self.xHat * self.scale[0], self.yHat * self.scale[1]

    @property
    def unit_vectors(self):
        return self.xHat, self.yHat


class Test(unittest.TestCase):
    def test_refrence_frame_origin(self):
        ref = ReferenceFrame(scale=(1, 1))
        self.assertEqual(ref.convert_to_local(Vector(0, 0)), (0, 0))
        self.assertEqual(ref.convert_to_local(Vector(1, 1)), (1, -1))

        ref = ReferenceFrame(scale=(2, 2))
        self.assertEqual(ref.convert_to_local(Vector(0, 0)), (0, 0))
        self.assertEqual(ref.convert_to_local(Vector(1, 1)), (0.5, -0.5))

        ref = ReferenceFrame(scale=(10, 100))
        self.assertEqual(ref.convert_to_local(Vector(0, 0)), (0, 0))
        self.assertEqual(ref.convert_to_local(Vector(1, 1)), (0.1, -0.01))

    def test_refrence_frame_new_origin(self):
        ref = ReferenceFrame(scale=(1, 1), origin=Vector(1, 1))
        self.assertEqual(ref.convert_to_local(Vector(0, 0)), (-1, 1))
        self.assertEqual(ref.convert_to_local(Vector(1, 1)), (0, 0))

        ref = ReferenceFrame(scale=(2, 2), origin=Vector(1, 1))
        self.assertEqual(ref.convert_to_local(Vector(0, 0)), (-0.5, 0.5))
        self.assertEqual(ref.convert_to_local(Vector(1, 1)), (0, 0))

        ref = ReferenceFrame(scale=(10, 100), origin=Vector(1, 1))
        self.assertEqual(ref.convert_to_local(Vector(1, 1)), (0, 0))
        self.assertEqual(ref.convert_to_local(Vector(2, 2)), (0.1, -0.01))


if __name__ == "__main__":
    unittest.main()
