try:
    node=nuke.thisNode()
    knob=nuke.thisKnob()
    name=knob.name()

    def updateKnobs():
        nodeWidth=node['bdwidth'].getValue()
        nodeHeight=node['bdheight'].getValue()
        node['sizeNode'].setValue([int(nodeWidth),int(nodeHeight)])
        node['node_position_x'].setValue(int(node['xpos'].value()))
        node['node_position_y'].setValue(int(node['ypos'].value()))
        node['zorder'].setValue(int(node['z_order'].getValue()))
        node['font_size'].setValue(int(node['note_font_size'].getValue()))
        node['oz_appearance'].setValue( node['appearance'].value() )
        node['oz_border_width'].setValue( node['border_width'].value() )
        #node['fontColor'].setValue(int(node['note_font_color'].getValue()))

    def updateLabelKnob():
        curLabel = node['label'].getValue()
        # Eliminar cualquier etiqueta HTML en el label (por si existen)
        curLabel = curLabel.replace('<p align=center>', '').replace('<p align=right>', '').replace('</p>', '').replace('<center>', '').replace('</center>', '')
        node['text'].setValue(curLabel)
        # Obtener la alineacion actual desde note_font_align
        alignment = int(node['note_font_align'].value())
        node['alignment'].setValue(alignment)


    ### OPENING SETUP
    if name=='showPanel':
        updateKnobs()
        updateLabelKnob()

    ### UPDATE STYLE
    if name in ['oz_appearance', 'oz_border_width']:
        node['appearance'].setValue( node['oz_appearance'].value() )
        node['border_width'].setValue( node['oz_border_width'].value() )

    ### CHANGE THE SIZE OF THE NODE
    if name=='sizeNode':
        node['bdwidth'].setValue(int(node['sizeNode'].getValue()[0]))
        node['bdheight'].setValue(int(node['sizeNode'].getValue()[1]))

    ### POSITION
    if name=='node_position_x' or name=='node_position_y':
        node.setXYpos(int(node['node_position_x'].getValue()),int(node['node_position_y'].getValue()))

    ### ZORDER
    if name=='zorder':
        node['z_order'].setValue(node['zorder'].getValue())

    ### UPDATE THE 'CURRENT SIZE' AND ORDER
    #if name=='bdwidth' or name=='bdheight' or name=='z_order':
    if name in ['bdwidth', 'bdheight', 'z_order']:
        updateKnobs()

    ### UPDATE LABEL
    title = node['name'].value()
    text = node['text'].value()

    if name in ['text', 'alignment', 'title', 'Oz_Backdrop_bold', 'note_font_color']:
        text = node['text'].value()
        alignment = node['alignment'].getValue()
        is_bold = node['Oz_Backdrop_bold'].value()

        # Establece el texto del label sin etiquetas HTML
        node['label'].setValue(text)

        # Establece la alineacion del texto usando la propiedad note_font_align
        node['note_font_align'].setValue(alignment)  # 0: izquierda, 1: centro, 2: derecha

        # Captura la fuente actual y muestra en consola
        current_font = node['note_font'].value()
        #print(f"Fuente antes de cambiar: {current_font}")

        # Solo proceder si current_font tiene un valor valido
        if current_font:
            font_family = current_font.replace(" Bold", "").strip()

            # Modifica la fuente segun el estado del checkbox de bold
            if is_bold:
                new_font = f"{font_family} Bold"
            else:
                new_font = font_family

            # Aplicar el nuevo valor de la fuente
            node['note_font'].setValue(new_font)
            #print(f"Fuente despues de cambiar: {new_font}")

        # Ya no es necesario actualizar el label nuevamente con newLabel
        # node['label'].setValue(newLabel)





    if name=="font_size":
        new_font_size = node["font_size"].value()
        node['note_font_size'].setValue(new_font_size)



    del newLabel

except:
    pass
