import math

def error_metrics(reference, approximation, zero_tolerance=1e-30):
    if len(reference) != len(approximation):
        raise ValueError("Vetores de tamanhos diferentes")
    absolute, relative = [], []
    for ref, approx in zip(reference, approximation):
        ae = abs(float(approx) - float(ref))
        absolute.append(ae)
        if abs(float(ref)) > zero_tolerance:
            relative.append(ae / abs(float(ref)))
    def summary(values):
        if not values:
            return {"mean": None, "max": None, "count": 0}
        return {"mean": sum(values)/len(values), "max": max(values), "count": len(values)}
    return {"absolute": summary(absolute), "relative": summary(relative),
            "relative_omitted_near_zero": len(reference)-len(relative)}
