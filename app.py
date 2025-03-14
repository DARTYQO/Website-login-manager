import flet as ft
import json
from datetime import datetime
import os
import requests
import base64
import asyncio

# הגדרת מחלקות בסיסיות
class Contact:
    def __init__(self, name, phone, email="", group=""):
        self.name = name
        self.phone = phone
        self.email = email
        self.group = group

class Event:
    def __init__(self, title, date, time, location, participants=None):
        self.title = title
        self.date = date
        self.time = time
        self.location = location
        self.participants = participants or []
        self.pending_participants = [] 
        self.pending_notes = {}
        
class Group:
    def __init__(self, name, description=""):
        self.name = name
        self.description = description
        self.members = []

class LoginManager:
    def __init__(self):
        self.current_user = None
        self.data_folder = "DATA"
        self.github_token = "your_github_token_here"  # יש להחליף בטוקן אמיתי
        self.page = None
        self.organization_field = None
        self.password_field = None
        self.error_text = None
        self.on_login_success = None

    def create_login_page(self, page, on_login_success):
        self.page = page
        self.on_login_success = on_login_success
        
        # הגדרות בסיסיות של החלון
        page.title = "כניסה למערכת"
        page.window_width = 400
        page.window_height = 400
        page.padding = 20
        page.rtl = True
        page.bgcolor = ft.colors.WHITE
        page.controls.clear()
        
        # יצירת שדות הטופס
        self.create_form_fields()
        
        # יצירת והצגת טופס ההתחברות
        login_form = self.create_login_form()
        page.add(
            ft.Container(
                content=login_form,
                alignment=ft.alignment.center
            )
        )
        page.update()

    def create_form_fields(self):
        self.organization_field = ft.TextField(
            label="שם ארגון",
            width=300,
            text_align="right",
            bgcolor=ft.colors.WHITE,
            focused_border_color=ft.colors.BLUE,
            prefix_icon=ft.Icons.BUSINESS
        )
        
        self.password_field = ft.TextField(
            label="סיסמה",
            width=300,
            password=True,
            text_align="right",
            bgcolor=ft.colors.WHITE,
            focused_border_color=ft.colors.BLUE,
            prefix_icon=ft.Icons.LOCK
        )
        
        self.error_text = ft.Text(
            color=ft.colors.RED,
            size=14,
            weight=ft.FontWeight.BOLD,
            text_align=ft.TextAlign.CENTER
        )

