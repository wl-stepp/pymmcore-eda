import pyglet
import numpy as np
import tqdm

pyglet.resource.path.append('Assets')
pyglet.resource.reindex()

frames = 100
size = 2048
number_of_bytes = frames*size*size*3
image_size = size*size*3

array = np.random.randint(0, 255, (frames, size, size, 3), dtype=np.uint8)
textures = []

window = pyglet.window.Window(size, size, caption='check my Cube Maps')
frame = 0
pImg = pyglet.image.ImageData(size,size,'RGB',
       array[0].ravel(),pitch=size*3)


import time
t0 = 0
@window.event
def on_draw():
    global frame, t0
    print(1/(time.perf_counter()-t0))
    texture = np.ctypeslib.as_ctypes(array[frame].ravel())
    pImg.set_data('RGB', size*3, texture)

    # pImg.set_data('RGB', size*3, image_texture[frame*image_size:(frame+1)*image_size])

    window.clear()
    pImg.blit(0,0)

    frame += 1
    frame = frame % frames
    return

FRAMERATE = 1.0/60
pyglet.clock.schedule_interval(lambda dt: None, FRAMERATE)
pyglet.app.run()