import sqlite3, csv, os, json, urllib.request, threading, ssl
ssl._create_default_https_context = ssl._create_unverified_context
from datetime import datetime
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.progressbar import ProgressBar
from kivy.uix.popup import Popup
from kivy.uix.widget import Widget
from kivy.core.window import Window
from kivy.metrics import dp
from kivy.clock import Clock, mainthread
from kivy.graphics import Color, RoundedRectangle, Line, Ellipse
from kivy.utils import get_color_from_hex

SYNC_URL = "https://hads-tracker-sync-default-rtdb.firebaseio.com/records.json"

Window.clearcolor = get_color_from_hex("#F1F5F9")

SECTIONS = [
    ("1. Госпитальная шкала тревоги и депрессии (HADS)", [
        ("1. Испытываю внутреннее напряжение, скованность:", "A", 
         ["Совсем не испытываю", "Время от времени", "Часто", "Постоянно"]),
        ("2. То, что приносило радость, доставляет удовольствие и сейчас:", "D", 
         ["Определенно так же", "Не в полной мере", "Лишь в малой степени", "Совсем не доставляет"]),
        ("3. Ощущение надвигающейся тревоги или страха:", "A", 
         ["Совсем нет", "Иногда, слабо", "Часто", "Постоянно и сильно"]),
        ("4. Способен посмеяться и увидеть смешное в событиях:", "D", 
         ["Всегда", "Часто", "Редко", "Совсем не способен"]),
        ("5. Беспокойные мысли занимают голову:", "A", 
         ["Лишь изредка", "Периодически", "Большую часть времени", "Постоянно"]),
        ("6. Чувствую себя бодрым и полным сил:", "D", 
         ["Практически весь день", "Большую часть дня", "Редко", "Совсем не чувствую"]),
        ("7. Легко сидеть спокойно и расслабляться:", "A", 
         ["Легко", "В основном да", "Редко удается", "Совсем не удается"]),
        ("8. Ощущение медлительности в реакциях и делах:", "D", 
         ["Совсем нет", "Иногда", "Часто", "Постоянно"]),
        ("9. Внутреннее напряжение или дрожь:", "A", 
         ["Совсем нет", "Изредка", "Часто", "Практически весь день"]),
        ("10. Внимание к собственному внешнему виду:", "D", 
         ["Как обычно", "Стараюсь, но меньше", "Уделяю мало внимания", "Совсем забросил"]),
        ("11. Сложно усидеть на месте из-за беспокойства:", "A", 
         ["Совсем нет", "Редко", "Часто", "Постоянно"]),
        ("12. Оптимистичный взгляд на дела и будущее:", "D", 
         ["Да, с уверенностью", "Меньше обычного", "Редко", "Совсем без оптимизма"]),
        ("13. Внезапные приступы паники или страха:", "A", 
         ["Не было вовсе", "Кратковременно", "Периодически", "Часто"]),
        ("14. Удовольствие от любимых занятий, книг или передач:", "D", 
         ["Да, с удовольствием", "Иногда", "Редко", "Совсем без интереса"])
    ]),
    ("2. Структура и качество сна (за прошедшую ночь)", [
        ("Процесс засыпания минувшей ночью:", "SLEEP", 
         ["Быстро (до 15 мин)", "Умеренно (15–30 мин)", "Трудно (30–60 мин)", "Бессонница (>1 часа)"]),
        ("Непрерывность ночного сна:", "SLEEP", 
         ["Крепкий сон без пробуждений", "1 кратковременное пробуждение", "Частые пробуждения", "Поверхностный рваный сон"]),
        ("Восстановление сил и ясность утром:", "SLEEP", 
         ["Полная бодрость и свежесть", "Умеренная работоспособность", "Вялость и сонливость", "Разбитость, отсутствие отдыха"])
    ]),
    ("3. Физическое самочувствие и тонус", [
        ("Мышечный дискомфорт, головная боль или спазмы:", "PHYS", 
         ["Отсутствуют", "Легкий дискомфорт", "Умеренная боль/напряжение", "Выраженный болевой синдром"]),
        ("Утомляемость от привычных дел за день:", "PHYS", 
         ["Сил хватает с запасом", "Усталость только к вечеру", "Быстрое утомление днем", "Полное физическое истощение"]),
        ("Общий соматический тонус организма:", "PHYS", 
         ["Высокий, энергичный", "Стабильный средний", "Сниженный, слабая выносливость", "Выраженная астения"])
    ])
]

