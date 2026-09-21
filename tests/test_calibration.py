import unittest
from calibration import calibrate, relative_displacement, render_input


class CalibrationTests(unittest.TestCase):
    def test_synthetic_bar_converges(self):
        modulus, response, history = calibrate(lambda e, n: 10.0 / e,
            1000, 3000, 0.005, 1e-6)
        self.assertEqual(modulus, 2000)
        self.assertEqual(response, 0.005)
        self.assertEqual(len(history), 3)

    def test_direction_independent_bisection(self):
        modulus, _, _ = calibrate(lambda e, n: e * e, 1, 5, 9, 1e-8)
        self.assertEqual(modulus, 3)

    def test_unbracketed_and_nonfinite_responses(self):
        with self.assertRaises(ValueError):
            calibrate(lambda e, n: 1., 1, 5, 10, 0.01)
        with self.assertRaises(ValueError):
            calibrate(lambda e, n: float('nan'), 1, 5, 10, 0.01)

    def test_evaluation_limit(self):
        calls = []
        def evaluate(e, n):
            calls.append(e)
            return e
        with self.assertRaises(RuntimeError):
            calibrate(evaluate, 1, 5, 2.3, 1e-12, max_evaluations=3)
        self.assertEqual(len(calls), 3)

    def test_instance_qualified_relative_displacement(self):
        values = [('A', 1, (1, 2, 3)), ('B', 1, (4, 6, 3)), ('C', 1, (99, 99, 99))]
        self.assertEqual(relative_displacement(values, ('A', 1), ('B', 1)), 5.)
        with self.assertRaises(ValueError):
            relative_displacement(values[:1], ('A', 1), ('B', 1))

    def test_only_explicit_material_marker_changes(self):
        template = '*Elastic\n{{YOUNGS_MODULUS}}, 0.3\n*Elastic\n42, 0.2\n'
        self.assertEqual(render_input(template, 100), '*Elastic\n100, 0.3\n*Elastic\n42, 0.2\n')
        with self.assertRaises(ValueError):
            render_input(template * 2, 100)


if __name__ == '__main__':
    unittest.main()
