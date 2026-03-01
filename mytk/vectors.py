import unittest
from math import sqrt


def same_basis(e1, e2):
    """Return True if two elements share the same basis."""
    if e1.basis is None and e2.basis is not None:
        return e2.basis.is_standard_basis
    elif e2.basis is None and e1.basis is not None:
        return e1.basis.is_standard_basis

    return e1.basis == e2.basis


def is_standard_basis(basis):
    """Return True if the basis is None or is the standard (identity) basis."""
    if basis is None:
        return True

    return basis.is_standard_basis


def same_origin(e1, e2):
    """Return True if two elements share the same origin."""
    return e1.origin == e2.origin


class PointDefault:
    """Context manager to temporarily override the default basis for Points."""

    def __init__(self, basis=None):
        self.save_default_basis = Point.default_basis
        Point.default_basis = basis

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        Point.default_basis = self.save_default_basis


class Vector:
    """Two-dimensional vector with optional basis for coordinate transformations."""

    def __init__(self, *args, basis=None):
        self.components = args
        self.basis = basis

    @property
    def c0(self):
        """Return the first component of the vector."""
        return self.components[0]

    @property
    def c1(self):
        """Return the second component of the vector."""
        return self.components[1]

    def __repr__(self):
        return str(self)

    def __str__(self):
        basis_str = ""
        if self.basis is not None and not self.basis.is_standard_basis:
            basis_str = f" basis=[{self.basis.e0}, {self.basis.e1}]"

        return f"V({self.c0:.1f}, {self.c1:.1f}){basis_str}"

    def __add__(self, rhs: "Vector"):
        if same_basis(self, rhs):
            return Vector(self.c0 + rhs.c0, self.c1 + rhs.c1, basis=self.basis)
        else:
            u = self.standard_coordinates()
            v = rhs.standard_coordinates()
            c0 = u.c0 + v.c0
            c1 = u.c1 + v.c1

            return Vector(c0, c1)

    def __radd__(self, rhs):
        return self.__add__(rhs)

    def __sub__(self, rhs: "Vector"):
        if same_basis(self, rhs):
            return Vector(self.c0 - rhs.c0, self.c1 - rhs.c1, basis=self.basis)
        else:
            u = self.standard_coordinates()
            v = rhs.standard_coordinates()
            c0 = u.c0 - v.c0
            c1 = u.c1 - v.c1

            return Vector(c0, c1)

    def __mul__(self, scalar):
        return Vector(self.c0 * scalar, self.c1 * scalar, basis=self.basis)

    def __rmul__(self, scalar):
        return self.__mul__(scalar)

    def __truediv__(self, scalar):
        return Vector(self.c0 / scalar, self.c1 / scalar, basis=self.basis)

    def __eq__(self, rhs: "Vector"):
        assert isinstance(rhs, Vector)

        return self.components == rhs.components and self.basis == rhs.basis

    @property
    def length(self):
        """Return the Euclidean length of the vector in standard coordinates."""
        v = self.standard_coordinates()
        return sqrt(v.c0 * v.c0 + v.c1 * v.c1)

    @property
    def is_unitary(self):
        """Return True if the vector has unit length within floating-point tolerance."""
        return abs(self.length - 1.0) < 1e-6

    def is_perpendicular(self, rhs):
        """Return True if this vector is perpendicular to rhs."""
        return abs(self.dot(rhs)) < 1e-6

    def dot(self, rhs: "Vector"):
        """Compute the dot product with another vector in the same basis."""
        assert same_basis(self, rhs)
        return self.c0 * rhs.c0 + self.c1 * rhs.c1

    def normalized(self):
        """Return a unit-length vector in the same direction and basis."""
        inv_l = 1.0 / self.length
        return Vector(self.c0 * inv_l, self.c1 * inv_l, basis=self.basis)

    def scaled(self, scale):
        """Return a new vector with each component multiplied by the corresponding scale factor."""
        return Vector(self.c0 * scale[0], self.c1 * scale[1], basis=self.basis)

    def in_basis(self, new_basis):
        """Express this vector in a different basis by projection."""
        v = self.standard_coordinates()
        e0, e1 = (new_basis.e0, new_basis.e1)

        c0 = v.dot(e0) / (e0.length * e0.length)
        c1 = v.dot(e1) / (e1.length * e1.length)

        return Vector(c0, c1, basis=new_basis)

    def change_basis(self, new_basis):
        """Re-express this vector in-place in the given basis."""
        v = self.in_basis(new_basis)

        self.components = (v.c0, v.c1)
        self.basis = v.basis

        return self

    def standard_tuple(self):
        """Return the components as a tuple in the standard basis."""
        p = self.standard_coordinates()
        return p.components

    def standard_coordinates(self):
        """Return an equivalent vector expressed in the standard basis."""
        if self.basis is None:
            return self

        assert self.basis.e0.basis is None
        assert same_basis(self.basis.e0, self.basis.e1)

        return self.c0 * self.basis.e0 + self.c1 * self.basis.e1


