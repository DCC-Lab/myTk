import unittest
from math import cos, sin, sqrt


def same_basis(e1, e2):
    return e1.basis == e2.basis


class Point:
    def __init__(self, *args, basis=None):
        self.coords = args
        self.basis = basis

    def __getitem__(self, index):
        return self.coords[index]

    def __sub__(self, rhs: "Point"):
        assert isinstance(rhs, Point)
        assert same_basis(self, rhs)

        return Vector(self[0] - rhs[0], self[1] - rhs[1], basis=self.basis)

    def __mul__(self, scalar):
        return Point(self[0] * scalar, self[1] * scalar, basis=self.basis)

    def __rmul__(self, scalar):
        return self.__mul__(scalar)

    def __truediv__(self, scalr):
        return Point(self[0] / scalar, self[1] / scalar, basis=self.basis)


class Vector:
    def __init__(self, *args, basis=None):
        self.components = args
        self.basis = basis

    @property
    def c0(self):
        return self.components[0]

    @property
    def c1(self):
        return self.components[1]

    def __getitem__(self, index):
        return self.components[index]

    def __repr__(self):
        return str(self)

    def __str__(self):
        basis_str = ""
        if self.basis is not None:
            basis_str = f" basis=[{self.basis.e0}, {self.basis.e1}]"

        return f"({self[0]},{self[1]}){basis_str}"

    def __add__(self, rhs: "Vector"):
        assert isinstance(rhs, Vector)
        assert same_basis(self, rhs)

        return Vector(self.c0 + rhs.c0, self.c1 + rhs.c1, basis=self.basis)

    def __radd__(self, rhs):
        return self.__add__(rhs)

    def __sub__(self, rhs: "Vector"):
        assert isinstance(rhs, Vector)
        assert same_basis(self, rhs)

        return Vector(self.c0 - rhs.c0, self.c1 - rhs.c1, basis=self.basis)

    def __mul__(self, scalar):
        return Vector(self.c0 * scalar, self.c1 * scalar, basis=self.basis)

    def __rmul__(self, scalar):
        return self.__mul__(scalar)

    def __truediv__(self, scalar):
        return Vector(self.c0 / scalar, self.c1 / scalar, basis=self.basis)

    @property
    def length(self):
        v = self.standard_coordinates()
        return sqrt(v.c0 * v.c0 + v.c1 * v.c1)

    @property
    def is_unitary(self):
        return abs(self.length - 1.0) < 1e-6

    def is_perpendicular(self, rhs):
        return abs(self.dot(rhs)) < 1e-6

    def dot(self, rhs: "Vector"):
        assert same_basis(self, rhs)
        return self.c0 * rhs.c0 + self.c1 * rhs.c1

    def normalized(self):
        inv_l = 1.0 / self.length()
        return Vector(self.c0 * inv_l, self.c1 * inv_l, basis=self.basis)

    def scaled(self, scale):
        return Vector(self.c0 * scale[0], self.c1 * scale[1], basis=self.basis)

    def change_to_basis(self, new_basis):
        v = self.standard_coordinates()
        e0, e1 = (new_basis.e0, new_basis.e1)

        c0 = v.dot(e0) / (e0.length*e0.length)
        c1 = v.dot(e1) / (e1.length*e1.length)

        self.components = (c0, c1)
        self.basis = new_basis

        return self

    def standard_coordinates(self):
        if self.basis is None:
            return self

        return self.c0 * self.basis.e0 + self.c1 * self.basis.e1


class Basis:
    def __init__(self, e0: Vector = None, e1: Vector = None):
        """
        Defaults to standard basis
        """
        if e0 is None:
            e0 = Vector(1, 0)
        if e1 is None:
            e1 = Vector(0, 1)

        assert e0.basis is None
        assert e1.basis is None
        assert e0.is_perpendicular(e1)

        self.e0 = e0
        self.e1 = e1

    def __eq__(self, rhs: "Basis"):
        assert isinstance(rhs, Basis)

        return self.e0 == rhs.e0 and self.e1 == rhs.e1


# class Vector(tuple):
#     def __new__(cls, *args):
#         if len(args) == 2:
#             return tuple.__new__(cls, args)
#         else:
#             return tuple.__new__(cls, tuple(*args))

#     @property
#     def x(self):
#         return self[0]

#     @property
#     def y(self):
#         return self[1]

#     def __add__(self, rhs):
#         return Vector(self[0] + rhs[0], self[1] + rhs[1])

#     def __radd__(self, rhs):
#         return self.__add__(rhs)

#     def __sub__(self, rhs):
#         return Vector(self[0] - rhs[0], self[1] - rhs[1])

#     def __mul__(self, scalar):
#         return Vector(self[0] * scalar, self[1] * scalar)

#     def __rmul__(self, scalar):
#         return self.__mul__(scalar)

