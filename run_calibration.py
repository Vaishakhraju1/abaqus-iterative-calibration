"""Run a synthetic analytical demo or calibrate through Abaqus/CAE."""
import argparse
import csv
import json
import math
from pathlib import Path
import sys
import uuid

sys.path.insert(0, str(Path(__file__).resolve().parent))
from calibration import calibrate, render_input


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--mode', choices=('demo', 'abaqus'), default='demo')
    parser.add_argument('--lower', type=float, default=1000.0)
    parser.add_argument('--upper', type=float, default=3000.0)
    parser.add_argument('--target', type=float, default=0.005)
    parser.add_argument('--tolerance', type=float, default=1e-6)
    parser.add_argument('--max-evaluations', type=int, default=25)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--template', type=Path)
    parser.add_argument('--step', default='LoadStep')
    parser.add_argument('--instance-a', default='BAR-1')
    parser.add_argument('--node-a', type=int, default=1)
    parser.add_argument('--instance-b', default='BAR-1')
    parser.add_argument('--node-b', type=int, default=2)
    parser.add_argument('--cpus', type=int, default=1)
    args = parser.parse_args(argv)
    if args.cpus < 1 or min(args.node_a, args.node_b) < 1:
        parser.error('CPU count and node labels must be positive')
    if args.mode == 'demo' and args.template is not None:
        parser.error('Demo mode uses the bundled bar example; custom templates require Abaqus mode')
    template_path = args.template or Path(__file__).parent / 'example.inp.template'
    template = template_path.read_text(encoding='utf-8')
    render_input(template, args.lower)
    run_id = uuid.uuid4().hex[:10]
    output = (args.output or Path('runs') / run_id).resolve()
    # A fresh output directory prevents overwriting an earlier run or source data.
    output.mkdir(parents=True, exist_ok=False)
    metadata = dict(mode=args.mode, lower=args.lower, upper=args.upper,
                    target=args.target, tolerance=args.tolerance,
                    max_evaluations=args.max_evaluations, cpus=args.cpus,
                    step=args.step, first=[args.instance_a, args.node_a],
                    second=[args.instance_b, args.node_b], status='running')
    (output / 'template.inp.txt').write_text(template, encoding='utf-8')
    (output / 'run.json').write_text(json.dumps(metadata, indent=2), encoding='utf-8')
    try:
        with (output / 'history.csv').open('w', newline='', encoding='utf-8') as history:
            writer = csv.writer(history)
            writer.writerow(('evaluation', 'youngs_modulus', 'relative_displacement', 'error', 'mode'))
            def evaluate(modulus, number):
                iteration = output / ('evaluation_%03d' % number)
                iteration.mkdir()
                job_name = 'cal_%s_%03d' % (run_id, number)
                inp = iteration / (job_name + '.inp')
                inp.write_text(render_input(template, modulus), encoding='utf-8')
                if args.mode == 'demo':
                    # Synthetic linear axial bar: F=1 N, L=10 mm, A=1 mm^2.
                    response = 10.0 / modulus
                else:
                    from abaqus_runner import run_and_measure
                    response = run_and_measure(inp, job_name, args.step,
                        (args.instance_a, args.node_a), (args.instance_b, args.node_b), args.cpus)
                if not math.isfinite(response):
                    raise ValueError('Non-finite solver response')
                writer.writerow((number, modulus, response, response - args.target, args.mode))
                history.flush()
                return response
            modulus, response, samples = calibrate(evaluate, args.lower, args.upper,
                args.target, args.tolerance, args.max_evaluations)
        metadata.update(status='converged', youngs_modulus=modulus,
                        response=response, evaluations=len(samples))
    except Exception as error:
        metadata.update(status='failed', error=str(error))
        raise
    finally:
        (output / 'run.json').write_text(json.dumps(metadata, indent=2), encoding='utf-8')
    print('%s: E=%.8g, relative displacement=%.8g (%d evaluations)' %
          (args.mode, modulus, response, len(samples)))
    print('Results:', output)


if __name__ == '__main__':
    arguments = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else sys.argv[1:]
    main(arguments)
