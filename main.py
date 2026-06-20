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
from kivy.uix.textinput import TextInput
from kivy.uix.image import Image
from kivy.uix.behaviors import ButtonBehavior
from kivy.clock import Clock
import sqlite3
import time
from datetime import date

class SetTextInput(TextInput):
    pass


class MenuScreen(Screen):
    pass

class ImageButton(ButtonBehavior, Image):
    pass

class ExerciseDetailScreen(Screen):
    def load_sets(self, workout_id, exercise_id, exercise_name):
        self.workout_id = workout_id
        self.exercise_id = exercise_id
        self.ids.exercise_title.text = exercise_name

        sets_list = self.ids.sets_list
        sets_list.clear_widgets()

        conn = sqlite3.connect('tracker.db')
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, set_number, weight, reps, completed, timer_seconds
            FROM workout_sets 
            WHERE workout_id=? AND exercise_id=?
            ORDER BY set_number
        ''', (workout_id, exercise_id))
        rows = cursor.fetchall()
        conn.close()

        for row in rows:
            item = SetItem(
                set_id=row[0], set_number=row[1], weight=row[2], 
                reps=row[3], completed=row[4], timer_seconds=row[5], screen=self
            )
            sets_list.add_widget(item)

class SetItem(BoxLayout):
    def __init__(self, set_id, set_number, weight, reps, completed, timer_seconds, screen, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.size_hint_y = None
        self.height = 240
        self.spacing = 8
        self.padding = 10
        self.set_id = set_id
        self.screen = screen
        self.completed = completed
        self.timer_running = False
        self.timer_seconds = float(timer_seconds) if timer_seconds else 0.0
        self.timer_event = None

        with self.canvas.before:
            from kivy.graphics import Color, RoundedRectangle
            Color(1, 1, 1, 0.15)
            self.bg = RoundedRectangle(pos=self.pos, size=self.size, radius=[15])
        self.bind(pos=self.update_bg, size=self.update_bg)

        self.add_widget(Label(
            text=f'Подход: {set_number}',
            color=(1, 1, 1, 1),
            size_hint_y=0.2,
            font_size='22sp'
        ))

        row = BoxLayout(orientation='horizontal', spacing=8, size_hint_y=0.4)

        weight_box = BoxLayout(orientation='vertical', spacing=2)
        self.weight_input = SetTextInput(
            text=str(weight) if weight else '',
            hint_text='Вес кг',
            input_filter='float',
            multiline=False
        )
        self.weight_input.bind(on_text_validate=lambda *args: self.save_set())
        self.weight_input.bind(focus=lambda *args: self.save_set() if not args[1] else None)
        self.weight_input.bind(size=lambda *args: setattr(self.weight_input, 'text_size', self.weight_input.size))
        weight_box.add_widget(self.weight_input)
        row.add_widget(weight_box)

        self.check_btn = ImageButton(
            source='Images/checkbutton/2.png' if completed else 'Images/checkbutton/1.png',
            size_hint_x=0.8
        )
        self.check_btn.bind(on_press=lambda x: self.toggle_completed())
        row.add_widget(self.check_btn)

        reps_box = BoxLayout(orientation='vertical', spacing=2)
        self.reps_input = SetTextInput(
            text=str(reps) if reps else '',
            hint_text='Повторы',
            input_filter='int',
            multiline=False
        )
        self.reps_input.bind(on_text_validate=lambda *args: self.save_set())
        self.reps_input.bind(focus=lambda *args: self.save_set() if not args[1] else None)
        self.reps_input.bind(size=lambda *args: setattr(self.reps_input, 'text_size', self.reps_input.size))
        reps_box.add_widget(self.reps_input)
        row.add_widget(reps_box)

        self.add_widget(row)

        seconds_part = int(self.timer_seconds)
        ms_part = int((self.timer_seconds - seconds_part) * 100)
        
        self.timer_btn = Button(
            text=f'{seconds_part}.{ms_part:02d}',
            size_hint_y=0.3,
            font_size='25sp'
        )
        self.timer_btn.bind(on_press=lambda x: self.toggle_timer())
        self.add_widget(self.timer_btn)

        app = App.get_running_app()
        if app and hasattr(app, 'active_timers') and set_id in app.active_timers:
            self.timer_running = True
            self.timer_event = Clock.schedule_interval(self.refresh_display, 0.05)
        else:
            self.timer_running = False

    def update_bg(self, *args):
        self.bg.pos = self.pos
        self.bg.size = self.size

    def save_set(self):
        conn = sqlite3.connect('tracker.db')
        cursor = conn.cursor()
        weight = float(self.weight_input.text) if self.weight_input.text.strip() else None
        reps = int(self.reps_input.text) if self.reps_input.text.strip() else None
        cursor.execute(
            'UPDATE workout_sets SET weight=?, reps=? WHERE id=?',
            (weight, reps, self.set_id)
        )
        conn.commit()
        conn.close()

    def toggle_completed(self):
        self.completed = 0 if self.completed else 1
        conn = sqlite3.connect('tracker.db')
        cursor = conn.cursor()
        cursor.execute('UPDATE workout_sets SET completed=? WHERE id=?', (self.completed, self.set_id))
        conn.commit()
        conn.close()
        self.check_btn.source = 'Images/checkbutton/2.png' if self.completed else 'Images/checkbutton/1.png'

    def toggle_timer(self):
        app = App.get_running_app()
        

        if self.timer_seconds > 0 and not self.timer_running:
            self.timer_seconds = 0.0
            self.save_timer()
            self.timer_btn.text = '0.00'
            return

        if self.timer_running:
            elapsed = time.time() - app.active_timers[self.set_id]
            self.timer_seconds = elapsed
            del app.active_timers[self.set_id]
            self.timer_running = False
            if self.timer_event:
                self.timer_event.cancel()
            self.save_timer()
            
            seconds_part = int(self.timer_seconds)
            ms_part = int((self.timer_seconds - seconds_part) * 100)
            self.timer_btn.text = f'{seconds_part}.{ms_part:02d}'
        else:
            app.active_timers[self.set_id] = time.time() - self.timer_seconds
            self.timer_running = True
            self.timer_event = Clock.schedule_interval(self.refresh_display, 0.05)

    def refresh_display(self, dt):
        app = App.get_running_app()
        if self.set_id in app.active_timers:
            elapsed = time.time() - app.active_timers[self.set_id]
            seconds_part = int(elapsed)
            ms_part = int((elapsed - seconds_part) * 100)
            self.timer_btn.text = f'{seconds_part}.{ms_part:02d}'

    def save_timer(self):
        conn = sqlite3.connect('tracker.db')
        cursor = conn.cursor()
        cursor.execute('UPDATE workout_sets SET timer_seconds=? WHERE id=?', (float(self.timer_seconds), self.set_id))
        conn.commit()
        conn.close()

    



class WorkoutDetailScreen(Screen):
    def on_enter(self):
        self.load_exercises()

    def load_exercises(self):
        ex_list=self.ids.detail_exercise_list
        ex_list.clear_widgets()

        conn = sqlite3.connect('tracker.db')
        cursor = conn.cursor()
        cursor.execute('''
            SELECT e.id, e.name 
            FROM workout_sets ws
            JOIN exercises e ON ws.exercise_id = e.id
            WHERE ws.workout_id = ?
        ''', (self.workout_id,))
        rows = cursor.fetchall()
        conn.close()

        for row in rows:
            btn = Button(text=row[1], size_hint_y=None, height=50)
            btn.bind(on_press=lambda x, eid=row[0], ename=row[1]: self.open_exercise(eid, ename))
            ex_list.add_widget(btn)
    
    def open_exercise(self, exercise_id, exercise_name):
        screen = self.manager.get_screen('exercise_detail')
        screen.load_sets(self.workout_id, exercise_id, exercise_name)
        self.manager.current = 'exercise_detail'

class CopyWorkoutScreen(Screen):
    def on_enter(self):
        self.load_workouts()

    def load_workouts(self):
        copy_list = self.ids.copy_list
        copy_list.clear_widgets()

        conn = sqlite3.connect('tracker.db')
        cursor = conn.cursor()
        cursor.execute('SELECT id, date, description FROM workouts ORDER BY date DESC')
        rows = cursor.fetchall()
        conn.close()

        for row in rows:
            btn = Button(
                text=f"{row[2] or 'Без описания'} | {row[1]}",
                size_hint_y=None,
                height=50
            )
            btn.bind(on_press=lambda x, wid=row[0]: self.copy_workout(wid))
            copy_list.add_widget(btn)

    def copy_workout(self, workout_id):
        conn = sqlite3.connect('tracker.db')
        cursor = conn.cursor()
        
        cursor.execute('SELECT date, bodyweight, description FROM workouts WHERE id = ?', (workout_id,))
        workout = cursor.fetchone()
        
        cursor.execute('''
            SELECT e.id, e.name 
            FROM workout_sets ws
            JOIN exercises e ON ws.exercise_id = e.id
            WHERE ws.workout_id = ?
        ''', (workout_id,))
        exercises = cursor.fetchall()
        conn.close()

        screen = self.manager.get_screen('new_workout')
        screen.coming_from_picker = True
        screen.ids.workout_date.text = workout[0] or ''
        screen.ids.bodyweight.text = str(workout[1]) if workout[1] else ''
        screen.ids.workout_desc.text = workout[2] or ''
        
        screen.ids.selected_exercises.clear_widgets()
        for ex in exercises:
            item = SelectedExerciseItem(exercise_id=ex[0], name=ex[1], screen=screen)
            screen.ids.selected_exercises.add_widget(item)

        self.manager.current = 'new_workout'


class SelectedExerciseItem(BoxLayout):
    def __init__(self, exercise_id, name, screen, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'horizontal'
        self.size_hint_y = None
        self.height = 50
        self.exercise_id = exercise_id
        self.screen = screen
        self.spacing = 5 

        self.add_widget(Label(text=name))

        btn_del = Button(text='X', size_hint_x=0.2)
        btn_del.bind(on_press=lambda x: self.remove_from_workout())
        self.add_widget(btn_del)

    def remove_from_workout(self):
        self.screen.ids.selected_exercises.remove_widget(self)

class PickerItem(BoxLayout):
    def __init__(self, exercise_id, name, screen, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'horizontal'
        self.size_hint_y = None
        self.height = 50
        self.exercise_id = exercise_id
        self.screen = screen
        self.spacing = 5 

        self.name_input = TextInput(text=name, multiline=False)
        self.name_input.bind(on_text_validate=lambda x: self.save_name())
        self.add_widget(self.name_input)

        btn_add = Button(text='Доб.', size_hint_x=0.2, font_size='13sp')
        btn_add.bind(on_press=lambda x: self.add_to_workout())
        self.add_widget(btn_add)

        btn_del = Button(text='X', size_hint_x=0.2)
        btn_del.bind(on_press=lambda x: self.delete_exercise())
        self.add_widget(btn_del)

    def save_name(self):
        conn = sqlite3.connect('tracker.db')
        cursor = conn.cursor()
        cursor.execute('UPDATE exercises SET name = ? WHERE id = ?',
                      (self.name_input.text, self.exercise_id))
        conn.commit()
        conn.close()

    def add_to_workout(self):
        new_workout_screen = self.screen.manager.get_screen('new_workout')
        new_workout_screen.coming_from_picker = True 
        new_workout_screen.on_exercise_selected(self.exercise_id, self.name_input.text)
        self.screen.manager.current = 'new_workout'

    def delete_exercise(self):
        conn = sqlite3.connect('tracker.db')
        cursor = conn.cursor()
        cursor.execute('DELETE FROM exercises WHERE id = ?', (self.exercise_id,))
        conn.commit()
        conn.close()
        self.screen.load_exercises()


class ExercisePickerScreen(Screen):
    def on_enter(self):
        self.load_exercises()

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

    def load_exercises(self):
        picker_list = self.ids.picker_list
        picker_list.clear_widgets()
        conn = sqlite3.connect('tracker.db')
        cursor = conn.cursor()
        cursor.execute('SELECT id, name FROM exercises')
        rows = cursor.fetchall()
        conn.close()
        for row in rows:
            item = PickerItem(exercise_id=row[0], name=row[1], screen=self)
            picker_list.add_widget(item)

    def select_exercise(self, exercise_id, exercise_name):
        self.manager.current = 'new_workout'
        new_workout_screen = self.manager.get_screen('new_workout')
        new_workout_screen.on_exercise_selected(exercise_id, exercise_name)
        

class NewWorkoutScreen(Screen):
    def on_enter(self):
        if hasattr(self, 'coming_from_picker') and self.coming_from_picker:
            self.coming_from_picker = False
            return
            
        self.ids.selected_exercises.clear_widgets()
        if not hasattr(self, 'editing_id') or self.editing_id is None:
            self.editing_id = None
            self.ids.submit_btn.text = 'Создать'
            self.ids.workout_date.text = ''
            self.ids.bodyweight.text = ''
            self.ids.workout_desc.text = ''
        else:
            self.load_workout_exercises()
    
    def load_workout_exercises(self):
        conn = sqlite3.connect('tracker.db')
        cursor = conn.cursor()
        cursor.execute('''
            SELECT e.id, e.name 
            FROM workout_sets ws
            JOIN exercises e ON ws.exercise_id = e.id
            WHERE ws.workout_id = ?
        ''', (self.editing_id,))
        rows = cursor.fetchall()
        conn.close()

        for row in rows:
            item = SelectedExerciseItem(exercise_id=row[0], name=row[1], screen=self)
            self.ids.selected_exercises.add_widget(item)

    def on_exercise_selected(self, exercise_id, exercise_name):
        item = SelectedExerciseItem(exercise_id=exercise_id, name=exercise_name, screen=self)
        self.ids.selected_exercises.add_widget(item)

    def set_today_date(self):
        from datetime import date
        self.ids.workout_date.text = date.today().strftime('%d.%m.%Y')

    def create_workout(self, date, bodyweight, description):
        if not date.strip():
            return
        conn = sqlite3.connect('tracker.db')
        cursor = conn.cursor()
        if self.editing_id:
            cursor.execute(
                'UPDATE workouts SET date=?, bodyweight=?, description=? WHERE id=?',
                (date, float(bodyweight) if bodyweight.strip() else None, description, self.editing_id)
            )
            workout_id = self.editing_id
            cursor.execute('DELETE FROM workout_sets WHERE workout_id = ?', (workout_id,))
        else:
            cursor.execute(
                'INSERT INTO workouts (date, bodyweight, description) VALUES (?, ?, ?)',
                (date, float(bodyweight) if bodyweight.strip() else None, description)
            )
            workout_id = cursor.lastrowid
        for item in self.ids.selected_exercises.children:
            cursor.execute(
                'INSERT INTO workout_sets (workout_id, exercise_id, set_number, reps, weight, completed) VALUES (?, ?, ?, ?, ?, ?)',
                (workout_id, item.exercise_id, 1, None, None, 0)
            )

        conn.commit()
        conn.close()
        self.ids.workout_date.text = ''
        self.ids.bodyweight.text = ''
        self.ids.workout_desc.text = ''
        self.editing_id = None
        self.manager.current = 'workouts'

class WorkoutItem(BoxLayout):
    def __init__(self, workout_id, date, bodyweight, description, screen, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'horizontal'
        self.size_hint_y = None
        self.height = 53
        self.spacing = 5 

        btn_main = Button(
            text=f"{description or 'Без описания'}\n{date} | Вес: {bodyweight or '-'}",
            halign='center',
            valign='middle',
            font_size= '16sp'
        )
        btn_main.bind(size=btn_main.setter('text_size'))
        btn_main.bind(on_press=lambda x: screen.open_workout(workout_id))
        self.add_widget(btn_main)

        btn_edit = Button(text='Ред.', size_hint_x=0.22, font_size= '16sp')
        btn_edit.bind(on_press=lambda x: screen.edit_workout(
            workout_id, date, bodyweight, description
        ))
        self.add_widget(btn_edit)

        btn_delete = Button(text='X', size_hint_x=0.22)
        btn_delete.bind(on_press=lambda x: self.delete_workout(workout_id, screen))
        self.add_widget(btn_delete)

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
    
    def edit_workout(self, workout_id, date, bodyweight, description):
        screen = self.manager.get_screen('new_workout')
        screen.editing_id = workout_id
        screen.ids.workout_date.text = date or ''
        screen.ids.bodyweight.text = str(bodyweight) if bodyweight else ''
        screen.ids.workout_desc.text = description or ''
        screen.ids.submit_btn.text = 'Сохранить изменения'
        self.manager.current = 'new_workout'
    
    def open_workout(self, workout_id):
        screen = self.manager.get_screen('workout_detail')
        screen.workout_id = workout_id
        self.manager.current = 'workout_detail'

class ExerciseItem(BoxLayout):
    def __init__(self, exercise_id, name, screen, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'horizontal'
        self.size_hint_y = None
        self.height = 50
        self.exercise_id = exercise_id
        self.spacing = 5 

        self.name_input = TextInput(text=name, multiline=False)
        self.name_input.bind(on_text_validate=lambda x: self.save_name())
        self.add_widget(self.name_input)

        btn = Button(text='X', size_hint_x=0.2)
        btn.bind(on_press=lambda x: self.delete_exercise(exercise_id, screen))
        self.add_widget(btn)

    def save_name(self):
        conn = sqlite3.connect('tracker.db')
        cursor = conn.cursor()
        cursor.execute('UPDATE exercises SET name = ? WHERE id = ?',
                      (self.name_input.text, self.exercise_id))
        conn.commit()
        conn.close()

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
        self.active_timers = {}
        return Builder.load_file('kv/tracker.kv')
    
    def init_db(self):
        conn = sqlite3.connect('tracker.db')
        cursor = conn.cursor()
        cursor.execute('CREATE TABLE IF NOT EXISTS exercises (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL)')
        cursor.execute('CREATE TABLE IF NOT EXISTS workouts (id INTEGER PRIMARY KEY AUTOINCREMENT, date TEXT NOT NULL, bodyweight REAL, description TEXT)')
        cursor.execute('CREATE TABLE IF NOT EXISTS workout_sets (id INTEGER PRIMARY KEY AUTOINCREMENT, workout_id INTEGER NOT NULL, exercise_id INTEGER NOT NULL, set_number INTEGER NOT NULL, reps INTEGER, weight REAL, completed INTEGER DEFAULT 0, timer_seconds REAL DEFAULT 0.0)')
        conn.commit()
        conn.close()

if __name__ == '__main__':
    TrackerApp().run()