x̂ = Vector(1, 0, basis=None)
ŷ = Vector(0, 1, basis=None)


class Point:
    """Two-dimensional point with basis and optional reference point for coordinate transforms."""

    default_basis = None

    def __init__(self, *args, basis: "Basis" = None, reference_point: "Point" = None):
        assert isinstance(args, tuple)
        assert len(args) == 2
        self.components = args
        if basis is None:
            if Point.default_basis is not None:
                basis = Basis(Point.default_basis.e0, Point.default_basis.e1)
            else:
                basis = Basis()

        self.basis = basis

        self.reference_point = reference_point

    @property
    def x(self):
        """Return the x (first) coordinate."""
        return self.c0

    @property
    def y(self):
        """Return the y (second) coordinate."""
        return self.c1

    @property
    def c0(self):
        """Return the first component of the point."""
        return self.components[0]

    @property
    def c1(self):
        """Return the second component of the point."""
        return self.components[1]

    def is_same_as(self, rhs):
        """Return True if this point is equal to rhs."""
        assert isinstance(rhs, Point)
        return self.__eq__(rhs)

    def __eq__(self, rhs: "Point"):
        assert isinstance(rhs, Point)

        c0_equality = abs(self.components[0] - rhs.components[0]) < 1e-6
        c1_equality = abs(self.components[1] - rhs.components[1]) < 1e-6

        return c0_equality and c1_equality and self.basis == rhs.basis

    def __repr__(self):
        return str(self)

    def __str__(self):
        basis_str = ""
        ref_str = ""
        if not self.basis.is_standard_basis:
            basis_str = f" basis=[{self.basis.e0}, {self.basis.e1}]"
        if self.reference_point is not None:
            ref_str = f" ref=P({self.reference_point.x}, {self.reference_point.y})"

        return f"P({self.x:.1f}, {self.y:.1f}){basis_str}{ref_str}"

    def __sub__(self, rhs: "Point"):
        # assert isinstance(rhs, Point)
        # assert same_basis(self, rhs)

        if same_basis(self, rhs):
            c0 = self.c0 - rhs.c0
            c1 = self.c1 - rhs.c1
            return Vector(c0, c1, basis=self.basis)
        else:
            u = self.standard_coordinates()
            v = rhs.standard_coordinates()
            c0 = u.c0 - v.c0
            c1 = u.c1 - v.c1

            return Vector(c0, c1)

    def __add__(self, rhs: "Vector"):
        # assert isinstance(rhs, Vector)
        if same_basis(self, rhs):
            return Point(
                self.c0 + rhs.c0,
                self.c1 + rhs.c1,
                basis=self.basis,
                reference_point=self.reference_point,
            )
        else:
            u = self.standard_coordinates()
            v = rhs.standard_coordinates()

            return Point(
                u.c0 + v.c0,
                u.c1 + v.c1,
                basis=u.basis,
                reference_point=self.reference_point,
            )

    def standard_tuple(self):
        """Return the components as a tuple in the standard basis."""
        p = self.standard_coordinates()
        return p.components

    def standard_coordinates(self):
        """Return an equivalent point expressed in the standard basis."""
        if self.basis.is_standard_basis and self.reference_point is None:
            return self

        assert is_standard_basis(
            self.basis.e0.basis
        )  # For now, hopefully anything later
        assert is_standard_basis(self.basis.e1.basis)

        reference_point = self.reference_point
        if reference_point is None:
            reference_point = Point(0, 0)

        reference_point = reference_point.standard_coordinates()
        e0 = self.basis.e0.standard_coordinates()
        e1 = self.basis.e1.standard_coordinates()
        v = reference_point + self.c0 * e0 + self.c1 * e1
        return Point(*v.components)

    def in_reference_frame(self, basis, new_reference_point):
        """Express this point in a new reference frame defined by basis and origin."""
        pt = self.standard_coordinates()
        ref_point = new_reference_point.standard_coordinates()
        vector_position = pt - ref_point

        position_vector = vector_position.in_basis(basis)
        return Point(
            *position_vector.components,
            basis=basis,
            reference_point=new_reference_point,
        )


