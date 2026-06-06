from kivy.app import App
from kivy.lang import Builder
import sqlite3
from kivy.config import Config
from kivy.uix.boxlayout import BoxLayout

# Настройки окна
Config.set('graphics', 'width', '360')
Config.set('graphics', 'height', '640')
Config.set('graphics', 'resizable', '0')

class MainScreen(BoxLayout):
    pass

def init_db():
    conn = sqlite3.connect('tracker.db')
    cursor = conn.cursor()
    cursor.execute('PRAGMA journal_mode=WAL;') #для просмотра в дбивере
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS exercises (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

class TrackerApp(App):
    def build(self):
        Builder.load_file('kv/tracker.kv')
        self.root_widget = MainScreen()
        self.load_exercises() 
        return self.root_widget
    
    def save_exercise(self, text):
        if not text.strip():
            return

        conn = sqlite3.connect('tracker.db')
        cursor = conn.cursor()
        cursor.execute('INSERT INTO exercises (name) VALUES (?)', (text,))
        conn.commit()
        conn.close()
        
        print(f"Упражнение '{text}' сохранено!")
        
        self.root_widget.ids.exercise_name.text = ""
        self.load_exercises()

    def load_exercises(self):
        conn = sqlite3.connect('tracker.db')
        cursor = conn.cursor()
        cursor.execute('SELECT name FROM exercises')
        rows = cursor.fetchall()
        conn.close()
        

        self.root_widget.ids.exercise_list.data = [{'text': row[0]} for row in rows]

if __name__ == '__main__':
    init_db()
    TrackerApp().run()