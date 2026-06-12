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
from datetime import date

class MenuScreen(Screen):
    pass

class EditorScreen(Screen):
    pass


class ExercisePickerScreen(Screen):
    def on_enter(self):
        self.load_exercises()

    def load_exercises(self):
        picker_list = self.ids.picker_list
        picker_list.clear_widgets()

        conn = sqlite3.connect('tracker.db')
        cursor = conn.cursor()
        cursor.execute('SELECT id, name FROM exercises')
        rows = cursor.fetchall()
        conn.close()

        for row in rows:
            btn = Button(
                text=row[1],
                size_hint_y=None,
                height=50
            )
            btn.bind(on_press=lambda x, eid=row[0], ename=row[1]: self.select_exercise(eid, ename))
            picker_list.add_widget(btn)

    def select_exercise(self, exercise_id, exercise_name):
        self.manager.current = 'new_workout'
        new_workout_screen = self.manager.get_screen('new_workout')
        new_workout_screen.on_exercise_selected(exercise_id, exercise_name)
        

class NewWorkoutScreen(Screen):
    def create_workout(self, date, bodyweight, description):
        if not date.strip():
            return
        conn = sqlite3.connect('tracker.db')
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO workouts (date, bodyweight, description) VALUES (?, ?, ?)',
            (date, float(bodyweight) if bodyweight.strip() else None, description)
        )
        conn.commit()
        conn.close()
        self.ids.workout_date.text = ''
        self.ids.bodyweight.text = ''
        self.ids.workout_desc.text = ''
        self.manager.current = 'workouts'
    def set_today_date(self):
        from datetime import date
        self.ids.workout_date.text = date.today().strftime('%d.%m.%Y')

class WorkoutItem(BoxLayout):
    def __init__(self, workout_id, date, bodyweight, description, screen, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'horizontal'
        self.size_hint_y = None
        self.height = 80

        btn_main = Button(
            text=f"{description or 'Без описания'}\n{date} | Вес: {bodyweight or '-'}",
            halign='center',
            valign='middle',
        )
        btn_main.bind(size=btn_main.setter('text_size'))
        btn_main.bind(on_press=lambda x: screen.open_workout(workout_id))
        self.add_widget(btn_main)

        btn_delete = Button(text='X', size_hint_x=0.2)
        btn_delete.bind(on_press=lambda x: self.delete_workout(workout_id, screen))
        self.add_widget(btn_delete)

    def delete_workout(self, workout_id, screen):
        conn = sqlite3.connect('tracker.db')
        cursor = conn.cursor()
        cursor.execute('DELETE FROM workouts WHERE id = ?', (workout_id,))
        conn.commit()
        conn.close()
        screen.load_workouts()

    def delete_workout(self, workout_id, screen):
        conn = sqlite3.connect('tracker.db')
        cursor = conn.cursor()
        cursor.execute('DELETE FROM workouts WHERE id = ?', (workout_id,))
        conn.commit()
        conn.close()
        screen.load_workouts()

class WorkoutsScreen(Screen):
    def on_enter(self):
        self.load_workouts()

    def open_workout(self, workout_id):
        pass
    
    def load_workouts(self):
        workout_list = self.ids.workout_list
        workout_list.clear_widgets()
    
        conn = sqlite3.connect('tracker.db')
        cursor = conn.cursor()
        cursor.execute('SELECT id, date, bodyweight, description FROM workouts ORDER BY date DESC')
        rows = cursor.fetchall()
        conn.close()

        for row in rows:
            item = WorkoutItem(
                workout_id=row[0], 
                date=row[1], 
                bodyweight=row[2], 
                description=row[3], 
                screen=self
            )
            workout_list.add_widget(item)

class ExerciseItem(BoxLayout):
    def __init__(self, exercise_id, name, screen, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'horizontal'
        self.size_hint_y = None
        self.height = 50
        self.add_widget(Label(text=name))
        btn = Button(text='X', size_hint_x=0.2)
        btn.bind(on_press=lambda x: self.delete_exercise(exercise_id, screen))
        self.add_widget(btn)

    def delete_exercise(self, exercise_id, screen):
        conn = sqlite3.connect('tracker.db')
        cursor = conn.cursor()
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
        cursor.execute('CREATE TABLE IF NOT EXISTS exercises (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL)')
        cursor.execute('CREATE TABLE IF NOT EXISTS workouts (id INTEGER PRIMARY KEY AUTOINCREMENT, date TEXT NOT NULL, bodyweight REAL, description TEXT)')
        cursor.execute('CREATE TABLE IF NOT EXISTS workout_sets (id INTEGER PRIMARY KEY AUTOINCREMENT, workout_id INTEGER NOT NULL, exercise_id INTEGER NOT NULL, sets INTEGER NOT NULL, reps INTEGER NOT NULL, weight REAL NOT NULL)')
        conn.commit()
        conn.close()

if __name__ == '__main__':
    TrackerApp().run()