class Basis:
    """Orthogonal 2D basis defined by two vectors, defaulting to the standard basis."""

    defined = {}

    def __init__(self, e0: Vector = None, e1: Vector = None):
        """Initialize with two basis vectors, defaulting to the standard basis."""
        if e0 is None:
            e0 = x̂
        if e1 is None:
            e1 = ŷ

        assert e0.basis is None
        assert e1.basis is None
        assert e0.is_perpendicular(e1)
        assert e0.length > 0
        assert e1.length > 0

        self._e0 = e0
        self._e1 = e1

    @property
    def e0(self):
        """Return the first basis vector."""
        return self._e0

    @property
    def e1(self):
        """Return the second basis vector."""
        return self._e1

    def __eq__(self, rhs: "Basis"):
        assert isinstance(rhs, Basis)

        e0_c0_equality = abs(self.e0.components[0] - rhs.e0.components[0]) < 1e-6
        e0_c1_equality = abs(self.e0.components[1] - rhs.e0.components[1]) < 1e-6

        e1_c0_equality = abs(self.e1.components[0] - rhs.e1.components[0]) < 1e-6
        e1_c1_equality = abs(self.e1.components[1] - rhs.e1.components[1]) < 1e-6

        return e0_c0_equality and e0_c1_equality and e1_c0_equality and e1_c1_equality

    def __repr__(self):
        return str(self)

    def __str__(self):
        return f"[{self.e0}, {self.e1}]"

    @property
    def is_standard_basis(self):
        """Return True if this is the standard Cartesian basis."""
        return self.e0.is_unitary and self.e0.c1 == 0 and self.e1.is_unitary and self.e1.c0 == 0

    @property
    def is_orthogonal(self):
        """Return True if the two basis vectors are perpendicular."""
        return self.e0.is_perpendicular(self.e1)

    @property
    def is_orthonormal(self):
        """Return True if the basis is orthogonal and both vectors are unitary."""
        if self.is_orthonormal:
            return self.e0.is_unitary and self.e1.is_unitary

class DynamicBasis(Basis):
    """Basis that reads its vectors dynamically from an attribute on a source object."""

    def __init__(self, source, basis_name):
        self.source = source
        self.basis_name = basis_name

    @property
    def e0(self):
        """Return the first basis vector resolved from the source at access time."""
        basis = getattr(self.source, self.basis_name)
        if basis is None:
            raise ValueError('Basis {self.basis_name} from {self.source} not found')
        return basis.e0

    @property
    def e1(self):
        """Return the second basis vector resolved from the source at access time."""
        basis = getattr(self.source, self.basis_name)
        if basis is None:
            raise ValueError('Basis {self.basis_name} from {self.source} not found')
        return basis.e1

