import json
import os
import sys
import re
import logging
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
import time
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QListWidget, QMessageBox,
    QDialog, QFormLayout, QTabWidget, QMenu, QSystemTrayIcon, QGroupBox, QCheckBox, QFileDialog
)
from PyQt6.QtCore import Qt, QSettings
from PyQt6.QtGui import QAction, QIcon, QClipboard
from PyQt6.QtCore import QThread, pyqtSignal
from cryptography.fernet import Fernet
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.remote.webelement import WebElement

# הגדרת Logger
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='login_manager.log'
)

@dataclass


            
class FieldScore:
    """מחלקה לחישוב וניהול ציוני התאמה של שדות"""
    element: WebElement
    base_score: float = 0
    context_score: float = 0
    position_score: float = 0
    relation_score: float = 0
    
    @property
    def total_score(self) -> float:
        return self.base_score + self.context_score + self.position_score + self.relation_score

class SmartLoginFieldsFinder:
    """מחלקה חכמה משופרת לזיהוי שדות התחברות"""
    
    # מילות מפתח מורחבות לזיהוי שדות משתמש/אימייל
    USERNAME_KEYWORDS = {
        'he': [
            'דואר אלקטרוני', 'אימייל', 'דוא"ל', 'שם משתמש', 'מזהה',
            'טלפון', 'נייד', 'ת.ז', 'תעודת זהות', 'שם פרטי',
            'מספר לקוח', 'מספר חבר', 'שם החשבון'
        ],
        'en': [
            'email', 'mail', 'username', 'user', 'login', 'phone',
            'mobile', 'account', 'id', 'identity', 'member',
            'customer', 'client', 'access', 'identifier'
        ],
        'patterns': [
            r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}',  # תבנית אימייל
            r'^\d{10}$',  # תבנית טלפון
            r'^\d{9}$',   # תבנית ת.ז
            r'^[a-zA-Z0-9_-]{3,20}$'  # תבנית שם משתמש כללית
        ]
    }
    
    # מילות מפתח מורחבות לזיהוי שדות סיסמה
    PASSWORD_KEYWORDS = {
        'he': [
            'סיסמה', 'סיסמא', 'קוד גישה', 'קוד סודי', 'קוד אימות',
            'מפתח גישה', 'קוד אבטחה', 'קוד משתמש'
        ],
        'en': [
            'password', 'pass', 'pwd', 'secret', 'security code',
            'access code', 'pin', 'passcode', 'auth code',
            'verification code', 'secure key'
        ],
        'patterns': [
            r'^(?=.*[A-Za-z])(?=.*\d)[A-Za-z\d]{8,}$',  # סיסמה חזקה
            r'^\d{4,8}$'  # PIN או קוד גישה מספרי
        ]
    }

    def __init__(self, driver):
        """אתחול המאתר החכם"""
        self.driver = driver
        self.logger = logging.getLogger(__name__)
        self.wait = WebDriverWait(self.driver, 10)
    def find_login_fields(self) -> Dict[str, Tuple[str, WebElement]]:
        """מוצא את שדות ההתחברות בדף בצורה חכמה ומתקדמת"""
        try:
            # המתנה לטעינת הדף
            self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            
            # 1. איסוף כל השדות הפוטנציאליים
            input_elements = self._collect_potential_fields()
            
            # 2. ניתוח וניקוד ראשוני של השדות
            username_candidates = []
            password_candidates = []
            
            for element in input_elements:
                try:
                    if not element.is_displayed() or not element.is_enabled():
                        continue
                        
                    username_score = FieldScore(element)
                    password_score = FieldScore(element)
                    
                    # ניתוח מקיף של כל שדה
                    self._analyze_basic_attributes(element, username_score, password_score)
                    self._analyze_surrounding_context(element, username_score, password_score)
                    self._analyze_field_position(element, username_score, password_score)
                    self._analyze_field_relationships(element, username_score, password_score)
                    
                    # הוספת המועמדים המתאימים לרשימות
                    if username_score.total_score > 3:  # סף מינימלי
                        username_candidates.append(username_score)
                    if password_score.total_score > 3:  # סף מינימלי
                        password_candidates.append(password_score)
                        
                except Exception as e:
                    self.logger.debug(f"שגיאה בניתוח שדה: {str(e)}")
                    continue
            
            # 3. בחירת השדות הטובים ביותר
            best_username = self._select_best_candidate(username_candidates)
            best_password = self._select_best_candidate(password_candidates)
            
            # 4. וידוא תקינות השילוב
            if best_username and best_password:
                if self._validate_field_combination(best_username.element, best_password.element):
                    return {
                        'username': self._get_smart_selectors(best_username.element),
                        'password': self._get_smart_selectors(best_password.element)
                    }
            
            return {}
            
        except Exception as e:
            self.logger.error(f"שגיאה בזיהוי שדות ההתחברות: {str(e)}")
            raise

    def _collect_potential_fields(self) -> List[WebElement]:
        """אוסף את כל שדות הקלט הפוטנציאליים מהדף"""
        potential_fields = []
        
        try:
            # חיפוש בתוך טפסים
            forms = self.driver.find_elements(By.TAG_NAME, 'form')
            for form in forms:
                form_fields = form.find_elements(By.TAG_NAME, 'input')
                potential_fields.extend(form_fields)
            
            # חיפוש שדות נוספים מחוץ לטפסים
            all_inputs = self.driver.find_elements(By.TAG_NAME, 'input')
            for input_el in all_inputs:
                if input_el not in potential_fields:
                    input_type = input_el.get_attribute('type')
                    if input_type in ['text', 'email', 'tel', 'password', 'number']:
                        potential_fields.append(input_el)
            
            # חיפוש שדות contenteditable
            editable_elements = self.driver.find_elements(
                By.CSS_SELECTOR, 
                '[contenteditable="true"]'
            )
            potential_fields.extend(editable_elements)
            
        except Exception as e:
            self.logger.error(f"שגיאה באיסוף שדות: {str(e)}")
        
        return list(set(potential_fields))  # הסרת כפילויות

    def _analyze_basic_attributes(self, element: WebElement, 
                                username_score: FieldScore, 
                                password_score: FieldScore):
        """מנתח את המאפיינים הבסיסיים של השדה"""
        try:
            # בדיקת type
            input_type = element.get_attribute('type')
            if input_type == 'password':
                password_score.base_score += 5
            elif input_type in ['email', 'tel']:
                username_score.base_score += 3
            
            # בדיקת מאפיינים נוספים
            attributes = ['name', 'id', 'class', 'aria-label', 'placeholder', 
                        'data-testid', 'role']
            
            for attr in attributes:
                value = element.get_attribute(attr)
                if not value:
                    continue
                
                value_lower = value.lower()
                
                # בדיקה מול מילות מפתח בעברית ואנגלית
                for lang in ['he', 'en']:
                    for keyword in self.USERNAME_KEYWORDS[lang]:
                        if keyword.lower() in value_lower:
                            username_score.base_score += self._calculate_keyword_score(
                                keyword, value_lower
                            )
                    
                    for keyword in self.PASSWORD_KEYWORDS[lang]:
                        if keyword.lower() in value_lower:
                            password_score.base_score += self._calculate_keyword_score(
                                keyword, value_lower
                            )
            
            # בדיקת תבניות
            for pattern in self.USERNAME_KEYWORDS['patterns']:
                if re.match(pattern, value_lower):
                    username_score.base_score += 2
            
            for pattern in self.PASSWORD_KEYWORDS['patterns']:
                if re.match(pattern, value_lower):
                    password_score.base_score += 2
            
            # בדיקת autocomplete
            autocomplete = element.get_attribute('autocomplete')
            if autocomplete:
                if any(x in autocomplete.lower() for x in ['username', 'email']):
                    username_score.base_score += 2
                elif 'current-password' in autocomplete.lower():
                    password_score.base_score += 2
            
            # בדיקת maxlength
            maxlength = element.get_attribute('maxlength')
            if maxlength:
                try:
                    maxlen = int(maxlength)
                    if 20 <= maxlen <= 128:  # טווח טיפוסי לסיסמאות
                        password_score.base_score += 1
                    elif 3 <= maxlen <= 50:   # טווח טיפוסי לשמות משתמש
                        username_score.base_score += 1
                except ValueError:
                    pass
            
        except Exception as e:
            self.logger.debug(f"שגיאה בניתוח מאפיינים בסיסיים: {str(e)}")
    def _analyze_surrounding_context(self, element: WebElement,
                                   username_score: FieldScore,
                                   password_score: FieldScore):
        """מנתח את ההקשר סביב השדה וטקסטים קשורים"""
        try:
            # בדיקת תוויות (labels) מקושרות
            element_id = element.get_attribute('id')
            if element_id:
                labels = self.driver.find_elements(
                    By.CSS_SELECTOR, 
                    f'label[for="{element_id}"]'
                )
                
                for label in labels:
                    label_text = label.text.lower()
                    self._analyze_text_content(
                        label_text, 
                        username_score,
                        password_score,
                        weight=3  # משקל גבוה לתוויות מקושרות
                    )

            # בדיקת טקסט בסביבה הקרובה
            surrounding_elements = self._get_surrounding_elements(element, max_distance=150)
            for elem in surrounding_elements:
                if elem != element:
                    elem_text = elem.text.lower()
                    self._analyze_text_content(
                        elem_text,
                        username_score,
                        password_score,
                        weight=1  # משקל נמוך יותר לטקסט סביבתי
                    )

            # בדיקת aria-describedby
            described_by = element.get_attribute('aria-describedby')
            if described_by:
                desc_elements = self.driver.find_elements(
                    By.ID, 
                    described_by
                )
                for desc in desc_elements:
                    desc_text = desc.text.lower()
                    self._analyze_text_content(
                        desc_text,
                        username_score,
                        password_score,
                        weight=2
                    )

        except Exception as e:
            self.logger.debug(f"שגיאה בניתוח הקשר: {str(e)}")

    def _analyze_field_position(self, element: WebElement,
                              username_score: FieldScore,
                              password_score: FieldScore):
        """מנתח את מיקום השדה בדף ויחסיו עם שדות אחרים"""
        try:
            # בדיקת מיקום אנכי בדף
            viewport_height = self.driver.execute_script(
                'return window.innerHeight'
            )
            element_position = element.location['y']
            
            # שדות בחלק העליון של הדף מקבלים ניקוד גבוה יותר
            if element_position < viewport_height / 3:
                username_score.position_score += 2
                password_score.position_score += 2
            elif element_position < viewport_height / 2:
                username_score.position_score += 1
                password_score.position_score += 1

            # בדיקת סדר השדות
            form = self._find_parent_form(element)
            if form:
                inputs = form.find_elements(By.TAG_NAME, 'input')
                try:
                    current_index = inputs.index(element)
                    
                    # בדיקת השדה הקודם
                    if current_index > 0:
                        prev_input = inputs[current_index - 1]
                        if prev_input.get_attribute('type') != 'password':
                            username_score.position_score += 1
                    
                    # בדיקת השדה הבא
                    if current_index < len(inputs) - 1:
                        next_input = inputs[current_index + 1]
                        if next_input.get_attribute('type') == 'password':
                            username_score.position_score += 2
                        elif element.get_attribute('type') == 'password':
                            password_score.position_score += 2
                
                except ValueError:
                    pass

            # בדיקת נראות
            if element.is_displayed():
                username_score.position_score += 1
                password_score.position_score += 1

        except Exception as e:
            self.logger.debug(f"שגיאה בניתוח מיקום: {str(e)}")

    def _analyze_field_relationships(self, element: WebElement,
                                   username_score: FieldScore,
                                   password_score: FieldScore):
        """מנתח את הקשרים בין השדות ומאפייני הטופס"""
        try:
            form = self._find_parent_form(element)
            if form:
                # בדיקת נוכחות כפתור שליחה
                submit_buttons = form.find_elements(
                    By.XPATH,
                    './/button[@type="submit"] | .//input[@type="submit"]'
                )
                if submit_buttons:
                    username_score.relation_score += 1
                    password_score.relation_score += 1

                # בדיקת שדות נוספים בטופס
                inputs = form.find_elements(By.TAG_NAME, 'input')
                has_text_input = False
                has_email_input = False
                has_password = False

                for input_el in inputs:
                    input_type = input_el.get_attribute('type')
                    if input_type == 'text':
                        has_text_input = True
                    elif input_type == 'email':
                        has_email_input = True
                    elif input_type == 'password':
                        has_password = True

                # ניקוד על בסיס שילובי השדות
                if has_password and (has_text_input or has_email_input):
                    username_score.relation_score += 2
                    password_score.relation_score += 2

                # בדיקת מאפייני הטופס
                form_method = form.get_attribute('method')
                if form_method and form_method.lower() == 'post':
                    username_score.relation_score += 1
                    password_score.relation_score += 1

                # בדיקת action של הטופס
                form_action = form.get_attribute('action')
                if form_action:
                    login_keywords = ['login', 'signin', 'auth', 'התחבר']
                    if any(keyword in form_action.lower() for keyword in login_keywords):
                        username_score.relation_score += 1
                        password_score.relation_score += 1

        except Exception as e:
            self.logger.debug(f"שגיאה בניתוח קשרים: {str(e)}")
    def _get_surrounding_elements(self, element: WebElement, 
                                max_distance: int = 150) -> List[WebElement]:
        """מוצא אלמנטים בסביבת השדה הנתון"""
        surrounding = []
        try:
            element_rect = element.rect
            element_center = {
                'x': element_rect['x'] + element_rect['width'] / 2,
                'y': element_rect['y'] + element_rect['height'] / 2
            }

            # חיפוש אלמנטים בסביבה
            potential_elements = self.driver.find_elements(
                By.XPATH,
                './/*[text()][not(self::script)][not(self::style)]'
            )

            for elem in potential_elements:
                try:
                    if not elem.is_displayed():
                        continue

                    elem_rect = elem.rect
                    elem_center = {
                        'x': elem_rect['x'] + elem_rect['width'] / 2,
                        'y': elem_rect['y'] + elem_rect['height'] / 2
                    }

                    # חישוב מרחק אוקלידי
                    distance = ((elem_center['x'] - element_center['x']) ** 2 + 
                              (elem_center['y'] - element_center['y']) ** 2) ** 0.5

                    if distance <= max_distance:
                        surrounding.append(elem)

                except Exception:
                    continue

        except Exception as e:
            self.logger.debug(f"שגיאה במציאת אלמנטים סביבתיים: {str(e)}")

        return surrounding

    def _analyze_text_content(self, text: str, 
                            username_score: FieldScore,
                            password_score: FieldScore,
                            weight: float = 1.0):
        """מנתח תוכן טקסטואלי ומעדכן את הניקוד בהתאם"""
        if not text:
            return

        text = text.lower()
        
        # בדיקת מילות מפתח בשתי השפות
        for lang in ['he', 'en']:
            # בדיקת מילות מפתח לשם משתמש
            for keyword in self.USERNAME_KEYWORDS[lang]:
                if keyword.lower() in text:
                    username_score.context_score += weight * 2
                    
            # בדיקת מילות מפתח לסיסמה
            for keyword in self.PASSWORD_KEYWORDS[lang]:
                if keyword.lower() in text:
                    password_score.context_score += weight * 2

        # בדיקת תבניות
        for pattern in self.USERNAME_KEYWORDS['patterns']:
            if re.search(pattern, text):
                username_score.context_score += weight
        
        for pattern in self.PASSWORD_KEYWORDS['patterns']:
            if re.search(pattern, text):
                password_score.context_score += weight

    def _get_smart_selectors(self, element: WebElement) -> Dict[str, str]:
        """יוצר מזהים חכמים לאלמנט"""
        selectors = {}
        
        try:
            # איסוף מזהים בסיסיים
            for attr in ['id', 'name', 'class', 'type']:
                value = element.get_attribute(attr)
                if value:
                    selectors[attr] = value

            # יצירת CSS Selector
            css_selector = self._create_css_selector(element)
            if css_selector:
                selectors['css'] = css_selector

            # יצירת XPath יחסי
            xpath = self._create_relative_xpath(element)
            if xpath:
                selectors['xpath'] = xpath

            # הוספת מזהים נוספים אם קיימים
            for attr in ['data-testid', 'aria-label']:
                value = element.get_attribute(attr)
                if value:
                    selectors[attr] = value

        except Exception as e:
            self.logger.debug(f"שגיאה ביצירת מזהים: {str(e)}")

        return selectors

    def _create_css_selector(self, element: WebElement) -> Optional[str]:
        """יוצר CSS Selector ייחודי לאלמנט"""
        try:
            # ניסיון ליצור סלקטור מינימלי
            for attr in ['id', 'name', 'data-testid']:
                value = element.get_attribute(attr)
                if value:
                    return f'[{attr}="{value}"]'

            # יצירת סלקטור מורכב יותר
            selectors = []
            current = element

            for _ in range(3):  # הגבלת עומק ל-3 רמות
                tag_name = current.tag_name
                
                # הוספת מחלקות
                classes = current.get_attribute('class')
                if classes:
                    class_names = classes.split()
                    class_selector = '.'.join(class_names)
                    selectors.insert(0, f"{tag_name}.{class_selector}")
                else:
                    selectors.insert(0, tag_name)

                # מעבר להורה
                parent = current.find_element(By.XPATH, '..')
                if parent == current:
                    break
                current = parent

            return ' > '.join(selectors)

        except Exception:
            return None

    def _select_best_candidate(self, candidates: List[FieldScore]) -> Optional[FieldScore]:
        """בחירת המועמד הטוב ביותר מתוך רשימת המועמדים"""
        if not candidates:
            return None
        
        # מיון המועמדים לפי הציון הכולל שלהם
        sorted_candidates = sorted(
            candidates,
            key=lambda x: x.total_score,
            reverse=True
        )
        
        return sorted_candidates[0]

    def _validate_field_combination(self, username_field: WebElement, 
                                  password_field: WebElement) -> bool:
        """וידוא שהשילוב של שדות ההתחברות הגיוני"""
        try:
            # בדיקה שהשדות נמצאים באותו טופס
            username_form = self._find_parent_form(username_field)
            password_form = self._find_parent_form(password_field)
            
            if username_form and password_form and username_form == password_form:
                return True
            
            # אם השדות לא באותו טופס, בדיקת מרחק מקסימלי ביניהם
            username_rect = username_field.rect
            password_rect = password_field.rect
            
            distance = ((username_rect['x'] - password_rect['x']) ** 2 + 
                       (username_rect['y'] - password_rect['y']) ** 2) ** 0.5
            
            return distance <= 300  # מרחק מקסימלי סביר בפיקסלים
            
        except Exception as e:
            self.logger.debug(f"שגיאה בוידוא שילוב השדות: {str(e)}")
            return False

    def _find_parent_form(self, element: WebElement) -> Optional[WebElement]:
        """מציאת טופס ההורה של אלמנט"""
        try:
            current = element
            for _ in range(5):  # הגבלת עומק החיפוש
                if current.tag_name == 'form':
                    return current
                
                parent = current.find_element(By.XPATH, '..')
                if parent == current:  # הגענו לשורש
                    break
                current = parent
                
        except Exception as e:
            self.logger.debug(f"שגיאה במציאת טופס הורה: {str(e)}")
        
        return None

    def _calculate_keyword_score(self, keyword: str, value: str) -> float:
        """חישוב ניקוד התאמה למילת מפתח"""
        score = 0.0
        
        # התאמה מדויקת
        if keyword.lower() == value.lower():
            score += 3.0
        
        # התאמה חלקית
        elif keyword.lower() in value.lower():
            # ניקוד גבוה יותר אם מילת המפתח בהתחלה
            if value.lower().startswith(keyword.lower()):
                score += 2.0
            else:
                score += 1.0
            
            # ניקוד נוסף בהתאם לאורך היחסי
            ratio = len(keyword) / len(value)
            score += ratio * 0.5
        
        return score        
