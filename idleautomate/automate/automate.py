import json
import logging
import os
import threading

from datetime import datetime, timedelta
from time import sleep
from Quartz.CoreGraphics import CGEventCreateKeyboardEvent
from Quartz.CoreGraphics import CGEventPostToPid

import idleautomate.idlegame.server_call as isc
from idleautomate.idlegame.idlegame import IdleGame

logging.basicConfig(level=logging.DEBUG)

BOLD = '\033[1m'
ENDC = '\033[0m'
RED = '\033[31m'
GREEN = '\033[32m'
YELLOW = '\033[33m'
BLUE = '\033[34m'
CYAN = '\033[36m'

logger = logging.getLogger('idleautomate.window.window')

homedir = os.getenv("HOME")
cachedir = 'Library/Application Support/Steam/steamapps/common/IdleChampions/IdleDragonsMac.app/Contents/Resources/Data/StreamingAssets/downloaded_files/'
cachepath = f'{homedir}/{cachedir}'
cachefile = 'cached_definitions.json'

# this probably only works on US keyboards
keyMap = {
    '7'      : 0x1a,
    'q'      : 0x0c,
    'w'      : 0x0d,
    'e'      : 0x0e,
    'g'      : 0x05,
    'x'      : 0x07,
    'right'  : 0x7c,
    'left'   : 0x7b,
    'esc'    : 0x35,
    'f1'     : 0x7a,
    'f2'     : 0x78,
    'f3'     : 0x63,
    'f4'     : 0x76,
    'f5'     : 0x60,
    'f6'     : 0x61,
    'f7'     : 0x62,
    'f8'     : 0x64,
    'f9'     : 0x65,
    'f10'    : 0x6d,
    'f11'    : 0x67,
    'f12'    : 0x6f,
    'ctrl'   : 0x3b,
    'command': 0x37,
    'cmd'    : 0x37,
    'shift'  : 0x38,
    'option' : 0x3a,
}

## automation implementation as a whole needs better thought

