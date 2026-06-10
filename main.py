from kivy.app import App
from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.properties import NumericProperty, StringProperty
import sqlite3
from kivy.config import Config

# Настройки окна
Config.set('graphics', 'width', '360')
Config.set('graphics', 'height', '640')
Config.set('graphics', 'resizable', '0')

# Классы экранов
class MenuScreen(Screen): pass
class EditorScreen(Screen): pass


class ExercisesScreen(Screen):
    def load_exercises(self):
        conn = sqlite3.connect('tracker.db')
        cursor = conn.cursor()
        cursor.execute('SELECT id, name FROM exercises')
        rows = cursor.fetchall()
        conn.close()
        self.ids.exercise_list.data = [{'text': row[1], 'exercise_id': row[0]} for row in rows]



class ExerciseItem(BoxLayout):
    text = StringProperty()
    exercise_id = NumericProperty()

    def delete_exercise(self):
        conn = sqlite3.connect('tracker.db')
        cursor = conn.cursor()
        cursor.execute('DELETE FROM exercises WHERE id = ?', (self.exercise_id,))
        conn.commit()
        conn.close()
        App.get_running_app().root.get_screen('exercises').load_exercises()

class TrackerApp(App):
    def build(self):
        self.init_db()
        return Builder.load_file('kv/tracker.kv')

    def init_db(self):
        conn = sqlite3.connect('tracker.db')
        cursor = conn.cursor()
        cursor.execute('PRAGMA journal_mode=WAL;')
        cursor.execute('''CREATE TABLE IF NOT EXISTS exercises 
                          (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL)''')
        conn.commit()
        conn.close()

    def save_exercise(self, text):
        if not text.strip(): return
        conn = sqlite3.connect('tracker.db')
        cursor = conn.cursor()
        cursor.execute('INSERT INTO exercises (name) VALUES (?)', (text,))
        conn.commit()
        conn.close()

        self.root.get_screen('exercises').load_exercises()

    def load_exercises(self):

        self.root.get_screen('exercises').load_exercises()

if __name__ == '__main__':
    TrackerApp().run()