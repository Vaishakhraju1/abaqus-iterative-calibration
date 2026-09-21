"""Bounded scalar calibration, independent of the solver."""
import math


def calibrate(evaluate, lower, upper, target, tolerance, max_evaluations=25):
    """Find a bracketed target by bisection; return parameter, response and history.

    evaluate(parameter, evaluation_number) must return a finite scalar response.
    A continuous response is required; monotonicity is recommended. Convergence
    is measured in response units, not parameter units.
    """
    if not all(math.isfinite(v) for v in (lower, upper, target, tolerance)):
        raise ValueError('Bounds, target and tolerance must be finite')
    if not 0 < lower < upper or target <= 0 or tolerance <= 0:
        raise ValueError('Require 0 < lower < upper and positive target/tolerance')
    if not isinstance(max_evaluations, int) or max_evaluations < 2:
        raise ValueError('At least two evaluations are required')
    history = []

    def sample(parameter):
        response = float(evaluate(parameter, len(history) + 1))
        if not math.isfinite(response):
            raise ValueError('Solver returned a non-finite response')
        history.append((parameter, response))
        return response, response - target

    low_response, low_error = sample(lower)
    if abs(low_error) <= tolerance:
        return lower, low_response, history
    high_response, high_error = sample(upper)
    if abs(high_error) <= tolerance:
        return upper, high_response, history
    if (low_error > 0) == (high_error > 0):
        raise ValueError('Target is not bracketed by responses at the bounds')
    while len(history) < max_evaluations:
        middle = lower + (upper - lower) / 2.0
        if middle == lower or middle == upper:
            raise RuntimeError('Parameter resolution exhausted before convergence')
        response, error = sample(middle)
        if abs(error) <= tolerance:
            return middle, response, history
        if (error > 0) == (low_error > 0):
            lower, low_error = middle, error
        else:
            upper = middle
    raise RuntimeError('Maximum evaluations reached without convergence')


def relative_displacement(values, first, second):
    """Magnitude of U(first)-U(second), using (instance, node label) keys."""
    if first == second:
        raise ValueError('Choose two different nodes')
    selected = {}
    for instance, label, components in values:
        key = (instance, label)
        if key not in (first, second):
            continue
        if key in selected:
            raise ValueError('Duplicate displacement record for selected node')
        components = tuple(float(value) for value in components)
        if len(components) != 3 or not all(math.isfinite(v) for v in components):
            raise ValueError('Expected three finite displacement components')
        selected[key] = components
    if first not in selected or second not in selected:
        raise ValueError('Selected node displacement is missing')
    return math.sqrt(sum((a - b) ** 2 for a, b in zip(selected[first], selected[second])))


def render_input(template, modulus):
    if not math.isfinite(modulus) or modulus <= 0:
        raise ValueError('Young modulus must be positive and finite')
    if template.count('{{YOUNGS_MODULUS}}') != 1:
        raise ValueError('Template must contain exactly one Young modulus marker')
    result = template.replace('{{YOUNGS_MODULUS}}', format(modulus, '.15g'))
    if '{{' in result or '}}' in result:
        raise ValueError('Unresolved template marker')
    return result
