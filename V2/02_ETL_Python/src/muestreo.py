"""Cuotas enteras y seleccion independientes del orden fisico."""
import hashlib
from collections import defaultdict
from comun import js, require

def select(candidates, quota, seed):
    groups = defaultdict(list)
    for record in candidates:
        groups[record["entity"]].append(record)
    require(len(groups) <= quota <= len(candidates), "Cuota inviable")
    remaining = quota - len(groups)
    weight = len(candidates) - len(groups)
    quotas = {key: 1 for key in groups}
    residues = []
    if weight:
        for key, group in groups.items():
            base, residue = divmod(remaining * (len(group) - 1), weight)
            quotas[key] += base
            residues.append((-residue, key))
        for _, key in sorted(residues)[:quota - sum(quotas.values())]:
            quotas[key] += 1
    selected = []
    for key in sorted(groups):
        group = groups[key]
        for record in group:
            record["priority"] = hashlib.sha256((seed + "\n" + record["canonical"]).encode("utf-8")).hexdigest()
        chosen = sorted(group, key=lambda r: (r["priority"], r["canonical"]))[:quotas[key]]
        for record in chosen:
            selected.append({**record, "population": len(group), "quota": quotas[key]})
    require(len(selected) == quota, "Cuota incompleta")
    return sorted(selected, key=lambda r: r["canonical"])
