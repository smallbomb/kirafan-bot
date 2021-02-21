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
        self.award_pause = False
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
        string = str(self.__class__) + ":\n"
        for item in self.__dict__:
            if item in ['objects', 'icons', 'waves']:
                for value in self.__dict__[item].values():
                    string += item + str(value) + "\n"
            else:
                string += "{} = {}\n\n".format(item, self.__dict__[item])
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

    def __init_flag(self, new_waveid: int):
        if new_waveid < self.wave_id:
            # is new battle
            self.award_pause = False
            # self.friend_used = False
            # self.orb_used = False

    def update_waveID(self) -> bool:
        for new_wid in gen_circle_list(self.wave_id, self.wave_total):
            if self.waves[str(new_wid)].current():
                self.__init_flag(new_wid)
                self.wave_change_flag = False if self.wave_id == new_wid else True
                self.wave_id = new_wid
                return True
        return False

    def get_current_wave(self) -> Optional[Wave]:
        return self.waves[str(self.wave_id)]

    def use_stamina(self):
        for s in self.stamina['priority']:
            if self.objects['stamina_{}'.format(s)].found():
                while not self.objects['stamina_add'].found():
                    self.objects['stamina_{}'.format(s)].click(1, 0.5)
                self.objects['stamina_add'].click(self.stamina['count'] - 1)
                self.objects['stamina_hai'].click(8)
                break

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
        self.award_pause = False
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
