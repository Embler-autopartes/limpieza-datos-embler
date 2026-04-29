"""
Orchestrator para procesar todas las categorias de ml_sin_match.
Usa EMBLER_HOJA env var para que los build_*.py escriban a new-output_v2/ml_sin_match/.
"""

import os
import subprocess
import sys

HOJA = "ml_sin_match"
ROOT = "new-output_v2"

CATEGORIAS = [
    ("herramientas", 10),
    ("tuning", 4),
    ("refacciones_clima", 2),
    ("refacciones_carroceria", 10),
    ("refacciones_transmision", 10),
    ("refacciones_electrico", 18),
    ("refacciones_frenos", 24),
    ("accesorios", 62),
    ("refacciones_otros", 63),
    ("otros", 68),
    ("refacciones_motor", 175),
    ("refacciones_suspension", 401),
]

BUILD_SCRIPT = {
    "herramientas": "build_herramientas_result_v2.py",
    "tuning": "build_tuning_result_v2.py",
    "otros": "build_otros_result_v2.py",
    "refacciones_clima": "build_clima_result_v2.py",
    "refacciones_transmision": "build_transmision_result_v2.py",
    "refacciones_electrico": "build_electrico_result_v2.py",
    "refacciones_carroceria": "build_carroceria_result_v2.py",
    "refacciones_frenos": "build_frenos_result_v2.py",
    "refacciones_otros": "build_refacciones_otros_result_v2.py",
    "refacciones_suspension": "build_suspension_result_v2.py",
    "refacciones_motor": "build_motor_result_v2.py",
    "accesorios": "build_accesorios_result_v2.py",
}


def run(cmd, env=None):
    full_env = os.environ.copy()
    if env:
        full_env.update(env)
    return subprocess.run(cmd, shell=True, env=full_env, capture_output=True, text=True)


def process_categoria(cat: str, total: int):
    print(f"\n=== {cat} ({total} filas) ===")
    BATCH = 50
    starts = list(range(0, total, BATCH))
    env = {"EMBLER_HOJA": HOJA}

    for inicio in starts:
        cantidad = min(BATCH, total - inicio)
        # Prep
        r = run(
            f"python scripts/02_preparar_batch_v2.py {cat} {inicio} {cantidad} {HOJA} {ROOT}",
            env=env,
        )
        if r.returncode != 0:
            print(f"  PREP FAIL @ {inicio}: {r.stderr}")
            return
        # Build
        r = run(f"python scripts/{BUILD_SCRIPT[cat]}", env=env)
        if r.returncode != 0:
            print(f"  BUILD FAIL @ {inicio}: {r.stderr}")
            return
        # Save
        r = run(
            f"python scripts/03_guardar_batch_v2.py {cat} {ROOT}/{HOJA}/{cat}_batch_result.json {HOJA} {ROOT}",
            env=env,
        )
        if r.returncode != 0:
            print(f"  SAVE FAIL @ {inicio}: {r.stderr}")
            return
        # Show progress
        last_line = r.stdout.strip().splitlines()[-1] if r.stdout.strip() else ""
        print(f"  batch {inicio}-{inicio+cantidad-1}: {last_line}")


def main():
    for cat, total in CATEGORIAS:
        process_categoria(cat, total)
    print("\n=== TODO COMPLETO ===")


if __name__ == "__main__":
    main()
