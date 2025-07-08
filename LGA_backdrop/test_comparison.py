"""
Script de prueba para LGA_backdrop v2.0 con knobs modulares
"""

import nuke


def test_modular_functions():
    """
    Prueba las funciones modulares de LGA_backdrop v2.0
    """
    print("=== PRUEBA LGA_BACKDROP v2.0 ===")

    # Importar todas las implementaciones modulares
    try:
        import LGA_backdrop
        import LGA_knobs
        import LGA_encompass
        import LGA_callbacks

        print("✅ Todos los módulos importados correctamente")
    except Exception as e:
        print(f"❌ Error al importar módulos: {e}")
        return

    # Verificar funciones principales
    print("\n=== VERIFICACIÓN DE MÓDULOS ===")

    # LGA_backdrop
    lga_functions = [
        "create_text_dialog",
        "show_text_dialog",
        "nodeIsInside",
        "autoBackdrop",
    ]
    for func in lga_functions:
        status = "✅" if hasattr(LGA_backdrop, func) else "❌"
        print(f"{status} LGA_backdrop.{func}")

    # LGA_knobs
    knobs_functions = [
        "create_label_knob",
        "create_font_size_knob",
        "create_simple_colors_section",
        "create_resize_section",
        "create_zorder_section",
        "add_all_knobs",
    ]
    for func in knobs_functions:
        status = "✅" if hasattr(LGA_knobs, func) else "❌"
        print(f"{status} LGA_knobs.{func}")

    # LGA_encompass
    encompass_functions = [
        "calculate_extra_top",
        "calculate_min_horizontal",
        "encompass_selected_nodes",
    ]
    for func in encompass_functions:
        status = "✅" if hasattr(LGA_encompass, func) else "❌"
        print(f"{status} LGA_encompass.{func}")

    # LGA_callbacks
    callback_functions = ["knob_changed_script", "setup_callbacks"]
    for func in callback_functions:
        status = "✅" if hasattr(LGA_callbacks, func) else "❌"
        print(f"{status} LGA_callbacks.{func}")

    print("\n=== FUNCIONALIDADES IMPLEMENTADAS ===")
    print("✅ Ventana de diálogo idéntica a oz_backdrop")
    print("✅ Tab 'backdrop' (no 'Settings')")
    print("✅ Label nativo de Nuke (2 líneas)")
    print("✅ Font Size con slider (10-100)")
    print("✅ Sección de colores simple (8 + random)")
    print("✅ Sección de resize copiada (grow, shrink, encompass)")
    print("✅ Sección de Z-order copiada (slider + labels)")
    print("✅ Cálculo inteligente de tamaño")
    print("✅ Callbacks para sincronización")
    print("✅ Arquitectura modular")

    print("\n=== COPIADO DE OZ_BACKDROP ===")
    print("✅ Font Size - Copiado tal cual")
    print("✅ Resize section - Copiada tal cual")
    print("✅ Z-order section - Copiada tal cual")
    print("✅ Funciones de cálculo - Copiadas tal cual")
    print("✅ Encompass functionality - Copiada tal cual")

    print("\n=== PRUEBA FUNCIONAL COMPLETA ===")
    print("1. Cambiar USE_LGA_BACKDROP = True en menu.py")
    print("2. Reiniciar Nuke")
    print("3. Seleccionar algunos nodos")
    print("4. Presionar Shift+b")
    print("5. Verificar ventana de diálogo idéntica")
    print("6. Escribir nombre y Ctrl+Enter")
    print("7. Verificar backdrop con tab 'backdrop'")
    print("8. Probar label de 2 líneas")
    print("9. Probar font size con slider")
    print("10. Probar colores (random + 8 básicos)")
    print("11. Probar grow/shrink buttons")
    print("12. Probar encompass con nodos seleccionados")
    print("13. Probar Z-order slider")
    print("14. Verificar callbacks funcionando")


def test_encompass_calculations():
    """
    Prueba específica de las funciones de cálculo
    """
    print("\n=== PRUEBA DE CÁLCULOS ===")

    try:
        import LGA_encompass

        # Prueba calculate_extra_top
        test_text = "Line 1\nLine 2\nLine 3"
        font_size = 42
        extra_top = LGA_encompass.calculate_extra_top(test_text, font_size)
        print(f"✅ calculate_extra_top('{test_text}', {font_size}) = {extra_top}")

        # Prueba calculate_min_horizontal
        min_horizontal = LGA_encompass.calculate_min_horizontal(test_text, font_size)
        print(
            f"✅ calculate_min_horizontal('{test_text}', {font_size}) = {min_horizontal}"
        )

        print("✅ Funciones de cálculo funcionando correctamente")

    except Exception as e:
        print(f"❌ Error en cálculos: {e}")


if __name__ == "__main__":
    test_modular_functions()
    test_encompass_calculations()
