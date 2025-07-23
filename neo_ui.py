import tkinter as tk
import threading
import time

class HPMonitorUI(tk.Tk):
    def __init__(self, mem_manager, game_data):
        super().__init__()

        self.refresh_rate=(int)(1000/60)

        self.allow_encounter=True
        self.force_encounter=False

        self.mem_manager = mem_manager
        self.game_data = game_data

        self.title("Tantalus Trainer")
        self.geometry("520x600")
        self.configure(bg="#1e1e1e")

        self.status_label = tk.Label(self, text="Not attached", fg="white", bg="#1e1e1e", font=("Arial", 12))
        self.status_label.pack(pady=5)

        self.scene_label = tk.Label(self, text="Scene Type: N/A | Scene ID: N/A", fg="white", bg="#1e1e1e", font=("Arial", 10))
        self.scene_label.pack(pady=2)

        self.timer_label = tk.Label(self, text="Timer: N/A", fg="white", bg="#1e1e1e", font=("Arial", 10))
        self.timer_label.pack(pady=5)

        self.battle_frame = tk.Frame(self, bg="#1e1e1e")
        self.battle_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.battle_widgets = {}
        self.battle_display_data = {}
        self.battle_pointer_map = {}
        self.battle_turns_data={}

        self.timer_address = None
        self.running = True

        threading.Thread(target=self.attach_loop, daemon=True).start()

        self.protocol("WM_DELETE_WINDOW", self.on_close)
        self.after(self.refresh_rate, self.update_loop)


    def attach_loop(self):
        while self.running:
            if not getattr(self.mem_manager, "attached", False):
                if self.mem_manager.attach():
                    self.status_label.config(text=f"Attached to {self.mem_manager.process_name}")
                else:
                    self.status_label.config(text=f"Waiting to attach to {self.mem_manager.process_name}...")
            time.sleep(2)



    def update_loop(self):
        if not getattr(self.mem_manager, "attached", False):
            self.status_label.config(text=f"Not attached to {self.mem_manager.process_name}")
            self.after(self.refresh_rate, self.update_loop)
            return

        self.game_data.override_taddler()

        scene_type = self.game_data.get_scene_type()
        scene_id = self.game_data.get_scene_id()

        if (scene_type != getattr(self, 'previous_scene_type', None)) or (scene_id != getattr(self, 'previous_scene_id', None)):
            self.clear_data_bars()

        self.previous_scene_type = scene_type
        self.previous_scene_id = scene_id

        self.scene_label.config(text=f"Scene Type: {scene_type if scene_type is not None else 'N/A'} | Scene ID: {scene_id if scene_id is not None else 'N/A'}")
     
        if scene_type == 3:
            self.status_label.config(text="Battle active: Tracking bosses")
            battle_data = self.game_data.scan_battle_pointers()
            battle_key = self.game_data.get_battle_key(scene_type, scene_id)
            self.update_battle_bars(battle_data, battle_key)
            self.timer_label.config(text="")
        else:
            self.timer_address = self.game_data.get_timer_address()
            raw_value=self.mem_manager.read_float(self.timer_address) 
            danger_value=f"{raw_value:07.3f}"
            is_check=raw_value==0                 
            msg=f"DANGER : {danger_value}"

            if is_check:
                self.timer_label.config(text=f"DANGER : CHECK !", fg="yellow")
            else:
                self.timer_label.config(text=f"{msg}",fg="white")
           
            self.game_data.active_pointers=[]
            self.battle_turns_data={}
            self.status_label.config(text="Waiting for battle to start...")

        self.after(self.refresh_rate, self.update_loop)

    def update_battle_bars(self, battle_data, battle_key):
        enemies = self.game_data.boss_data.get("battles", {}).get(battle_key, [])

        for enemy in enemies:
            raw_max_hp = enemy['max_hp']
            name = enemy.get("name", "Unknown")
            override = enemy.get("max_hp_override")
            override_val = None

            if override:
                try:
                    val = int(override)
                    if 0 < val < raw_max_hp:
                        override_val = val
                except:
                    pass

            for ptr, vals in battle_data.items():
                curr_hp=vals['curr_hp']
                max_hp=vals['max_hp']
                curr_mp=vals['curr_mp']
                max_mp=vals['max_mp']
                curr_atb=vals['curr_atb']
                max_atb=vals['max_atb']               
                had_turn = vals['had_turn']   
                
                if max_hp == raw_max_hp:
                    # Apply override to curr_hp if applicable
                    if override_val is not None and override_val < raw_max_hp:
                        curr_hp = max(0, curr_hp - (raw_max_hp - override_val))
                        max_hp = override_val
                    
                    self.battle_pointer_map[ptr] = ptr
                    self.battle_display_data[ptr] = (curr_hp, max_hp,curr_mp,max_mp,curr_atb,max_atb, name, override_val, raw_max_hp)
    
                    if ptr not in self.battle_turns_data:
                        self.battle_turns_data[ptr]=0
                    self.battle_turns_data[ptr]+=had_turn

                    if ptr not in self.battle_widgets:
                        frame = tk.Frame(self.battle_frame, bg="#1e1e1e")
                        frame.pack(fill=tk.X, pady=2)
                        label = tk.Label(frame, text="", fg="white", bg="#1e1e1e", anchor="w")
                        label.pack(fill=tk.X)
                        canvas = tk.Canvas(frame, height=20, bg="#1e1e1e", highlightthickness=0)
                        canvas.pack(fill=tk.X, pady=2)
                        bg_rect = canvas.create_rectangle(0, 0, 0, 48, fill="gray", width=0)
                        atb_rect= canvas.create_rectangle(0, 0, 0, 16, fill="cyan", width=0) 
                        mp_rect = canvas.create_rectangle(0, 0, 0, 32, fill="pink", width=0) 
                        hp_rect = canvas.create_rectangle(0, 0, 0, 48, fill="green", width=0)
                        self.battle_widgets[ptr] = (frame, label, canvas,hp_rect, mp_rect,atb_rect,bg_rect)

                    self.update_bar(ptr)

    def update_bar(self, ptr):
                
        if ptr in self.battle_display_data and ptr in self.battle_widgets and ptr in self.battle_turns_data:

            curr_hp, max_hp,curr_mp,max_mp,curr_atb,max_atb, name, _, _ = self.battle_display_data[ptr]
            frame, label, canvas, hp_rect,mp_rect,atb_rect,bg_rect = self.battle_widgets[ptr]
            turns =  self.battle_turns_data[ptr]
            
            hp_percentage = max(0.0, min(curr_hp / max_hp if max_hp else 0, 1.0)) 
            mp_percentage = max(0.0, min(curr_mp / max_mp if max_mp else 0, 1.0))              
            atb_percentage=curr_atb/max_atb
    
            label.config(text=f"{name}: HP {curr_hp}/{max_hp} MP {curr_mp}/{max_mp} - turns :{turns}")

            canvas_width = canvas.winfo_width() or 200
            hp_bar_width = int(canvas_width * hp_percentage)   
            mp_bar_width = int(canvas_width * mp_percentage)         
            atb_width = int(canvas_width*atb_percentage)

            if hp_percentage > 0.5:
                color = "lime green"
            elif hp_percentage > 0.3:
                color = "yellow"
            elif hp_percentage > 0.1:
                color = "orange"
            else:
                color = "red"

        canvas.coords(bg_rect, 0, 0, canvas_width, 48)
        canvas.coords(atb_rect, 0, 16, atb_width, 32)
        canvas.coords(mp_rect,  0, 8, mp_bar_width, 16)
        canvas.coords(hp_rect,  0, 0, hp_bar_width, 8)
   
   
        canvas.itemconfig(bg_rect, fill="gray")
        canvas.itemconfig(atb_rect, fill="cyan")
        canvas.itemconfig(mp_rect, fill="pink")
        canvas.itemconfig(hp_rect, fill=color)

            
    def clear_data_bars(self):
        for frame, label, canvas, hp_rect,mp_rect,atb_rect,bg_rect in self.battle_widgets.values():
            frame.destroy()
        self.battle_widgets.clear()
        self.battle_display_data.clear()
        self.battle_pointer_map.clear()

    def on_close(self):
        self.running = False
        self.destroy()