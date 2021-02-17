from typeguard import typechecked
from defined import Optional, Tuple, Dict
from data import uData
from wave import Wave, gen_circle_list
from icon import Icon
from object import Load_Objects


@typechecked
class BOT:
    def __init__(self):
        self.wave_id = -1
        self.wave_change_flag = None
        self.data = uData.setting
        self.region = self.data['game_region']
        self.wave_total = self.data['wave']['total']
        self.loop_count = self.data['loop_count']
        self.session_check = self.data['set_timer']['session_check']
        self.sleep = self.data['sleep']
        self.crea_stop = self.data['crea_stop']
        self.stamina = self.data['stamina']
        self.objects = Load_Objects("bot")
        self.icons = self.__load_icons()
        self.waves = self.__load_waves()

    def __str__(self) -> str:
        string = str(self.__class__) + ":\n" + "\n\n".join("{} = {}".format(item, self.__dict__[item]) for item in self.__dict__ if item not in ['objects', 'icons', 'waves']) + "\n\n"
        string += "\n\n".join("{} = {}".format(item, "\n".join(str(value) for value in self.__dict__[item].values())) for item in self.__dict__ if item in ['objects', 'icons', 'waves'])
        return string

    def __load_icons(self) -> Dict:
        images = ['kirara_face.png', 'kuromon.png', 'ok.png', 'hai.png', 'tojiru.png']
        if self.stamina['used']:
            images += ['stamina_Au.png']
        if self.loop_count > 0:
            images += ['again.png']
        icons = [Icon(image, self.data['common_confidence']) for image in images]
        return {icon.name: icon for icon in icons}

    def __load_waves(self) -> Dict:
        return {str(wave_id): Wave(wave_id, self.wave_total)
                for wave_id in range(1, self.wave_total + 1)}

    def update_waveID(self) -> bool:
        for c in gen_circle_list(self.wave_id, self.wave_total):
            if self.waves[str(c)].current():
                self.wave_change_flag = False if self.wave_id == c else True
                self.wave_id = c
                return True
        return False

    def get_current_wave(self) -> Optional[Wave]:
        return self.waves[str(self.wave_id)]

    def use_stamina(self) -> bool:
        for s in self.stamina['priority']:
            if self.objects['stamina_{}'.format(s)].found():
                while not self.objects['stamina_add'].found():
                    self.objects['stamina_{}'.format(s)].click(1, 0.5)
                self.objects['stamina_add'].click(self.stamina['count'] - 1)
                self.objects['stamina_hai'].click(8)
                return True
        return False

    def miss_icon_files(self) -> Tuple:
        ret = tuple()
        for wave in self.waves.values():
            if not wave.icon.file_exist():
                ret += (wave.icon.name, wave.icon.path)
        for icon in self.icons.values():
            if not icon.file_exist():
                ret += (icon.name, icon.path)
        return tuple(zip(ret[0::2], ret[1::2]))

    def objects_found_all(self):
        print("objects found:")
        for object in Load_Objects('all').values():
            print("  {:16s} {}".format(object.name, object.found()))

    def icons_found_all(self):
        print("icons found:")
        for icon in self.icons.values():
            print("  {:16s} {}".format(icon.name, icon.get_center()))
        for wave in self.waves.values():
            print("  {:16s} {}".format(wave.name, wave.get_icon_coord()))

    def reload(self):
        # self.wave_id = -1
        # self.wave_change_flag = None
        self.data = uData.setting
        self.region = self.data['game_region']
        self.wave_total = self.data['wave']['total']
        self.loop_count = self.data['loop_count']
        self.session_check = self.data['set_timer']['session_check']
        self.sleep = self.data['sleep']
        self.crea_stop = self.data['crea_stop']
        self.stamina = self.data['stamina']
        self.objects = Load_Objects("bot")
        self.icons = self.__load_icons()
        self.waves = self.__load_waves()


# Test
if __name__ == '__main__':
    bot = BOT()
    print(bot.miss_icon_files())
