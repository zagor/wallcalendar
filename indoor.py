import datetime
import math
from PIL import ImageDraw, ImageFont

import color
import homeassistant
from config import Config


class Indoor:
    def __init__(self, draw: ImageDraw):
        self.draw: ImageDraw = draw
        self.config = Config().get(__class__.__name__)
        self.font = '/usr/share/fonts/truetype/msttcorefonts/verdana.ttf'
        self.xpos = 0
        self.ypos = 10
        self.width = 200
        self.height = 100
        self.pixels_per_second = 0.0
        self.pixels_per_degree = 0.0
        self.min_temp = 1000.0
        self.max_temp = -1000.0

    @staticmethod
    def find_range(data: dict) -> (int, int):
        min_temp = 100
        max_temp = -100
        for entity in data:
            for entry in entity:
                state: str = entry['state']
                if state.startswith('u'):  # unknown or unavailable
                    continue
                temp = float(state)
                if temp > max_temp:
                    max_temp = temp
                if temp < min_temp:
                    min_temp = temp
        return min_temp, max_temp

    def background(self, start_time: datetime.datetime, end_time: datetime.datetime):
        x = self.xpos
        y = self.ypos
        w = self.width
        h = self.height
        self.draw.line((x + w, y, x + w, y + h), fill=color.mgray, width=1)
        self.draw.line((x, y + h, x + w, y + h), fill=color.mgray, width=1)
        f = ImageFont.truetype(self.font, 9)
        _, _, _, font_height = f.getbbox('0.0')
        self.draw.text((x + w + 1, y - font_height / 2), f'{self.max_temp}', font=f, fill=color.dgray)
        self.draw.text((x + w + 1, y + h - font_height / 2), f'{self.min_temp}', font=f, fill=color.dgray)
        for t in range(math.floor(self.min_temp), math.ceil(self.max_temp)):
            if self.min_temp < t < self.max_temp:
                temp_offset = (t - self.min_temp) * self.pixels_per_degree
                self.draw.line((x, y + h - temp_offset, x + w, y + h - temp_offset), fill=color.lred, width=1)
        vertical = start_time.astimezone()
        vertical = vertical.replace(second=0, minute=0, hour=vertical.hour - (vertical.hour % 6))
        vertical += datetime.timedelta(hours=6)
        f = ImageFont.truetype(self.font, 11)
        text_width = f.getlength('00')
        while vertical < end_time.astimezone():
            time_offset = (vertical - start_time).total_seconds() * self.pixels_per_second
            self.draw.line((x + time_offset, y, x + time_offset, y + h), fill=color.lgray, width=1)
            self.draw.text((x + time_offset - text_width/2, y + h), f'{vertical.hour:02d}', font=f, fill=color.dgray)
            vertical += datetime.timedelta(hours=6)

    def render(self):
        data = homeassistant.get_history(self.config['entities'].keys())
        self.min_temp, self.max_temp = self.find_range(data)
        end_time = datetime.datetime.now(datetime.timezone.utc)
        start_time = end_time - datetime.timedelta(days=1)
        self.pixels_per_second = self.width / 86400
        self.pixels_per_degree = self.height / (self.max_temp - self.min_temp)
        self.background(start_time, end_time)
        incolor = [color.red, color.blue, color.green, color.orange, color.lilac, color.dgray, color.black]
        f = ImageFont.truetype(self.font, 8)
        for entity in data:
            coordinates = []
            lasty = 0
            lasttemp = 0
            tcolor = incolor.pop(0)
            for entry in entity:
                state: str = entry['state']
                if state.startswith('u'):  # unknown or unavailable
                    continue
                temp = float(state)
                if not temp:
                    continue
                change_time = datetime.datetime.fromisoformat(entry['last_changed'])
                x = (change_time - start_time).total_seconds() * self.pixels_per_second
                y = self.height - ((temp - self.min_temp) * self.pixels_per_degree)
                coordinates.append((x + self.xpos, y + self.ypos))
                lasty = y
                lasttemp = temp
            self.draw.line(coordinates, fill=tcolor, width=1)
            string = f"{lasttemp} {self.config['entities'][entity[0]['entity_id']]}"
            self.draw.text((self.xpos + self.width + 5, self.ypos + lasty - 5), string, font=f, fill=tcolor)
