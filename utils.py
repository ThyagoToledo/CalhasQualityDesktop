# -*- coding: utf-8 -*-
"""
Funções utilitárias para formatação de dados
"""


def format_measure(measure):
    """
    Formata uma medida única.
    
    Args:
        measure: Valor numérico da medida
        
    Returns:
        String formatada da medida
    """
    if not measure or measure == 0:
        return "-"
    return f"{measure:.2f}m"


def format_dimensions(width, length):
    """
    Formata dimensões de largura e comprimento.
    
    Args:
        width: Largura em metros (float)
        length: Comprimento em metros (float)
        
    Returns:
        String formatada das dimensões (ex: "100 x 50")
    """
    if not width or width == 0:
        if not length or length == 0:
            return "-"
        return f"{length:.2f}m"
    
    if not length or length == 0:
        return f"{width:.2f}m"
    
    return f"{width:.2f} x {length:.2f}m"
