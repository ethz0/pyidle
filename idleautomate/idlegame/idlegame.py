#!/usr/bin/env python3
import logging
import psutil
import Quartz

import struct

from AppKit import NSWorkspace
from subprocess import PIPE
from time import sleep

from idleautomate.memory import memory

logger = logging.getLogger('idleautomate.window.window')

BOLD = '\033[1m'
ENDC = '\033[0m'
RED = '\033[31m'
GREEN = '\033[32m'
YELLOW = '\033[33m'
BLUE = '\033[34m'
CYAN = '\033[36m'

idle_app = "Idle Champions"

class IdleGame(object):
    def __init__(self):
        super().__init__()
        self._pid = None
        self._p = None
        self._proc = None
        self._gamedata = None
        self._base_addr = None
        self._mono_addr = None
        self._mono_size = None
        self._mono_table = None


    def __str__(self):
        pass


    def __repr__(self):
        pass


    def attach(self):
        if self.check:
            self._getGame()
            self._getProcess()


    def startGame(self):
        self._p = psutil.Popen(["open", "steam://run/627690"], stdin=PIPE)


    def endGame(self):
        if self._p == None:
            logger.log(logging.INFO, "Game started manually")
            logger.debug(f"Trying to acquire process {self.pid}")
            self._p = psutil.Process(self._pid)
            logger.debug(f"Got {self._p}")
        else:
            self._p.suspend()


    def _getGame(self):
        # windows = Quartz.CGWindowListCopyWindowInfo(Quartz.kCGWindowListOptionOnScreenOnly, Quartz.kCGNullWindowID)
        windows = Quartz.CGWindowListCopyWindowInfo(Quartz.kCGWindowListExcludeDesktopElements, Quartz.kCGNullWindowID)
        for win in windows:
            if win.get(Quartz.kCGWindowOwnerName, '') == 'Idle Champions':
                self._pid = win.get(Quartz.kCGWindowOwnerPID, '')
        self._p = psutil.Process(self._pid)


    def _getProcess(self):
        logging.debug(f"Acquire process and memory")
        if self.check:
            self._proc = memory.Process(pid=self._pid)
            self._base_addr = self._proc.find_region()
            logging.debug(f"self._base_addr: {self._base_addr:#x}")
            try:
                self._mono_addr, self._mono_size = self._proc.find_region(dylib_name="libmonobdwgc-2.0.dylib")
                logging.debug(f"self._mono_addr: {self._mono_addr:#x}")
                self._mono_table = self.monoPointers()
            except:
                logging.debug("Failure to get monoPointers, retrying")
                sleep(1)
                self._getProcess()


    def _check(self):
        running = False
        windows = Quartz.CGWindowListCopyWindowInfo(Quartz.kCGWindowListExcludeDesktopElements, Quartz.kCGNullWindowID)
        for win in windows:
            if win.get(Quartz.kCGWindowOwnerName, '') == 'Idle Champions':
                running = True

        if running:
            return True
        else:
            return False


    def hideWindow(self):
        workspace = NSWorkspace.sharedWorkspace()
        activeApps = workspace.runningApplications()
        for app in activeApps:
            if app.localizedName() == 'Idle Champions':
                app.hide()


    def _testcheck(self):
        running = False
        try:
            windows = Quartz.CGWindowListCopyWindowInfo(Quartz.kCGWindowListExcludeDesktopElements, Quartz.kCGNullWindowID)
            for win in windows:
                if win.get(Quartz.kCGWindowOwnerName, '') == 'Idle Champions':
                    testpid = win.get(Quartz.kCGWindowOwnerPID, '')
                    running = True
            logging.debug(f"got win pid: {testpid}")   
            if testpid == self._pid:
                logging.debug('pid match')
            else:
                logging.debug('pid mismatch, getting new pid')
                self._pid = testpid
                self._p = psutil.Process(self._pid)
                self._gamedata = False
        except:
            pass

        if self._gamedata == False and self._p.status() == 'running':
            self._getProcess()

        if running:
            return True
        else:
            return False


    def monoPointers(self):
        pointer_table = self._proc.vm_read(self._mono_addr + 0x3EEE08, 16 * 46) 
        ptr_tbl = struct.Struct('<QQ')

        mono_ptr_lst = []
        for i in ptr_tbl.iter_unpack(memoryview(pointer_table)):
            if i[0] != 0:
                mono_ptr_lst.append(i)
        return mono_ptr_lst


    def monoObject(self):
        result = []
        res = self._proc.vm_read(self._mono_addr + 0x3eee08, 0x10)
        result.append(struct.unpack('<QQ', res))
        return result

    # def offsets(self, table, start_addr, end_addr):
    #     p_list = []
    #     for i in table:
    #         if i[0] != 0:
    #             # print(f"{BOLD}addr: {i[0]:#x} size: {i[1]:#x}{ENDC}")
    #             p_list.append(i)
    #     return p_list


    def _list_object(self, addr, offset, res=None):
        """ creates a list object definition
        """
        if res is None:
            res = []

        rr = struct.unpack('<QLL', self._proc.vm_read(addr + offset, 0x10))
        if rr[0] != 0 or rr[1] != 0:
            res.append(rr)
            return self._list_object(addr, offset + 16, res)
        else:
            return res[0]


    def _list_parse(self, obj):
        """ builds a list from a list object definition
        """
        list_struct = struct.Struct('<Q')
        gen_list = []

        for i in list_struct.iter_unpack(obj):
            if i[0] != 0:
                gen_list.append(i[0])
        return gen_list


    def _parseOffset(self, addr, offset, bytes=8, type='int'):
        try:
            result = self._proc.vm_read(addr + offset, bytes)

            if type == 'int':
                return int.from_bytes(result, 'little')

            elif type == 'float':
                return struct.unpack('<f', result)

            elif type == 'list':
                addr = self._parseOffset(addr, offset)
                list_def = self._list_object(addr, 0x10)
                list_def_res = self._proc.vm_read(list_def[0] + 0x20, 8 * list_def[1])
                result = struct.unpack('<' + 'Q' * list_def[1], list_def_res)
                return result

            elif type == 'UTF-16':
                address = int.from_bytes(result, 'little')
                length = self._parseOffset(address, 0x10, bytes=4)
                result = self._proc.vm_read(address + 0x14, length * 2)
                return result.decode('UTF-16')

            ## TODO need to implement dict/hash types

        except:
            return 0

    
    def formation(self):
        form_list = []
        slots_list = self._formationSlots

        for s in slots_list:
            result = {}
            hero_addr = self._hero(s)
            hero_def = self._heroDef(hero_addr)
            hero_id = self._heroId(hero_def)
            hero_alive = self._heroAlive(s)
            hero_name = self.heroesDefName(hero_def)
            hero_seat = self.heroesDefSeatID(hero_def)
            
            if hero_id != 0:
                result['hero_addr'] = hero_addr
                result['hero_def'] = hero_def
                result['hero_id'] = hero_id
                result['hero_name'] = hero_name
                result['hero_seat'] = hero_seat
                result['hero_alive'] = hero_alive

                form_list.append(result)
                
        return form_list
    

    @property
    def pid(self):
        return self._pid
    

    @property
    def check(self):
        return self._check()


    @property
    def base_addr(self):
        return self._base_addr

    
    @property
    def mono_addr(self):
        return self._mono_addr


    @property
    def mono_size(self):
        return self._mono_size

    
    @property
    def _gameInstance(self):
        try:
            return self._parseOffset(self._mono_table[0][0], 0x9d28)
        except IndexError as e:
            logging.debug('Index error in mono table, retrying')
            sleep(2)
            return self._parseOffset(self._mono_table[0][0], 0x9d28)
  

    @property
    def click_damage(self):
        return self._parseOffset(self._gameInstance, 0x108, bytes=4)


    @property
    def resetsSinceLastManual(self):
        return self._parseOffset(self._gameInstance, 0xf4, bytes=4)

    
    @property
    def _controller(self):
        return self._parseOffset(self._gameInstance, 0x18)
        
        
    @property
    def _userData(self):
        return self._parseOffset(self._controller, 0xb8)


    @property
    def _activeUserGameInstance(self):
        return self._parseOffset(self._userData, 0x294, bytes=4)

    
    @property
    def _lootHandler(self):
        return self._parseOffset(self._userData, 0x18)
            

    @property
    def _chestHandler(self):
        return self._parseOffset(self._userData, 0x20)

    
    @property
    def userDataInited(self):
        return self._parseOffset(self._userData, 0x280, bytes=4)


    @property
    def gems(self):
        return self._parseOffset(self._userData, 0x264, bytes=4)