class Doublet(tuple):
    """Immutable two-element tuple with arithmetic operations for 2D math."""

    def __new__(cls, *args):
        """Create a new Doublet from two values or from a single iterable."""
        if len(args) == 2:
            return tuple.__new__(cls, args)
        else:
            return tuple.__new__(cls, tuple(*args))

    @property
    def x(self):
        """Return the first element."""
        return self[0]

    @property
    def y(self):
        """Return the second element."""
        return self[1]

    def __add__(self, rhs):
        return Doublet(self[0] + rhs[0], self[1] + rhs[1])

    def __radd__(self, rhs):
        return self.__add__(rhs)

    def __sub__(self, rhs):
        return Doublet(self[0] - rhs[0], self[1] - rhs[1])

    def __mul__(self, scalar):
        return Doublet(self[0] * scalar, self[1] * scalar)

    def __rmul__(self, scalar):
        return self.__mul__(scalar)

    def __truediv__(self, scalar):
        return Doublet(self[0] / scalar, self[1] / scalar)

    @property
    def length(self):
        """Return the Euclidean length."""
        return sqrt(self[0] * self[0] + self[1] * self[1])

    def dot(self, rhs):
        """Compute the dot product with another two-element sequence."""
        return self[0] * rhs[0] + self[1] * rhs[1]

    def normalized(self):
        """Return a unit-length doublet in the same direction."""
        inv_l = 1.0 / self.length()
        return Doublet(self[0] * inv_l, self[1] * inv_l)

    def scaled(self, scale):
        """Return a new doublet with each element multiplied by the corresponding scale factor."""
        return Doublet(self[0] * scale[0], self[1] * scale[1])


class ReferenceFrame:
    """Coordinate reference frame defined by a basis, scale, and origin point."""

    def __init__(self, basis=None, scale=None, reference_point: Point = None):
        assert basis is not None or scale is not None

        if basis is not None:
            self.basis = basis
        else:
            self.basis = Basis(Vector(scale[0], 0), Vector(0, scale[1]))
        assert is_standard_basis(
            reference_point.basis
        )  # We always provide origin in standard coordinates
        self.reference_point = reference_point

    @property
    def scale(self):
        """Return the scale factors as a tuple of basis vector lengths."""
        return (self.basis.e0.length, self.basis.e1.length)

    def convert_to_local(self, point: Point):
        """Convert a point from standard coordinates to local frame coordinates."""
        point.change_refence_frame(self.basis, self.origin_position)  # noqa: F821
        return self.origin + v  # noqa: F821

    def convert_to_canvas(self, local_point):
        """Convert a local-frame point to canvas (standard) coordinates."""
        x_c, y_c = (local_point[0] * self.scale[0], local_point[1] * self.scale[1])

        return self.origin + self.xHat * x_c + self.yHat * y_c

    def scale_to_canvas(self, size):
        """Scale a size tuple from local units to canvas units."""
        return (size[0] * abs(self.scale[0]), size[1] * abs(self.scale[1]))

    def scale_to_local(self, size):
        """Scale a size tuple from canvas units to local units."""
        return (size[0] / abs(self.scale[0]), size[1] / abs(self.scale[1]))

    @property
    def unit_vectors_scaled(self):
        """Return the unit vectors multiplied by their respective scale factors."""
        return self.xHat * self.scale[0], self.yHat * self.scale[1]

    @property
    def unit_vectors(self):
        """Return the unit vectors of the frame."""
        return self.xHat, self.yHat