class AdvancedLoginDialog(QDialog):
    """חלון דו-שיח להוספת ועריכת אתרים"""
    
    def __init__(self, parent=None, site_data=None):
        super().__init__(parent)
        self.site_data = site_data or {}
        self.setup_ui()
        
        # מילוי נתונים אם יש עריכה
        if self.site_data:
            self.fill_existing_data()

    def setup_ui(self):
        """הגדרת ממשק המשתמש של החלון"""
        self.setWindowTitle("הוספת/עריכת אתר")
        self.setMinimumWidth(400)
        
        layout = QVBoxLayout(self)
        
        # טופס הזנת פרטים
        form_layout = QFormLayout()
        
        # שדות הזנה
        self.fields = {}
        field_configs = {
            'site_name': {
                'label': 'שם האתר:',
                'placeholder': 'הזן שם ייחודי לאתר...',
                'type': 'text'
            },
            'url': {
                'label': 'כתובת האתר:',
                'placeholder': 'https://...',
                'type': 'text'
            },
            'username': {
                'label': 'שם משתמש/אימייל:',
                'placeholder': 'הזן את שם המשתמש...',
                'type': 'text'
            },
            'password': {
                'label': 'סיסמה:',
                'placeholder': 'הזן את הסיסמה...',
                'type': 'password'
            }
        }
        
        # יצירת שדות הקלט
        for field_id, config in field_configs.items():
            container = QWidget()
            field_layout = QHBoxLayout(container)
            field_layout.setContentsMargins(0, 0, 0, 0)
            
            line_edit = QLineEdit()
            line_edit.setPlaceholderText(config['placeholder'])
            if config['type'] == 'password':
                line_edit.setEchoMode(QLineEdit.EchoMode.Password)
                
                # כפתור הצג/הסתר סיסמה
                toggle_btn = QPushButton("👁")
                toggle_btn.setFixedWidth(30)
                toggle_btn.setToolTip("הצג/הסתר סיסמה")
                toggle_btn.clicked.connect(
                    lambda checked, le=line_edit: self.toggle_password_visibility(le)
                )
                field_layout.addWidget(toggle_btn)
            
            field_layout.addWidget(line_edit)
            self.fields[field_id] = line_edit
            
            form_layout.addRow(config['label'], container)
        
        layout.addLayout(form_layout)
        
        # כפתורי פעולה
        buttons_layout = QHBoxLayout()
        
        save_btn = QPushButton("שמור")
        save_btn.clicked.connect(self.accept)
        
        cancel_btn = QPushButton("ביטול")
        cancel_btn.clicked.connect(self.reject)
        
        buttons_layout.addWidget(save_btn)
        buttons_layout.addWidget(cancel_btn)
        
        layout.addLayout(buttons_layout)

    def toggle_password_visibility(self, password_field):
        """החלפת מצב תצוגת הסיסמה"""
        if password_field.echoMode() == QLineEdit.EchoMode.Password:
            password_field.setEchoMode(QLineEdit.EchoMode.Normal)
        else:
            password_field.setEchoMode(QLineEdit.EchoMode.Password)

    def fill_existing_data(self):
        """מילוי נתונים קיימים בעת עריכה"""
        for field_id, value in self.site_data.items():
            if field_id in self.fields:
                self.fields[field_id].setText(value)

    def get_data(self):
        """קבלת הנתונים שהוזנו"""
        return {
            'site_name': self.fields['site_name'].text(),
            'url': self.fields['url'].text(),
            'username': self.fields['username'].text(),
            'password': self.fields['password'].text()
        }        