def get_export_folder():
    android_dir = "/storage/emulated/0/Download"
    if os.path.exists(android_dir):
        return android_dir
    pc_downloads = os.path.join(os.path.expanduser("~"), "Downloads")
    if os.path.exists(pc_downloads):
        return pc_downloads
    return os.path.abspath(".")

class Card(BoxLayout):
    def __init__(self, bg_color="#FFFFFF", border_color="#E2E8F0", radius=10, **kwargs):
        super().__init__(**kwargs)
        self.bg_hex = bg_color
        self.border_hex = border_color
        self.radius_val = radius
        self.bind(pos=self.update_canvas, size=self.update_canvas)

    def update_canvas(self, *args):
        self.canvas.before.clear()
        with self.canvas.before:
            Color(*get_color_from_hex(self.bg_hex))
            RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(self.radius_val)])
            Color(*get_color_from_hex(self.border_hex))
            Line(rounded_rectangle=[self.x, self.y, self.width, self.height, dp(self.radius_val)], width=1)

class RadioCircle(Widget):
    def __init__(self, is_selected=False, **kwargs):
        super().__init__(**kwargs)
        self.is_selected = is_selected
        self.size_hint = (None, None)
        self.size = (dp(22), dp(22))
        self.bind(pos=self.redraw, size=self.redraw)

    def set_state(self, selected):
        self.is_selected = selected
        self.redraw()

    def redraw(self, *args):
        self.canvas.clear()
        with self.canvas:
            if self.is_selected:
                Color(*get_color_from_hex("#2563EB"))
                Line(circle=(self.center_x, self.center_y, dp(9)), width=dp(2))
                Color(*get_color_from_hex("#2563EB"))
                Ellipse(pos=(self.center_x - dp(5), self.center_y - dp(5)), size=(dp(10), dp(10)))
            else:
                Color(*get_color_from_hex("#64748B"))
                Line(circle=(self.center_x, self.center_y, dp(9)), width=dp(1.8))
                Color(1, 1, 1, 1)
                Ellipse(pos=(self.center_x - dp(4), self.center_y - dp(4)), size=(dp(8), dp(8)))

class RadioRow(BoxLayout):
    def __init__(self, text, on_select_cb, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'horizontal'
        self.size_hint_y = None
        self.height = dp(38)
        self.spacing = dp(10)
        self.padding = [dp(6), dp(4), dp(6), dp(4)]
        self.on_select_cb = on_select_cb
        self.is_selected = False

        self.circle = RadioCircle(is_selected=False)
        self.add_widget(self.circle)

        self.lbl = Label(
            text=text,
            color=get_color_from_hex("#334155"),
            font_size='12sp',
            halign='left',
            valign='middle'
        )
        self.lbl.bind(size=self.lbl.setter('text_size'))
        self.add_widget(self.lbl)
        self.bind(pos=self.update_bg, size=self.update_bg)

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            self.on_select_cb()
            return True
        return super().on_touch_down(touch)

    def set_checked(self, checked):
        self.is_selected = checked
        self.circle.set_state(checked)
        self.lbl.color = get_color_from_hex("#1E3A8A" if checked else "#334155")
        self.update_bg()

    def update_bg(self, *args):
        self.canvas.before.clear()
        if self.is_selected:
            with self.canvas.before:
                Color(*get_color_from_hex("#DBEAFE"))
                RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(6)])

