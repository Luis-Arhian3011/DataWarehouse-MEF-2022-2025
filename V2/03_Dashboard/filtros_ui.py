"""Selecciones opcionales: None=todas; ()=vacia tras un reajuste."""
def reajustar_seleccion(seleccion, disponibles, bloqueado=False):
    options=set(disponibles)
    valid=tuple(v for v in seleccion if v in options)
    removed=tuple(v for v in seleccion if v not in options)
    return valid,not valid and (bool(removed) or bloqueado),removed

def filtro_efectivo(seleccion,bloqueado):
    return tuple(seleccion) if seleccion else (() if bloqueado else None)
