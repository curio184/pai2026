import bpy
from pathlib import Path
bpy.ops.wm.open_mainfile(filepath=str(Path.cwd()/'assets/civic_realism/revision03.blend'))
for m in bpy.data.materials:
 if m.use_nodes:
  for n in m.node_tree.nodes:
   if n.type in ['VOLUME_SCATTER','VOLUME_PRINCIPLED']:print('VOLUME',m.name,n.name,[(i.name,str(i.default_value)) for i in n.inputs if i.name in ['Density','Color','Anisotropy']])