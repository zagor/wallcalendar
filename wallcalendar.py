from PIL import Image, ImageDraw
import locale
import cal
import color
import indoor
import outdoor

xsize = 1280
ysize = 800

locale.setlocale(locale.LC_TIME, 'sv_SE.utf8')

image = Image.new(mode='RGB', size=(xsize, ysize), color=color.white)
draw = ImageDraw.Draw(image)

cal.Calendar(draw, xsize, ysize).render()
indoor.Indoor(draw).render()
outdoor.Outdoor(draw).render()

image.save("wallcalendar.png")