#     def __truediv__(self, scalr):
#         return Vector(self[0] / scalar, self[1] / scalar)

#     @property
#     def length(self):
#         return sqrt(self[0] * self[0] + self[1] * self[1])

#     def dot(self, rhs):
#         return self[0] * rhs[0] + self[1] * rhs[1]

#     def normalized(self):
#         inv_l = 1.0 / self.length()
#         return Vector(self[0] * inv_l, self[1] * inv_l)

#     def scaled(self, scale):
#         return Vector(self[0] * scale[0], self[1] * scale[1])


class ReferenceFrame:
    def __init__(
        self, scale: Vector, origin=Vector(0, 0), xHat=Vector(1, 0), yHat=Vector(0, -1)
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

    def scale_to_canvas(self, size):
        return (size[0] * abs(self.scale[0]), size[1] * abs(self.scale[1]))

    def scale_to_local(self, size):
        return (size[0] / abs(self.scale[0]), size[1] / abs(self.scale[1]))

    @property
    def unit_vectors_scaled(self):
        return self.xHat * self.scale[0], self.yHat * self.scale[1]

    @property
    def unit_vectors(self):
        return self.xHat, self.yHat


class TestCase(unittest.TestCase):
    # def test_refrence_frame_origin(self):
    #     ref = ReferenceFrame(scale=(1, 1))
    #     self.assertEqual(ref.convert_to_local(Vector(0, 0)), (0, 0))
    #     self.assertEqual(ref.convert_to_local(Vector(1, 1)), (1, -1))

    #     ref = ReferenceFrame(scale=(2, 2))
    #     self.assertEqual(ref.convert_to_local(Vector(0, 0)), (0, 0))
    #     self.assertEqual(ref.convert_to_local(Vector(1, 1)), (0.5, -0.5))

    #     ref = ReferenceFrame(scale=(10, 100))
    #     self.assertEqual(ref.convert_to_local(Vector(0, 0)), (0, 0))
    #     self.assertEqual(ref.convert_to_local(Vector(1, 1)), (0.1, -0.01))

    # def test_refrence_frame_new_origin(self):
    #     ref = ReferenceFrame(scale=(1, 1), origin=Vector(1, 1))
    #     self.assertEqual(ref.convert_to_local(Vector(0, 0)), (-1, 1))
    #     self.assertEqual(ref.convert_to_local(Vector(1, 1)), (0, 0))

    #     ref = ReferenceFrame(scale=(2, 2), origin=Vector(1, 1))
    #     self.assertEqual(ref.convert_to_local(Vector(0, 0)), (-0.5, 0.5))
    #     self.assertEqual(ref.convert_to_local(Vector(1, 1)), (0, 0))

    #     ref = ReferenceFrame(scale=(10, 100), origin=Vector(1, 1))
    #     self.assertEqual(ref.convert_to_local(Vector(1, 1)), (0, 0))
    #     self.assertEqual(ref.convert_to_local(Vector(2, 2)), (0.1, -0.01))

    def test_point(self):
        p1 = Point(1, 2)
        p2 = Point(3, 4)
        v = p2 - p1
        self.assertTrue(isinstance(v, Vector))

    def test_vector(self):
        v1 = Vector(1, 2)
        v2 = Vector(3, 4)
        print(v2.dot(v1))

    def test_basis(self):
        b = Basis(Vector(1, -1), Vector(1, 1))
        p1 = Point(1, 2, basis=b)
        p2 = Point(3, 4, basis=b)
        print(p2 - p1)

    def test_basis_change(self):
        b1 = Basis(e0=Vector(1, -1), e1=Vector(1, 1))
        b2 = Basis()
        v1 = Vector(1, 2, basis=b1)
        print(v1)
        print(v1.standard_coordinates())

        print(v1.length)
        print(v1.standard_coordinates().length)

        print(v1.change_to_basis(b1).length)

        # print(v1.change_to_basis(b1))
        # print(v1.change_to_basis(b2))

    def test_basis_change2(self):
        b3 = Basis(e0=Vector(1,-1), e1=Vector(1,1))
        b2 = Basis(e0=Vector(2,0), e1=Vector(0,2))
        b1 = Basis()
        v1 = Vector(1, 3, basis=b1)
        print(v1)
        print(v1.change_to_basis(b2))
        # print(v1.standard_coordinates())
        # v2 = Vector(0.5, 1, basis=b2)


        # print(v2)
        # print(v2.standard_coordinates())
        # v2.change_to_basis(b1)
        # print(v2)
        # print(v2.standard_coordinates())

        # v2.change_to_basis(b3)
        # print(v2)
        # print(v2.standard_coordinates())

        # # print(v1.change_to_basis(b1))
        # # print(v1.change_to_basis(b2))

if __name__ == "__main__":
    unittest.main(defaultTest=["TestCase.test_basis_change2"])
