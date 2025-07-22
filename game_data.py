import json
import os

JSON_FILE = "boss_data.json"

class FF9GameData:
    def __init__(self, mem_manager):
        self.mem = mem_manager

        self.event_base_offset = 0x011167C8
        self.event_timer_offset = [0x698, 0x4E8, 0x10, 0x98, 0x918, 0x148, 0x700]

        self.scene_base_offset = 0x0115BEA8
        self.scene_offsets = [0x48, 0x10, 0x98, 0x270, 0x10, 0x140]
        self.scene_id_offsets = [0x28, 0x10, 0x0, 0x120, 0x30, 0x28, 0x10, 0x10, 0x5C]

        self.base_address_offset = 0x01071080

        self.active_pointers=[]

        # pointer to BTL_DATA[]
        self.btl_data = [
            [0x28, 0x10, 0x0, 0x120, 0x40, 0x50, 0x68,0x18],
            [0x28, 0x10, 0x0, 0x120, 0x40, 0x50, 0x68,0x28],
            [0x28, 0x10, 0x0, 0x120, 0x40, 0x50, 0x38],
        ]

        # HP pointer chains IN BTL_LIST
        self.hp_chains = [
            [0x28, 0x10, 0x0, 0x120, 0x40, 0x50, 0x68, 0x10, 0x30, 0x10],
        ]
        
        self.max_hp_chains = [
            [0x28, 0x10, 0x0, 0x120, 0x40, 0x50, 0x68, 0x10, 0x28, 0x10],
        ]
        
        self.atb_chains =[
            [0x28, 0x10, 0x0, 0x120, 0x40, 0x50, 0x68, 0x10, 0x30, 0x14],
        ]
        
        self.max_atb_chains =[
            [0x28, 0x10, 0x0, 0x120, 0x40, 0x50, 0x68, 0x10, 0x28, 0x14],
        ]


        self.battle_data = {}
        self.atb_data = {}

        # Load JSON boss data
        self.boss_data = self.load_boss_data()

    def load_boss_data(self):
        if os.path.exists(JSON_FILE):
            try:
                with open(JSON_FILE, "r") as f:
                    data = json.load(f)
                if "battles" not in data:
                    data["battles"] = {}
                # Ensure max_hp_override key exists for each enemy
                for battle_key, enemies in data["battles"].items():
                    for enemy in enemies:
                        if "max_hp_override" not in enemy:
                            enemy["max_hp_override"] = None
                return data
            except Exception as e:
                print(f"[!] Failed to load {JSON_FILE}: {e}")
        # Default empty structure
        return {"battles": {}}

    def get_scene_type(self):
        if not self.mem.attached:
            return None
        base_addr = self.mem.base_module + self.scene_base_offset
        addr = self.mem.read_pointer_chain(base_addr, self.scene_offsets)
        if addr:
            return self.mem.read_int(addr)
        return None

    def get_scene_id(self):
        if not self.mem.attached:
            return None
        base_addr = self.mem.base_module + self.base_address_offset
        addr = self.mem.read_pointer_chain(base_addr, self.scene_id_offsets)
        if addr:
            return self.mem.read_int(addr)
        return None

    def get_timer(self):
        if not self.mem.attached:
            return None
        base_addr = self.mem.base_module + self.event_base_offset
        timer_obj_ptr = self.mem.read_pointer_chain(base_addr, self.event_timer_offset)
        if timer_obj_ptr is None or timer_obj_ptr == 0:
            return None
        timer_value_addr = timer_obj_ptr + 0x140
        return self.mem.read_float(timer_value_addr)

    def get_timer_address(self):
        if not self.mem.attached:
            return None
        base_addr = self.mem.base_module + self.event_base_offset
        timer_obj_ptr = self.mem.read_pointer_chain(base_addr, self.event_timer_offset)
        if timer_obj_ptr is None or timer_obj_ptr == 0:
            return None
        return timer_obj_ptr + 0x140

    def scan_battle_pointers(self):
        if not self.mem.attached:
            return {}
        self.battle_data = self.read_BTL_Data_list()
        #self.battle_data.update(self.read_BTL_Data_array())
        return self.battle_data

    def read_BTL_Data(self,btl_ptr):
        data={}
        try:
            curr_stats_ptr = self.mem.read_int(btl_ptr + 0x30)
            data['curr_hp'] = self.mem.read_ushort(curr_stats_ptr + 0x10)
            data['curr_mp'] = self.mem.read_ushort(curr_stats_ptr + 0x12)
            data['curr_atb'] = self.mem.read_ushort(curr_stats_ptr + 0x14)
            max_stats_ptr = self.mem.read_int(btl_ptr + 0x28)
            data['max_hp'] = self.mem.read_ushort(max_stats_ptr + 0x10)
            data['max_mp'] = self.mem.read_ushort(max_stats_ptr + 0x12)
            data['max_atb'] = self.mem.read_ushort(max_stats_ptr + 0x14)
            if data['curr_hp'] is None:
                return None
            if btl_ptr in self.atb_data:
                if self.atb_data[btl_ptr] > data['curr_atb']:
                    #this means the enemy had a turn...
                    data['had_turn']=1
                else:
                    data['had_turn']=0                        
            else:
                data['had_turn']=0                   
            self.atb_data[btl_ptr]=data['curr_atb']
        except Exception:
            return None 
        return data

    def read_BTL_Data_array(self):
        base_addr = self.mem.base_module + self.base_address_offset
        btl_data = {}
        
        for ptr in self.active_pointers:
            data = self.read_BTL_Data(ptr)
            if data is not None:                 
                btl_data[ptr]=data   
        
        for j in range(3):
            btl_data_ptr = self.mem.read_int(self.mem.read_pointer_chain(base_addr, self.btl_data[j]))            
            if(btl_data_ptr is not None):
                for i in range(8):
                    addr = btl_data_ptr + i * 8
                    ptr = self.mem.read_int(addr)
                    if ptr is not None and ptr not in self.active_pointers and ptr> 0:
                        data = self.read_BTL_Data(ptr)
                        self.active_pointers.append(ptr)
                        if data is not None and data['curr_hp'] is not None and data['curr_hp']>0:                 
                            btl_data[ptr]=data
                            
        return btl_data

    def read_BTL_Data_list(self):
        btl_data = {}
        for ptr in self.active_pointers:
            data = self.read_BTL_Data(ptr)
            if data is not None:                 
                btl_data[ptr]=data   
        
        base_addr = self.mem.base_module + self.base_address_offset
        
        btl_data_offsets=[0x28, 0x10, 0x0, 0x120, 0x40, 0x50, 0x68]
        btl_data_ptr = self.mem.read_int(self.mem.read_pointer_chain(base_addr, btl_data_offsets))            
        data = self.read_BTL_Data(btl_data_ptr)
        
        if data is not None and data['curr_hp'] is not None and data['curr_hp']>0:                 
            btl_data[btl_data_ptr]=data
        
        while(btl_data_ptr is not None):
            btl_data_offsets.append(0x10)
            btl_data_ptr = self.mem.read_int(self.mem.read_pointer_chain(base_addr, btl_data_offsets))            
            data = self.read_BTL_Data(btl_data_ptr)
            if data is not None and data['curr_hp'] is not None and data['curr_hp']==data['max_hp']:                 
                btl_data[btl_data_ptr]=data
                self.active_pointers.append(btl_data_ptr)
                          
        return btl_data


    def get_battle_key(self, scene_type, scene_id):
        if scene_type is None or scene_id is None:
            return None
        return f"{scene_type}-{scene_id}"

    def get_enemy_name_and_override(self, battle_key, max_hp):
        """Return tuple (name, max_hp_override) matching max_hp in the battle data"""
        if battle_key is None:
            return ("Unknown", None)
        enemies = self.boss_data.get("battles", {}).get(battle_key, [])
        for enemy in enemies:
            if enemy.get("max_hp") == max_hp:
                return (enemy.get("name", "Unknown"), enemy.get("max_hp_override"))
        return ("Unknown", None)

    def set_max_hp_override(self, battle_key, max_hp, override_value):
        if battle_key is None:
            return False
        enemies = self.boss_data.get("battles", {}).get(battle_key, [])
        for enemy in enemies:
            if enemy.get("max_hp") == max_hp:
                enemy["max_hp_override"] = override_value
                self.save_boss_data()
                return True
        return False