####################
# timescales
    @property
    def _timeScales(self):
        return self._parseOffset(self._gameInstance, 0xd8, type='list')
    
    
    def _timeScalesMultiplies(self, ts_addr):
        return self._parseOffset(ts_addr, 0x10, type='dict')
    
# end timescales

# buffHandler
    @property
    def _buffHandler(self):
        return self._parseOffset(self._userData, 0x28)
    

    @property
    def _inventoryBuffs(self):
        return self._parseOffset(self._buffHandler, 0x20, type='list')
    

    def _buffName(self, ib_addr):
        return self._parseOffset(ib_addr, 0x20, type='UTF-16')

# end buffHandler

# statHandler
    @property
    def _statHandler(self):
        return self._parseOffset(self._userData, 0x30)


    ## beadle / grimm rest stacks
    def _brs_addr(self):
        return self._statHandler + 0x316


    def _grs_addr(self):
        return self._statHandler + 0x320
    ## beadle / grimm rest stacks


    @property
    def ss_addr(self):
        return self._statHandler + 0x300


    @property
    def bs_stacks(self):
        return self._parseOffset(self._statHandler, 0x300, bytes=4)

    
    @property
    def hs_addr(self):
        return self._statHandler + 0x304


    @property
    def bh_stacks(self):
        return self._parseOffset(self._statHandler, 0x304, bytes=4)
    
