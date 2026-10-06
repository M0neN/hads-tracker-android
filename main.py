import sqlite3, csv, os
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
from kivy.core.window import Window
from kivy.graphics import Color, RoundedRectangle, Line
from kivy.utils import get_color_from_hex

Window.clearcolor = get_color_from_hex("#F1F5F9")

SECTIONS = [
    ("1. Госпитальная шкала тревоги и депрессии (HADS)", [
        ("1. Испытываю внутреннее напряжение, скованность:", "A", 
         ["Совсем не испытываю", "Время от времени", "Часто", "Постоянно"]),
        ("2. То, что приносило радость, радует и сейчас:", "D", 
         ["Определенно так же", "Не в полной мере", "Лишь в малой степени", "Совсем не доставляет"]),
        ("3. Ощущение надвигающейся тревоги или страха:", "A", 
         ["Совсем нет", "Иногда, слабо", "Часто", "Постоянно и сильно"]),
        ("4. Способен посмеяться и увидеть смешное:", "D", 
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
            RoundedRectangle(pos=self.pos, size=self.size, radius=[self.radius_val])
            Color(*get_color_from_hex(self.border_hex))
            Line(rounded_rectangle=[self.x, self.y, self.width, self.height, self.radius_val], width=1)


class HADSApp(App):
    def build(self):
        self.title = "HADS Мониторинг"
        self.db_path = os.path.join(self.user_data_dir, "survey_data.db")
        self.init_db()

        self.answers = {}
        self.q_types = {}
        self.buttons = {}
        self.selected_record_id = None
        self.selected_row_box = None

        # Корневой экран с отступом под строку уведомлений Android
        self.root = BoxLayout(orientation='vertical', padding=[10, 32, 10, 10], spacing=8)

        # Верхняя панель переключения вкладок
        tab_bar = BoxLayout(orientation='horizontal', size_hint_y=None, height=44, spacing=6)
        self.tab_survey_btn = Button(
            text="📋 Прохождение теста", bold=True, font_size='12.5sp',
            background_normal='', background_color=get_color_from_hex("#2563EB"),
            color=get_color_from_hex("#FFFFFF")
        )
        self.tab_data_btn = Button(
            text="📈 Аналитика и датасет", bold=True, font_size='12.5sp',
            background_normal='', background_color=get_color_from_hex("#E2E8F0"),
            color=get_color_from_hex("#475569")
        )
        self.tab_survey_btn.bind(on_press=lambda inst: self.switch_tab(0))
        self.tab_data_btn.bind(on_press=lambda inst: self.switch_tab(1))
        tab_bar.add_widget(self.tab_survey_btn)
        tab_bar.add_widget(self.tab_data_btn)
        self.root.add_widget(tab_bar)

        # Контейнер содержимого активной вкладки
        self.content_area = BoxLayout(orientation='vertical')
        self.root.add_widget(self.content_area)

        # Инициализация экранов
        self.init_survey_view()
        self.init_data_view()

        # Старт с вкладки опросника
        self.switch_tab(0)
        return self.root

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

    # ---------------------------------------------------------
    # ВКЛАДКА 1: ОПРОСНИК
    # ---------------------------------------------------------
    def init_survey_view(self):
        self.survey_scroll = ScrollView(size_hint=(1, 1), do_scroll_x=False, bar_width=5)
        content = BoxLayout(orientation='vertical', size_hint_y=None, spacing=10, padding=[0, 4, 0, 8])
        content.bind(minimum_height=content.setter('height'))

        # Шапка прогресса
        h_card = Card(orientation='vertical', size_hint_y=None, height=98, padding=10, spacing=4)
        t_row = BoxLayout(orientation='horizontal', size_hint_y=None, height=24)
        today_str = datetime.now().strftime("%d.%m.%Y")
        t_title = Label(
            text=f"[b]📅 Оценка за сутки ({today_str})[/b]", markup=True,
            color=get_color_from_hex("#0F172A"), font_size='14sp', halign='left'
        )
        t_title.bind(size=t_title.setter('text_size'))
        self.progress_lbl = Label(
            text="0 / 20", bold=True,
            color=get_color_from_hex("#2563EB"), font_size='13sp', size_hint_x=0.3, halign='right'
        )
        self.progress_lbl.bind(size=self.progress_lbl.setter('text_size'))
        t_row.add_widget(t_title)
        t_row.add_widget(self.progress_lbl)
        h_card.add_widget(t_row)

        sub_lbl = Label(
            text="Выбор показателей психосоматического состояния",
            color=get_color_from_hex("#64748B"), font_size='11sp', size_hint_y=None, height=16, halign='left'
        )
        sub_lbl.bind(size=sub_lbl.setter('text_size'))
        h_card.add_widget(sub_lbl)

        self.pbar = ProgressBar(max=20, value=0, size_hint_y=None, height=12)
        h_card.add_widget(self.pbar)
        content.add_widget(h_card)

        # Профиль
        p_card = Card(orientation='horizontal', size_hint_y=None, height=54, padding=[10, 6, 10, 6], spacing=6)
        self.fio_input = TextInput(
            text="Студент", hint_text="ФИО / ID", multiline=False, size_hint_x=0.65,
            background_color=get_color_from_hex("#F8FAFC"), foreground_color=get_color_from_hex("#0F172A"),
            padding=[8, 6, 8, 6]
        )
        self.age_input = TextInput(
            text="20", hint_text="Возраст", multiline=False, input_filter='int', size_hint_x=0.35,
            background_color=get_color_from_hex("#F8FAFC"), foreground_color=get_color_from_hex("#0F172A"),
            padding=[8, 6, 8, 6]
        )
        p_card.add_widget(self.fio_input)
        p_card.add_widget(self.age_input)
        content.add_widget(p_card)

        # Вопросы
        q_idx = 0
        for sec_title, items in SECTIONS:
            sec_header = Label(
                text=f"[b]{sec_title}[/b]", markup=True,
                color=get_color_from_hex("#1E3A8A"), font_size='13sp',
                size_hint_y=None, height=30, halign='left'
            )
            sec_header.bind(size=sec_header.setter('text_size'))
            content.add_widget(sec_header)

            for text, q_type, options in items:
                self.q_types[q_idx] = q_type
                self.buttons[q_idx] = []

                card = Card(orientation='vertical', size_hint_y=None, height=185, padding=10, spacing=4)
                q_lbl = Label(
                    text=f"[b]{text}[/b]", markup=True,
                    color=get_color_from_hex("#0F172A"), font_size='12sp',
                    size_hint_y=None, height=32, halign='left', valign='middle'
                )
                q_lbl.bind(size=q_lbl.setter('text_size'))
                card.add_widget(q_lbl)

                for score, opt_text in enumerate(options):
                    btn = Button(
                        text=f"  ○  {opt_text}",
                        size_hint_y=None, height=30,
                        halign='left', valign='middle',
                        font_size='11sp',
                        background_normal='',
                        background_color=get_color_from_hex("#F8FAFC"),
                        color=get_color_from_hex("#334155")
                    )
                    btn.bind(size=btn.setter('text_size'))
                    btn.bind(on_press=lambda inst, qi=q_idx, sc=score, ot=opt_text: self.select_option(qi, sc, ot))
                    self.buttons[q_idx].append((btn, opt_text))
                    card.add_widget(btn)

                content.add_widget(card)
                q_idx += 1

        # Живой счетчик
        live_card = Card(
            bg_color="#E2E8F0", border_color="#CBD5E1",
            orientation='vertical', size_hint_y=None, height=66, padding=8, spacing=3
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

        # Кнопка сохранения дня
        save_btn = Button(
            text="💾 Зафиксировать результат за день", bold=True, font_size='13sp',
            size_hint_y=None, height=44,
            background_normal='', background_color=get_color_from_hex("#2563EB"),
            color=get_color_from_hex("#FFFFFF")
        )
        save_btn.bind(on_press=self.save_data)
        content.add_widget(save_btn)

        self.survey_scroll.add_widget(content)

    # ---------------------------------------------------------
    # ВКЛАДКА 2: АНАЛИТИКА И ДАТАСЕТ
    # ---------------------------------------------------------
    def init_data_view(self):
        self.data_container = BoxLayout(orientation='vertical', spacing=8)

        # Карточки KPI
        kpi_grid = GridLayout(cols=2, spacing=6, size_hint_y=None, height=110)
        self.kpi_total_card, self.kpi_total_val = self.create_kpi_card("Всего записей")
        self.kpi_anx_card, self.kpi_anx_val = self.create_kpi_card("Ср. тревога")
        self.kpi_dep_card, self.kpi_dep_val = self.create_kpi_card("Ср. депрессия")
        self.kpi_slp_card, self.kpi_slp_val = self.create_kpi_card("Ср. балл сна")

        kpi_grid.add_widget(self.kpi_total_card)
        kpi_grid.add_widget(self.kpi_anx_card)
        kpi_grid.add_widget(self.kpi_dep_card)
        kpi_grid.add_widget(self.kpi_slp_card)
        self.data_container.add_widget(kpi_grid)

        # Панель кнопок действий
        actions_grid = GridLayout(cols=3, spacing=5, size_hint_y=None, height=76)
        
        btn_refresh = Button(
            text="Обновить", font_size='11sp', bold=True,
            background_normal='', background_color=get_color_from_hex("#FFFFFF"),
            color=get_color_from_hex("#334155")
        )
        btn_refresh.bind(on_press=lambda inst: self.refresh_table_data())

        btn_summary = Button(
            text="📊 Прогноз", font_size='11sp', bold=True,
            background_normal='', background_color=get_color_from_hex("#2563EB"),
            color=get_color_from_hex("#FFFFFF")
        )
        btn_summary.bind(on_press=lambda inst: self.show_summary_popup())

        btn_csv = Button(
            text="📥 CSV", font_size='11sp', bold=True,
            background_normal='', background_color=get_color_from_hex("#0D9488"),
            color=get_color_from_hex("#FFFFFF")
        )
        btn_csv.bind(on_press=lambda inst: self.export_csv())

        btn_report = Button(
            text="📄 Отчет", font_size='11sp', bold=True,
            background_normal='', background_color=get_color_from_hex("#475569"),
            color=get_color_from_hex("#FFFFFF")
        )
        btn_report.bind(on_press=lambda inst: self.export_report())

        btn_delete = Button(
            text="🗑 Удалить", font_size='11sp', bold=True,
            background_normal='', background_color=get_color_from_hex("#EF4444"),
            color=get_color_from_hex("#FFFFFF")
        )
        btn_delete.bind(on_press=lambda inst: self.delete_selected_record())

        actions_grid.add_widget(btn_refresh)
        actions_grid.add_widget(btn_summary)
        actions_grid.add_widget(btn_csv)
        actions_grid.add_widget(btn_report)
        actions_grid.add_widget(btn_delete)
        self.data_container.add_widget(actions_grid)

        # Заголовок таблицы
        table_hdr = Card(
            bg_color="#E2E8F0", border_color="#CBD5E1",
            orientation='horizontal', size_hint_y=None, height=30, padding=[4, 0, 4, 0]
        )
        table_hdr.add_widget(Label(text="[b]ID[/b]", markup=True, color=get_color_from_hex("#334155"), font_size='10sp', size_hint_x=0.12))
        table_hdr.add_widget(Label(text="[b]Дата[/b]", markup=True, color=get_color_from_hex("#334155"), font_size='10sp', size_hint_x=0.32))
        table_hdr.add_widget(Label(text="[b]Трев.[/b]", markup=True, color=get_color_from_hex("#334155"), font_size='10sp', size_hint_x=0.18))
        table_hdr.add_widget(Label(text="[b]Депр.[/b]", markup=True, color=get_color_from_hex("#334155"), font_size='10sp', size_hint_x=0.18))
        table_hdr.add_widget(Label(text="[b]Сон[/b]", markup=True, color=get_color_from_hex("#334155"), font_size='10sp', size_hint_x=0.10))
        table_hdr.add_widget(Label(text="[b]Физ.[/b]", markup=True, color=get_color_from_hex("#334155"), font_size='10sp', size_hint_x=0.10))
        self.data_container.add_widget(table_hdr)

        # Скролл строк таблицы
        self.table_scroll = ScrollView(size_hint=(1, 1), do_scroll_x=False, bar_width=4)
        self.table_rows_box = BoxLayout(orientation='vertical', size_hint_y=None, spacing=3)
        self.table_rows_box.bind(minimum_height=self.table_rows_box.setter('height'))
        self.table_scroll.add_widget(self.table_rows_box)
        self.data_container.add_widget(self.table_scroll)

    def create_kpi_card(self, title):
        card = Card(orientation='vertical', padding=6, spacing=2)
        t_lbl = Label(text=title, color=get_color_from_hex("#64748B"), font_size='10.5sp', bold=True)
        v_lbl = Label(text="0.0", color=get_color_from_hex("#0F172A"), font_size='16sp', bold=True)
        card.add_widget(t_lbl)
        card.add_widget(v_lbl)
        return card, v_lbl

    # ---------------------------------------------------------
    # ЛОГИКА И БАЗА ДАННЫХ
    # ---------------------------------------------------------
    def init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.cursor().execute("""CREATE TABLE IF NOT EXISTS results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT, fio TEXT, age INTEGER, gender TEXT,
                anxiety INTEGER, anxiety_status TEXT,
                depression INTEGER, depression_status TEXT,
                sleep INTEGER, physical INTEGER
            )""")
            conn.commit()

    def select_option(self, q_idx, score, opt_text):
        self.answers[q_idx] = score
        for btn, text in self.buttons[q_idx]:
            if text == opt_text:
                btn.text = f"  ◉  {text}"
                btn.background_color = get_color_from_hex("#DBEAFE")
                btn.color = get_color_from_hex("#1E3A8A")
            else:
                btn.text = f"  ○  {text}"
                btn.background_color = get_color_from_hex("#F8FAFC")
                btn.color = get_color_from_hex("#334155")

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
        if score <= 7: return "Норма"
        if score <= 10: return "Субклинический"
        return "Клинический"

    def show_alert(self, title, text):
        layout = BoxLayout(orientation='vertical', padding=10, spacing=8)
        layout.add_widget(Label(text=text, color=get_color_from_hex("#FFFFFF"), font_size='12sp', halign='center'))
        btn = Button(
            text="OK", size_hint_y=None, height=36,
            background_normal='', background_color=get_color_from_hex("#2563EB")
        )
        popup = Popup(title=title, content=layout, size_hint=(0.85, 0.42))
        btn.bind(on_press=popup.dismiss)
        layout.add_widget(btn)
        popup.open()

    def save_data(self, instance):
        if len(self.answers) < 20:
            self.show_alert("Внимание", "Необходимо ответить на все 20 вопросов перед сохранением.")
            return

        fio = self.fio_input.text.strip() or "Студент"
        age = int(self.age_input.text.strip() or 20)

        anx = sum(sc for qi, sc in self.answers.items() if self.q_types[qi] == "A")
        dep = sum(sc for qi, sc in self.answers.items() if self.q_types[qi] == "D")
        slp = sum(sc for qi, sc in self.answers.items() if self.q_types[qi] == "SLEEP")
        phy = sum(sc for qi, sc in self.answers.items() if self.q_types[qi] == "PHYS")

        anx_st = self.get_hads_status(anx)
        dep_st = self.get_hads_status(dep)
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M")

        with sqlite3.connect(self.db_path) as conn:
            conn.cursor().execute("""INSERT INTO results (date, fio, age, gender, anxiety, anxiety_status,
                                depression, depression_status, sleep, physical)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""", (now_str, fio, age, "Мужской", anx, anx_st, dep, dep_st, slp, phy))
            conn.commit()

        # Сброс опросника
        self.answers.clear()
        for qi, b_list in self.buttons.items():
            for btn, text in b_list:
                btn.text = f"  ○  {text}"
                btn.background_color = get_color_from_hex("#F8FAFC")
                btn.color = get_color_from_hex("#334155")

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
        self.selected_row_box = None

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

        for r in rows:
            rec_id = r[0]
            row_box = Card(
                bg_color="#FFFFFF", border_color="#E2E8F0", radius=6,
                orientation='horizontal', size_hint_y=None, height=36, padding=[4, 0, 4, 0]
            )
            short_date = r[1][5:16] if len(r[1]) >= 16 else r[1]
            row_box.add_widget(Label(text=str(rec_id), color=get_color_from_hex("#0F172A"), font_size='10sp', size_hint_x=0.12))
            row_box.add_widget(Label(text=short_date, color=get_color_from_hex("#475569"), font_size='9.5sp', size_hint_x=0.32))
            row_box.add_widget(Label(text=f"{r[5]} ({r[6][:3]})", color=get_color_from_hex("#1E3A8A"), font_size='9.5sp', size_hint_x=0.18))
            row_box.add_widget(Label(text=f"{r[7]} ({r[8][:3]})", color=get_color_from_hex("#1E3A8A"), font_size='9.5sp', size_hint_x=0.18))
            row_box.add_widget(Label(text=str(r[9]), color=get_color_from_hex("#0F172A"), font_size='10sp', size_hint_x=0.10))
            row_box.add_widget(Label(text=str(r[10]), color=get_color_from_hex("#0F172A"), font_size='10sp', size_hint_x=0.10))

            # Клик по строке для выбора
            select_btn = Button(
                size_hint=(1, 1), background_normal='', background_color=(0, 0, 0, 0)
            )
            select_btn.bind(on_press=lambda inst, rid=rec_id, rbox=row_box: self.select_table_row(rid, rbox))
            
            # Контейнер наложения кнопки поверх строки
            wrapper = BoxLayout(size_hint_y=None, height=36)
            wrapper.add_widget(row_box)
            row_box.add_widget(select_btn)
            self.table_rows_box.add_widget(wrapper)

    def select_table_row(self, rec_id, row_box):
        if self.selected_row_box:
            self.selected_row_box.bg_hex = "#FFFFFF"
            self.selected_row_box.update_canvas()

        self.selected_record_id = rec_id
        self.selected_row_box = row_box
        row_box.bg_hex = "#DBEAFE"
        row_box.update_canvas()

    def delete_selected_record(self):
        if not self.selected_record_id:
            self.show_alert("Выбор записи", "Необходимо нажать на строку в таблице перед удалением.")
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
            self.show_alert("Итоги", "Требуется минимум 2 записи для расчета корреляции.")
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
            f"Итог: {verdict}"
        )
        self.show_alert("📊 Предиктивный отчет", text)

    def export_csv(self):
        with sqlite3.connect(self.db_path) as conn:
            rows = conn.cursor().execute("SELECT * FROM results").fetchall()

        if not rows:
            self.show_alert("Экспорт", "База данных пуста.")
            return

        csv_path = os.path.join(self.user_data_dir, "dataset_hads.csv")
        with open(csv_path, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f, delimiter=";")
            writer.writerow(["id", "date", "fio", "age", "gender", "anxiety", "anxiety_status",
                             "depression", "depression_status", "sleep", "physical"])
            writer.writerows(rows)

        self.show_alert("Экспорт завершен", f"Файл сохранен:\n{csv_path}")

    def export_report(self):
        with sqlite3.connect(self.db_path) as conn:
            rows = conn.cursor().execute("SELECT * FROM results ORDER BY id ASC").fetchall()

        if not rows:
            self.show_alert("Отчет", "База данных пуста.")
            return

        report_path = os.path.join(self.user_data_dir, "summary_report.html")
        table_html = "".join([
            f"<tr><td align='center'>{r[0]}</td><td>{r[1]}</td>"
            f"<td align='center'><b>{r[5]}</b> ({r[6]})</td>"
            f"<td align='center'><b>{r[7]}</b> ({r[8]})</td>"
            f"<td align='center'>{r[9]}</td><td align='center'>{r[10]}</td></tr>"
            for r in rows
        ])
        html = f"""
        <html><head><meta charset='utf-8'><style>
            body {{ font-family: sans-serif; padding: 15px; color: #0F172A; }}
            table {{ width: 100%; border-collapse: collapse; margin-top: 10px; font-size: 12px; }}
            th, td {{ border: 1px solid #CBD5E1; padding: 6px; }}
            th {{ background: #F1F5F9; }}
        </style></head><body>
            <h2>СВОДНЫЙ ОТЧЕТ МОНИТОРИНГА (HADS + СОН)</h2>
            <p><b>Записей:</b> {len(rows)} | <b>Участник:</b> {rows[-1][2]}</p>
            <table>
                <tr><th>ID</th><th>Дата</th><th>Тревога</th><th>Депрессия</th><th>Сон</th><th>Тонус</th></tr>
                {table_html}
            </table>
        </body></html>
        """
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(html)

        self.show_alert("Готово", f"Сводный отчет сохранен:\n{report_path}")

if __name__ == '__main__':
    HADSApp().run()
