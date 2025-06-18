""" 
  Script para crear los knobs en las preferencias.
  Lo use porque aunque me aparecian las prefs no se guardaban en el archivo de settings
"""

import nuke

def create_backdrop_preferences():
    p = nuke.toNode('preferences')
    
    color_options = ["Random"] + list(range(256))  # Opciones de color simples para este ejemplo
    
    try:
        if p.knob("Oz_Backdrop_Appearance"):
            print("Knobs already exist")
            return
    except:
        pass

    try:
        k = nuke.Tab_Knob("Oz_Backdrop", "Oz Backdrop")
        k.setFlag(nuke.ALWAYS_SAVE)
        p.addKnob(k)

        k = nuke.Enumeration_Knob("Oz_Backdrop_Appearance", "Appearance", ["Fill", "Border"])
        k.setFlag(nuke.ALWAYS_SAVE)
        p.addKnob(k)

        k = nuke.Enumeration_Knob("Oz_Backdrop_color", "Backdrop color", color_options)
        k.setFlag(nuke.ALWAYS_SAVE)
        p.addKnob(k)

        k = nuke.Enumeration_Knob("Oz_Backdrop_text_alignment", "Text alignment", ["left", "center", "right"])
        k.setFlag(nuke.ALWAYS_SAVE)
        p.addKnob(k)

        k = nuke.Double_Knob("Oz_Backdrop_font_size", "Font Size")
        k.setFlag(nuke.ALWAYS_SAVE)
        k.setRange(10, 128)
        k.setValue(50)
        p.addKnob(k)

        k = nuke.Double_Knob("Oz_Backdrop_margin", "Inner Margin")
        k.setFlag(nuke.ALWAYS_SAVE)
        k.setRange(10, 100)
        k.setValue(50)
        p.addKnob(k)

        k = nuke.Boolean_Knob("Oz_Backdrop_bold", "Bold Text")
        k.setFlag(nuke.ALWAYS_SAVE)
        p.addKnob(k)
        print("Knobs created")
    except Exception as e:
        print("Error creating knobs:", e)

create_backdrop_preferences()

"""
>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
Este es otro script, para leer/chequear que esas prefs existan
>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
"""

import nuke
import time

def get_preference_value(pref_name, default_value):
    preferences = nuke.toNode('preferences')
    if preferences:
        try:
            return preferences[pref_name].value()
        except:
            return default_value
    else:
        return default_value

# Intentar obtener el nodo de preferencias varias veces con un retraso
preferences = None
for _ in range(5):  # Intentar 5 veces
    preferences = nuke.toNode('preferences')
    if preferences:
        break
    time.sleep(0.5)  # Esperar medio segundo antes de intentar nuevamente

# Si no se pudo obtener el nodo de preferencias, usar valores por defecto
if preferences:
    try:
        appearance_value = preferences['Oz_Backdrop_Appearance'].value()
        default_color = preferences['Oz_Backdrop_color'].value()
        alignment_value = preferences['Oz_Backdrop_text_alignment'].value()
        note_font_size = int(preferences['Oz_Backdrop_font_size'].value())
        margin_value = int(preferences['Oz_Backdrop_margin'].value())
        bold_value = preferences['Oz_Backdrop_bold'].value()
        print("Appearance:", appearance_value)
        print("Default Color:", default_color)
        print("Alignment:", alignment_value)
        print("Font Size:", note_font_size)
        print("Margin:", margin_value)
        print("Bold:", bold_value)
    except Exception as e:
        print("Error reading preferences:", e)
else:
    print("Preferences node not found")