# end statHandler
    
# activeCampaignData
    @property
    def _activeCampaignData(self):
        return self._parseOffset(self._gameInstance, 0x28)


    @property
    def _currentArea(self):
        return self._parseOffset(self._activeCampaignData, 0x28)
    

    @property
    def _currentAreaLevel(self):
        return self._parseOffset(self._currentArea, 0x54)
            
# end activeCampaignData
    
# resetHandler
    @property
    def _resetHandler(self):
        return self._parseOffset(self._gameInstance, 0x40)


    @property
    def _resetting(self):
        return self._parseOffset(self._resetHandler, 0x38)

# end resetHandler
            
# modronHandler
    @property
    def _modronHandler(self):
        return self._parseOffset(self._userData, 0xd8)
    

    @property
    def _modronSaves(self):
        return self._parseOffset(self._modronHandler, 0x20, type='list')

    
    @property
    def modron_reset_level(self): # modronTargetArea 
        try:
            return self._parseOffset(self._modronSaves[2], 0x54, bytes=4)
        except:
            return 2001
    
    
    def modronTargetArea(self, save_addr):
        return self._parseOffset(save_addr, 0x54, bytes=4)
    

    def modronCoreId(self, save_addr):
        return self._parseOffset(save_addr, 0x48, bytes=4)

    
    def modronInstanceId(self, save_addr):
        return self._parseOffset(save_addr, 0x4c, bytes=4)

# end modronHandler

# heroHandler
    @property
    def _heroHandler(self):
        return self._parseOffset(self._userData, 0x10)

    
    @property
    def heroes(self):
        return self._parseOffset(self._heroHandler, 0x18, type='list')


    def heroesDef(self, hero_addr):
        return self._parseOffset(hero_addr, 0x18)

    
    def heroesDefName(self, hero_def):
        return self._parseOffset(hero_def, 0x38, type='UTF-16')

    
    def heroesDefSeatID(self, hero_def):
        return self._parseOffset(hero_def, 0x1c8, bytes=4)
    

    def heroesEffects(self, hero_addr):
        return self._parseOffset(hero_addr, 0x90)


    def heroesEffectsKeysByName(self, effects_addr):
        return self._parseOffset(effects_addr, 0x58, type='dict')

    
    def heroesHealth(self, hero_addr):
        return self._parseOffset(hero_addr, 0x358)
    

    def heroesSlotID(self, hero_addr):
        return self._parseOffset(hero_addr, 0x30c, bytes=4)
    

    def heroesOwned(self, hero_addr):
        return self._parseOffset(hero_addr, 0x308, bytes=4)

    
    def heroesBenched(self, hero_addr):
        return self._parseOffset(hero_addr, 0x318, bytes=4)

    
    def heroesLevel(self, hero_addr):
        return self._parseOffset(hero_addr, 0x334, bytes=4)
    
# end heroHandler

# area
    @property
    def area_addr(self):
        try:
            return self._parseOffset(self._activeCampaignData, 0x28)
        except:
            return 0


    @property
    def area(self): # instanceLoadTimeSinceLastSave
        return self._parseOffset(self._currentArea, 0x54, bytes=4)

    
    @property
    def _area(self):
        return self._parseOffset(self._controller, 0x18)


    @property
    def areaActive(self):
        return self._parseOffset(self._area, 0x1dc, bytes=4)


    @property
    def basicMobsSpawnedThisArea(self):
        return self._parseOffset(self._area, 0x240)

    
    @property
    def secSinceStart(self):
        res = self._parseOffset(self._area, 0x204, bytes=4, type='float')
        try:
            return res[0]
        except:
            return 0

