import os
import time
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QLabel, QTextEdit, QStackedWidget, QFrame, QListWidget, QListWidgetItem, 
                             QMessageBox, QScrollArea, QSlider, QInputDialog, QLineEdit, QDialog)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer, QUrl, QDateTime
from PyQt6.QtMultimedia import QMediaRecorder, QAudioInput, QMediaCaptureSession, QMediaFormat, QMediaPlayer, QAudioOutput
import qtawesome as qta
from src.database.db_manager import db_manager
from src.ui.theme_manager import theme_manager
from src.ui.button_styles import style_button

class NoteListItemWidget(QWidget):
    """Custom widget for note list items with Edit and Delete buttons."""
    edit_requested = pyqtSignal(dict)
    delete_requested = pyqtSignal(dict)
    play_requested = pyqtSignal(dict)

    def __init__(self, note_data):
        super().__init__()
        self.note_data = note_data
        self.init_ui()

    def init_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(10)

        # Icon based on type
        icon_name = "fa5s.microphone" if self.note_data['type'] == 'voice' else "fa5s.file-alt"
        self.icon_lbl = QLabel()
        self.icon_lbl.setPixmap(qta.icon(icon_name, color="#4318ff").pixmap(20, 20))
        layout.addWidget(self.icon_lbl)

        # Text Info
        info_layout = QVBoxLayout()
        info_layout.setSpacing(2)
        
        display_name = self.note_data.get('title') or (f"Voice Note" if self.note_data['type'] == 'voice' else "Written Note")
        self.name_lbl = QLabel(display_name)
        self.name_lbl.setStyleSheet("font-weight: bold; font-size: 13px;")
        info_layout.addWidget(self.name_lbl)

        date_str = self.note_data['created_at'].split()[0]
        meta_text = f"{date_str}"
        if self.note_data.get('duration'):
            meta_text += f" | {self.note_data['duration']}"
        self.meta_lbl = QLabel(meta_text)
        self.meta_lbl.setStyleSheet("font-size: 11px; color: #718096;")
        info_layout.addWidget(self.meta_lbl)
        
        layout.addLayout(info_layout)
        layout.addStretch()

        # Action Buttons
        self.edit_btn = QPushButton()
        self.edit_btn.setIcon(qta.icon("fa5s.edit", color="#4318ff"))
        self.edit_btn.setFixedSize(30, 30)
        self.edit_btn.setStyleSheet("background: transparent; border: none;")
        self.edit_btn.clicked.connect(lambda: self.edit_requested.emit(self.note_data))
        layout.addWidget(self.edit_btn)

        self.delete_btn = QPushButton()
        self.delete_btn.setIcon(qta.icon("fa5s.trash", color="#ee5d50"))
        self.delete_btn.setFixedSize(30, 30)
        self.delete_btn.setStyleSheet("background: transparent; border: none;")
        self.delete_btn.clicked.connect(lambda: self.delete_requested.emit(self.note_data))
        layout.addWidget(self.delete_btn)

    def mouseDoubleClickEvent(self, event):
        self.play_requested.emit(self.note_data)
        super().mouseDoubleClickEvent(event)