class Game(threading.Thread):
    def __init__(self):
        super().__init__()
        self._stop_event = threading.Event()

        self.idlegame = IdleGame()
        self.mode = 'fourj'
        self.MISSED_STACK = False
        self.AUTOMATION = True
        self.ALIGNMENT = True
        self._STACK_TIME = 8
        self.BUY_SILVER = False
        self.BUY_GOLD = False
        self.BUY_SILVER_COUNT = 50
        self.BUY_GOLD_COUNT = 5
        self.OPEN_SILVER = False
        self.OPEN_GOLD = False
        self.OPEN_EVENT = False
        self.OPEN_ELECTRUM = False
        self.OPEN_MODRON = False
        self.OPEN_MIRT = False
        self.OPEN_VAJRA = False
        self.OPEN_STRAHD = False
        self.OPEN_ZARIEL = False
        self.GEM_BANK = 250000

        self.stuck = False
        self.offline_stacking = False
        self.hide_window = False

        self.URL = isc.getServer()

        if self.mode == 'fourj' or self.mode == 'none':
            self._STEEL_STACKS = 22086 # reset 940
            # self._STEEL_STACKS = 11200 # reset 835
            # self._STEEL_STACKS = 10600 # reset 830
            # self._STEEL_STACKS = 8750 # reset 800
            # self._STEEL_STACKS = 8300 # reset 790
            # self._STEEL_STACKS = 6285 # reset 750
            # self._STACK_ZONE = 671
            self._STACK_ZONE = 621
        elif self.mode == 'sixj' or self.mode == 'sixjnoa':
            # self._STEEL_STACKS = 3675 # no metalborn
            self._STEEL_STACKS = 1555
            self._STACK_ZONE = 421


        self.start_time = datetime.now()
        self.resets = 0

        self.status = {
            'aligned': False,
            'aligning': False,
            'dash': False,
            'haste': False,
            'stacked': False,
            'stacking': False,
            'reset': False,
            'form': 'q',
            'imps': 0,
        }


    # def __str__(self):
    #     output = 'test'
    #     # output = f"{self.idlegame.area:4d}/{self.status['form']}  {self.idlegame.bs_stacks:5d}/{self.idlegame.bh_stacks:5d} align[ed]/[ing]: {self.status['aligned']:1}/{self.status['aligning']:1} stack[ed]/[ing]: {self.status['stacked']:1}/{self.status['stacking']:1} resets: {self.resets:3d}"
    #     return output


    def stop(self):
        self._stop_event.set()


    def clear(self):
        self._stop_event.clear()


    def stopped(self):
        return self._stop_event.is_set()


    # def check_thread(self):
    #     for thread in threading.enumerate():
    #         logger.log(logging.INFO, thread.name)%                                                                                                                                          


    # @property
    # def status(self):
    #     return self.status


    @property
    def clock(self):
        return (datetime.now() - self.start_time)


    @property
    def STEEL_STACKS(self):
        return self._STEEL_STACKS


    @STEEL_STACKS.setter
    def STEEL_STACKS(self, value):
        self._STEEL_STACKS = int(value)


    @property
    def STACK_ZONE(self):
        return self._STACK_ZONE


    @STACK_ZONE.setter
    def STACK_ZONE(self, value):
        self._STACK_ZONE = int(value)


    @property
    def STACK_TIME(self):
        return self._STACK_TIME


    @STACK_TIME.setter
    def STACK_TIME(self, value):
        self._STACK_TIME = int(value)


    @property
    def bossArea(self):
        return self.idlegame.area % 5 == 0


    @property
    def checkAlignment(self):

        ## need to build this in to the UI or some sort of automate template
        if self.mode == 'fourj':
            # return self.idlegame.area % 10 == 1 or self.idlegame.area % 10 == 6
            return self.idlegame.area % 10 == 2 or self.idlegame.area % 10 == 7
        elif self.mode == 'sixj':
            return ((not self.idlegame.area % 10 == 3 
                    and not self.idlegame.area % 10 == 8)
                    and (not self.idlegame.area % 10 == 1
                    and not self.idlegame.area % 10 == 6))
        elif self.mode == 'sixjnoa' or 'none':
            return True
        # #  / Freely 
        # return area % 10 == 4 or area % 10 == 9


    def displayStatus(self):
        output = f"{self.idlegame.area:4d}/{self.status['form']}  {self.idlegame.bs_stacks:5d}/{self.idlegame.bh_stacks:5d} align[ed]/[ing]: {self.status['aligned']:1}/{self.status['aligning']:1} stack[ed]/[ing]: {self.status['stacked']:1}/{self.status['stacking']:1} resets: {self.resets:3d}"
        # logger.debug(output)


    def keyPress(self, k, modifier=None):
        if modifier:
            print(f'set mod {modifier}')
            CGEventPostToPid(self.idlegame.pid, CGEventCreateKeyboardEvent(None, keyMap[modifier], True))
            sleep(0.1)

        CGEventPostToPid(self.idlegame.pid, CGEventCreateKeyboardEvent(None, keyMap[k], True))
        sleep(0.1)
        CGEventPostToPid(self.idlegame.pid, CGEventCreateKeyboardEvent(None, keyMap[k], False))

        if modifier:
            CGEventPostToPid(self.idlegame.pid, CGEventCreateKeyboardEvent(None, keyMap[modifier], False))
            sleep(0.1)

        sleep(0.1)

        if k in ['q', 'w', 'e']:
            self.status['form'] = k


    def toggleAutoProgress(self):
        self.keyPress('g')


    def resumeRun(self):
        self.keyPress('left')
        self.keyPress('q')
        self.toggleAutoProgress()


    def dash(self):
        self.status['dash'] == True
        if self.idlegame.autoProgressToggle == 1:
            self.toggleAutoProgress()
        start_dashtime = self.idlegame.secSinceStart
        while self.idlegame.secSinceStart - start_dashtime < 30:
            sleep(.1)
        if self.idlegame.autoProgressToggle == 0:
            self.toggleAutoProgress()


    def startGame(self):
        if self.idlegame.check:
            logger.log(logging.INFO, "Game is running ignoring start request")
        else:
            logger.log(logging.INFO, "Starting game")
            self.idlegame.startGame()


    def endGame(self):
        if self.idlegame.check:
            logger.log(logging.INFO, "Closing game")
            ## this doesn't thrill me but without other options c'est la vie
            os.system("""osascript -e 'tell application \"Idle Champions\" to quit'""")
        else:
            logger.log(logging.INFO, "Game not running ignoring stop request")


    def checkMem(self):
        #### check game mem is loaded
        # this could be better
        if (self.idlegame.check
                and self.idlegame.secSinceStart > 5
                and self.idlegame.areaActive == 1
                and self.idlegame.offlineProgressType == 1):
            logging.debug(f"trying to attach")
        #### end check game mem is loaded


    def alignment(self):
        self.status['aligned'] = self.checkAlignment

        if self.mode == 'fourj':

            if (5 < self.idlegame.area < self.STACK_ZONE - 5 
                    and self.status['aligned'] == False 
                    and self.status['aligning'] == False):

                self.status['aligning'] = True
                self.keyPress('e')

            elif self.status['aligning'] == True and self.status['aligned'] == True:

                self.keyPress('q')
                self.status['aligning'] = False

        elif self.mode == 'sixj':

            if (self.status['aligned'] == False
                    and self.status['aligning'] == False):

                self.status['aligning'] = True
                self.keyPress('e')

            elif self.status['aligning'] == True and self.status['aligned'] == True:

                self.keyPress('q')
                self.status['aligning'] = False

        elif self.mode == 'noalign':

            pass


    def buyChests(self):
        CALL_URL = self.URL + isc.URI
        logger.log(logging.INFO, "Buying chests")
        if self.BUY_SILVER:
            isc.buyChests(CALL_URL, '1', int(self.BUY_SILVER_COUNT)) # buy silvers
        if self.BUY_GOLD:
            isc.buyChests(CALL_URL, '2', int(self.BUY_GOLD_COUNT)) # buy golds


    def calcChestCost(self):
        cost = 0
        if self.BUY_GOLD:
            cost += int(self.BUY_GOLD_COUNT) * 500
        if self.BUY_SILVER:
            cost += int(self.BUY_SILVER_COUNT) * 50

        return cost


    def reset(self):
        self.end_time = datetime.now()
        self.resets += 1

        # on reset set things back to starting values
        self.status['aligned'] = False
        self.status['aligning'] = False
        self.status['dash'] = False
        self.status['stacked'] = False
        self.status['stacking'] = False
        self.status['reset'] = False
        self.status['form'] = 'q'
        self.status['imps'] = 0
        self.MISSED_STACK = False

        if (self.idlegame.gems > (int(self.GEM_BANK) + self.calcChestCost()) 
                and (self.BUY_SILVER or self.BUY_GOLD)):
            logging.debug(f"gems: {self.idlegame.gems} chest costs: {self.calcChestCost()}")
            self.buyChests()

        logger.log(logging.INFO, f"Reset count: {self.resets} run time: {self.end_time - self.start_time}")
        self.start_time = datetime.now()


    def stacking(self):
        self.stack_start = datetime.now()
        self.status['stacking'] = True

        self.keyPress('w')
        if self.idlegame.autoProgressToggle == 0:
            self.toggleAutoProgress()

        sleep(1)

        if self.offline_stacking == False:
            sleep(5)
            self.keyPress('esc')

        offline = True
        started = False
        ended = False

        while offline and self.offline_stacking and self.MISSED_STACK == False:
            if ended == False:
                logging.debug("Offline stack endgame")
                self.endGame()
                ended = True

            if started == False and ended == True:
                offline_sleep = True
                logging.debug("Offline sleeping")  

                if self.resets % 2 == 0: # and self.resets != 0:
                    td = timedelta(seconds=self.STACK_TIME)
                    open_starttime = datetime.now()
                    offline_sleep = False
                    logging.debug('Offline stack open chests')
                    self.openChests()
                    open_time = datetime.now() - open_starttime
                    logging.debug(f"Open chest time: {open_time}")
                    if open_time < td:
                        st = td - open_time
                        logging.debug(f"Sleeping: {st}")
                        sleep(st.seconds)

                if offline_sleep == True:
                    logging.debug(f"Offline stack sleep {self.STACK_TIME}s")
                    sleep(self.STACK_TIME)

                logging.debug("Offline stack start game")
                self.startGame()
                self.URL = isc.getServer()
                started = True

            if self.idlegame.check and started == True:
                logging.debug("Attempting re-attach") 
                self.idlegame.attach()

                if self.hide_window:
                    logging.debug('Hiding game window')
                    self.idlegame.hideWindow()

                offline = False

        if self.MISSED_STACK == True:
            while self.idlegame.bs_stacks < self.STEEL_STACKS:
                if self.bossArea:
                    self.keyPress('left')                
                sleep(1)

        logging.debug('reached end of stacking()')

    def stacked(self):
        try:
            self.stack_start
        except:
            self.stack_start = datetime.now()


        self.status['stacked'] = True
        self.status['stacking'] = False

        self.stack_end = datetime.now()

        logger.log(logging.INFO, f'Stacking complete: {self.stack_end - self.stack_start}')

        sleep(1)
        self.resumeRun()

        self.status['reset'] = True


    def openChests(self):
        CALL_URL = self.URL + isc.URI
        userdetails = isc.getUserDetails2(CALL_URL, isc.headers)
        if userdetails['success'] == True:
            instance_id = userdetails['details']['instance_id']

            with open (cachepath + cachefile) as cfile:
                cdata = json.load(cfile)

            isc.opengenericchest['instance_id'] = instance_id
            for k,v in userdetails['details']['chests'].items():
                if v != 0:
                    # do not open non-electrum, 282 is electrum
                    # if k in ['1', '2']:
                    if ((k == '1' and self.OPEN_SILVER)
                        or (k =='2' and self.OPEN_GOLD)
                        or (k == '282' and self.OPEN_ELECTRUM)):
                        for c in cdata['chest_type_defines']:
                            if c['id'] == int(k):
                                if v > 1:
                                    logger.info(f"Opening {v} {c['name_plural']}")
                                else:
                                    logger.info(f"Opening {v} {c['name']}")
                                loot = isc.openChests2(k, CALL_URL, count=v)
                        logging.debug(f"{GREEN}{loot}{ENDC}")
                        logging.debug("Parsing chests")
                        isc.parseChests2(loot)


    def automate(self):
        try:
            while self.AUTOMATION and not self.stopped():
                try: 
                    self.start_time
                except:
                    self.start_time = datetime.now()

                if self.idlegame.area == 16:
                    self.keyPress('q')

                #### reset code
                if self.idlegame.area < 10 and self.status['reset'] == True:

                    self.reset()
                ##### end reset code

                # #### shandie dash
                # if self.idlegame.area > 10 and self.status['dash'] == False:
                #     self.dash()
                # #### end shandie dash

                #### check for haste stacks 
                if self.idlegame.bh_stacks > 49:
                    self.status['haste'] = True
                else:
                    self.status['haste'] = False
                #### end check for haste stacks

                #### align to checkAlignment code
                if self.ALIGNMENT == True and self.status['haste'] == True: 
                    self.alignment()
                #### end align to checkAlignment code

                ### catch stuck conditions and missed stacks
                # progress stuck?
                if (self.idlegame.bs_stacks > self.STEEL_STACKS 
                    and self.idlegame.bs_stacks > self.STEEL_STACKS
                    and self.idlegame.secSinceStart > 20
                    and self.idlegame.autoProgressToggle == 0
                    and self.status['reset'] == True):
                    self.resumeRun()
                # end progress stuck?

                if self.idlegame.bs_stacks > self.STEEL_STACKS and self.status['stacked'] == False:
                    logging.debug("Main automate loop, caught stacked")
                    self.stacked()

                if (self.idlegame.bs_stacks > self.STEEL_STACKS
                        and self.status['stacked'] == True
                        # and self.idlegame.offlineProgressType == 0
                        and len(self.idlegame.formation()) == 1):
                        # and self.idlegame.secSinceStart > 20):

                    logging.debug(f"{YELLOW}Main automate loop, stuck stacked{ENDC}")
                    self.resumeRun()

                if (self.idlegame.bs_stacks < self.STEEL_STACKS 
                        and self.idlegame.area > (self.idlegame.modron_reset_level - 30)
                        # and self.idlegame.area > 870
                        and self.status['stacked'] == False
                        and self.status['reset'] == False
                        and self.idlegame.secSinceStart > 0):

                    logging.debug(f"{RED}Main automate loop, missed stacking{ENDC}")
                    self.MISSED_STACK = True
                    self.stacking()

                if self.idlegame.check and self.idlegame._controller == '0x0':
                    pass
                ### end catch stuck conditions

                #### briv stacking logic
                while (self.status['stacked'] == False
                            and self.STACK_ZONE - 5 < self.idlegame.area < self.STACK_ZONE + 9):

                    if self.idlegame.bs_stacks > self.STEEL_STACKS and self.status['stacked'] == False:
                        logging.debug("stacking loop, caught stacked")
                        self.stacked()

                    if self.bossArea:
                        self.keyPress('left')

                    if (self.idlegame.bs_stacks < self.STEEL_STACKS
                            and self.status['stacking'] == False
                            and self.status['reset'] == False):

                        logging.debug("Main stacking loop, normal stacking (if)")
                        self.stacking()

                    elif self.idlegame.bs_stacks > self.STEEL_STACKS and self.idlegame.finishedOfflineProgressType == 1:
                        logging.debug("Main stacking loop, normal stacked (else)")
                        self.stacked()

                    self.displayStatus()
                    sleep(0.3)
                    if self._stop_event.wait(.5):
                        break
                #### end briv stacking logic

                self.displayStatus()
                # self.checkMem()

                #### break when UI sends stop event, stacking code doesn't break (yet)
                if self._stop_event.wait(.5):
                    break

            self.clear()

        except Exception as e:
            print('Failure in automate loop')
            print(f'error: {e}')
