## to save backdrops default setting in nuke preferences
import nuke
from oz_colors import colors

def Oz_BackdropPreferencesCallback():
    p = nuke.toNode('preferences')
    
    color_options = [color for color,_ in colors.items()]
    color_options.insert(0, "Random")
    
    try:
        jopsKnobsPresent = p["Oz_Backdrop"]
        # Making sure that if new color options are added they also show up in
        # the settings.
        nuke.toNode('preferences')['Oz_Backdrop_color'].setValues(color_options)
    except (SyntaxError, NameError):
        k = nuke.Tab_Knob("Oz_Backdrop")
        k.setFlag(nuke.ALWAYS_SAVE)
        p.addKnob(k)
        
        k = nuke.Text_Knob('Oz_Backdrop_info1','<b>Defaults</b>')
        p.addKnob(k)
        
        options = ["Fill", "Border"]
        k = nuke.Enumeration_Knob("Oz_Backdrop_appearance", "Appearance", options)
        k.setFlag(nuke.ALWAYS_SAVE)
        #k.setValue(1.0)
        #k.setTooltip(" ")
        p.addKnob(k)

        k = nuke.Enumeration_Knob("Oz_Backdrop_color", "Backdrop color", color_options)
        k.setFlag(nuke.ALWAYS_SAVE)
        #k.setValue(1.0)
        #k.setTooltip(" ")
        p.addKnob(k)

        options = ["left", "center", "right"]
        k = nuke.Enumeration_Knob("Oz_Backdrop_text_alignment", "Text alignment", options)
        k.setFlag(nuke.ALWAYS_SAVE)
        #k.setValue(1.0)
        #k.setTooltip(" ")
        p.addKnob(k)
        
        k = nuke.Double_Knob("Oz_Backdrop_margin", "Inner Margin")
        k.setFlag(nuke.ALWAYS_SAVE)
        k.setRange(10, 100)
        k.setValue(50)
        #k.setTooltip(" ")
        p.addKnob(k)
        k.setValue(50)        

        k = nuke.Double_Knob("Oz_Backdrop_font_size", "Font Size")
        k.setFlag(nuke.ALWAYS_SAVE)
        k.setRange(10, 128)
        #k.setTooltip(" ")
        p.addKnob(k)
        k.setValue(50)

        k = nuke.Boolean_Knob("Oz_Backdrop_bold", "Bold Text")
        k.setFlag(nuke.ALWAYS_SAVE | nuke.STARTLINE)
        k.setTooltip("Set default text to bold")
        p.addKnob(k)



        # k = nuke.addButton("Oz_Backdrop_drop_recurse45", "Replace...")
        # k.setLabel("Click me!")
        # k.setTooltip(" ")
        # p.addKnob(k)
    

#Adding callbacks to ensure knobs added if needed, and interpreted. 
#Root is done to catch the case where there are no custom prefs,
#so no creation callback for it.
nuke.addOnCreate(Oz_BackdropPreferencesCallback, nodeClass='Preferences')
nuke.addOnCreate(Oz_BackdropPreferencesCallback, nodeClass='Root')