class TestCase(unittest.TestCase):
    """Unit tests for Vector, Point, and Basis coordinate operations."""

    b1 = Basis()
    b2 = Basis(e0=Vector(2, 0), e1=Vector(0, 2))
    b3 = Basis(e0=Vector(1, -1), e1=Vector(1, 1))

    def test_point(self):
        """Test basic point creation and standard coordinate conversion."""
        p = Point(1, 2)
        print(p.standard_coordinates())
        p.move_origin(Point(1, 1))
        print(p)
        p.move_origin(Point(-10, -10))
        print(p)
        # print(p.standard_coordinates())

    def test_point_reference_frame_same_origin(self):
        """Test reference frame conversions with the origin at (0, 0)."""
        p0 = Point(1, 2)
        p1 = Point(1.0, 2.0)
        self.assertTrue(p0.is_same_as(p1))

        p2 = p0.in_reference_frame(self.b1, Point(0, 0))
        self.assertEqual(p2, Point(1, 2))
        self.assertEqual(
            p0.in_reference_frame(self.b3, Point(0, 0)).standard_coordinates(), p0
        )
        self.assertEqual(
            p0.in_reference_frame(self.b1, Point(0, 0)).standard_coordinates(), p0
        )
        self.assertEqual(
            p0.in_reference_frame(self.b1, Point(0, 0)).standard_coordinates(), p0
        )

    def test_point_reference_frame_new_origin(self):
        """Test reference frame conversions with a shifted origin."""
        p0 = Point(1, 2, reference_point=Point(1, 2))
        self.assertEqual(p0.standard_coordinates(), Point(2, 4))

        p2 = Point(1, 2, basis=self.b2, reference_point=Point(1, 1))
        self.assertEqual(p2.standard_coordinates(), Point(3, 5))

        p3 = Point(1, 2, basis=self.b3, reference_point=Point(1, 1))
        self.assertEqual(p3.standard_coordinates(), Point(4, 2))

    def test_point_reference_frame_new_origin_not_standard_coordinates(self):
        """Test reference frame with a non-standard-basis origin point."""
        p0 = Point(1, 2, reference_point=Point(1, 2, basis=self.b2))
        self.assertEqual(p0.standard_coordinates(), Point(3, 6))

        p0 = Point(
            1,
            2,
            reference_point=Point(1, 2, basis=self.b2, reference_point=Point(1, 2)),
        )
        self.assertEqual(p0.standard_coordinates(), Point(4, 8))

    def test_define_default_basis(self):
        """Test that PointDefault context manager sets a default basis."""
        b_local = Basis(e0=Vector(10, 0), e1=Vector(0, 30))

        points = []
        with PointDefault(points, basis=b_local):
            points.append(Point(0, 0))
            points.append(Point(10, 3))
            points.append(Point(10, 3))
            points.append(Point(10, 3))

        for point in points:
            self.assertTrue(point.basis == b_local)

    def test_define_default_reference(self):
        """Test that PointDefault context manager sets a default reference point."""
        ref = Point(1, 2)

        points = []
        with PointDefault(points, reference_point=ref):
            points.append(Point(0, 0))
            points.append(Point(10, 3))
            points.append(Point(10, 3))
            points.append(Point(10, 3))

        for point in points:
            self.assertTrue(point.reference_point == ref)

    def test_define_default(self):
        """Test PointDefault with both basis and reference point."""
        ref = Point(1, 2)
        b_local = Basis(e0=Vector(10, 0), e1=Vector(0, 30))

        points = []
        with PointDefault(points, basis=b_local, reference_point=ref):
            points.append(Point(0, 0))
            points.append(Point(10, 3))
            points.append(Point(10, 3))
            points.append(Point(10, 3))

        for point in points:
            self.assertTrue(point.reference_point == ref)

    def test_get_line_in_canvas_coordinates(self):
        """Test converting a sequence of local-basis points to standard coordinates."""
        b_local = Basis(e0=Vector(10, 0), e1=Vector(0, -30))

        points = []
        with PointDefault(points, basis=b_local, reference_point=Point(100, 300)):
            points.append(Point(0, 0))
            points.append(Point(10, 3))
            points.append(Point(20, -3))
            points.append(Point(60, 20))

        for point in [point.standard_coordinates() for point in points]:
            print(point)

    # def test_refrence_frame_origin(self):
    #     b1 = Basis(e0=Vector(1,0), e1=Vector(0,1))

    #     ref = ReferenceFrame(basis=b1, origin_position=Point(0,0))

    #     self.assertEqual(ref.convert_to_local(Point(0, 0)), (0, 0))
    #     self.assertEqual(ref.convert_to_local(Point(1, 1)), (1, -1))

    #     ref = ReferenceFrame(scale=(2, 2))
    #     self.assertEqual(ref.convert_to_local(Vector(0, 0)), (0, 0))
    #     self.assertEqual(ref.convert_to_local(Vector(1, 1)), (0.5, -0.5))

    #     ref = ReferenceFrame(scale=(10, 100))
    #     self.assertEqual(ref.convert_to_local(Vector(0, 0)), (0, 0))
    #     self.assertEqual(ref.convert_to_local(Vector(1, 1)), (0.1, -0.01))

    # def test_refrence_frame_new_origin(self):
    #     ref = ReferenceFrame(basis=Basis(), origin_position=Vector(1, 1))
    #     self.assertEqual(ref.convert_to_local(Vector(0, 0)), (-1, 1))
    #     self.assertEqual(ref.convert_to_local(Vector(1, 1)), (0, 0))

    #     ref = ReferenceFrame(scale=(2, 2), origin_position=Vector(1, 1))
    #     self.assertEqual(ref.convert_to_local(Vector(0, 0)), (-0.5, 0.5))
    #     self.assertEqual(ref.convert_to_local(Vector(1, 1)), (0, 0))

    #     ref = ReferenceFrame(scale=(10, 100), origin_position=Vector(1, 1))
    #     self.assertEqual(ref.convert_to_local(Vector(1, 1)), (0, 0))
    #     self.assertEqual(ref.convert_to_local(Vector(2, 2)), (0.1, -0.01))

    def test_point_subtraction(self):
        """Test that subtracting two points produces a Vector."""
        p1 = Point(1, 2)
        p2 = Point(3, 4)
        v = p2 - p1
        self.assertTrue(isinstance(v, Vector))

    def test_vector(self):
        """Test basic vector dot product computation."""
        v1 = Vector(1, 2)
        v2 = Vector(3, 4)
        print(v2.dot(v1))

    def test_basis(self):
        """Test point subtraction within a non-standard basis."""
        b = Basis(Vector(1, -1), Vector(1, 1))
        p1 = Point(1, 2, basis=b)
        p2 = Point(3, 4, basis=b)
        print(p2 - p1)

    def test_basis_change(self):
        """Test changing a vector from one basis to another."""
        b1 = Basis(e0=Vector(1, -1), e1=Vector(1, 1))
        _b2 = Basis()
        v1 = Vector(1, 2, basis=b1)
        print(v1)
        print(v1.standard_coordinates())

        print(v1.length)
        print(v1.standard_coordinates().length)

        print(v1.change_basis(b1).length)

        # print(v1.change_basis(b1))
        # print(v1.change_basis(b2))

    def test_basis_change2(self):
        """Test changing basis with a scaled (non-unitary) basis."""
        _b3 = Basis(e0=Vector(1, -1), e1=Vector(1, 1))
        b2 = Basis(e0=Vector(2, 0), e1=Vector(0, 2))
        b1 = Basis()
        v1 = Vector(1, 3, basis=b1)
        print(v1)
        print(v1.change_basis(b2))
        # print(v1.standard_coordinates())
        # v2 = Vector(0.5, 1, basis=b2)

        # print(v2)
        # print(v2.standard_coordinates())
        # v2.change_basis(b1)
        # print(v2)
        # print(v2.standard_coordinates())

        # v2.change_basis(b3)
        # print(v2)
        # print(v2.standard_coordinates())

        # # print(v1.change_basis(b1))
        # # print(v1.change_basis(b2))


if __name__ == "__main__":
    # unittest.main()
    unittest.main(defaultTest=["TestCase.test_get_line_in_canvas_coordinates"])
