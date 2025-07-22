from memory_manager import MemoryManager
from game_data import FF9GameData
from neo_ui import HPMonitorUI

def main():
    process_name = "FF9.exe"
    mem_manager = MemoryManager(process_name)
    game_data = FF9GameData(mem_manager)
    app = HPMonitorUI(mem_manager, game_data)
    app.protocol("WM_DELETE_WINDOW", app.on_close)
    app.mainloop()

if __name__ == "__main__":
    main()