class AdvancedLoginManager(QMainWindow):
    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self.login_worker = None
        # הגדרת המשתנים הבסיסיים
        self.sites_file = 'sites.json'
        self.key_file = 'key.key'
        self.settings = QSettings('AdvancedLoginManager', 'Settings')
        self.sites = {}
        self.cipher = None
        self.sites_list = None
        self.status_bar = None
        self.search_box = None
        self.tab_widget = None
        self.tray_icon = None
        self.edit_btn = None  # חדש: שמירת התייחסות לכפתור עריכה
        self.system_password = self.settings.value('SystemPassword', '')
        self.password_protected = self.settings.value('PasswordProtected', False, type=bool)

        # אתחול בסדר הנכון
        self.init_encryption()
        self.setup_ui()
        self.load_sites()
        self.update_sites_list()
        self.setup_tray()
        self.update_edit_button_state()  # חדש: עדכון מצב כפתור העריכה

        
    def set_system_password(self):
        """הגדרת סיסמת מערכת"""
        dialog = QDialog(self)
        dialog.setWindowTitle("הגדרת סיסמת מערכת")
        layout = QVBoxLayout(dialog)

        form_layout = QFormLayout()
        password_field = QLineEdit()
        password_field.setEchoMode(QLineEdit.EchoMode.Password)
        confirm_field = QLineEdit()
        confirm_field.setEchoMode(QLineEdit.EchoMode.Password)
        
        form_layout.addRow("סיסמה חדשה:", password_field)
        form_layout.addRow("אימות סיסמה:", confirm_field)
        
        buttons = QHBoxLayout()
        save_btn = QPushButton("שמור")
        cancel_btn = QPushButton("ביטול")
        
        buttons.addWidget(save_btn)
        buttons.addWidget(cancel_btn)
        
        layout.addLayout(form_layout)
        layout.addLayout(buttons)
        
        save_btn.clicked.connect(dialog.accept)
        cancel_btn.clicked.connect(dialog.reject)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            if password_field.text() == confirm_field.text():
                if password_field.text():
                    self.system_password = self.encrypt(password_field.text())
                    self.settings.setValue('SystemPassword', self.system_password)
                    self.password_protected = True
                    self.settings.setValue('PasswordProtected', True)
                    QMessageBox.information(self, "הצלחה", "סיסמת המערכת הוגדרה בהצלחה")
                else:
                    self.system_password = ''
                    self.settings.setValue('SystemPassword', '')
                    self.password_protected = False
                    self.settings.setValue('PasswordProtected', False)
                    QMessageBox.information(self, "הצלחה", "הגנת הסיסמה בוטלה")
                self.update_edit_button_state()
            else:
                QMessageBox.warning(self, "שגיאה", "הסיסמאות אינן תואמות")

    def toggle_password_protection(self, state):
        """הפעלת/כיבוי הגנת סיסמה"""
        if state and not self.system_password:
            reply = QMessageBox.question(
                self,
                "הגנת סיסמה",
                "להפעלת הגנת סיסמה יש להגדיר סיסמת מערכת. האם להגדיר כעת?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                self.set_system_password()
            else:
                sender = self.sender()
                if sender:
                    sender.setChecked(False)
                return
                
        self.password_protected = bool(state)
        self.settings.setValue('PasswordProtected', bool(state))
        self.update_edit_button_state()

    def verify_system_password(self):
        """אימות סיסמת מערכת"""
        if not self.password_protected or not self.system_password:
            return True
            
        dialog = QDialog(self)
        dialog.setWindowTitle("אימות סיסמת מערכת")
        layout = QVBoxLayout(dialog)
        
        password_field = QLineEdit()
        password_field.setEchoMode(QLineEdit.EchoMode.Password)
        password_field.setPlaceholderText("הזן סיסמת מערכת...")
        
        buttons = QHBoxLayout()
        ok_btn = QPushButton("אישור")
        cancel_btn = QPushButton("ביטול")
        
        buttons.addWidget(ok_btn)
        buttons.addWidget(cancel_btn)
        
        layout.addWidget(password_field)
        layout.addLayout(buttons)
        
        ok_btn.clicked.connect(dialog.accept)
        cancel_btn.clicked.connect(dialog.reject)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            entered_password = password_field.text()
            stored_password = self.decrypt(self.system_password)
            return entered_password == stored_password
            
        return False

    def update_edit_button_state(self):
        """עדכון מצב כפתור העריכה בהתאם למצב הגנת הסיסמה"""
        if hasattr(self, 'edit_btn') and self.edit_btn:
            self.edit_btn.setEnabled(not self.password_protected or self.verify_system_password())        
        
    def encrypt(self, data: str) -> str:
        """הצפנת מחרוזת"""
        try:
            if not data:
                return ""
            return self.cipher.encrypt(data.encode()).decode()
        except Exception as e:
            self.logger.error(f"שגיאה בהצפנה: {str(e)}")
            return ""

    def decrypt(self, encrypted_data: str) -> str:
        """פענוח מחרוזת מוצפנת"""
        try:
            if not encrypted_data:
                return ""
            return self.cipher.decrypt(encrypted_data.encode()).decode()
        except Exception as e:
            self.logger.error(f"שגיאה בפענוח: {str(e)}")
            return ""      

    def init_encryption(self):
        """אתחול מערכת ההצפנה"""
        try:
            if os.path.exists(self.key_file):
                with open(self.key_file, 'rb') as f:
                    self.key = f.read()
            else:
                self.key = Fernet.generate_key()
                with open(self.key_file, 'wb') as f:
                    f.write(self.key)
            
            self.cipher = Fernet(self.key)
        except Exception as e:
            QMessageBox.critical(self, "שגיאת אבטחה", f"שגיאה באתחול מערכת ההצפנה: {str(e)}")
            sys.exit(1)

    def load_sites(self):
        """טעינת האתרים השמורים מהקובץ"""
        if os.path.exists(self.sites_file):
            try:
                with open(self.sites_file, 'r', encoding='utf-8') as f:
                    encrypted_sites = json.load(f)
                    for site_name, site_data in encrypted_sites.items():
                        self.sites[site_name] = {
                            'site_name': site_name,
                            'url': site_data['url'],
                            'username_field': site_data.get('username_field', ''),
                            'password_field': site_data.get('password_field', ''),
                            'username': self.decrypt(site_data['username']),
                            'password': self.decrypt(site_data['password'])
                        }
            except Exception as e:
                QMessageBox.critical(self, "שגיאה", f"שגיאה בטעינת קובץ האתרים: {str(e)}")
                self.sites = {}

    def save_sites(self):
        """שמירת האתרים לקובץ"""
        try:
            encrypted_sites = {}
            for site_name, site_data in self.sites.items():
                encrypted_sites[site_name] = {
                    'url': site_data['url'],
                    'username_field': site_data.get('username_field', ''),
                    'password_field': site_data.get('password_field', ''),
                    'username': self.encrypt(site_data['username']),
                    'password': self.encrypt(site_data['password'])
                }
            
            with open(self.sites_file, 'w', encoding='utf-8') as f:
                json.dump(encrypted_sites, f, indent=4, ensure_ascii=False)
            self.status_bar.showMessage("הנתונים נשמרו בהצלחה", 3000)
        except Exception as e:
            QMessageBox.critical(self, "שגיאה", f"שגיאה בשמירת הנתונים: {str(e)}")

    def setup_ui(self):
        """הגדרת ממשק המשתמש"""
        self.setWindowTitle("מנהל התחברויות מתקדם")
        self.setMinimumSize(900, 600)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # סרגל כלים
        toolbar = self.create_toolbar()
        main_layout.addWidget(toolbar)
        
        # תצוגת טאבים
        self.tab_widget = QTabWidget()
        sites_tab = self.create_sites_tab()
        settings_tab = self.create_settings_tab()
        
        self.tab_widget.addTab(sites_tab, "אתרים שמורים")
        self.tab_widget.addTab(settings_tab, "הגדרות")
        
        main_layout.addWidget(self.tab_widget)
        
        # סרגל סטטוס
        self.status_bar = self.statusBar()
        self.update_status_bar()

    def create_toolbar(self):
        """יצירת סרגל כלים"""
        toolbar = QWidget()
        toolbar_layout = QHBoxLayout(toolbar)
        toolbar_layout.setContentsMargins(5, 5, 5, 5)
        
        add_btn = QPushButton("הוסף אתר חדש")
        add_btn.setIcon(QIcon.fromTheme("list-add"))
        add_btn.clicked.connect(self.add_site)
        
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("חיפוש אתרים...")
        self.search_box.textChanged.connect(self.filter_sites)
        
        refresh_btn = QPushButton("רענן")
        refresh_btn.setIcon(QIcon.fromTheme("view-refresh"))
        refresh_btn.clicked.connect(self.update_sites_list)
        
        toolbar_layout.addWidget(add_btn)
        toolbar_layout.addWidget(self.search_box)
        toolbar_layout.addWidget(refresh_btn)
        toolbar_layout.addStretch()
        
        return toolbar

    def create_sites_tab(self):
        """יצירת טאב רשימת האתרים"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        self.sites_list = QListWidget()
        self.sites_list.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
        self.sites_list.itemDoubleClicked.connect(self.login_to_site)
        self.sites_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.sites_list.customContextMenuRequested.connect(self.show_site_context_menu)
        
        buttons_layout = QHBoxLayout()
        
        self.edit_btn = QPushButton("ערוך")  # שמירת התייחסות לכפתור
        self.edit_btn.clicked.connect(self.edit_site)
        self.edit_btn.setEnabled(not self.password_protected)  # כפתור מושבת כברירת מחדל אם יש הגנת סיסמה
        
        delete_btn = QPushButton("מחק")
        delete_btn.clicked.connect(self.delete_site)
        
        login_btn = QPushButton("התחבר")
        login_btn.clicked.connect(self.login_to_site)
        
        for btn in [self.edit_btn, delete_btn, login_btn]:
            buttons_layout.addWidget(btn)
        
        layout.addWidget(self.sites_list)
        layout.addLayout(buttons_layout)
        
        return tab

    def create_settings_tab(self):
        """יצירת טאב הגדרות"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # הגדרות כלליות
        general_group = QGroupBox("הגדרות כלליות")
        general_layout = QVBoxLayout(general_group)
        
        minimize_cb = QCheckBox("מזער למגש המערכת בעת סגירה")
        minimize_cb.setChecked(self.settings.value('MinimizeToTray', True, type=bool))
        minimize_cb.stateChanged.connect(
            lambda state: self.settings.setValue('MinimizeToTray', bool(state))
        )
        
        general_layout.addWidget(minimize_cb)
        
        # הגדרות אבטחה
        security_group = QGroupBox("הגדרות אבטחה")
        security_layout = QVBoxLayout(security_group)
        
        password_protection_cb = QCheckBox("הפעל הגנת סיסמה")
        password_protection_cb.setChecked(self.password_protected)
        password_protection_cb.stateChanged.connect(self.toggle_password_protection)
        
        set_password_btn = QPushButton("הגדר סיסמת מערכת")
        set_password_btn.clicked.connect(self.set_system_password)
        
        change_key_btn = QPushButton("החלף מפתח הצפנה...")
        change_key_btn.clicked.connect(self.change_encryption_key)
        
        security_layout.addWidget(password_protection_cb)
        security_layout.addWidget(set_password_btn)
        security_layout.addWidget(change_key_btn)
        
        layout.addWidget(general_group)
        layout.addWidget(security_group)
        layout.addStretch()
        
        return tab

    def setup_tray(self):
        """הגדרת אייקון מגש המערכת"""
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setToolTip('מנהל התחברויות מתקדם')
        
        tray_menu = QMenu()
        show_action = QAction("הצג", self)
        quit_action = QAction("יציאה", self)
        
        show_action.triggered.connect(self.show)
        quit_action.triggered.connect(QApplication.quit)
        
        tray_menu.addAction(show_action)
        tray_menu.addAction(quit_action)
        
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()

    def add_site(self):
        """הוספת אתר חדש"""
        dialog = AdvancedLoginDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            site_data = dialog.get_data()
            if not all(site_data.values()):
                QMessageBox.warning(self, "שגיאה", "יש למלא את כל השדות")
                return
            
            site_name = site_data['site_name']
            if site_name in self.sites:
                QMessageBox.warning(self, "שגיאה", "שם האתר כבר קיים")
                return
            
            self.sites[site_name] = site_data
            self.save_sites()
            self.update_sites_list()

    def edit_site(self):
        """עריכת אתר קיים"""
        current_item = self.sites_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, "אזהרה", "יש לבחור אתר לעריכה")
            return
        
        site_name = current_item.text()
        dialog = AdvancedLoginDialog(self, self.sites[site_name])
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            site_data = dialog.get_data()
            if not all(site_data.values()):
                QMessageBox.warning(self, "שגיאה", "יש למלא את כל השדות")
                return
            
            if site_name != site_data['site_name']:
                del self.sites[site_name]
            
            self.sites[site_data['site_name']] = site_data
            self.save_sites()
            self.update_sites_list()

    def delete_site(self):
        """מחיקת אתר"""
        current_item = self.sites_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, "אזהרה", "יש לבחור אתר למחיקה")
            return
        
        site_name = current_item.text()
        reply = QMessageBox.question(
            self, 
            "אישור מחיקה",
            f"האם למחוק את האתר {site_name}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            del self.sites[site_name]
            self.save_sites()
            self.update_sites_list()

    def login_to_site(self, item=None):
        """ביצוע התחברות לאתר"""
        if not item:
            item = self.sites_list.currentItem()
        if not item:
            QMessageBox.warning(self, "שגיאה", "יש לבחור אתר להתחברות")
            return
        
        site_name = item.text()
        site_data = self.sites[site_name]
        
        try:
            options = webdriver.ChromeOptions()
            options.add_argument("--disable-blink-features=AutomationControlled")
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option('useAutomationExtension', False)
            
            driver = webdriver.Chrome(options=options)
            driver.get(site_data['url'])
            
            # בדיקה אם זה Gmail
            is_gmail = 'gmail.com' in site_data['url'] or 'accounts.google.com' in site_data['url']
            
            if is_gmail:
                self._handle_gmail_login(driver, site_data)
            else:
                finder = SmartLoginFieldsFinder(driver)
                login_fields = finder.find_login_fields()
                
                if not login_fields:
                    raise Exception("לא נמצאו שדות התחברות באתר")
                
                username = site_data['username']
                password = site_data['password']
                
                for field_type, selectors in login_fields.items():
                    value = username if field_type == 'username' else password
                    for selector_type, selector in selectors.items():
                        try:
                            if selector_type == 'id':
                                element = driver.find_element(By.ID, selector)
                            elif selector_type == 'name':
                                element = driver.find_element(By.NAME, selector)
                            elif selector_type == 'css':
                                element = driver.find_element(By.CSS_SELECTOR, selector)
                            elif selector_type == 'xpath':
                                element = driver.find_element(By.XPATH, selector)
                            else:
                                continue
                            
                            element.clear()
                            element.send_keys(value)
                            break
                        except:
                            continue

            self.status_bar.showMessage(f"התחברות לאתר {site_name} בוצעה בהצלחה", 5000)
            
        except Exception as e:
            QMessageBox.critical(self, "שגיאת התחברות", str(e))
    def _handle_gmail_login(self, driver, site_data):
        """טיפול בהתחברות מיוחדת ל-Gmail"""
        try:
            wait = WebDriverWait(driver, 10)
            
            # שלב 1: הזנת האימייל
            print("מזין כתובת אימייל...")  # לוג לדיבוג
            email_field = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'input[type="email"]')))
            email_field.clear()
            email_field.send_keys(site_data['username'])
            
            # המתנה קצרה אחרי הזנת האימייל
            time.sleep(2)
            
            # שלב 2: לחיצה על כפתור "הבא" הראשון
            print("מחפש כפתור 'הבא' ראשון...")  # לוג לדיבוג
            next_button = wait.until(EC.element_to_be_clickable(
                (By.CSS_SELECTOR, '#identifierNext button, div#identifierNext button')
            ))
            next_button.click()
            
            # המתנה לטעינת דף הסיסמה
            time.sleep(3)
            
            # שלב 3: הזנת הסיסמה
            print("מזין סיסמה...")  # לוג לדיבוג
            password_field = wait.until(EC.presence_of_element_located(
                (By.CSS_SELECTOR, 'input[type="password"]')
            ))
            password_field.clear()
            password_field.send_keys(site_data['password'])
            
            # המתנה קצרה אחרי הזנת הסיסמה
            time.sleep(2)
            
            # שלב 4: לחיצה על כפתור "הבא" השני
            print("מחפש כפתור 'הבא' שני...")  # לוג לדיבוג
            try:
                password_next = wait.until(EC.element_to_be_clickable(
                    (By.CSS_SELECTOR, '#passwordNext button, div#passwordNext button')
                ))
                password_next.click()
            except:
                try:
                    # ניסיון שני עם JavaScript
                    password_next = driver.find_element(By.CSS_SELECTOR, '#passwordNext button, div#passwordNext button')
                    driver.execute_script("arguments[0].click();", password_next)
                except:
                    raise Exception("לא נמצא כפתור 'הבא' אחרי הזנת הסיסמה")
            
            # המתנה לסיום ההתחברות
            time.sleep(3)
            
        except TimeoutException:
            raise Exception("תהליך ההתחברות נכשל - זמן ההמתנה עבר")
        except Exception as e:
            raise Exception(f"שגיאה בהתחברות ל-Gmail: {str(e)}")
        
    def _submit_login_form(self, driver):
        """שליחת טופס ההתחברות"""
        try:
            # ניסיון למצוא כפתור התחברות
            submit_buttons = driver.find_elements(
                By.XPATH,
                "//button[@type='submit'] | //input[@type='submit']"
            )
            
            for button in submit_buttons:
                if button.is_displayed() and button.is_enabled():
                    button.click()
                    return
            
            # אם לא נמצא כפתור, ננסה להגיש את הטופס
            forms = driver.find_elements(By.TAG_NAME, 'form')
            for form in forms:
                if any(input_el.get_attribute('type') == 'password' 
                      for input_el in form.find_elements(By.TAG_NAME, 'input')):
                    form.submit()
                    return
            
            raise Exception("לא נמצאה דרך לשלוח את טופס ההתחברות")
            
        except Exception as e:
            raise Exception(f"שגיאה בשליחת טופס ההתחברות: {str(e)}")

    def update_sites_list(self):
        """עדכון רשימת האתרים בממשק"""
        self.sites_list.clear()
        for site_name in sorted(self.sites.keys()):
            self.sites_list.addItem(site_name)
        self.update_status_bar()

    def update_status_bar(self):
        """עדכון סרגל הסטטוס"""
        total_sites = len(self.sites)
        self.status_bar.showMessage(f"סה\"כ אתרים שמורים: {total_sites}")

    def filter_sites(self, text: str):
        """סינון רשימת האתרים לפי טקסט חיפוש"""
        self.sites_list.clear()
        search_text = text.lower()
        for site_name in sorted(self.sites.keys()):
            if search_text in site_name.lower() or \
               search_text in self.sites[site_name]['url'].lower():
                self.sites_list.addItem(site_name)

    def show_site_context_menu(self, position):
        """הצגת תפריט הקשר לאתר נבחר"""
        item = self.sites_list.itemAt(position)
        if not item:
            return
            
        menu = QMenu()
        
        login_action = menu.addAction("התחבר")
        edit_action = menu.addAction("ערוך")
        delete_action = menu.addAction("מחק")
        copy_action = menu.addAction("העתק פרטי התחברות")
        
        action = menu.exec(self.sites_list.mapToGlobal(position))
        
        if action == login_action:
            self.login_to_site(item)
        elif action == edit_action:
            self.edit_site()
        elif action == delete_action:
            self.delete_site()
        elif action == copy_action:
            self.copy_login_details(item.text())

    def copy_login_details(self, site_name: str):
        """העתקת פרטי התחברות ללוח"""
        if site_name in self.sites:
            site_data = self.sites[site_name]
            details = f"אתר: {site_name}\n"
            details += f"כתובת: {site_data['url']}\n"
            details += f"שם משתמש: {site_data['username']}"
            
            clipboard = QApplication.clipboard()
            clipboard.setText(details)
            
            self.status_bar.showMessage("פרטי ההתחברות הועתקו ללוח", 3000)

    def change_encryption_key(self):
        """שינוי מפתח ההצפנה"""
        reply = QMessageBox.warning(
            self,
            "שינוי מפתח הצפנה",
            "האם אתה בטוח שברצונך להחליף את מפתח ההצפנה? פעולה זו תדרוש הצפנה מחדש של כל הנתונים.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                # גיבוי הנתונים הנוכחיים
                old_sites = self.sites.copy()
                
                # יצירת מפתח חדש
                self.key = Fernet.generate_key()
                with open(self.key_file, 'wb') as f:
                    f.write(self.key)
                self.cipher = Fernet(self.key)
                
                # הצפנה מחדש של כל הנתונים
                self.sites = old_sites
                self.save_sites()
                
                QMessageBox.information(
                    self,
                    "הצלחה",
                    "מפתח ההצפנה הוחלף בהצלחה והנתונים הוצפנו מחדש."
                )
                
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "שגיאה",
                    f"שגיאה בהחלפת מפתח ההצפנה: {str(e)}"
                )

    def export_data(self):
        """ייצוא נתונים מוצפנים"""
        try:
            filename, _ = QFileDialog.getSaveFileName(
                self,
                "שמירת נתונים מוצפנים",
                "",
                "קבצי JSON (*.json)"
            )
            
            if filename:
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(self.sites, f, indent=4, ensure_ascii=False)
                self.status_bar.showMessage("הנתונים יוצאו בהצלחה", 3000)
                
        except Exception as e:
            QMessageBox.critical(
                self,
                "שגיאה",
                f"שגיאה בייצוא הנתונים: {str(e)}"
            )

    def import_data(self):
        """ייבוא נתונים מוצפנים"""
        try:
            filename, _ = QFileDialog.getOpenFileName(
                self,
                "טעינת נתונים מוצפנים",
                "",
                "קבצי JSON (*.json)"
            )
            
            if filename:
                with open(filename, 'r', encoding='utf-8') as f:
                    imported_sites = json.load(f)
                
                # בדיקת תקינות הנתונים
                for site_name, site_data in imported_sites.items():
                    required_fields = ['url', 'username', 'password']
                    if not all(field in site_data for field in required_fields):
                        raise ValueError(f"נתונים חסרים באתר {site_name}")
                
                # מיזוג הנתונים
                self.sites.update(imported_sites)
                self.save_sites()
                self.update_sites_list()
                self.status_bar.showMessage("הנתונים יובאו בהצלחה", 3000)
                
        except Exception as e:
            QMessageBox.critical(
                self,
                "שגיאה",
                f"שגיאה בייבוא הנתונים: {str(e)}"
            )

    def closeEvent(self, event):
        """טיפול באירוע סגירת החלון"""
        if self.settings.value('MinimizeToTray', True, type=bool):
            event.ignore()
            self.hide()
        else:
            event.accept()

def main():
    app = QApplication(sys.argv)
    app.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
    
    # הגדרת סגנון
    app.setStyle('Fusion')
    
    # יצירת והצגת החלון הראשי
    window = AdvancedLoginManager()
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()      
