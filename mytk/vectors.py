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
    def __init__(self, scale:Vector, origin:Vector = None):
        """
        Scale is the length of the x and y unit vectors in canvas units
        """
        self.scale = scale

        if origin is None:
            origin = Vector(0,0)
        self.origin_in_canvas_coords = origin

    def convert_canvas_to_local(self, pt_canvas_coords):
        local_pt_in_canvas_coords = pt_canvas_coords - self.origin_in_canvas_coords
        return Vector(
            local_pt_in_canvas_coords[0]/self.scale[0], 
            local_pt_in_canvas_coords[1]/self.scale[1]
        )

    def convert_local_to_canvas(self, pt_local_coords):
        pt_canvas_coords = Vector(pt_local_coords[0]*self.scale[0],
                                  pt_local_coords[1]*self.scale[1])

        return pt_canvas_coords + self.origin_in_canvas_coords

    @property
    def unit_vectors(self):
        return Vector(self.scale[0], 0), Vector(0, self.scale[1])

class Test(unittest.TestCase):
    def test_refrence_frame_origin(self):
        ref = ReferenceFrame(scale=(1,1))
        self.assertEqual(ref.convert_canvas_to_local( Vector(0,0) ), (0,0) )
        self.assertEqual(ref.convert_canvas_to_local( Vector(1,1) ), (1,1) )

        ref = ReferenceFrame(scale=(2, 2))
        self.assertEqual(ref.convert_canvas_to_local( Vector(0,0) ), (0,0) )
        self.assertEqual(ref.convert_canvas_to_local( Vector(1,1) ), (0.5,0.5) )

        ref = ReferenceFrame(scale=(10, 100))
        self.assertEqual(ref.convert_canvas_to_local( Vector(0,0) ), (0,0) )
        self.assertEqual(ref.convert_canvas_to_local( Vector(1,1) ), (0.1, 0.01) )

    def test_refrence_frame_new_origin(self):
        ref = ReferenceFrame(scale=(1,1), origin=Vector(1,1))
        self.assertEqual(ref.convert_canvas_to_local( Vector(0,0) ), (-1,-1) )
        self.assertEqual(ref.convert_canvas_to_local( Vector(1,1) ), (0,0) )

        ref = ReferenceFrame(scale=(2, 2), origin=Vector(1,1))
        self.assertEqual(ref.convert_canvas_to_local( Vector(0,0) ), (-0.5, -0.5) )
        self.assertEqual(ref.convert_canvas_to_local( Vector(1,1) ), (0,0) )

        ref = ReferenceFrame(scale=(10, 100), origin=Vector(1,1))
        self.assertEqual(ref.convert_canvas_to_local( Vector(1,1) ), (0,0) )
        self.assertEqual(ref.convert_canvas_to_local( Vector(2,2) ), (0.1, 0.01) )

if __name__ == "__main__":
    unittest.main()