class PlaybackOverlay(QFrame):
    """Overlay for controlling voice note playback."""
    def __init__(self, player, parent=None):
        super().__init__(parent)
        self.player = player
        self.setObjectName("playback_overlay")
        self.init_ui()
        self.hide() # Hidden by default
        
        # Connect player signals
        self.player.positionChanged.connect(self.update_position)
        self.player.durationChanged.connect(self.update_duration)
        self.player.playbackStateChanged.connect(self.update_state)

    def init_ui(self):
        bg_color = "#f8fafc" if not theme_manager.is_dark else "#1e293b"
        border_color = "#e2e8f0" if not theme_manager.is_dark else "#334155"
        self.setStyleSheet(f"""
            QFrame#playback_overlay {{
                background-color: {bg_color};
                border-top: 1px solid {border_color};
                border-bottom-left-radius: 20px;
                border-bottom-right-radius: 20px;
            }}
            QLabel {{ font-size: 11px; color: #718096; }}
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 10, 15, 10)
        
        # Title of playing note
        self.playing_title = QLabel("Playing...")
        self.playing_title.setStyleSheet("font-weight: bold; color: #4318ff;")
        layout.addWidget(self.playing_title)
        
        # Slider & Timers
        time_layout = QHBoxLayout()
        self.curr_time_lbl = QLabel("0:00")
        time_layout.addWidget(self.curr_time_lbl)
        
        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.setStyleSheet("""
            QSlider::groove:horizontal { border: 1px solid #e2e8f0; height: 4px; background: #e2e8f0; border-radius: 2px; }
            QSlider::handle:horizontal { background: #4318ff; border: 1px solid #4318ff; width: 12px; height: 12px; margin: -4px 0; border-radius: 6px; }
        """)
        self.slider.sliderMoved.connect(self.set_position)
        time_layout.addWidget(self.slider)
        
        self.total_time_lbl = QLabel("0:00")
        time_layout.addWidget(self.total_time_lbl)
        layout.addLayout(time_layout)
        
        # Controls
        ctrl_layout = QHBoxLayout()
        ctrl_layout.addStretch()
        
        self.pp_btn = QPushButton() # Play/Pause
        self.pp_btn.setIcon(qta.icon("fa5s.pause", color="white"))
        self.pp_btn.setFixedSize(40, 40)
        style_button(self.pp_btn, variant="primary")
        self.pp_btn.clicked.connect(self.toggle_playback)
        ctrl_layout.addWidget(self.pp_btn)
        
        self.stop_btn = QPushButton()
        self.stop_btn.setIcon(qta.icon("fa5s.stop", color="white"))
        self.stop_btn.setFixedSize(40, 40)
        style_button(self.stop_btn, variant="danger")
        self.stop_btn.clicked.connect(self.stop_playback)
        ctrl_layout.addWidget(self.stop_btn)
        
        ctrl_layout.addStretch()
        layout.addLayout(ctrl_layout)

    def toggle_playback(self):
        if self.player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.player.pause()
        else:
            self.player.play()

    def stop_playback(self):
        self.player.stop()
        self.hide()

    def update_state(self, state):
        if state == QMediaPlayer.PlaybackState.PlayingState:
            self.pp_btn.setIcon(qta.icon("fa5s.pause", color="white"))
        else:
            self.pp_btn.setIcon(qta.icon("fa5s.play", color="white"))
            
        if state == QMediaPlayer.PlaybackState.StoppedState:
            self.hide()

    def update_position(self, position):
        self.slider.setValue(position)
        self.curr_time_lbl.setText(self.format_time(position))

    def update_duration(self, duration):
        self.slider.setRange(0, duration)
        self.total_time_lbl.setText(self.format_time(duration))

    def set_position(self, position):
        self.player.setPosition(position)

    def format_time(self, ms):
        s = ms // 1000
        m = s // 60
        s = s % 60
        return f"{m}:{s:02}"

    def show_for_note(self, title, path):
        self.playing_title.setText(f"Playing: {title}")
        self.player.setSource(QUrl.fromLocalFile(path))
        self.player.play()
        self.show()

class NotesExternalWindow(QWidget):
    """
    External window for taking voice and written notes.
    Disables the main window while open.
    """
    closed = pyqtSignal()

    def __init__(self, parent_to_reenable=None):
        super().__init__()
        self.parent_to_reenable = parent_to_reenable
        if self.parent_to_reenable:
            self.parent_to_reenable.setEnabled(False)
            
        self.setWindowTitle("Pharmacy Notes")
        self.setFixedSize(550, 680) # Slightly taller for playback bar
        self.setWindowFlags(Qt.WindowType.Window | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        # Multimedia Setup
        self.session = QMediaCaptureSession()
        self.audio_input = QAudioInput()
        self.session.setAudioInput(self.audio_input)
        self.recorder = QMediaRecorder()
        self.session.setRecorder(self.recorder)
        
        # Player
        self.player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.player.setAudioOutput(self.audio_output)
        
        # Audio Storage
        self.notes_dir = os.path.join(db_manager.base_dir, "PharmacyNotes")
        os.makedirs(self.notes_dir, exist_ok=True)
        
        self.recording_start_time = None
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_rec_timer)
        
        self.init_ui()
        self.load_notes()

    def init_ui(self):
        self.main_container = QFrame(self)
        self.main_container.setObjectName("notes_container")
        self.main_container.setFixedSize(self.size())
        
        bg_color = "#ffffff" if not theme_manager.is_dark else "#1a1c2e"
        border_color = "#e2e8f0" if not theme_manager.is_dark else "#2d3748"
        text_color = "#1a202c" if not theme_manager.is_dark else "#f7fafc"
        
        self.main_container.setStyleSheet(f"""
            QFrame#notes_container {{
                background-color: {bg_color};
                border: 2px solid {border_color};
                border-radius: 20px;
            }}
            QLabel {{ color: {text_color}; }}
            QTextEdit {{
                background-color: {'#f8fafc' if not theme_manager.is_dark else '#111827'};
                border: 1px solid {border_color};
                border-radius: 10px;
                padding: 10px;
                color: {text_color};
                font-size: 14px;
            }}
            QListWidget {{ background: transparent; border: none; outline: none; }}
            QListWidget::item {{ background: transparent; padding: 0; margin-bottom: 5px; }}
        """)
        
        self.main_vbox = QVBoxLayout(self.main_container)
        self.main_vbox.setContentsMargins(0, 0, 0, 0)
        self.main_vbox.setSpacing(0)
        
        # Upper area padding
        content_frame = QFrame()
        layout = QVBoxLayout(content_frame)
        layout.setContentsMargins(30, 30, 30, 20)
        layout.setSpacing(15)
        
        # Header
        header = QHBoxLayout()
        title_lbl = QLabel("Pharmacy Notes")
        title_lbl.setStyleSheet("font-size: 22px; font-weight: bold;")
        header.addWidget(title_lbl)
        header.addStretch()
        
        close_btn = QPushButton(qta.icon("fa5s.times", color="#718096"), "")
        close_btn.setFixedSize(30, 30)
        close_btn.setStyleSheet("background: transparent; border: none; font-size: 18px;")
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.clicked.connect(self.close_and_exit)
        header.addWidget(close_btn)
        layout.addLayout(header)
        
        # Mode Switcher
        self.stack = QStackedWidget()
        
        # 1. Main Options View
        options_page = QWidget()
        opt_lay = QVBoxLayout(options_page)
        opt_lay.addStretch()
        lbl = QLabel("What would you like to record?")
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl.setStyleSheet("font-size: 16px; color: #718096; margin-bottom: 20px;")
        opt_lay.addWidget(lbl)
        
        btn_lay = QHBoxLayout()
        self.voice_mode_btn = QPushButton(" Voice Note")
        self.voice_mode_btn.setIcon(qta.icon("fa5s.microphone", color="white"))
        self.voice_mode_btn.setFixedSize(180, 100)
        style_button(self.voice_mode_btn, variant="primary")
        self.voice_mode_btn.clicked.connect(lambda: self.stack.setCurrentIndex(1))
        btn_lay.addWidget(self.voice_mode_btn)
        
        self.write_mode_btn = QPushButton(" Written Note")
        self.write_mode_btn.setIcon(qta.icon("fa5s.pen", color="white"))
        self.write_mode_btn.setFixedSize(180, 100)
        style_button(self.write_mode_btn, variant="success")
        self.write_mode_btn.clicked.connect(lambda: self.stack.setCurrentIndex(2))
        btn_lay.addWidget(self.write_mode_btn)
        opt_lay.addLayout(btn_lay)
        opt_lay.addStretch()
        
        # 2. Voice Recording Page
        voice_page = QWidget()
        v_lay = QVBoxLayout(voice_page)
        self.rec_status_lbl = QLabel("Ready to record")
        self.rec_status_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.rec_status_lbl.setStyleSheet("font-size: 18px; font-weight: bold; color: #4318ff;")
        v_lay.addWidget(self.rec_status_lbl)
        
        self.timer_lbl = QLabel("00:00")
        self.timer_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.timer_lbl.setStyleSheet("font-size: 48px; font-weight: bold; font-family: 'Courier New';")
        v_lay.addWidget(self.timer_lbl)
        
        rec_btn_lay = QHBoxLayout()
        self.start_rec_btn = QPushButton(" Start Recording")
        style_button(self.start_rec_btn, variant="danger")
        self.start_rec_btn.clicked.connect(self.start_recording)
        rec_btn_lay.addWidget(self.start_rec_btn)
        
        self.stop_rec_btn = QPushButton(" Stop & Save")
        style_button(self.stop_rec_btn, variant="primary")
        self.stop_rec_btn.clicked.connect(self.stop_recording)
        self.stop_rec_btn.setEnabled(False)
        rec_btn_lay.addWidget(self.stop_rec_btn)
        v_lay.addLayout(rec_btn_lay)
        
        back_btn = QPushButton("Cancel")
        back_btn.clicked.connect(lambda: self.stack.setCurrentIndex(0))
        style_button(back_btn, variant="outline")
        v_lay.addWidget(back_btn)

        # 3. Written Note Page
        write_page = QWidget()
        w_lay = QVBoxLayout(write_page)
        self.note_edit = QTextEdit()
        self.note_edit.setPlaceholderText("Type your note here...")
        w_lay.addWidget(self.note_edit)
        save_btn = QPushButton(" Save Written Note")
        style_button(save_btn, variant="primary")
        save_btn.clicked.connect(self.save_written_note)
        w_lay.addWidget(save_btn)
        back_btn2 = QPushButton("Cancel")
        back_btn2.clicked.connect(lambda: self.stack.setCurrentIndex(0))
        style_button(back_btn2, variant="outline")
        w_lay.addWidget(back_btn2)

        self.stack.addWidget(options_page)
        self.stack.addWidget(voice_page)
        self.stack.addWidget(write_page)
        layout.addWidget(self.stack)
        
        # Recent Notes Section
        layout.addWidget(QLabel("Recent Notes"))
        self.notes_list = QListWidget()
        self.notes_list.setFixedHeight(230)
        layout.addWidget(self.notes_list)
        
        self.main_vbox.addWidget(content_frame)
        
        # Playback Control Overlay at the bottom
        self.playback_bar = PlaybackOverlay(self.player, self.main_container)
        self.main_vbox.addWidget(self.playback_bar)

    def load_notes(self):
        from src.core.blocking_task_manager import task_manager

        def do_load():
            try:
                with db_manager.get_pharmacy_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("SELECT * FROM pharmacy_notes ORDER BY created_at DESC LIMIT 20")
                    return {"success": True, "notes": [dict(r) for r in cursor.fetchall()]}
            except Exception as e:
                return {"success": False, "error": str(e)}

        def on_finished(result):
            if not result["success"]:
                print(f"Error loading notes: {result['error']}")
                return

            self.notes_list.clear()
            for note_data in result["notes"]:
                item = QListWidgetItem(self.notes_list)
                widget = NoteListItemWidget(note_data)
                widget.edit_requested.connect(self.rename_note)
                widget.delete_requested.connect(self.delete_note)
                widget.play_requested.connect(self.play_or_view_note)
                
                item.setSizeHint(widget.sizeHint())
                self.notes_list.addItem(item)
                self.notes_list.setItemWidget(item, widget)

        task_manager.run_task(do_load, on_finished=on_finished)

    def update_rec_timer(self):
        if self.recording_start_time:
            elapsed = int(time.time() - self.recording_start_time)
            mins = elapsed // 60
            secs = elapsed % 60
            self.timer_lbl.setText(f"{mins:02}:{secs:02}")

    def start_recording(self):
        filename = f"voice_note_{int(time.time())}.m4a"
        self.current_voice_path = os.path.join(self.notes_dir, filename)
        self.recorder.setOutputLocation(QUrl.fromLocalFile(self.current_voice_path))
        format = QMediaFormat()
        format.setFileFormat(QMediaFormat.FileFormat.MPEG4)
        format.setAudioCodec(QMediaFormat.AudioCodec.AAC)
        self.recorder.setMediaFormat(format)
        self.recorder.record()
        self.recording_start_time = time.time()
        self.timer.start(1000)
        self.rec_status_lbl.setText("Recording...")
        self.rec_status_lbl.setStyleSheet("color: #ee5d50; font-weight: bold; font-size: 18px;")
        self.start_rec_btn.setEnabled(False)
        self.stop_rec_btn.setEnabled(True)

    def stop_recording(self):
        self.recorder.stop()
        self.timer.stop()
        duration = self.timer_lbl.text()
        from src.core.blocking_task_manager import task_manager

        def do_save():
            try:
                with db_manager.get_pharmacy_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("INSERT INTO pharmacy_notes (type, content, duration) VALUES (?, ?, ?)",
                                 ('voice', self.current_voice_path, duration))
                    conn.commit()
                return True
            except Exception as e:
                return str(e)

        def on_finished(result):
            if result is True:
                self.start_rec_btn.setEnabled(True)
                self.stop_rec_btn.setEnabled(False)
                self.rec_status_lbl.setText("Recording Saved")
                self.timer_lbl.setText("00:00")
                self.load_notes()
                QTimer.singleShot(1500, lambda: self.stack.setCurrentIndex(0))
            else:
                QMessageBox.critical(self, "Error", f"Failed to save voice note: {result}")

        task_manager.run_task(do_save, on_finished=on_finished)

    def save_written_note(self):
        content = self.note_edit.toPlainText().strip()
        if not content: return
        from src.core.blocking_task_manager import task_manager

        def do_save():
            try:
                with db_manager.get_pharmacy_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("INSERT INTO pharmacy_notes (type, content) VALUES (?, ?)", ('written', content))
                    conn.commit()
                return True
            except Exception as e:
                return str(e)

        def on_finished(result):
            if result is True:
                self.note_edit.clear()
                self.load_notes()
                self.stack.setCurrentIndex(0)
            else:
                QMessageBox.critical(self, "Error", f"Failed to save written note: {result}")

        task_manager.run_task(do_save, on_finished=on_finished)

    def play_or_view_note(self, data):
        if data['type'] == 'voice':
            path = data['content']
            if os.path.exists(path):
                title = data.get('title') or f"Voice Note ({data['created_at'].split()[0]})"
                self.playback_bar.show_for_note(title, path)
            else:
                QMessageBox.warning(self, "File Not Found", "The voice note file could not be found.")
        else:
            QMessageBox.information(self, "Written Note", f"{data.get('title') or 'Note'}:\n\n{data['content']}")

    def rename_note(self, data):
        curr_title = data.get('title') or ""
        new_title, ok = QInputDialog.getText(self, "Rename Note", "Enter new name:", QLineEdit.EchoMode.Normal, curr_title)
        if ok and new_title.strip():
            from src.core.blocking_task_manager import task_manager
            
            def do_rename():
                try:
                    with db_manager.get_pharmacy_connection() as conn:
                        cursor = conn.cursor()
                        cursor.execute("UPDATE pharmacy_notes SET title = ? WHERE id = ?", (new_title.strip(), data['id']))
                        conn.commit()
                    return True
                except Exception as e:
                    return str(e)

            def on_finished(result):
                if result is True:
                    self.load_notes()
                else:
                    QMessageBox.critical(self, "Error", f"Failed to rename: {result}")

            task_manager.run_task(do_rename, on_finished=on_finished)

    def delete_note(self, data):
        confirm = QMessageBox.question(self, "Confirm Delete", "Are you sure you want to delete this note?", 
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if confirm == QMessageBox.StandardButton.Yes:
            from src.core.blocking_task_manager import task_manager

            def do_delete():
                try:
                    with db_manager.get_pharmacy_connection() as conn:
                        cursor = conn.cursor()
                        cursor.execute("DELETE FROM pharmacy_notes WHERE id = ?", (data['id'],))
                        conn.commit()
                    
                    if data['type'] == 'voice' and os.path.exists(data['content']):
                        try: os.remove(data['content'])
                        except: pass
                    return True
                except Exception as e:
                    return str(e)

            def on_finished(result):
                if result is True:
                    self.load_notes()
                    if self.player.source().toLocalFile() == data['content']:
                        self.player.stop()
                else:
                    QMessageBox.critical(self, "Error", f"Failed to delete: {result}")

            task_manager.run_task(do_delete, on_finished=on_finished)

    def close_and_exit(self):
        self.player.stop()
        if self.parent_to_reenable:
            self.parent_to_reenable.setEnabled(True)
        self.closed.emit()
        self.close()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_pos = event.globalPosition().toPoint()

    def mouseMoveEvent(self, event):
        if hasattr(self, 'drag_pos'):
            delta = event.globalPosition().toPoint() - self.drag_pos
            self.move(self.x() + delta.x(), self.y() + delta.y())
            self.drag_pos = event.globalPosition().toPoint()
