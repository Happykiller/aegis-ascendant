"""Bake portable artistic roughness and tangent normals from the generated metal scan."""
import bpy


def bake_maps(source,directory):
    original=bpy.context.window.scene
    temporary=bpy.data.scenes.new('TEMP | PBR baking')
    bpy.context.window.scene=temporary
    temporary.render.engine='CYCLES'
    temporary.cycles.samples=1
    bpy.ops.mesh.primitive_plane_add(size=2)
    plane=bpy.context.object
    material=bpy.data.materials.new('TEMP | map baker')
    material.use_nodes=True
    plane.data.materials.append(material)
    nodes=material.node_tree.nodes
    links=material.node_tree.links
    bsdf=nodes.get('Principled BSDF')
    output=nodes.get('Material Output')
    texture=nodes.new('ShaderNodeTexImage')
    texture.image=source
    bump=nodes.new('ShaderNodeBump')
    bump.inputs['Strength'].default_value=.16
    bump.inputs['Distance'].default_value=.012
    links.new(texture.outputs['Color'],bump.inputs['Height'])
    links.new(bump.outputs['Normal'],bsdf.inputs['Normal'])
    target=nodes.new('ShaderNodeTexImage')
    nodes.active=target
    maps={}
    for kind in ['normal','roughness']:
        image=bpy.data.images.new('LC | gunmetal '+kind,width=1254,height=1254,alpha=False)
        image.colorspace_settings.name='Non-Color'
        target.image=image
        if kind=='normal':
            bpy.ops.object.bake(type='NORMAL')
        else:
            gray=nodes.new('ShaderNodeRGBToBW')
            links.new(texture.outputs['Color'],gray.inputs[0])
            remap=nodes.new('ShaderNodeMapRange')
            remap.inputs['From Max'].default_value=.25
            remap.inputs['To Min'].default_value=.58
            remap.inputs['To Max'].default_value=.30
            links.new(gray.outputs[0],remap.inputs['Value'])
            emission=nodes.new('ShaderNodeEmission')
            links.new(remap.outputs[0],emission.inputs['Color'])
            links.new(emission.outputs[0],output.inputs['Surface'])
            bpy.ops.object.bake(type='EMIT')
        image.filepath_raw=str(directory/f'gunmetal_{kind}.png')
        image.file_format='PNG'
        image.save()
        image.pack()
        maps[kind]=image
    bpy.context.window.scene=original
    bpy.data.scenes.remove(temporary)
    bpy.data.objects.remove(plane,do_unlink=True)
    return maps