class HADSApp(App):
    def build(self):
        self.title = "HADS Мониторинг"
        self.db_path = os.path.join(self.user_data_dir, "survey_data.db")
        self.init_db()

        self.answers = {}
        self.q_types = {}
        self.radio_rows = {}
        self.selected_record_id = None
        self.selected_row_widgets = []

        self.root = BoxLayout(orientation='vertical', padding=[dp(10), dp(42), dp(10), dp(10)], spacing=dp(8))

        tab_bar = Card(
            bg_color="#E2E8F0", border_color="#CBD5E1", radius=8,
            orientation='horizontal', size_hint_y=None, height=dp(44), padding=dp(3), spacing=dp(4)
        )
        self.tab_survey_btn = Button(
            text="Прохождение теста", bold=True, font_size='12.5sp',
            background_normal='', background_color=get_color_from_hex("#2563EB"),
            color=get_color_from_hex("#FFFFFF")
        )
        self.tab_data_btn = Button(
            text="Аналитика и датасет", bold=True, font_size='12.5sp',
            background_normal='', background_color=get_color_from_hex("#E2E8F0"),
            color=get_color_from_hex("#475569")
        )
        self.tab_survey_btn.bind(on_press=lambda inst: self.switch_tab(0))
        self.tab_data_btn.bind(on_press=lambda inst: self.switch_tab(1))
        tab_bar.add_widget(self.tab_survey_btn)
        tab_bar.add_widget(self.tab_data_btn)
        self.root.add_widget(tab_bar)

        self.content_area = BoxLayout(orientation='vertical')
        self.root.add_widget(self.content_area)

        self.init_survey_view()
        self.init_data_view()

        self.switch_tab(0)
        return self.root

    def on_start(self):
        threading.Thread(target=lambda: self.sync_data(silent=True), daemon=True).start()
        Clock.schedule_interval(lambda dt: threading.Thread(target=lambda: self.sync_data(silent=True), daemon=True).start(), 60)

    def switch_tab(self, tab_index):
        self.content_area.clear_widgets()
        if tab_index == 0:
            self.tab_survey_btn.background_color = get_color_from_hex("#2563EB")
            self.tab_survey_btn.color = get_color_from_hex("#FFFFFF")
            self.tab_data_btn.background_color = get_color_from_hex("#E2E8F0")
            self.tab_data_btn.color = get_color_from_hex("#475569")
            self.content_area.add_widget(self.survey_scroll)
        else:
            self.tab_data_btn.background_color = get_color_from_hex("#2563EB")
            self.tab_data_btn.color = get_color_from_hex("#FFFFFF")
            self.tab_survey_btn.background_color = get_color_from_hex("#E2E8F0")
            self.tab_survey_btn.color = get_color_from_hex("#475569")
            self.refresh_table_data()
            self.content_area.add_widget(self.data_container)
            threading.Thread(target=lambda: self.sync_data(silent=True), daemon=True).start()

    def init_survey_view(self):
        self.survey_scroll = ScrollView(size_hint=(1, 1), do_scroll_x=False, bar_width=dp(5))
        content = BoxLayout(orientation='vertical', size_hint_y=None, spacing=dp(12), padding=[0, dp(4), 0, dp(25)])
        content.bind(minimum_height=content.setter('height'))

        h_card = Card(orientation='vertical', size_hint_y=None, padding=dp(12), spacing=dp(5))
        h_card.bind(minimum_height=h_card.setter('height'))

        t_row = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(26))
        today_str = datetime.now().strftime("%d.%m.%Y")
        t_title = Label(
            text=f"[b]Оценка за сутки ({today_str})[/b]", markup=True,
            color=get_color_from_hex("#0F172A"), font_size='14sp', halign='left'
        )
        t_title.bind(size=t_title.setter('text_size'))
        self.progress_lbl = Label(
            text="0 / 20", bold=True,
            color=get_color_from_hex("#2563EB"), font_size='13.5sp', size_hint_x=0.25, halign='right'
        )
        self.progress_lbl.bind(size=self.progress_lbl.setter('text_size'))
        t_row.add_widget(t_title)
        t_row.add_widget(self.progress_lbl)
        h_card.add_widget(t_row)

        sub_lbl = Label(
            text="Фиксация показателей психосоматического статуса",
            color=get_color_from_hex("#64748B"), font_size='11sp', size_hint_y=None, height=dp(18), halign='left'
        )
        sub_lbl.bind(size=sub_lbl.setter('text_size'))
        h_card.add_widget(sub_lbl)

        self.pbar = ProgressBar(max=20, value=0, size_hint_y=None, height=dp(12))
        h_card.add_widget(self.pbar)
        content.add_widget(h_card)

        p_card = Card(orientation='horizontal', size_hint_y=None, height=dp(54), padding=[dp(10), dp(6), dp(10), dp(6)], spacing=dp(8))
        self.fio_input = TextInput(
            text="Студент", hint_text="ФИО / ID", multiline=False, size_hint_x=0.65,
            background_color=get_color_from_hex("#F8FAFC"), foreground_color=get_color_from_hex("#0F172A"),
            padding=[dp(10), dp(8), dp(10), dp(8)], font_size='12sp'
        )
        self.age_input = TextInput(
            text="20", hint_text="Возраст", multiline=False, input_filter='int', size_hint_x=0.35,
            background_color=get_color_from_hex("#F8FAFC"), foreground_color=get_color_from_hex("#0F172A"),
            padding=[dp(10), dp(8), dp(10), dp(8)], font_size='12sp'
        )
        p_card.add_widget(self.fio_input)
        p_card.add_widget(self.age_input)
        content.add_widget(p_card)

        q_idx = 0
        for sec_title, items in SECTIONS:
            sec_header = Label(
                text=f"[b]{sec_title}[/b]", markup=True,
                color=get_color_from_hex("#1E3A8A"), font_size='13sp',
                size_hint_y=None, height=dp(32), halign='left'
            )
            sec_header.bind(size=sec_header.setter('text_size'))
            content.add_widget(sec_header)

            for text, q_type, options in items:
                self.q_types[q_idx] = q_type
                self.radio_rows[q_idx] = []

                card = Card(orientation='vertical', size_hint_y=None, padding=dp(12), spacing=dp(5))
                card.bind(minimum_height=card.setter('height'))

                q_lbl = Label(
                    text=f"[b]{text}[/b]", markup=True,
                    color=get_color_from_hex("#0F172A"), font_size='12sp',
                    size_hint_y=None, height=dp(34), halign='left', valign='middle'
                )
                q_lbl.bind(size=q_lbl.setter('text_size'))
                card.add_widget(q_lbl)

                for score, opt_text in enumerate(options):
                    row = RadioRow(
                        text=opt_text,
                        on_select_cb=lambda qi=q_idx, sc=score: self.select_option(qi, sc)
                    )
                    self.radio_rows[q_idx].append(row)
                    card.add_widget(row)

                content.add_widget(card)
                q_idx += 1

        live_card = Card(
            bg_color="#E2E8F0", border_color="#CBD5E1",
            orientation='vertical', size_hint_y=None, height=dp(68), padding=dp(8), spacing=dp(3)
        )
        l_row1 = BoxLayout(orientation='horizontal')
        self.live_anx = Label(text="Тревога: 0 б.", bold=True, color=get_color_from_hex("#1E293B"), font_size='11.5sp')
        self.live_dep = Label(text="Депрессия: 0 б.", bold=True, color=get_color_from_hex("#1E293B"), font_size='11.5sp')
        l_row1.add_widget(self.live_anx)
        l_row1.add_widget(self.live_dep)

        l_row2 = BoxLayout(orientation='horizontal')
        self.live_slp = Label(text="Сон: 0 б.", bold=True, color=get_color_from_hex("#1E293B"), font_size='11.5sp')
        self.live_phy = Label(text="Физ. дискомфорт: 0 б.", bold=True, color=get_color_from_hex("#1E293B"), font_size='11.5sp')
        l_row2.add_widget(self.live_slp)
        l_row2.add_widget(self.live_phy)

        live_card.add_widget(l_row1)
        live_card.add_widget(l_row2)
        content.add_widget(live_card)

        save_btn = Button(
            text="Зафиксировать результат за день", bold=True, font_size='13sp',
            size_hint_y=None, height=dp(46),
            background_normal='', background_color=get_color_from_hex("#2563EB"),
            color=get_color_from_hex("#FFFFFF")
        )
        save_btn.bind(on_press=self.save_data)
        content.add_widget(save_btn)

        self.survey_scroll.add_widget(content)

    def init_data_view(self):
        self.data_container = BoxLayout(orientation='vertical', spacing=dp(8))

        kpi_grid = GridLayout(cols=2, spacing=dp(6), size_hint_y=None, height=dp(114))
        self.kpi_total_card, self.kpi_total_val = self.create_kpi_card("Всего записей")
        self.kpi_anx_card, self.kpi_anx_val = self.create_kpi_card("Ср. тревога")
        self.kpi_dep_card, self.kpi_dep_val = self.create_kpi_card("Ср. депрессия")
        self.kpi_slp_card, self.kpi_slp_val = self.create_kpi_card("Ср. балл сна")

        kpi_grid.add_widget(self.kpi_total_card)
        kpi_grid.add_widget(self.kpi_anx_card)
        kpi_grid.add_widget(self.kpi_dep_card)
        kpi_grid.add_widget(self.kpi_slp_card)
        self.data_container.add_widget(kpi_grid)

        actions_grid = GridLayout(cols=3, spacing=dp(5), size_hint_y=None, height=dp(76))
        
        btn_refresh = Button(
            text="Обновить", font_size='11sp', bold=True,
            background_normal='', background_color=get_color_from_hex("#FFFFFF"),
            color=get_color_from_hex("#334155")
        )
        btn_refresh.bind(on_press=lambda inst: self.refresh_table_data())

        btn_sync = Button(
            text="Синхронизация", font_size='11sp', bold=True,
            background_normal='', background_color=get_color_from_hex("#2563EB"),
            color=get_color_from_hex("#FFFFFF")
        )
        btn_sync.bind(on_press=lambda inst: threading.Thread(target=lambda: self.sync_data(silent=False), daemon=True).start())

        btn_summary = Button(
            text="Итоги и прогноз", font_size='11sp', bold=True,
            background_normal='', background_color=get_color_from_hex("#3B82F6"),
            color=get_color_from_hex("#FFFFFF")
        )
        btn_summary.bind(on_press=lambda inst: self.show_summary_popup())

        btn_csv = Button(
            text="Экспорт CSV", font_size='11sp', bold=True,
            background_normal='', background_color=get_color_from_hex("#0D9488"),
            color=get_color_from_hex("#FFFFFF")
        )
        btn_csv.bind(on_press=lambda inst: self.export_csv())

        btn_pdf = Button(
            text="Протокол в PDF", font_size='11sp', bold=True,
            background_normal='', background_color=get_color_from_hex("#475569"),
            color=get_color_from_hex("#FFFFFF")
        )
        btn_pdf.bind(on_press=lambda inst: self.export_pdf())

        btn_delete = Button(
            text="Удалить запись", font_size='11sp', bold=True,
            background_normal='', background_color=get_color_from_hex("#EF4444"),
            color=get_color_from_hex("#FFFFFF")
        )
        btn_delete.bind(on_press=lambda inst: self.delete_selected_record())

        actions_grid.add_widget(btn_refresh)
        actions_grid.add_widget(btn_sync)
        actions_grid.add_widget(btn_summary)
        actions_grid.add_widget(btn_csv)
        actions_grid.add_widget(btn_pdf)
        actions_grid.add_widget(btn_delete)
        self.data_container.add_widget(actions_grid)

        self.table_widths = [
            dp(45), dp(130), dp(110), dp(55), dp(65),
            dp(65), dp(100), dp(65), dp(100), dp(50), dp(55)
        ]
        total_tbl_w = sum(self.table_widths)

        self.table_hscroll = ScrollView(size_hint=(1, 1), do_scroll_x=True, do_scroll_y=False, bar_width=dp(4))
        table_inner_box = BoxLayout(orientation='vertical', size_hint=(None, 1), width=total_tbl_w)

        tbl_hdr_box = BoxLayout(orientation='horizontal', size_hint=(None, None), width=total_tbl_w, height=dp(34))
        hdr_titles = ["ID", "Дата", "Участник", "Возраст", "Пол", "Тревога", "Статус Т.", "Депрессия", "Статус Д.", "Сон", "Физ."]
        for title, w in zip(hdr_titles, self.table_widths):
            lbl = Label(
                text=f"[b]{title}[/b]", markup=True,
                color=get_color_from_hex("#334155"), font_size='10.5sp',
                size_hint=(None, 1), width=w, halign='center', valign='middle'
            )
            lbl.bind(size=lbl.setter('text_size'))
            tbl_hdr_box.add_widget(lbl)
        table_inner_box.add_widget(tbl_hdr_box)

        self.table_vscroll = ScrollView(size_hint=(None, 1), width=total_tbl_w, do_scroll_x=False, do_scroll_y=True, bar_width=dp(4))
        self.table_rows_box = BoxLayout(orientation='vertical', size_hint=(None, None), width=total_tbl_w, spacing=dp(2))
        self.table_rows_box.bind(minimum_height=self.table_rows_box.setter('height'))
        self.table_vscroll.add_widget(self.table_rows_box)
        table_inner_box.add_widget(self.table_vscroll)

        self.table_hscroll.add_widget(table_inner_box)
        self.data_container.add_widget(self.table_hscroll)

    def create_kpi_card(self, title):
        card = Card(orientation='vertical', padding=dp(6), spacing=dp(2))
        t_lbl = Label(text=title, color=get_color_from_hex("#64748B"), font_size='10.5sp', bold=True)
        v_lbl = Label(text="0.0", color=get_color_from_hex("#0F172A"), font_size='16sp', bold=True)
        card.add_widget(t_lbl)
        card.add_widget(v_lbl)
        return card, v_lbl

    def init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.cursor().execute("""CREATE TABLE IF NOT EXISTS results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT UNIQUE, fio TEXT, age INTEGER, gender TEXT,
                anxiety INTEGER, anxiety_status TEXT,
                depression INTEGER, depression_status TEXT,
                sleep INTEGER, physical INTEGER
            )""")
            conn.commit()

    def select_option(self, q_idx, score):
        self.answers[q_idx] = score
        for sc, row in enumerate(self.radio_rows[q_idx]):
            row.set_checked(sc == score)

        ans_count = len(self.answers)
        self.pbar.value = ans_count
        self.progress_lbl.text = f"{ans_count} / 20"

        anx = sum(sc for qi, sc in self.answers.items() if self.q_types[qi] == "A")
        dep = sum(sc for qi, sc in self.answers.items() if self.q_types[qi] == "D")
        slp = sum(sc for qi, sc in self.answers.items() if self.q_types[qi] == "SLEEP")
        phy = sum(sc for qi, sc in self.answers.items() if self.q_types[qi] == "PHYS")

        self.live_anx.text = f"Тревога: {anx} б."
        self.live_dep.text = f"Депрессия: {dep} б."
        self.live_slp.text = f"Сон: {slp} б."
        self.live_phy.text = f"Физ. дискомфорт: {phy} б."

    def get_hads_status(self, score):
        return "Норма" if score <= 7 else ("Субклинический" if score <= 10 else "Клинический")

    def show_alert(self, title, text):
        layout = BoxLayout(orientation='vertical', padding=dp(12), spacing=dp(10))
        layout.add_widget(Label(text=text, color=get_color_from_hex("#FFFFFF"), font_size='12sp', halign='center'))
        btn = Button(
            text="OK", size_hint_y=None, height=dp(36),
            background_normal='', background_color=get_color_from_hex("#2563EB")
        )
        popup = Popup(title=title, content=layout, size_hint=(0.88, 0.45))
        btn.bind(on_press=popup.dismiss)
        layout.add_widget(btn)
        popup.open()

    def save_data(self, instance):
        if len(self.answers) < 20:
            self.show_alert("Внимание", "Требуется ответить на все 20 вопросов перед сохранением.")
            return

        fio = self.fio_input.text.strip() or "Студент"
        age = int(self.age_input.text.strip() or 20)

        anx = sum(sc for qi, sc in self.answers.items() if self.q_types[qi] == "A")
        dep = sum(sc for qi, sc in self.answers.items() if self.q_types[qi] == "D")
        slp = sum(sc for qi, sc in self.answers.items() if self.q_types[qi] == "SLEEP")
        phy = sum(sc for qi, sc in self.answers.items() if self.q_types[qi] == "PHYS")

        anx_st = self.get_hads_status(anx)
        dep_st = self.get_hads_status(dep)
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        with sqlite3.connect(self.db_path) as conn:
            conn.cursor().execute("""INSERT OR IGNORE INTO results (date, fio, age, gender, anxiety, anxiety_status,
                                depression, depression_status, sleep, physical)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""", (now_str, fio, age, "Мужской", anx, anx_st, dep, dep_st, slp, phy))
            conn.commit()

        threading.Thread(target=lambda: self.sync_data(silent=True), daemon=True).start()

        self.answers.clear()
        for qi in self.radio_rows:
            for row in self.radio_rows[qi]:
                row.set_checked(False)

        self.pbar.value = 0
        self.progress_lbl.text = "0 / 20"
        self.live_anx.text = "Тревога: 0 б."
        self.live_dep.text = "Депрессия: 0 б."
        self.live_slp.text = "Сон: 0 б."
        self.live_phy.text = "Физ. дискомфорт: 0 б."

        msg = f"Запись сохранена!\n\nТревога: {anx} ({anx_st})\nДепрессия: {dep} ({dep_st})\nДефицит сна: {slp} из 9\nФиз. дискомфорт: {phy} из 9"
        self.show_alert("Успешно", msg)
        self.switch_tab(1)

    def refresh_table_data(self):
        self.table_rows_box.clear_widgets()
        self.selected_record_id = None
        self.selected_row_widgets = []

        with sqlite3.connect(self.db_path) as conn:
            rows = conn.cursor().execute("SELECT * FROM results ORDER BY id DESC").fetchall()

        count = len(rows)
        self.kpi_total_val.text = f"{count} дн."
        if count > 0:
            avg_anx = sum(r[5] for r in rows) / count
            avg_dep = sum(r[7] for r in rows) / count
            avg_slp = sum(r[9] for r in rows) / count
            self.kpi_anx_val.text = f"{avg_anx:.1f}"
            self.kpi_dep_val.text = f"{avg_dep:.1f}"
            self.kpi_slp_val.text = f"{avg_slp:.1f}"
        else:
            self.kpi_anx_val.text = "0.0"
            self.kpi_dep_val.text = "0.0"
            self.kpi_slp_val.text = "0.0"

        for row_idx, r in enumerate(rows):
            rec_id = r[0]
            bg_col = "#FFFFFF" if row_idx % 2 == 0 else "#F8FAFC"
            
            row_box = BoxLayout(orientation='horizontal', size_hint=(None, None), width=sum(self.table_widths), height=dp(34))
            row_labels = []

            vals = [
                str(r[0]), str(r[1][:16]), str(r[2]), str(r[3]), str(r[4]),
                str(r[5]), str(r[6]), str(r[7]), str(r[8]), str(r[9]), str(r[10])
            ]
            for val, w in zip(vals, self.table_widths):
                lbl = Button(
                    text=val,
                    font_size='10sp',
                    color=get_color_from_hex("#0F172A"),
                    background_normal='',
                    background_color=get_color_from_hex(bg_col),
                    size_hint=(None, 1),
                    width=w
                )
                lbl.bind(on_press=lambda inst, rid=rec_id, rlabels=row_labels: self.select_table_row(rid, rlabels))
                row_labels.append(lbl)
                row_box.add_widget(lbl)

            self.table_rows_box.add_widget(row_box)

    def select_table_row(self, rec_id, row_labels):
        if self.selected_row_widgets:
            for lbl in self.selected_row_widgets:
                lbl.background_color = get_color_from_hex("#FFFFFF")

        self.selected_record_id = rec_id
        self.selected_row_widgets = row_labels
        for lbl in row_labels:
            lbl.background_color = get_color_from_hex("#DBEAFE")

    def delete_selected_record(self):
        if not self.selected_record_id:
            self.show_alert("Выбор записи", "Требуется нажать на строку в таблице перед удалением.")
            return

        with sqlite3.connect(self.db_path) as conn:
            conn.cursor().execute("DELETE FROM results WHERE id = ?", (self.selected_record_id,))
            conn.commit()

        self.show_alert("Успешно", f"Запись #{self.selected_record_id} удалена.")
        self.refresh_table_data()

    def show_summary_popup(self):
        with sqlite3.connect(self.db_path) as conn:
            rows = conn.cursor().execute("SELECT anxiety, depression, sleep, physical FROM results").fetchall()

        n = len(rows)
        if n < 2:
            self.show_alert("Итоги", "Требуется минимум 2 записи для расчета.")
            return

        anx = [r[0] for r in rows]
        dep = [r[1] for r in rows]
        slp = [r[2] for r in rows]
        phy = [r[3] for r in rows]

        def corr(x, y):
            mx, my = sum(x) / n, sum(y) / n
            vx, vy = sum((v - mx)**2 for v in x), sum((v - my)**2 for v in y)
            return (sum((x[i] - mx) * (y[i] - my) for i in range(n)) / ((vx * vy)**0.5)) if vx and vy else 0.0

        r_slp_anx = corr(slp, anx)
        r_phy_dep = corr(phy, dep)
        norm_pct = (sum(1 for a in anx if a <= 7) / n) * 100

        verdict = "Качество сна выступает ключевым предиктором тревоги." if r_slp_anx > 0.4 else "Прямой связи между сном и тревогой не выявлено."
        text = (
            f"Наблюдений: {n} дн.\n"
            f"• Норма эмоционального фона: {norm_pct:.1f}%\n"
            f"• Связь сна и тревоги (r): {r_slp_anx:.2f}\n"
            f"• Связь тонуса и депрессии (r): {r_phy_dep:.2f}\n\n"
            f"Итог модели: {verdict}"
        )
        self.show_alert("Итоги и прогноз", text)

    def export_csv(self):
        with sqlite3.connect(self.db_path) as conn:
            rows = conn.cursor().execute("SELECT * FROM results").fetchall()

        if not rows:
            self.show_alert("Экспорт", "База данных пуста.")
            return

        target_dir = get_export_folder()
        csv_path = os.path.join(target_dir, "dataset_hads.csv")

        with open(csv_path, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f, delimiter=";")
            writer.writerow(["id", "date", "fio", "age", "gender", "anxiety", "anxiety_status",
                             "depression", "depression_status", "sleep", "physical"])
            writer.writerows(rows)

        self.show_alert("Экспорт CSV завершен", f"Файл сохранен в Загрузки:\n{csv_path}")

    def export_pdf(self):
        with sqlite3.connect(self.db_path) as conn:
            rows = conn.cursor().execute("SELECT * FROM results ORDER BY id ASC").fetchall()

        if not rows:
            self.show_alert("Экспорт PDF", "База данных пуста.")
            return

        target_dir = get_export_folder()
        pdf_path = os.path.join(target_dir, "summary_report.pdf")

        try:
            from fpdf import FPDF

            pdf = FPDF(orientation='P', unit='mm', format='A4')
            pdf.add_page()

            font_path = None
            for p in ["/system/fonts/Roboto-Regular.ttf", "C:\\Windows\\Fonts\\arial.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"]:
                if os.path.exists(p):
                    font_path = p
                    break

            if font_path:
                pdf.add_font("CustomFont", "", font_path, uni=True)
                pdf.set_font("CustomFont", "", 13)
            else:
                pdf.set_font("Helvetica", "", 12)

            pdf.cell(0, 10, "СВОДНЫЙ ОТЧЕТ МОНИТОРИНГА (HADS + СОН)", ln=True, align='C')
            pdf.set_font("CustomFont" if font_path else "Helvetica", "", 9)
            pdf.cell(0, 7, f"Участник: {rows[-1][2]} | Записей: {len(rows)} | Дата: {datetime.now().strftime('%d.%m.%Y %H:%M')}", ln=True, align='C')
            pdf.ln(4)

            col_w = [14, 40, 36, 36, 18, 18]
            headers = ["ID", "Дата", "Тревога", "Депрессия", "Сон", "Физ."]

            pdf.set_fill_color(241, 245, 249)
            for h, w in zip(headers, col_w):
                pdf.cell(w, 8, h, border=1, align='C', fill=True)
            pdf.ln()

            for r in rows:
                pdf.cell(col_w[0], 7, str(r[0]), border=1, align='C')
                pdf.cell(col_w[1], 7, str(r[1][:16]), border=1, align='C')
                pdf.cell(col_w[2], 7, f"{r[5]} ({r[6][:4]})", border=1, align='C')
                pdf.cell(col_w[3], 7, f"{r[7]} ({r[8][:4]})", border=1, align='C')
                pdf.cell(col_w[4], 7, str(r[9]), border=1, align='C')
                pdf.cell(col_w[5], 7, str(r[10]), border=1, align='C')
                pdf.ln()

            pdf.output(pdf_path)
            self.show_alert("Протокол PDF сформирован", f"Файл сохранен в Загрузки:\n{pdf_path}")
        except Exception as e:
            self.show_alert("Ошибка PDF", f"Сбой формирования: {str(e)}")

    def sync_data(self, silent=False):
        try:
            with sqlite3.connect(self.db_path) as conn:
                local_rows = conn.cursor().execute("SELECT date, fio, age, gender, anxiety, anxiety_status, depression, depression_status, sleep, physical FROM results").fetchall()

            req = urllib.request.Request(SYNC_URL, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=5) as response:
                raw_data = response.read().decode('utf-8')
                cloud_data = json.loads(raw_data) if raw_data != "null" else {}

            cloud_records = list(cloud_data.values()) if isinstance(cloud_data, dict) else (cloud_data or [])
            cloud_dates = {rec.get("date") for rec in cloud_records if isinstance(rec, dict)}

            new_to_cloud = 0
            for r in local_rows:
                if r[0] not in cloud_dates:
                    payload = {
                        "date": r[0], "fio": r[1], "age": r[2], "gender": r[3],
                        "anxiety": r[4], "anxiety_status": r[5],
                        "depression": r[6], "depression_status": r[7],
                        "sleep": r[8], "physical": r[9]
                    }
                    post_req = urllib.request.Request(
                        SYNC_URL,
                        data=json.dumps(payload).encode('utf-8'),
                        headers={'Content-Type': 'application/json'}
                    )
                    urllib.request.urlopen(post_req, timeout=5)
                    new_to_cloud += 1

            new_to_local = 0
            with sqlite3.connect(self.db_path) as conn:
                for rec in cloud_records:
                    if isinstance(rec, dict) and rec.get("date"):
                        cur = conn.cursor()
                        cur.execute("""
                            INSERT OR IGNORE INTO results (date, fio, age, gender, anxiety, anxiety_status, depression, depression_status, sleep, physical)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            rec.get("date"), rec.get("fio"), rec.get("age"), rec.get("gender"),
                            rec.get("anxiety"), rec.get("anxiety_status"),
                            rec.get("depression"), rec.get("depression_status"),
                            rec.get("sleep"), rec.get("physical")
                        ))
                        if cur.rowcount > 0:
                            new_to_local += 1
                conn.commit()

            self.update_ui_after_sync(silent, new_to_cloud, new_to_local)
        except Exception as e:
            if not silent:
                self.show_alert_mainthread("Ошибка синхронизации", str(e))

    @mainthread
    def update_ui_after_sync(self, silent, new_to_cloud, new_to_local):
        self.refresh_table_data()
        if not silent:
            self.show_alert("Синхронизация", f"Успешно!\nОтправлено в облако: {new_to_cloud}\nЗагружено на телефон: {new_to_local}")

    @mainthread
    def show_alert_mainthread(self, title, text):
        self.show_alert(title, text)

if __name__ == '__main__':
    HADSApp().run()
