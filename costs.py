"""Calculadora didactica. Tarifas ficticias, no cotizacion de AWS."""


def estimate_cost(hourly_rate, hours, instances):
    if min(hourly_rate, hours, instances) < 0:
        raise ValueError("Los valores no pueden ser negativos")
    return hourly_rate * hours + instances