# end area

# patronHandler
    @property
    def _patronHandler(self):
        return self._parseOffset(self._gameInstance, 0x58)

    @property
    def _activePatron(self):
        return self._parseOffset(self._patronHandler, 0x20)

    @property
    def patronId(self):
        return self._parseOffset(self._activePatron, 0x10, bytes=4)

    @property
    def patronTier(self):
        return self._parseOffset(self._activePatron, 0xc0, bytes=4)

# end patronHandler

# formationSaveHandler
    @property
    def _formationSaveHandler(self):
        return self._parseOffset(self._gameInstance, 0x68)


    @property
    def formationCampaignId(self):
        return self._parseOffset(self._formationSaveHandler, 0x78, bytes=4)
        

    @property
    def _formationSavesV2(self):
        return self._parseOffset(self._formationSaveHandler, 0x30, type='list')


    def formationFav(self, addr):
        return self._parseOffset(addr, 0x40, bytes=4)


    def fornmationName(self, addr):
        return self._parseOffset(addr, 0x30, type='UTF-16')
    

    def formationForm(self, addr):
        return self._parseOffset(addr, 0x18, type='list')

# end formationSaveHandler

# formation
    @property
    def _formation(self):
        return self._parseOffset(self._controller, 0x28)


    @property
    def _formationSlots(self):
        return self._parseOffset(self._formation, 0x28, type='list')

    
    def _hero(self, form_addr):
        return self._parseOffset(form_addr, 0x28)
    

    def _heroDef(self, hero_addr):
        return self._parseOffset(hero_addr, 0x18)
    

    def _heroId(self, hdef_addr):
        return self._parseOffset(hdef_addr, 0x10, bytes=4)
    

    def _heroAlive(self, form_addr):
        return self._parseOffset(form_addr, 0x249, bytes=4)

    
    @property
    def mobs(self):
        return self._parseOffset(self._formation, 0x1b0, bytes=4)


    @property
    def rangedMobs(self):
        return self._parseOffset(self._formation, 0x1b4, bytes=4)
    
# end formation

# offlineHandler
    @property
    def _offlineHandler(self):
        return self._parseOffset(self._gameInstance, 0x20)
    

    @property
    def finishedOfflineProgressType(self):
        return self._parseOffset(self._offlineHandler, 0x98, bytes=4)


    @property
    def offlineProgressType(self):  # this is no more
        return self._parseOffset(self._offlineHandler, 0x98, bytes=4)

# end offlineHandler

# screen uiController
    @property
    def _screen(self):
        return self._parseOffset(self._gameInstance, 0x10)

    
    @property
    def _uiController(self):
        return self._parseOffset(self._screen, 0x3b8)


    @property
    def _topBar(self):
        return self._parseOffset(self._uiController, 0x18)


    @property
    def _objectiveProgressBox(self):
        return self._parseOffset(self._topBar, 0x358)


    @property
    def _areaBar(self):
        return self._parseOffset(self._objectiveProgressBox, 0x390)


    @property
    def _autoProgressButton(self):
        return self._parseOffset(self._areaBar, 0x360)

    
    @property
    def autoProgressToggle(self):
        return self._parseOffset(self._autoProgressButton, 0x3ca, bytes=4)


    @property
    def _bottomBar(self):
        return self._parseOffset(self._uiController, 0x20)

    
    @property
    def _heroPanel(self):
        return self._parseOffset(self._bottomBar, 0x378)
    

    @property
    def _activeBoxes(self):
        return self._parseOffset(self._heroPanel, 0x3b8, type='list')
    

    def _nextUpgrade(self, ab_addr):
        """ takes an _activeBoxes as an addr"""
        return self._parseOffset(ab_addr, 0x400)
    

    def _isPurchased(self, nu_addr):
        """ takes nextUpgrade as an addr """
        return self._parseOffset(nu_addr, 0xa8, bytes=4)
    

    @property
    def _ultimatesBar(self):
        return self._parseOffset(self._uiController, 0x28)

    
    @property
    def _ultimateItems(self):
        return self._parseOffset(self._ultimatesBar, 0x3a0, type='list')
    

    def _uiHero(self, ui_addr):
        return self._parseOffset(ui_addr, 0x390)
    

    def _uiHeroDef(self, uih_addr):
        return self._parseOffset(uih_addr, 0x18)


    def _uiHeroDefId(self, uihd_addr):
        return self._parseOffset(uihd_addr, 0x10)

# end screen uiController