# המשך מחלקת LoginManager
    def create_login_form(self):
        return ft.Container(
            content=ft.Column(
                [
                    ft.Container(
                        content=ft.Text(
                            "ברוכים הבאים",
                            size=32,
                            weight=ft.FontWeight.BOLD,
                            text_align=ft.TextAlign.CENTER
                        ),
                        margin=ft.margin.only(bottom=20)
                    ),
                    self.organization_field,
                    ft.Container(height=10),
                    self.password_field,
                    ft.Container(height=10),
                    self.error_text,
                    ft.Container(height=20),
                    ft.ElevatedButton(
                        content=ft.Text(
                            "התחבר",
                            size=16,
                            weight=ft.FontWeight.BOLD
                        ),
                        width=300,
                        height=45,
                        on_click=self.try_login,
                        bgcolor=ft.colors.BLUE,
                        color=ft.colors.WHITE
                    ),
                    ft.Container(height=20),
                    ft.TextButton(
                        text="להרשמה לחץ כאן",
                        on_click=lambda _: self.page.launch_url("https://github.com/DARTYQO/people/blob/main/DATA/register.html")
                    )
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER
            ),
            padding=30,
            bgcolor=ft.colors.WHITE,
            border_radius=10
        )

    def try_login(self, e):
        print("בודק התחברות")
        if self.validate_organization(self.organization_field.value, self.password_field.value):
            self.current_user = self.organization_field.value
            self.on_login_success()
        else:
            self.error_text.value = "שם ארגון או סיסמה שגויים"
            self.page.update()

    def validate_organization(self, org_name, password):
        try:
            if not os.path.exists(self.data_folder):
                return False
            
            org_file_path = os.path.join(self.data_folder, "organizations.json")
            if not os.path.exists(org_file_path):
                return False
            
            with open(org_file_path, 'r', encoding='utf-8') as f:
                orgs_data = json.load(f)
            
            return org_name in orgs_data and orgs_data[org_name]["password"] == password
            
        except Exception as e:
            print(f"שגיאה באימות: {str(e)}")
            return False

    def load_organization_data(self):
        if not self.current_user:
            return None
        
        try:
            # ניסיון לטעון מגיטהאב
            headers = {
                "Authorization": f"Bearer {self.github_token}",
                "Accept": "application/vnd.github.v3+json"
            }
            
            file_path = f"DATA/{self.current_user}/data.json"
            url = f"https://api.github.com/repos/DARTYQO/people/contents/{file_path}"
            
            response = requests.get(url, headers=headers)
            
            if response.status_code == 200:
                content = base64.b64decode(response.json()["content"]).decode('utf-8')
                data = json.loads(content)
                self.show_message("הנתונים נטענו בהצלחה מגיטהאב", ft.colors.GREEN)
                return data
                
        except Exception as e:
            print(f"שגיאה בטעינה מגיטהאב: {str(e)}")
        
        # אם הטעינה מגיטהאב נכשלה, ננסה לטעון מקומית
        try:
            local_path = os.path.join(self.data_folder, self.current_user, "data.json")
            if os.path.exists(local_path):
                with open(local_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                self.show_message("הנתונים נטענו מהמחשב המקומי", ft.colors.BLUE)
                return data
        except Exception as e:
            print(f"שגיאה בטעינה מקומית: {str(e)}")
        
        return None

    def save_organization_data(self, data):
        if not self.current_user:
            return False
        
        try:
            # שמירה מקומית
            org_folder = os.path.join(self.data_folder, self.current_user)
            if not os.path.exists(org_folder):
                os.makedirs(org_folder)
            
            local_path = os.path.join(org_folder, "data.json")
            json_data = json.dumps(data, ensure_ascii=False, indent=4)
            
            with open(local_path, 'w', encoding='utf-8') as f:
                f.write(json_data)
            
            # שמירה לגיטהאב
            self._save_to_github(json_data)
            return True
            
        except Exception as e:
            print(f"שגיאה בשמירת הנתונים: {str(e)}")
            return False

    def _save_to_github(self, json_data):
        headers = {
            "Authorization": f"Bearer {self.github_token}",
            "Accept": "application/vnd.github.v3+json"
        }
        
        file_path = f"DATA/{self.current_user}/data.json"
        url = f"https://api.github.com/repos/DARTYQO/people/contents/{file_path}"
        
        try:
            # בדיקה אם הקובץ קיים
            response = requests.get(url, headers=headers)
            sha = response.json()["sha"] if response.status_code == 200 else None
            
            # הכנת התוכן לשמירה
            content = base64.b64encode(json_data.encode('utf-8')).decode('utf-8')
            
            data = {
                "message": f"עדכון נתונים - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                "content": content
            }
            
            if sha:
                data["sha"] = sha
            
            # שליחת העדכון לגיטהאב
            response = requests.put(url, headers=headers, json=data)
            
            if response.status_code in [200, 201]:
                self.show_message("הנתונים נשמרו בהצלחה בגיטהאב", ft.colors.GREEN)
            else:
                self.show_message(f"שגיאה בשמירה לגיטהאב: {response.status_code}", ft.colors.RED)
                
        except Exception as e:
            self.show_message(f"שגיאה בתקשורת עם גיטהאב: {str(e)}", ft.colors.RED)

    def show_message(self, message, color):
        if self.page:
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text(message),
                bgcolor=color
            )
            self.page.snack_bar.open = True
            self.page.update()

class AppManager:
    def __init__(self):
        self.contacts = []
        self.events = []
        self.groups = []
        self.current_edit_contact = None
        self.login_manager = None
        
        # משתני ממשק
        self.contacts_list_view = None
        self.events_grid_view = None
        self.groups_list_view = None
        self.tabs = None
        
        # שדות טפסים
        self.name_field = None
        self.phone_field = None
        self.email_field = None
        self.group_field = None
        self.search_field = None
        self.event_title = None
        self.event_date = None
        self.event_time = None
        self.event_location = None
        self.group_name_field = None
        self.group_description_field = None

    def initialize_app(self, page: ft.Page):
        self.login_manager = LoginManager()
        self.login_manager.create_login_page(page, self.setup_main_page)

    def setup_main_page(self):
        # הגדרת המסך הראשי
        self.login_manager.page.title = "מערכת ניהול אנשי קשר ואירועים"
        self.login_manager.page.window_width = 1200
        self.login_manager.page.window_height = 800
        self.login_manager.page.padding = 20
        self.login_manager.page.rtl = True
        self.login_manager.page.bgcolor = ft.colors.WHITE
        
        # יצירת הרכיבים
        self.create_form_fields()
        self.create_list_views()
        self.create_tabs()
        
        # טעינת נתונים
        self.load_data()
        
        # ניקוי והצגת הממשק החדש
        self.login_manager.page.clean()
        self.login_manager.page.add(
            ft.Text(
                "מערכת ניהול אנשי קשר ואירועים",
                size=30,
                weight=ft.FontWeight.BOLD,
                text_align=ft.TextAlign.CENTER
            ),
            self.tabs
        )
        self.login_manager.page.update()

    def create_contact_card(self, contact):
        is_selected = contact == self.current_edit_contact
        return ft.Card(
            content=ft.Container(
                content=ft.Row(
                    [
                        ft.Icon(
                            ft.Icons.PERSON,
                            color=ft.colors.BLUE if is_selected else ft.colors.BLACK,
                            size=30
                        ),
                        ft.Column(
                            [
                                ft.Text(
                                    contact.name,
                                    size=16,
                                    weight=ft.FontWeight.BOLD
                                ),
                                ft.Text(f"טלפון: {contact.phone}"),
                                ft.Text(f"אימייל: {contact.email}" if contact.email else ""),
                                ft.Text(f"קבוצה: {contact.group}" if contact.group else "")
                            ],
                            spacing=5,
                            expand=True
                        ),
                        ft.Row(
                            [
                                ft.IconButton(
                                    icon=ft.Icons.EDIT,
                                    icon_color=ft.colors.BLUE,
                                    tooltip="ערוך",
                                    on_click=lambda _, c=contact: self.edit_contact(c)
                                ),
                                ft.IconButton(
                                    icon=ft.Icons.DELETE,
                                    icon_color=ft.colors.RED,
                                    tooltip="מחק",
                                    on_click=lambda _, c=contact: self.delete_contact(c)
                                )
                            ],
                            spacing=0
                        )
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                ),
                padding=10,
                bgcolor=ft.colors.BLUE_50 if is_selected else None
            )
        )

    def create_event_card(self, event):
        def delete_event(e, event_to_delete):
            self.events.remove(event_to_delete)
            self.events_grid_view.controls = [self.create_event_card(evt) for evt in self.events]
            self.save_data()
            self.show_message("האירוע נמחק בהצלחה", ft.colors.RED)
            self.login_manager.page.update()

        return ft.Card(
            content=ft.Container(
                content=ft.Column([
                    ft.ListTile(
                        leading=ft.Icon(ft.Icons.EVENT, color=ft.colors.BLUE),
                        title=ft.Text(
                            event.title,
                            size=20,
                            weight=ft.FontWeight.BOLD
                        ),
                        subtitle=ft.Text(
                            f"תאריך: {event.date}\nשעה: {event.time}\nמיקום: {event.location}"
                        )
                    ),
                    ft.Container(
                        content=ft.Row(
                            [
                                ft.IconButton(
                                    icon=ft.Icons.EDIT,
                                    icon_color=ft.colors.BLUE,
                                    tooltip="ערוך אירוע",
                                    on_click=lambda e: self.manage_event(event)
                                ),
                                ft.IconButton(
                                    icon=ft.Icons.DELETE,
                                    icon_color=ft.colors.RED,
                                    tooltip="מחק אירוע",
                                    on_click=lambda e, evt=event: delete_event(e, evt)
                                )
                            ],
                            alignment=ft.MainAxisAlignment.END
                        ),
                        padding=ft.padding.only(right=10, bottom=10)
                    )
                ]),
                padding=10,
                bgcolor=ft.colors.WHITE
            ),
            elevation=3
        )


    def create_group_card(self, group):
        return ft.Card(
            content=ft.Container(
                content=ft.Column([
                    ft.ListTile(
                        leading=ft.Icon(ft.Icons.GROUP, color=ft.colors.BLUE),
                        title=ft.Text(
                            group.name,
                            size=18,
                            weight=ft.FontWeight.BOLD
                        ),
                        subtitle=ft.Column([
                            ft.Text(group.description) if group.description else ft.Text("אין תיאור"),
                            ft.Text(f"מספר חברים: {len(group.members)}", weight=ft.FontWeight.BOLD),
                            ft.Text("חברי הקבוצה:", weight=ft.FontWeight.BOLD),
                            ft.Text(", ".join([member.name for member in group.members]) if group.members else "אין חברים בקבוצה")
                        ])
                    ),
                    ft.Row(
                        [
                            ft.ElevatedButton(
                                "כניסה לקבוצה",
                                icon=ft.Icons.LOGIN,
                                on_click=lambda e, g=group: self.enter_group(g)
                            ),
                            ft.ElevatedButton(
                                "ערוך קבוצה",
                                icon=ft.Icons.EDIT,
                                on_click=lambda e, g=group: self.edit_group(g)
                            ),
                            ft.ElevatedButton(
                                "מחק קבוצה",
                                icon=ft.Icons.DELETE,
                                bgcolor=ft.colors.RED,
                                color=ft.colors.WHITE,
                                on_click=lambda e, g=group: self.delete_group(g)
                            )
                        ],
                        alignment=ft.MainAxisAlignment.END
                    )
                ]),
                padding=10
            )
        )

    def create_participant_card(self, participant, status, event, participants_grid):
        is_confirmed = status == "confirmed"
        return ft.Card(
            content=ft.Container(
                content=ft.Row(
                    [
                        ft.Icon(
                            ft.Icons.CHECK_CIRCLE if is_confirmed else ft.Icons.PENDING,
                            color=ft.colors.GREEN if is_confirmed else ft.colors.ORANGE
                        ),
                        ft.Column(
                            [
                                ft.Text(participant.name, size=16, weight=ft.FontWeight.BOLD),
                                ft.Text(f"טלפון: {participant.phone}"),
                                ft.Text(f"אימייל: {participant.email}" if participant.email else ""),
                                ft.Text(
                                    "מאושר" if is_confirmed else "ממתין לאישור",
                                    color=ft.colors.GREEN if is_confirmed else ft.colors.ORANGE
                                )
                            ],
                            spacing=5,
                            expand=True
                        ),
                        ft.Row(
                            [
                                ft.IconButton(
                                    icon=ft.Icons.CHECK,
                                    icon_color=ft.colors.GREEN,
                                    tooltip="אשר השתתפות",
                                    visible=not is_confirmed,
                                    on_click=lambda _, p=participant: self.confirm_participation(p, event, participants_grid)
                                ),
                                ft.IconButton(
                                    icon=ft.Icons.DELETE,
                                    icon_color=ft.colors.RED,
                                    tooltip="הסר מהאירוע",
                                    on_click=lambda _, p=participant: self.remove_participant(p, event, participants_grid)
                                )
                            ]
                        )
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                ),
                padding=10,
                bgcolor=ft.colors.GREEN_50 if is_confirmed else ft.colors.ORANGE_50
            )
        )        
    def update_group_options(self):
        """
        מעדכן את האפשרויות בתיבת הבחירה של הקבוצות
        """
        # יצירת רשימת אפשרויות מהקבוצות הקיימות
        group_options = [
            ft.dropdown.Option(group.name) 
            for group in self.groups
        ]
        
        # הוספת אפשרויות ברירת מחדל
        default_options = [
            ft.dropdown.Option("משפחה"),
            ft.dropdown.Option("חברים"),
            ft.dropdown.Option("עבודה"),
            ft.dropdown.Option("אחר")
        ]
        
        # הוספת האפשרויות לרשימה הכללית
        all_options = []
        all_options.extend(group_options)
        
        # הוספת אפשרויות ברירת המחדל רק אם הן לא קיימות כבר
        for option in default_options:
            if option not in all_options:
                all_options.append(option)
        
        # עדכון האפשרויות בשדה הקבוצה
        self.group_field.options = all_options
        
        # אם יש ערך נוכחי שכבר נבחר, נשמור אותו
        current_value = self.group_field.value
        if current_value and current_value not in [opt.key for opt in all_options]:
            self.group_field.value = None
            
        # עדכון התצוגה
        if self.login_manager and self.login_manager.page:
            self.login_manager.page.update()

    def edit_group(self, group):
        """
        פותח חלון לעריכת פרטי הקבוצה
        """
        def save_changes(e):
            if new_name_field.value:
                group.name = new_name_field.value
                group.description = new_description_field.value
                self.update_views()
                self.save_data()
                dlg.open = False
                self.login_manager.page.update()
                self.show_message("הקבוצה עודכנה בהצלחה", ft.colors.GREEN)

        new_name_field = ft.TextField(
            label="שם הקבוצה",
            value=group.name,
            width=300,
            text_align="right"
        )
        
        new_description_field = ft.TextField(
            label="תיאור הקבוצה",
            value=group.description,
            width=300,
            multiline=True,
            text_align="right"
        )

        dlg = ft.AlertDialog(
            title=ft.Text("עריכת קבוצה"),
            content=ft.Column([
                new_name_field,
                new_description_field
            ], tight=True),
            actions=[
                ft.TextButton("ביטול", on_click=lambda e: setattr(dlg, 'open', False)),
                ft.TextButton("שמור", on_click=save_changes)
            ],
            actions_alignment=ft.MainAxisAlignment.END
        )

        self.login_manager.page.dialog = dlg
        dlg.open = True
        self.login_manager.page.update()

    def delete_group(self, group):
        """
        מוחק קבוצה מהמערכת
        """
        def confirm_delete(e):
            self.groups.remove(group)
            # עדכון אנשי הקשר ששייכים לקבוצה
            for contact in self.contacts:
                if contact.group == group.name:
                    contact.group = None
            self.update_views()
            self.save_data()
            dlg.open = False
            self.login_manager.page.update()
            self.show_message("הקבוצה נמחקה בהצלחה", ft.colors.RED)

        dlg = ft.AlertDialog(
            title=ft.Text("מחיקת קבוצה"),
            content=ft.Text(f"האם אתה בטוח שברצונך למחוק את הקבוצה '{group.name}'?"),
            actions=[
                ft.TextButton("ביטול", on_click=lambda e: setattr(dlg, 'open', False)),
                ft.TextButton("מחק", on_click=confirm_delete)
            ],
            actions_alignment=ft.MainAxisAlignment.END
        )

        self.login_manager.page.dialog = dlg
        dlg.open = True
        self.login_manager.page.update()

    def toggle_group_member(self, e, group, contact):
        """
        מוסיף או מסיר חבר מקבוצה
        """
        if e.control.value:  # אם הצ'קבוקס נבחר
            if contact not in group.members:
                group.members.append(contact)
                contact.group = group.name
        else:  # אם הצ'קבוקס בוטל
            if contact in group.members:
                group.members.remove(contact)
                if contact.group == group.name:
                    contact.group = None
        
        self.update_views()
        self.save_data()
        
    def create_form_fields(self):
        # שדות טופס אנשי קשר
        self.name_field = ft.TextField(
            label="שם",
            width=200,
            text_align="right",
            prefix_icon=ft.Icons.PERSON
        )
        
        self.phone_field = ft.TextField(
            label="טלפון",
            width=200,
            text_align="right",
            prefix_icon=ft.Icons.PHONE
        )
        
        self.email_field = ft.TextField(
            label="אימייל",
            width=200,
            text_align="right",
            prefix_icon=ft.Icons.EMAIL
        )

        self.group_field = ft.Dropdown(
            label="קבוצה",
            width=200,
            options=[
                ft.dropdown.Option("משפחה"),
                ft.dropdown.Option("חברים"),
                ft.dropdown.Option("עבודה"),
                ft.dropdown.Option("אחר")
            ]
        )

        self.search_field = ft.TextField(
            label="חיפוש",
            width=200,
            prefix_icon=ft.Icons.SEARCH,
            on_change=lambda e: self.filter_contacts(e.control.value)
        )

        # שדות טופס אירועים
        self.event_title = ft.TextField(
            label="כותרת האירוע",
            width=200,
            text_align="right",
            prefix_icon=ft.Icons.EVENT_NOTE
        )

        self.event_date = ft.TextField(
            label="תאריך",
            hint_text="הזן תאריך",
            width=200,
            text_align="right",
            prefix_icon=ft.Icons.CALENDAR_TODAY
        )

        self.event_time = ft.TextField(
            label="שעה",
            hint_text="HH:MM",
            width=200,
            text_align="right",
            prefix_icon=ft.Icons.SCHEDULE
        )

        self.event_location = ft.TextField(
            label="מיקום",
            width=200,
            text_align="right",
            prefix_icon=ft.Icons.LOCATION_ON
        )

        # שדות טופס קבוצות
        self.group_name_field = ft.TextField(
            label="שם הקבוצה",
            width=300,
            text_align="right",
            prefix_icon=ft.Icons.GROUP
        )

        self.group_description_field = ft.TextField(
            label="תיאור הקבוצה",
            width=300,
            text_align="right",
            multiline=True,
            prefix_icon=ft.Icons.DESCRIPTION
        )
    def create_list_views(self):
        # יצירת תצוגת אנשי קשר
        self.contacts_list_view = ft.ListView(
            expand=True,
            spacing=10,
            padding=20,
            height=400
        )

        # יצירת תצוגת אירועים
        self.events_grid_view = ft.GridView(
            expand=True,
            runs_count=2,
            max_extent=400,
            child_aspect_ratio=2.0,
            spacing=10,
            run_spacing=10,
            padding=20,
            height=400
        )

        # יצירת תצוגת קבוצות
        self.groups_list_view = ft.ListView(
            expand=True,
            spacing=10,
            padding=20,
            height=400
        )

    def create_tabs(self):
        # יצירת טופס אנשי קשר
        contacts_form = self.create_contacts_form()
        events_form = self.create_events_form()
        groups_form = self.create_groups_form()

        # יצירת הכרטיסיות
        self.tabs = ft.Tabs(
            selected_index=0,
            animation_duration=300,
            tabs=[
                ft.Tab(
                    text="אנשי קשר",
                    icon=ft.Icons.PEOPLE,
                    content=contacts_form
                ),
                ft.Tab(
                    text="קבוצות",
                    icon=ft.Icons.GROUPS,
                    content=groups_form
                ),
                ft.Tab(
                    text="אירועים",
                    icon=ft.Icons.EVENT,
                    content=events_form
                ),
            ],
            expand=1,
            tab_alignment=ft.TabAlignment.START
        )

    def create_contacts_form(self):
        add_contact_button = ft.ElevatedButton(
            text="+",
            icon=ft.Icons.PERSON_ADD,
            on_click=self.add_or_update_contact,
            bgcolor=ft.colors.BLUE,
            color=ft.colors.WHITE
        )

        return ft.Column([
            ft.Container(
                content=ft.Row(
                    controls=[
                        ft.Container(
                            content=add_contact_button,
                            padding=ft.padding.only(right=10)
                        ),
                        ft.Container(
                            content=self.name_field,
                            width=200,
                            padding=5
                        ),
                        ft.Container(
                            content=self.phone_field,
                            width=200,
                            padding=5
                        ),
                        ft.Container(
                            content=self.email_field,
                            width=200,
                            padding=5
                        ),
                        ft.Container(
                            content=self.group_field,
                            width=200,
                            padding=5
                        ),
                        ft.Container(
                            content=self.search_field,
                            padding=ft.padding.only(left=10)
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                ),
                padding=10,
            ),
            ft.Container(
                content=self.contacts_list_view,
                expand=True,
                margin=ft.margin.all(10),
                border=ft.border.all(1, ft.colors.BLACK12),
                border_radius=10,
                padding=10
            )
        ])

    def create_events_form(self):
        add_event_button = ft.ElevatedButton(
            text="+",
            icon=ft.Icons.EVENT_AVAILABLE,
            on_click=self.add_event,
            bgcolor=ft.colors.BLUE,
            color=ft.colors.WHITE
        )

        return ft.Column([
            ft.Container(
                content=ft.Row(
                    controls=[
                        ft.Container(
                            content=add_event_button,
                            padding=ft.padding.only(right=10)
                        ),
                        ft.Container(
                            content=self.event_title,
                            width=200,
                            padding=5
                        ),
                        ft.Container(
                            content=self.event_date,
                            width=200,
                            padding=5
                        ),
                        ft.Container(
                            content=self.event_time,
                            width=200,
                            padding=5
                        ),
                        ft.Container(
                            content=self.event_location,
                            width=200,
                            padding=5
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.START,
                ),
                padding=10,
            ),
            ft.Container(
                content=self.events_grid_view,
                expand=True,
                margin=ft.margin.all(10),
                border=ft.border.all(1, ft.colors.BLACK12),
                border_radius=10,
                padding=10
            )
        ])
    
    def create_groups_form(self):
        add_group_button = ft.ElevatedButton(
            text="+",
            icon=ft.Icons.GROUP_ADD,
            on_click=self.add_group,
            bgcolor=ft.colors.BLUE,
            color=ft.colors.WHITE
        )

        return ft.Column([
            ft.Container(
                content=ft.Row(
                    controls=[
                        ft.Container(
                            content=add_group_button,
                            padding=ft.padding.only(right=10)
                        ),
                        ft.Container(
                            content=self.group_name_field,
                            padding=5
                        ),
                        ft.Container(
                            content=self.group_description_field,
                            padding=5
                        )
                    ],
                    alignment=ft.MainAxisAlignment.START
                ),
                padding=10
            ),
            ft.Container(
                content=self.groups_list_view,
                expand=True,
                margin=ft.margin.all(10),
                border=ft.border.all(1, ft.colors.BLACK12),
                border_radius=10,
                padding=10
            )
        ])

    # פונקציות ניהול אנשי קשר
    def add_or_update_contact(self, e):
        if not self.name_field.value:
            self.show_message("אנא הזן שם!", ft.colors.RED)
            return
        if not self.phone_field.value:
            self.show_message("אנא הזן מספר טלפון!", ft.colors.RED)
            return

        if self.current_edit_contact:
            # עדכון איש קשר קיים
            if self.current_edit_contact.group:
                old_group = next((g for g in self.groups if g.name == self.current_edit_contact.group), None)
                if old_group and self.current_edit_contact in old_group.members:
                    old_group.members.remove(self.current_edit_contact)

            self.current_edit_contact.name = self.name_field.value
            self.current_edit_contact.phone = self.phone_field.value
            self.current_edit_contact.email = self.email_field.value
            self.current_edit_contact.group = self.group_field.value
            contact = self.current_edit_contact
            self.show_message("איש הקשר עודכן בהצלחה", ft.colors.GREEN)
            self.current_edit_contact = None
        else:
            # הוספת איש קשר חדש
            contact = Contact(
                self.name_field.value,
                self.phone_field.value,
                self.email_field.value,
                self.group_field.value
            )
            self.contacts.append(contact)
            self.show_message("איש הקשר נוסף בהצלחה", ft.colors.GREEN)

        # עדכון שיוך לקבוצה
        if contact.group:
            new_group = next((g for g in self.groups if g.name == contact.group), None)
            if new_group and contact not in new_group.members:
                new_group.members.append(contact)

        self.clear_contact_fields()
        self.update_views()
        self.save_data()

    def edit_contact(self, contact):
        self.current_edit_contact = contact
        self.name_field.value = contact.name
        self.phone_field.value = contact.phone
        self.email_field.value = contact.email
        self.group_field.value = contact.group
        self.filter_contacts("")
        self.login_manager.page.update()

    def delete_contact(self, contact):
        self.contacts.remove(contact)
        self.filter_contacts("")
        self.update_participants_list()
        self.show_message("איש הקשר נמחק בהצלחה", ft.colors.RED)
        self.login_manager.page.update()

    def filter_contacts(self, search_text):
        if not search_text:
            self.contacts_list_view.controls = [self.create_contact_card(contact) for contact in self.contacts]
        else:
            filtered = [
                contact for contact in self.contacts
                if search_text.lower() in contact.name.lower() or
                   search_text in contact.phone or
                   search_text.lower() in contact.email.lower()
            ]
            self.contacts_list_view.controls = [self.create_contact_card(contact) for contact in filtered]
        self.login_manager.page.update()

    def add_event(self, e):
        if not self.event_title.value:
            self.show_message("אנא הזן כותרת לאירוע!", ft.colors.RED)
            return
        if not self.event_date.value:
            self.show_message("אנא הזן תאריך!", ft.colors.RED)
            return
        if not self.event_time.value:
            self.show_message("אנא הזן שעה!", ft.colors.RED)
            return

        # יצירת אירוע חדש עם כל המאפיינים הנדרשים
        new_event = Event(
            self.event_title.value,
            self.event_date.value,
            self.event_time.value,
            self.event_location.value if self.event_location.value else ""
        )
        
        # איתחול רשימות המשתתפים
        new_event.participants = []
        new_event.pending_participants = []
        new_event.pending_notes = {}
        
        # הוספת האירוע לרשימת האירועים
        self.events.append(new_event)
        
        # עדכון התצוגה
        self.events_grid_view.controls = [self.create_event_card(event) for event in self.events]
        
        # שמירת הנתונים
        self.save_data()
        
        # ניקוי השדות והצגת הודעה
        self.clear_event_fields()
        self.show_message("האירוע נוסף בהצלחה", ft.colors.GREEN)
        self.login_manager.page.update()

    def manage_event(self, event):
        """מנהל את תצוגת האירוע ומשתתפיו"""
        
        # נוסיף מילון לשמירת סטטוס המשתתפים
        participant_status = {p: "confirmed" for p in event.participants}
        if not hasattr(event, 'pending_participants'):
            event.pending_participants = []
        if not hasattr(event, 'pending_notes'):
            event.pending_notes = {}

        # העתקת הממתינים הקיימים לרשימה זמנית
        pending_participants = event.pending_participants.copy()

        def close_event_tab(e):
            event.pending_participants = pending_participants.copy()
            self.save_data()
            self.tabs.tabs = [tab for tab in self.tabs.tabs if tab.text != f"אירוע: {event.title}"]
            self.tabs.selected_index = 2
            self.login_manager.page.update()

        # יצירת הרשתות
        participants_grid = ft.GridView(
            expand=True,
            runs_count=2,
            max_extent=300,
            child_aspect_ratio=2.0,
            spacing=10,
            run_spacing=10,
            padding=20,
            height=400
        )

        available_contacts_grid = ft.GridView(
            expand=True,
            runs_count=2,
            max_extent=300,
            child_aspect_ratio=2.0,
            spacing=10,
            run_spacing=10,
            padding=20,
            height=400
        )

        def add_note_to_pending(e, participant):
            def save_note(e):
                note = note_field.value
                event.pending_notes[participant] = note
                note_dialog.open = False
                update_event_participants()
                self.save_data()
                self.login_manager.page.update()

            note_field = ft.TextField(
                label="הערה",
                value=event.pending_notes.get(participant, ""),
                width=400,
                multiline=True,
                min_lines=3,
                max_lines=5,
                text_align=ft.TextAlign.RIGHT,
                text_direction=ft.TextDirection.RTL
            )

            note_dialog = ft.AlertDialog(
                title=ft.Text(f"הוספת הערה עבור {participant.name}"),
                content=note_field,
                actions=[
                    ft.TextButton("ביטול", on_click=lambda e: setattr(note_dialog, 'open', False)),
                    ft.TextButton("שמור", on_click=save_note)
                ],
                actions_alignment=ft.MainAxisAlignment.END
            )

            self.login_manager.page.dialog = note_dialog
            note_dialog.open = True
            self.login_manager.page.update()

        def toggle_contact_selection(e, contact):
            if e.control.value and contact not in event.participants and contact not in pending_participants:
                pending_participants.append(contact)
            elif not e.control.value:
                if contact in pending_participants:
                    pending_participants.remove(contact)
                if contact in event.participants:
                    event.participants.remove(contact)
                    participant_status.pop(contact, None)
            update_event_participants()
            event.pending_participants = pending_participants.copy()
            self.save_data()

        def confirm_participation(contact):
            if contact in pending_participants:
                pending_participants.remove(contact)
                event.participants.append(contact)
                participant_status[contact] = "confirmed"
                event.pending_participants = pending_participants.copy()
                update_event_participants()
                self.save_data()

        def remove_participant(participant):
            if participant in event.participants:
                event.participants.remove(participant)
                participant_status.pop(participant, None)
            if participant in pending_participants:
                pending_participants.remove(participant)
            event.pending_participants = pending_participants.copy()
            update_event_participants()
            self.save_data()

        def update_event_participants():
            if not participants_grid or not available_contacts_grid:
                return
                
            # עדכון רשימת המשתתפים המאושרים והממתינים
            all_participants = []
            
            # הוספת משתתפים מאושרים
            for participant in event.participants:
                if participant:  # בדיקה שהמשתתף קיים
                    all_participants.append(
                        ft.Card(
                            content=ft.Container(
                                content=ft.Row(
                                    [
                                        ft.Icon(name=ft.Icons.CHECK_CIRCLE, color="green"),
                                        ft.Column(
                                            [
                                                ft.Text(participant.name, size=16, weight=ft.FontWeight.BOLD),
                                                ft.Text(f"טלפון: {participant.phone}"),
                                                ft.Text(f"אימייל: {participant.email}" if participant.email else ""),
                                                ft.Text("מאושר", color="green")
                                            ],
                                            spacing=5,
                                            expand=True
                                        ),
                                        ft.IconButton(
                                            icon=ft.Icons.DELETE,
                                            icon_color="red",
                                            tooltip="הסר מהאירוע",
                                            on_click=lambda _, p=participant: remove_participant(p)
                                        )
                                    ],
                                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                                ),
                                padding=10,
                                bgcolor="#E8F5E9"
                            )
                        )
                    )

            # הוספת משתתפים ממתינים
            for participant in pending_participants:
                if participant:  # בדיקה שהמשתתף קיים
                    note = event.pending_notes.get(participant, "")
                    all_participants.append(
                        ft.Card(
                            content=ft.Container(
                                content=ft.Column([
                                    ft.Row(
                                        [
                                            ft.Icon(name=ft.Icons.PENDING, color="orange"),
                                            ft.Column(
                                                [
                                                    ft.Text(participant.name, size=16, weight=ft.FontWeight.BOLD),
                                                    ft.Text(f"טלפון: {participant.phone}"),
                                                    ft.Text(f"אימייל: {participant.email}" if participant.email else ""),
                                                    ft.Text("ממתין לאישור", color="orange"),
                                                    ft.Text(f"הערה: {note}", color="grey") if note else None
                                                ],
                                                spacing=5,
                                                expand=True
                                            ),
                                            ft.Row(
                                                [
                                                    ft.IconButton(
                                                        icon=ft.Icons.NOTE_ADD,
                                                        icon_color="blue",
                                                        tooltip="הוסף הערה",
                                                        on_click=lambda e, p=participant: add_note_to_pending(e, p)
                                                    ),
                                                    ft.IconButton(
                                                        icon=ft.Icons.CHECK,
                                                        icon_color="green",
                                                        tooltip="אשר השתתפות",
                                                        on_click=lambda _, p=participant: confirm_participation(p)
                                                    ),
                                                    ft.IconButton(
                                                        icon=ft.Icons.DELETE,
                                                        icon_color="red",
                                                        tooltip="הסר מהאירוע",
                                                        on_click=lambda _, p=participant: remove_participant(p)
                                                    )
                                                ]
                                            )
                                        ],
                                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                                    )
                                ]),
                                padding=10,
                                bgcolor="#FFF3E0"
                            )
                        )
                    )

            try:
                # עדכון רשת המשתתפים
                if participants_grid and all_participants:
                    participants_grid.controls = all_participants

                # עדכון רשת אנשי הקשר הזמינים
                available_contacts = [
                    contact for contact in self.contacts 
                    if contact and contact not in event.participants and contact not in pending_participants
                ]
                
                if available_contacts_grid:
                    available_contacts_grid.controls = [
                        ft.Card(
                            content=ft.Container(
                                content=ft.Row(
                                    [
                                        ft.Checkbox(
                                            value=False,
                                            on_change=lambda e, c=contact: toggle_contact_selection(e, c)
                                        ),
                                        ft.Column(
                                            [
                                                ft.Text(contact.name, size=16, weight=ft.FontWeight.BOLD),
                                                ft.Text(f"טלפון: {contact.phone}"),
                                                ft.Text(f"אימייל: {contact.email}" if contact.email else ""),
                                                ft.Text(f"קבוצה: {contact.group}" if contact.group else "")
                                            ],
                                            spacing=5,
                                            expand=True
                                        )
                                    ],
                                    alignment=ft.MainAxisAlignment.START
                                ),
                                padding=10
                            )
                        ) for contact in available_contacts if contact
                    ]
                
                self.login_manager.page.update()
            except Exception as e:
                print(f"שגיאה בעדכון המשתתפים: {str(e)}")

        # בדיקה אם הכרטיסייה כבר קיימת
        for tab in self.tabs.tabs:
            if tab.text == f"אירוע: {event.title}":
                self.tabs.selected_index = self.tabs.tabs.index(tab)
                self.login_manager.page.update()
                return

        # יצירת הכרטיסייה החדשה
        tab = ft.Tab(
            text=f"אירוע: {event.title}",
            content=ft.Container(
                content=ft.Column(
                    [
                        ft.Row(
                            [
                                ft.Text("ניהול אירוע", size=30, weight=ft.FontWeight.BOLD),
                                ft.IconButton(
                                    icon=ft.Icons.CLOSE,
                                    icon_color="red",
                                    tooltip="סגור",
                                    on_click=close_event_tab
                                )
                            ],
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                        ),
                        ft.Divider(),
                        ft.Text("פרטי האירוע:", size=20, weight=ft.FontWeight.BOLD),
                        ft.Text(f"כותרת: {event.title}"),
                        ft.Text(f"תאריך: {event.date}"),
                        ft.Text(f"שעה: {event.time}"),
                        ft.Text(f"מיקום: {event.location}"),
                        ft.Divider(),
                        ft.Text("משתתפים באירוע:", size=20, weight=ft.FontWeight.BOLD),
                        participants_grid,
                        ft.Divider(),
                        ft.Text("הוסף משתתפים:", size=20, weight=ft.FontWeight.BOLD),
                        available_contacts_grid
                    ],
                    scroll=ft.ScrollMode.AUTO
                ),
                padding=20
            )
        )

        # עדכון התצוגה הראשונית
        update_event_participants()

        # הוספת הטאב והמעבר אליו
        self.tabs.tabs.append(tab)
        self.tabs.selected_index = len(self.tabs.tabs) - 1
        self.login_manager.page.update()
        
        
        def on_tab_change(e):
            update_event_participants()
            self.login_manager.page.update()



    # פונקציות ניהול קבוצות
    def add_group(self, e):
        if not self.group_name_field.value:
            self.show_message("אנא הזן שם קבוצה!", ft.colors.RED)
            return

        new_group = Group(
            self.group_name_field.value,
            self.group_description_field.value
        )
        self.groups.append(new_group)
        self.groups_list_view.controls.append(self.create_group_card(new_group))
        
        self.update_group_options()
        self.clear_group_fields()
        
        self.show_message("הקבוצה נוספה בהצלחה", ft.colors.GREEN)
        self.login_manager.page.update()
        self.save_data()

    def enter_group(self, group):
        dlg = ft.AlertDialog(
            title=ft.Text(f"קבוצה: {group.name}"),
            content=ft.Column(
                [
                    ft.Text("חברי הקבוצה:"),
                    ft.Column([
                        ft.Checkbox(
                            label=contact.name,
                            value=contact in group.members,
                            on_change=lambda e, c=contact: self.toggle_group_member(e, group, c)
                        )
                        for contact in self.contacts
                    ], scroll=ft.ScrollMode.AUTO, height=200)
                ],
                tight=True
            )
        )
        self.login_manager.page.dialog = dlg
        dlg.open = True
        self.login_manager.page.update()

    # פונקציות עזר
    def clear_contact_fields(self):
        self.name_field.value = ""
        self.phone_field.value = ""
        self.email_field.value = ""
        self.group_field.value = None

    def clear_event_fields(self):
        self.event_title.value = ""
        self.event_date.value = ""
        self.event_time.value = ""
        self.event_location.value = ""

    def clear_group_fields(self):
        self.group_name_field.value = ""
        self.group_description_field.value = ""

    def update_views(self):
        self.contacts_list_view.controls = [self.create_contact_card(contact) for contact in self.contacts]
        self.events_grid_view.controls = [self.create_event_card(event) for event in self.events]
        self.groups_list_view.controls = [self.create_group_card(group) for group in self.groups]
        self.update_group_options()
        self.login_manager.page.update()

    def show_message(self, message, color):
        self.login_manager.page.snack_bar = ft.SnackBar(
            content=ft.Text(message),
            bgcolor=color
        )
        self.login_manager.page.snack_bar.open = True
        self.login_manager.page.update()

    def save_data(self):
        try:
            data = {
                "contacts": [
                    {
                        "name": contact.name,
                        "phone": contact.phone,
                        "email": contact.email,
                        "group": contact.group
                    }
                    for contact in self.contacts
                ],
                "events": [
                    {
                        "title": event.title,
                        "date": event.date,
                        "time": event.time,
                        "location": event.location,
                        "participants": [p.name for p in event.participants if p],
                        "pending_participants": [p.name for p in event.pending_participants if p],
                        "pending_notes": {p.name: note for p, note in event.pending_notes.items() if p}
                    }
                    for event in self.events
                ],
                "groups": [
                    {
                        "name": group.name,
                        "description": group.description,
                        "members": [member.name for member in group.members if member]
                    }
                    for group in self.groups
                ]
            }
            
            # שמירת הנתונים
            if self.login_manager.save_organization_data(data):
                print("הנתונים נשמרו בהצלחה")
            else:
                print("שגיאה בשמירת הנתונים")
                
        except Exception as e:
            print(f"שגיאה בשמירת הנתונים: {str(e)}")

        
    def load_data(self):
        data = self.login_manager.load_organization_data()
        if data:
            self.contacts = []
            self.events = []
            self.groups = []

            # טעינת אנשי קשר
            for contact_data in data.get("contacts", []):
                contact = Contact(**contact_data)
                self.contacts.append(contact)

            # טעינת אירועים
            for event_data in data.get("events", []):
                event = Event(
                    event_data["title"],
                    event_data["date"],
                    event_data["time"],
                    event_data["location"]
                )
                # טעינת משתתפים מאושרים
                for participant_name in event_data.get("participants", []):
                    participant = next((c for c in self.contacts if c.name == participant_name), None)
                    if participant:
                        event.participants.append(participant)
                
                # טעינת משתתפים ממתינים
                for pending_name in event_data.get("pending_participants", []):
                    pending = next((c for c in self.contacts if c.name == pending_name), None)
                    if pending:
                        event.pending_participants.append(pending)
                
                self.events.append(event)

            # טעינת קבוצות
            for group_data in data.get("groups", []):
                group = Group(group_data["name"], group_data.get("description", ""))
                for member_name in group_data.get("members", []):
                    member = next((c for c in self.contacts if c.name == member_name), None)
                    if member:
                        group.members.append(member)
                self.groups.append(group)

            self.update_views()
            return True
        return False

    def create_event_tab(self, event, update_callback, participants_grid):
        """יוצר כרטיסייה חדשה לניהול אירוע"""
        
        # יצירת רשימת אנשי קשר לבחירה
        contacts_list = ft.ListView(
            expand=True,
            spacing=10,
            padding=20,
            height=200
        )

        def add_participant(contact):
            if contact not in event.participants:
                event.participants.append(contact)
                update_callback()
                self.save_data()
                self.show_message(f"{contact.name} נוסף לאירוע", ft.colors.GREEN)

        # עדכון רשימת אנשי הקשר הזמינים
        for contact in self.contacts:
            if contact not in event.participants:
                contacts_list.controls.append(
                    ft.ListTile(
                        leading=ft.Icon(ft.Icons.PERSON),
                        title=ft.Text(contact.name),
                        subtitle=ft.Text(contact.phone),
                        trailing=ft.IconButton(
                            icon=ft.Icons.ADD,
                            tooltip="הוסף לאירוע",
                            on_click=lambda _, c=contact: add_participant(c)
                        )
                    )
                )

        return ft.Tab(
            text=f"אירוע: {event.title}",
            icon=ft.Icons.EVENT_NOTE,
            content=ft.Column([
                ft.Container(
                    content=ft.Column([
                        ft.Text(
                            f"פרטי האירוע: {event.title}",
                            size=24,
                            weight=ft.FontWeight.BOLD
                        ),
                        ft.Text(f"תאריך: {event.date}"),
                        ft.Text(f"שעה: {event.time}"),
                        ft.Text(f"מיקום: {event.location}"),
                        ft.Divider(),
                        ft.Text("משתתפים:", size=20, weight=ft.FontWeight.BOLD),
                        participants_grid,
                        ft.Divider(),
                        ft.Text("הוסף משתתפים:", size=20, weight=ft.FontWeight.BOLD),
                        contacts_list
                    ]),
                    padding=20
                )
            ])
        )
# פונקציית main
def main(page: ft.Page):
    app = AppManager()
    app.initialize_app(page)

ft.app(target=main)
