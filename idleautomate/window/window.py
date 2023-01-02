import logging
import pyglet
import queue
import threading
import tkinter as tk

from PIL import ImageTk, Image
from tkinter import ttk
from tkinter.scrolledtext import ScrolledText

from idleautomate.arguments import args
from idleautomate.automate.automate import Game

logger = logging.getLogger(__name__)

text_color = "#F6E6C6"
bg_color = "#211302"
gr_tab = "#557F36"
red_tab = "#4D1010"
tab_text = "#F4B254"

## this has memory issues, major work needed

class Table:
    def __init__(self, root, data):
        self.rows = len(data)
        self.columns = len(data[0])
        for i in range(self.rows):
            for j in range(self.columns):
                self.e = tk.Entry(root, width=12)
                self.e.grid(row=i, column=j)
                self.e.insert(tk.END, data[i][j])


# https://beenje.github.io/blog/posts/logging-to-a-tkinter-scrolledtext-widget/
class QueueHandler(logging.Handler):
    """Class to send logging records to a queue
    It can be used from different threads
    """

    def __init__(self, log_queue):
        super().__init__()
        self.log_queue = log_queue

    def emit(self, record):
        self.log_queue.put(record)


class IcWindow(tk.Frame):
    def __init__(self) -> None:
        self.game = Game()
        if self.game.idlegame.check:
            self.game.idlegame.attach()
        self.win = tk.Tk()

        # this is not working on macos
        pyglet.font.add_file('./assets/Tiamat Condensed SC Regular Regular.ttf')

        text_color = "#f4b254"
        bg_color = "#211302"
        gr_tab = "#557F36"
        red_tab = "#4D1010"
        tab_text = "#F4B254"
        
        self.win.title("ic automator")
        self.win.iconphoto(False, tk.PhotoImage(file='./assets/Icon_GemPile2_0.png'))
        self.win.grid_rowconfigure(0, weight=1)
        self.win.grid_columnconfigure(0, weight=1)

        self.logo = Image.open("./assets/idleChampions_logo_transparent_small.png")
        self.logo = ImageTk.PhotoImage(self.logo)

        self.style = ttk.Style()
        self.style.theme_create( "ic", parent="alt", settings={
                ".": {
                    "configure": {
                        "background": bg_color,
                        "font": tab_text
                    } 
                },
                "TNotebook": {
                    "configure": {
                        "tabmargins": [2, 5, 2, 0] 
                    } 
                },
                "TNotebook.Tab": {
                    "configure": {
                        "foreground": text_color,
                        "padding": [5, 1], 
                        "background": red_tab,
                        "font": tab_text
                    },
                    "map": {
                        "background": [("selected", gr_tab)],
                        "font": tab_text,
                        "expand": [("selected", [1, 1, 1, 0])] 
                    } 
                } 
        } )        
        self.style.theme_use("ic")

        self.border = tk.Frame(self.win, bg="light gray", width=450, height=550)
        self.border.grid(row=0, sticky="nsew", padx=3, pady=3)
        self.border.grid_rowconfigure(0, weight=0)
        self.border.grid_rowconfigure(1, weight=1)
        self.border.grid_rowconfigure(2, weight=0)
        self.border.grid_columnconfigure(0, weight=1)

        self._createTopFrame()
        self._createTabFrames()
        self._createBottomFrame()

        # # logging queue/handler stuff
        self.log_queue = queue.Queue()
        self.queue_handler = QueueHandler(self.log_queue)
        formatter = logging.Formatter('%(asctime)s - %(message)s')
        self.queue_handler.setFormatter(formatter)
        logger.addHandler(self.queue_handler)

        self.win.mainloop()


    def poll_log_queue(self):
        # Check every 100ms if there is a new message in the queue to display
        while True:
            try:
                record = self.log_queue.get(block=False)
            except queue.Empty:
                break
            else:
                self.display(record)
        self.tab_automate.after(100, self.poll_log_queue)


    def display(self, record):
        msg = self.queue_handler.format(record)
        self.scrolled_text.configure(state='normal')
        self.scrolled_text.insert(tk.END, msg + '\n', record.levelname)
        self.scrolled_text.configure(state='disabled')
        self.scrolled_text.yview(tk.END) # Autoscroll to the bottom


    def _createTopFrame(self):
        self.top_frame = tk.Frame(self.border, bg=bg_color, height=60)
        self.top_frame.grid(row=0, sticky="ew", padx=3, pady=3)
        self.top_frame.grid_rowconfigure(0, weight=1)
        self.top_frame.grid_columnconfigure(0, weight=1)

        # main top frame logo
        self.lbl_logo = tk.Label(self.top_frame, bg=bg_color, image=self.logo)
        self.lbl_logo.grid(row=0, rowspan=8, column=0,  sticky="w")

        # start game button
        self.start_button = tk.Button(self.top_frame, text="start", bg=bg_color, command=self.game.startGame)
        # end game button
        self.end_button = tk.Button(self.top_frame, text="stop", bg=bg_color, command=self.game.endGame)
        # main top re-aquire button
        self.lbl_button = tk.Button(self.top_frame, text="getmem", bg=bg_color, command=self.game.idlegame.attach)

        # main top frame details
        self.lbl_pid = tk.Label(self.top_frame, fg=text_color, bg=bg_color, justify="right", text=f"PID: ")
        self.lbl_pid_value = tk.Label(self.top_frame, fg=text_color, bg=bg_color, font=('Tiamat Condensed SC', 12))
        self.lbl_base_addr = tk.Label(self.top_frame, fg=text_color, bg=bg_color, justify="right", text=f"base addr: ")
        self.lbl_base_addr_value = tk.Label(self.top_frame, fg=text_color, bg=bg_color, font=('Tiamat Condensed SC', 12))
        self.lbl_mono_addr = tk.Label(self.top_frame, fg=text_color, bg=bg_color, justify="right", text=f"mono addr: ")
        self.lbl_mono_addr_value = tk.Label(self.top_frame, fg=text_color, bg=bg_color, font=('Tiamat Condensed SC', 12))

        # main top frame automation checkbox
        self.AUTOMATE = tk.BooleanVar()
        self.lbl_activate = tk.Checkbutton(self.top_frame,
                                           fg=text_color,
                                           bg=bg_color,
                                           justify="right",
                                           text=f"Enable Automation",
                                           variable=self.AUTOMATE,
                                           onvalue=1,
                                           offvalue=0,
                                           command=self.automate)

        # main frame layout
        self.start_button.grid(row=0, column=1, sticky="e", pady=1)
        self.end_button.grid(row=0, column=2, sticky="e", pady=1)
        self.lbl_button.grid(row=1, column=2, columnspan=2, sticky="e", pady=1)
        self.lbl_pid.grid(row=4, column=1, sticky="e", pady=0)
        self.lbl_pid_value.grid(row=4, column=2, sticky="e", pady=0)
        self.lbl_base_addr.grid(row=5, column=1, sticky="e", pady=0)
        self.lbl_base_addr_value.grid(row=5, column=2, sticky="e", pady=0)
        self.lbl_mono_addr.grid(row=6, column=1, sticky="e", pady=0)
        self.lbl_mono_addr_value.grid(row=6, column=2, sticky="e", pady=0)

        self.lbl_activate.grid(row=7, column=1, columnspan=2, sticky="e")

        self.pidLbl()
        self.baseAddrLbl()
        self.monoAddrLbl()


    def _createTabFrames(self):
        # center frame tab control
        self.tab_control = ttk.Notebook(self.border, padding=0)

        # center frame main tab
        self.tab1 = tk.Frame(self.tab_control, bg=bg_color)
        self.tab_control.add(self.tab1, text="Main")

        ## center frame main tab variables
        self.STACK_ZONE = tk.StringVar()
        self.STEEL_STACKS = tk.StringVar()
        self.STACK_TIME = tk.StringVar()

        # center frame main tab stack zone / haste stacks input
        self.lbl_stackzone = tk.Label(self.tab1, fg=text_color, bg=bg_color, text=f"Stack Zone: ", font=('Tiamat Condensed SC', 20))
        self.ent_stackzone = tk.Entry(self.tab1, textvariable=self.STACK_ZONE, width=5, fg=text_color, justify="right", font=('Tiamat Condensed SC', 20), exportselection=0)        
        self.ent_stackzone.bind('<Return>', self._setStackZone)
        self.ent_stackzone.insert(tk.END, self.game.STACK_ZONE)

        self.lbl_steelstacks = tk.Label(self.tab1, fg=text_color, bg=bg_color, text=f"Steel Stacks: ", font=('Tiamat Condensed SC', 20))
        self.ent_steelstacks = tk.Entry(self.tab1, textvariable=self.STEEL_STACKS, width=5, fg=text_color, justify="right", font=('Tiamat Condensed SC', 20), exportselection=0)        
        self.ent_steelstacks.bind('<Return>', self._setSteelStacks)
        self.ent_steelstacks.insert(tk.END, self.game.STEEL_STACKS)

        self.lbl_stacktime = tk.Label(self.tab1, fg=text_color, bg=bg_color, text=f"Stack Time: ", font=('Tiamat Condensed SC', 20))
        self.ent_stacktime = tk.Entry(self.tab1, textvariable=self.STACK_TIME, width=5, fg=text_color, justify="right", font=('Tiamat Condensed SC', 20), exportselection=0)        
        self.ent_stacktime.bind('<Return>', self._setStackTime)
        self.ent_stacktime.insert(tk.END, self.game.STACK_TIME)

        self.OFFLINE_STACKING = tk.BooleanVar()
        self.offline_stacking_activate = tk.Checkbutton(self.tab1,
                                                        fg=text_color,
                                                        bg=bg_color,
                                                        text="Offline Stacking",
                                                        variable=self.OFFLINE_STACKING,
                                                        onvalue=1,
                                                        offvalue=0,
                                                        command=self._setOfflineStack)

        self.HIDE_WINDOW = tk.BooleanVar()
        self.hide_game = tk.Checkbutton(self.tab1,
                                        fg=text_color,
                                        bg=bg_color,
                                        text="Hide Game Window",
                                        variable=self.HIDE_WINDOW,
                                        onvalue=1,
                                        offvalue=0,
                                        command=self._hideWindow)

        # center frame main tab area level 
        self.lbl_area = tk.Label(self.tab1, fg=text_color, bg=bg_color, text="Area: ", font=('Tiamat Condensed SC', 20))
        self.lbl_area_value = tk.Label(self.tab1, fg=text_color, bg=bg_color, font=('Tiamat Condensed SC', 20))
        
        # center frame main tab modron reset level
        self.lbl_rst_area = tk.Label(self.tab1, fg=text_color, bg=bg_color, text="Reset Area: ", font=('Tiamat Condensed SC', 20))
        self.lbl_rst_area_value = tk.Label(self.tab1, fg=text_color, bg=bg_color, font=('Tiamat Condensed SC', 20))

        # center frame main tab game data labels
        self.lbl_clickDmg = tk.Label(self.tab1, fg=text_color, bg=bg_color, text="Click Damage: ", font=('Tiamat Condensed SC', 20))
        self.lbl_clickDmg_value = tk.Label(self.tab1, fg=text_color, bg=bg_color, font=('Tiamat Condensed SC', 20))
        self.lbl_bss = tk.Label(self.tab1, fg=text_color, bg=bg_color, text="Steel Stacks: ", font=('Tiamat Condensed SC', 20))
        self.lbl_bss_value = tk.Label(self.tab1, fg=text_color, bg=bg_color, font=('Tiamat Condensed SC', 20))
        self.lbl_bhs = tk.Label(self.tab1, fg=text_color, bg=bg_color, text="Haste Stacks: ", font=('Tiamat Condensed SC', 20))
        self.lbl_bhs_value = tk.Label(self.tab1, fg=text_color, bg=bg_color, font=('Tiamat Condensed SC', 20))

        # center frame main tab element layout
        self.lbl_stackzone.grid(row=0, column=0, sticky='w')
        self.ent_stackzone.grid(row=0, column=1)

        self.lbl_rst_area.grid(row=0, column=2, padx=20, sticky='w')
        self.lbl_rst_area_value.grid(row=0, column=3, sticky='e')

        self.lbl_steelstacks.grid(row=1, column=0, sticky='w')
        self.ent_steelstacks.grid(row=1, column=1)
        self.offline_stacking_activate.grid(row=1, column=2, columnspan=2, padx=18, sticky='w')
        
        self.lbl_stacktime.grid(row=2, column=0, sticky='w')
        self.ent_stacktime.grid(row=2, column=1)
        self.hide_game.grid(row=2, column=2, columnspan=2, padx=18, sticky='w')

        self.lbl_area.grid(row=3, column=0, sticky='w')
        self.lbl_area_value.grid(row=3, column=1, sticky='e')

        self.lbl_clickDmg.grid(row=4, column=0, sticky='w')
        self.lbl_clickDmg_value.grid(row=4, column=1, sticky='e')
        self.lbl_bss.grid(row=5, column=0, sticky='w')
        self.lbl_bss_value.grid(row=5, column=1, sticky='e')
        self.lbl_bhs.grid(row=6, column=0, sticky='w')
        self.lbl_bhs_value.grid(row=6, column=1, sticky='e')

        ## chest options tab
        self.chest_tab = tk.Frame(self.tab_control, bg=bg_color)
        self.tab_control.add(self.chest_tab, text="Chest Options")

        self.GEM_RESERVE = tk.StringVar()
        self.lbl_gem_reserve = tk.Label(self.chest_tab, fg=text_color, bg=bg_color, text=f"Gem Reserve: ", font=('Tiamat Condensed SC', 12))
        self.ent_gem_reserve = tk.Entry(self.chest_tab, textvariable=self.GEM_RESERVE, width=7, fg=text_color, justify="right", font=('Tiamat Condensed SC', 12), exportselection=0)
        self.ent_gem_reserve.bind('<Return>', self._setGemReserve)
        self.ent_gem_reserve.insert(tk.END, self.game.GEM_BANK)

        self.BUY_SILVER = tk.BooleanVar()
        self.buy_silver = tk.Checkbutton(self.chest_tab,
                                        fg=text_color,
                                        bg=bg_color,
                                        text="Buy Silver Chests",
                                        variable=self.BUY_SILVER,
                                        onvalue=1,
                                        offvalue=0,
                                        command=self._buySilver)

        self.BUY_SILVER_COUNT = tk.StringVar()
        self.lbl_buy_silver = tk.Label(self.chest_tab, fg=text_color, bg=bg_color, text=f"Silver to buy: ", font=('Tiamat Condensed SC', 12))
        self.ent_buy_silver = tk.Entry(self.chest_tab, textvariable=self.BUY_SILVER_COUNT, width=7, fg=text_color, justify="right", font=('Tiamat Condensed SC', 12), exportselection=0)        
        self.ent_buy_silver.bind('<Return>', self._setBuySilverCount)
        self.ent_buy_silver.insert(tk.END, self.game.BUY_SILVER_COUNT)

        self.BUY_GOLD = tk.BooleanVar()
        self.buy_gold = tk.Checkbutton(self.chest_tab,
                                        fg=text_color,
                                        bg=bg_color,
                                        text="Buy Gold Chests",
                                        variable=self.BUY_GOLD,
                                        onvalue=1,
                                        offvalue=0,
                                        command=self._buyGold)

        self.BUY_GOLD_COUNT = tk.StringVar()
        self.lbl_buy_gold = tk.Label(self.chest_tab, fg=text_color, bg=bg_color, text=f"Gold to buy: ", font=('Tiamat Condensed SC', 12))
        self.ent_buy_gold = tk.Entry(self.chest_tab, textvariable=self.BUY_GOLD_COUNT, width=7, fg=text_color, justify="right", font=('Tiamat Condensed SC', 12), exportselection=0)        
        self.ent_buy_gold.bind('<Return>', self._setBuyGoldCount)
        self.ent_buy_gold.insert(tk.END, self.game.BUY_GOLD_COUNT)

        self.OPEN_SILVER = tk.BooleanVar()
        self.open_silver = tk.Checkbutton(self.chest_tab,
                                        fg=text_color,
                                        bg=bg_color,
                                        text="Open Silver Chests",
                                        variable=self.OPEN_SILVER,
                                        onvalue=1,
                                        offvalue=0,
                                        command=self._openSilver)

        self.OPEN_GOLD = tk.BooleanVar()
        self.open_gold = tk.Checkbutton(self.chest_tab,
                                        fg=text_color,
                                        bg=bg_color,
                                        text="Open Gold Chests",
                                        variable=self.OPEN_GOLD,
                                        onvalue=1,
                                        offvalue=0,
                                        command=self._openGold)

        self.OPEN_EVENT = tk.BooleanVar()
        self.open_event = tk.Checkbutton(self.chest_tab,
                                        fg=text_color,
                                        bg=bg_color,
                                        text="Open Event Chests",
                                        variable=self.OPEN_EVENT,
                                        onvalue=1,
                                        offvalue=0,
                                        command=self._openEvent)

        self.OPEN_ELECTRUM = tk.BooleanVar()
        self.open_electrum = tk.Checkbutton(self.chest_tab,
                                        fg=text_color,
                                        bg=bg_color,
                                        text="Open Electrum Chests",
                                        variable=self.OPEN_ELECTRUM,
                                        onvalue=1,
                                        offvalue=0,
                                        command=self._openElectrum)

        self.OPEN_MODRON = tk.BooleanVar()
        self.open_modron = tk.Checkbutton(self.chest_tab,
                                        fg=text_color,
                                        bg=bg_color,
                                        text="Open Modron Chests",
                                        variable=self.OPEN_MODRON,
                                        onvalue=1,
                                        offvalue=0,
                                        command=self._openModron)

        self.OPEN_MIRT = tk.BooleanVar()
        self.open_mirt = tk.Checkbutton(self.chest_tab,
                                        fg=text_color,
                                        bg=bg_color,
                                        text="Open Mirt Chests",
                                        variable=self.OPEN_MIRT,
                                        onvalue=1,
                                        offvalue=0,
                                        command=self._openMirt)

        self.OPEN_VAJRA = tk.BooleanVar()
        self.open_vajra = tk.Checkbutton(self.chest_tab,
                                        fg=text_color,
                                        bg=bg_color,
                                        text="Open Vajra Chests",
                                        variable=self.OPEN_VAJRA,
                                        onvalue=1,
                                        offvalue=0,
                                        command=self._openVajra)

        self.OPEN_STRAHD = tk.BooleanVar()
        self.open_strahd = tk.Checkbutton(self.chest_tab,
                                        fg=text_color,
                                        bg=bg_color,
                                        text="Open Strahd Chests",
                                        variable=self.OPEN_STRAHD,
                                        onvalue=1,
                                        offvalue=0,
                                        command=self._openStrahd)

        self.OPEN_ZARIEL = tk.BooleanVar()
        self.open_zariel = tk.Checkbutton(self.chest_tab,
                                        fg=text_color,
                                        bg=bg_color,
                                        text="Open Zariel Chests",
                                        variable=self.OPEN_ZARIEL,
                                        onvalue=1,
                                        offvalue=0,
                                        command=self._openZariel)

        self.lbl_gem_reserve.grid(row=0, column=1, sticky='e')
        self.ent_gem_reserve.grid(row=0, column=2, sticky='e')

        self.buy_silver.grid(row=2, column=0, padx=10, sticky='w')
        self.lbl_buy_silver.grid(row=2, column=1, sticky='e')
        self.ent_buy_silver.grid(row=2, column=2, sticky='e')

        self.buy_gold.grid(row=3, column=0, padx=10, sticky='w')
        self.lbl_buy_gold.grid(row=3, column=1, sticky='e')
        self.ent_buy_gold.grid(row=3, column=2, sticky='e')

        self.open_silver.grid(row=4, column=0, padx=10, sticky='w')
        self.open_gold.grid(row=5, column=0, padx=10, sticky='w')
        self.open_event.grid(row=6, column=0, padx=10, sticky='w')
        self.open_electrum.grid(row=7, column=0, padx=10, sticky='w')
        self.open_modron.grid(row=8, column=0, padx=10, sticky='w')
        self.open_mirt.grid(row=9, column=0, padx=10, sticky='w')
        self.open_vajra.grid(row=10, column=0, padx=10, sticky='w')
        self.open_strahd.grid(row=11, column=0, padx=10, sticky='w')
        self.open_zariel.grid(row=12, column=0, padx=10, sticky='w')

        ## code claim tab
        # TODO create code claim tab

        # center frame automate log tab
        self.tab_automate = tk.Frame(self.tab_control, bg=bg_color)
        self.tab_control.add(self.tab_automate, text="Automate Log")
        self.tab_automate.after(1000, self.poll_log_queue)

        self.scrolled_text = ScrolledText(self.tab_automate, state='disabled', bg=bg_color)
        self.scrolled_text.grid(row=0, column=0, sticky='NSEW')

        # center frame layout
        self.tab_control.grid(row=1, sticky="nsew", padx=3)
        self.tab_control.grid_rowconfigure(0, weight=1, pad=0)
        self.tab_control.grid_rowconfigure(1, weight=1, pad=0)
        self.tab_control.grid_columnconfigure(0, weight=1)

        # center frame debug tab
        if args.d:
            self.tab2 = tk.Frame(self.tab_control, bg=bg_color)
            self.tab_control.add(self.tab2, text="Debug")        
        
            self.tab2.grid_propagate(False)
            self.tab2.grid_rowconfigure(0, weight=1)
            self.tab2.grid_columnconfigure(0, weight=1)

            self.scroll_bar = tk.Scrollbar(self.tab2, orient="vertical")
            self.scroll_bar.grid(row=0, column=10, sticky='ns')

            self.reset_stacking_button = tk.Button(self.tab2, text="Reset stacking", bg=bg_color, command=self._resetStacking)
            self.reset_stacking_button.grid(row=0, column=1, sticky="w", pady=1)

            # self.tab2.config(yscrollcommand=self.scroll_bar.set)
            # self.scroll_bar.config(command=self.tab2.yview)
        
        ## populate dynamic labels
        ## is this the way, or should this be something else
        ## functions used to display dynamic data 
        self.areaLbl()
        self.rstAreaLbl()
        self.clickDmgLbl()
        self.bssLbl()
        self.bhsLbl()


    def _createBottomFrame(self):
        self.bottom_frame = tk.Frame(self.border, bg=bg_color, height=20)
        self.bottom_frame.grid_rowconfigure(0, weight=0)
        self.bottom_frame.grid_columnconfigure(0, weight=0)
        self.bottom_frame.grid(row=2, sticky="ew", padx=3, pady=3)
     
        # # aligned
        self.lbl_aligned = tk.Label(self.bottom_frame, fg=text_color, bg=bg_color, text="aligned: ", font=('Tiamat Condensed SC', 12))
        self.lbl_aligned_value = tk.Label(self.bottom_frame, fg=text_color, bg=bg_color, font=('Tiamat Condensed SC', 12))
        self.lbl_aligned.grid(row=1, column=1, sticky="w")
        self.lbl_aligned_value.grid(row=1, column=2, sticky="w")

        # # aligning
        self.lbl_aligning = tk.Label(self.bottom_frame, fg=text_color, bg=bg_color, text="aligning: ", font=('Tiamat Condensed SC', 12))
        self.lbl_aligning_value = tk.Label(self.bottom_frame, fg=text_color, bg=bg_color, font=('Tiamat Condensed SC', 12))
        self.lbl_aligning.grid(row=1, column=3, sticky="w")
        self.lbl_aligning_value.grid(row=1, column=4, sticky="w")

        # # stacked
        self.lbl_stacked = tk.Label(self.bottom_frame, fg=text_color, bg=bg_color, text="stacked: ", font=('Tiamat Condensed SC', 12))
        self.lbl_stacked_value = tk.Label(self.bottom_frame, fg=text_color, bg=bg_color, font=('Tiamat Condensed SC', 12))
        self.lbl_stacked.grid(row=1, column=5)
        self.lbl_stacked_value.grid(row=1, column=6)

        # # stacking
        self.lbl_stacking = tk.Label(self.bottom_frame, fg=text_color, bg=bg_color, text="stacking: ", font=('Tiamat Condensed SC', 12))
        self.lbl_stacking_value = tk.Label(self.bottom_frame, fg=text_color, bg=bg_color, font=('Tiamat Condensed SC', 12))
        self.lbl_stacking.grid(row=1, column=7)
        self.lbl_stacking_value.grid(row=1, column=8)

        # # form 
        self.lbl_form = tk.Label(self.bottom_frame, fg=text_color, bg=bg_color, text="form: ", font=('Tiamat Condensed SC', 12))
        self.lbl_form_value = tk.Label(self.bottom_frame, fg=text_color, bg=bg_color, font=('Tiamat Condensed SC', 12))
        self.lbl_form.grid(row=1, column=9, sticky="e")
        self.lbl_form_value.grid(row=1, column=10, sticky="e")

        # # reset
        self.lbl_reset = tk.Label(self.bottom_frame, fg=text_color, bg=bg_color, text="reset: ", font=('Tiamat Condensed SC', 12))
        self.lbl_reset_value = tk.Label(self.bottom_frame, fg=text_color, bg=bg_color, font=('Tiamat Condensed SC', 12))
        self.lbl_reset.grid(row=1, column=11, sticky="e")
        self.lbl_reset_value.grid(row=1, column=12, sticky="e")

        # # resets
        self.lbl_resets = tk.Label(self.bottom_frame, fg=text_color, bg=bg_color, text="resets: ", font=('Tiamat Condensed SC', 12))
        self.lbl_resets_value = tk.Label(self.bottom_frame, fg=text_color, bg=bg_color, font=('Tiamat Condensed SC', 12))
        self.lbl_resets.grid(row=1, column=13, sticky="e")
        self.lbl_resets_value.grid(row=1, column=14, sticky="e")

        self.alignedLbl()
        self.aligningLbl()
        self.stackedLbl()
        self.stackingLbl()
        self.formLbl()
        self.resetLbl()
        self.resetsLbl()
            

    def pidLbl(self):
        pid = self.game.idlegame.pid
        self.lbl_pid_value.config(text=pid)
        self.win.after(1000, self.pidLbl)


    def baseAddrLbl(self):
        if self.game.idlegame.base_addr is not None:
            base_addr = f'{self.game.idlegame.base_addr:#x}'
        else:
            base_addr = "None"
        self.lbl_base_addr_value.config(text=base_addr)
        self.win.after(1000, self.baseAddrLbl)


    def monoAddrLbl(self):
        if self.game.idlegame.mono_addr is not None:
            mono_addr = f'{self.game.idlegame.mono_addr:#x}'
        else:
            mono_addr = "None"
        self.lbl_mono_addr_value.config(text=mono_addr)
        self.win.after(1000, self.monoAddrLbl)


    def areaLbl(self):
        area = self.game.idlegame.area
        self.lbl_area_value.config(text=area)
        self.win.after(500, self.areaLbl)


    def rstAreaLbl(self):
        rstArea = self.game.idlegame.modron_reset_level
        self.lbl_rst_area_value.config(text=rstArea)
        self.win.after(1000, self.rstAreaLbl)


    def clickDmgLbl(self):
        clickDmg = self.game.idlegame.click_damage
        self.lbl_clickDmg_value.config(text=clickDmg)
        self.win.after(1000, self.clickDmgLbl)


    def bssLbl(self):
        bss = self.game.idlegame.bs_stacks
        self.lbl_bss_value.config(text=bss)
        self.win.after(500, self.bssLbl)

    
    def bhsLbl(self):
        bhs = self.game.idlegame.bh_stacks
        self.lbl_bhs_value.config(text=bhs)
        self.win.after(1000, self.bhsLbl)


    def clockLbl(self):
        clock = self.game.clock
        self.lbl_clock_value.config(text=clock)
        self.win.after(1000, self.clockLbl)


    def alignedLbl(self):
        aligned = self.game.status['aligned']
        self.lbl_aligned_value.config(text=aligned)
        self.win.after(1000, self.alignedLbl)


    def aligningLbl(self):
        aligning = self.game.status['aligning']
        self.lbl_aligning_value.config(text=aligning)
        self.win.after(1000, self.aligningLbl)


    def stackedLbl(self):
        stacked = self.game.status['stacked']
        self.lbl_stacked_value.config(text=stacked)
        self.win.after(1000, self.stackedLbl)


    def stackingLbl(self):
        stacking = self.game.status['stacking']
        self.lbl_stacking_value.config(text=stacking)
        self.win.after(1000, self.stackingLbl)
    

    def formLbl(self):
        form = self.game.status['form']
        self.lbl_form_value.config(text=form)
        self.win.after(1000, self.formLbl)
    

    def resetLbl(self):
        reset = self.game.status['reset']
        self.lbl_reset_value.config(text=reset)
        self.win.after(1000, self.resetLbl)

    def resetsLbl(self):
        resets = self.game.resets
        self.lbl_resets_value.config(text=resets)
        self.win.after(1000, self.resetsLbl)


    def debugTable(self):
        result = []
        debug_table = self.game.idlegame._mono_table
        id = 0
        for d in debug_table:
            result.append((id, hex(d[0]), hex(d[1])))
            id += 1
        return result


    def _setStackZone(self, value):
        self.game.STACK_ZONE = self.STACK_ZONE.get()


    def _setSteelStacks(self, value):
        self.game.STEEL_STACKS = self.STEEL_STACKS.get()


    def _setStackTime(self, value):
        self.game.STACK_TIME = self.STACK_TIME.get()


    def _resetStacking(self):
        self.game.status['stacking'] = False


    def _setOfflineStack(self):
        if self.OFFLINE_STACKING.get() == True:
            logger.log(logging.INFO, "Offline stacking on")
        else:
            logger.log(logging.INFO, "Offline stacking off")
        self.game.offline_stacking = self.OFFLINE_STACKING.get()


    def _hideWindow(self):
        if self.HIDE_WINDOW.get() == True:
            logger.log(logging.INFO, "Hide game window on")
        else:
            logger.log(logging.INFO, "Hide game window off")
        self.game.hide_window = self.HIDE_WINDOW.get()


    def _setGemReserve(self, value):
        self.game.GEM_BANK = self.GEM_RESERVE.get()


    def _buySilver(self):
        if self.BUY_SILVER.get() == True:
            logger.log(logging.INFO, "Buy Silver Chests on")
        else:
            logger.log(logging.INFO, "Buy Silver Chests off")
        self.game.BUY_SILVER = self.BUY_SILVER.get()


    def _setBuySilverCount(self, value):
        self.game.BUY_SILVER_COUNT = self.BUY_SILVER_COUNT.get()


    def _buyGold(self):
        if self.BUY_GOLD.get() == True:
            logger.log(logging.INFO, "Buy Gold Chests on")
        else:
            logger.log(logging.INFO, "Buy Gold Chests off")
        self.game.BUY_GOLD = self.BUY_GOLD.get()


    def _setBuyGoldCount(self, value):
        self.game.BUY_GOLD_COUNT = self.BUY_GOLD_COUNT.get()


    def _openSilver(self):
        if self.OPEN_SILVER.get() == True:
            logger.log(logging.INFO, "Open Silver Chests on")
        else:
            logger.log(logging.INFO, "Open Silver Chests off")
        self.game.OPEN_SILVER = self.OPEN_SILVER.get()


    def _openGold(self):
        if self.OPEN_GOLD.get() == True:
            logger.log(logging.INFO, "Open Gold Chests on")
        else:
            logger.log(logging.INFO, "Open Gold Chests off")
        self.game.OPEN_GOLD = self.OPEN_GOLD.get()


    def _openEvent(self):
        if self.OPEN_EVENT.get() == True:
            logger.log(logging.INFO, "Open Event Chests on")
        else:
            logger.log(logging.INFO, "Open Event Chests off")
        self.game.OPEN_EVENT = self.OPEN_EVENT.get()


    def _openElectrum(self):
        if self.OPEN_ELECTRUM.get() == True:
            logger.log(logging.INFO, "Open Electrum Chests on")
        else:
            logger.log(logging.INFO, "Open Electrum Chests off")
        self.game.OPEN_ELECTRUM = self.OPEN_ELECTRUM.get()


    def _openModron(self):
        if self.OPEN_MODRON.get() == True:
            logger.log(logging.INFO, "Open Modron Chests on")
        else:
            logger.log(logging.INFO, "Open Modron Chests off")
        self.game.OPEN_MODRON = self.OPEN_MODRON.get()


    def _openMirt(self):
        if self.OPEN_MIRT.get() == True:
            logger.log(logging.INFO, "Open Mirt Chests on")
        else:
            logger.log(logging.INFO, "Open Mirt Chests off")
        self.game.OPEN_MIRT = self.OPEN_MIRT.get()


    def _openVajra(self):
        if self.OPEN_VAJRA.get() == True:
            logger.log(logging.INFO, "Open Vajra Chests on")
        else:
            logger.log(logging.INFO, "Open Vajra Chests off")
        self.game.OPEN_VAJRA = self.OPEN_VAJRA.get()


    def _openStrahd(self):
        if self.OPEN_STRAHD.get() == True:
            logger.log(logging.INFO, "Open Strahd Chests on")
        else:
            logger.log(logging.INFO, "Open Strahd Chests off")
        self.game.OPEN_STRAHD = self.OPEN_STRAHD.get()


    def _openZariel(self):
        if self.OPEN_ZARIEL.get() == True:
            logger.log(logging.INFO, "Open Zariel Chests on")
        else:
            logger.log(logging.INFO, "Open Zariel Chests off")
        self.game.OPEN_ZARIEL = self.OPEN_ZARIEL.get()


    def stackZoneLbl(self):
        pass

    
    def automate(self):
        # needs work on proper thread control, this breaks during restarts?
        if self.AUTOMATE.get() == True:
            logger.log(logging.INFO, 'Automate on')
            self.x = threading.Thread(target=self.game.automate).start()
        elif self.AUTOMATE.get() == False:
            logger.log(logging.INFO, 'Automate off')
            self.game.stop()
