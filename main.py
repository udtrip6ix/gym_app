from kivy.config import Config
Config.set('graphics', 'width', '360')
Config.set('graphics', 'height', '640')
Config.set('graphics', 'resizable', '0')


from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.lang import Builder
from kivy.uix.button import Button
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
import sqlite3



class MenuScreen(Screen):
    pass

class EditorScreen(Screen):
    pass

class NewWorkoutScreen(Screen):
    def create_workout(self, date, bodyweight):
        if not date.strip():
            return
        
        weight = float(bodyweight) if bodyweight.strip() else None

        conn = sqlite3.connect('tracker.db')
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO workouts (date, bodyweight) VALUES (?, ?)',
            (date, weight)
        )
        conn.commit()
        conn.close()
        self.ids.workout_date.text = ''
        self.ids.bodyweight.text = ''
        self.manager.current = 'workouts'

class WorkoutsScreen(Screen):
    def on_enter(self):
        self.load_workouts()

    def load_workouts(self):
        workout_list=self.ids.workout_list
        workout_list.clear_widgets()
    
        conn = sqlite3.connect('tracker.db')
        cursor = conn.cursor()
        cursor.execute('SELECT id, date FROM workouts ORDER BY date DESC')
        rows = cursor.fetchall()
        conn.close()

        for row in rows:
            btn = Button(text=row[1], size_hint_y=None, height=50)
            workout_list.add_widget(btn)

        
class ExerciseItem(BoxLayout):
    def __init__(self, exercise_id, name, screen, **kwargs):
            super().__init__(**kwargs)
            self.orientation='horizontal'
            self.size_hint_y=None
            self.height=50

            self.add_widget(Label(text=name))

            btn=Button(text='X', size_hint_x=0.2)
            btn.bind(on_press=lambda x: self.delete_exercise(exercise_id, screen))
            self.add_widget(btn)
    def delete_exercise(self, exercise_id, screen):
         conn = sqlite3.connect('tracker.db')
         cursor=conn.cursor()
         cursor.execute('DELETE FROM exercises WHERE id = ?', (exercise_id,))
         conn.commit()
         conn.close()
         screen.load_exercises()
         


class ExercisesScreen(Screen):
    def on_enter(self):
        self.load_exercises()

    def load_exercises(self):
        exercise_list = self.ids.exercise_list
        exercise_list.clear_widgets()

        conn = sqlite3.connect('tracker.db')
        cursor = conn.cursor()
        cursor.execute('SELECT id, name FROM exercises')
        rows = cursor.fetchall()
        conn.close()

        for row in rows:
            item = ExerciseItem(exercise_id=row[0], name=row[1], screen=self)
            exercise_list.add_widget(item)

    def save_exercise(self, text):
            if not text.strip():
                return
            conn = sqlite3.connect('tracker.db')
            cursor = conn.cursor()
            cursor.execute('INSERT INTO exercises (name) VALUES (?)', (text,))
            conn.commit()
            conn.close()
            self.ids.exercise_name.text = ''
            self.load_exercises()

class TrackerApp(App):
    def build(self):
        self.init_db()
        return Builder.load_file('kv/tracker.kv')
    
    def init_db(self):
        conn = sqlite3.connect('tracker.db')
        cursor = conn.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS exercises
            (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL)
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS workouts
            (id INTEGER PRIMARY KEY AUTOINCREMENT, 
            date TEXT NOT NULL,
            bodyweight REAL)
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS workout_sets
            (id INTEGER PRIMARY KEY AUTOINCREMENT,
            workout_id INTEGER NOT NULL,
            exercise_id INTEGER NOT NULL,
            sets INTEGER NOT NULL,
            reps INTEGER NOT NULL,
            weight REAL NOT NULL)
        ''')
        
        conn.commit()
        conn.close()

if __name__=='__main__':
    TrackerApp().run()