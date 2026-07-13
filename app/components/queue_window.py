# components/queue_window.py
from pathlib import Path
from PyQt5.QtCore import Qt, pyqtSignal, QRectF, QPoint
from PyQt5.QtGui import QColor, QPainter, QPainterPath, QBrush, QPixmap, QPen
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QApplication, QSizePolicy, QGraphicsScene, QGraphicsPixmapItem, QGraphicsBlurEffect
from qfluentwidgets import ScrollArea, BodyLabel, FluentIcon as FIF, Theme

from app.core.app_state import AppState
from app.core.metadata_reader import MetadataReader
from app.components.marquee_label import MarqueeLabel

def blur_pixmap(pixmap: QPixmap, radius: int = 12) -> QPixmap:
    """Создает размытую копию QPixmap."""
    if pixmap.isNull():
        return pixmap
    scene = QGraphicsScene()
    item = QGraphicsPixmapItem(pixmap)
    blur = QGraphicsBlurEffect()
    blur.setBlurRadius(radius)
    item.setGraphicsEffect(blur)
    scene.addItem(item)
    
    blurred = QPixmap(pixmap.size())
    blurred.fill(Qt.transparent)
    painter = QPainter(blurred)
    scene.render(painter)
    painter.end()
    return blurred


class RoundedImageLabel(QLabel):
    """QLabel, который обрезает QPixmap по закругленным углам."""
    def __init__(self, radius: int = 8, parent=None):
        super().__init__(parent)
        self.setAlignment(Qt.AlignCenter)
        self._pixmap = QPixmap()
        self._radius = radius
        self.setStyleSheet("background: #222222;") # Фоллбек цвет

    def setPixmap(self, pixmap):
        self._pixmap = pixmap
        self.update()

    def paintEvent(self, event):
        if self._pixmap.isNull():
            super().paintEvent(event)
            return
        
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)
        
        # Масштабируем с сохранением пропорций (KeepAspectRatioByExpanding)
        scaled = self._pixmap.scaled(self.size(), Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
        
        # Центрируем изображение
        x = (self.width() - scaled.width()) // 2
        y = (self.height() - scaled.height()) // 2
        
        # Создаем путь для клиппинга (обрезки)
        path = QPainterPath()
        path.addRoundedRect(0, 0, self.width(), self.height(), self._radius, self._radius)
        
        painter.setClipPath(path)
        painter.drawPixmap(x, y, scaled)
        

class QueueTrackItem(QWidget):
    """Виджет одного трека в очереди. Поддерживает перетаскивание."""
    drag_started = pyqtSignal(object)
    drag_moved = pyqtSignal(object, QPoint)
    drag_finished = pyqtSignal(object)
    track_double_clicked = pyqtSignal(Path)

    def __init__(self, track_path: Path, is_current: bool, parent=None):
        super().__init__(parent)
        self.track_path = track_path
        self.is_current = is_current
        self.is_dragging = False
        
        self.setFixedHeight(56)
        self.setObjectName("QueueTrackItem")
        
        # Основной горизонтальный лейаут
        h_layout = QHBoxLayout(self)
        h_layout.setSpacing(10)
        h_layout.setContentsMargins(8, 8, 8, 8)
        
        # Обложка
        self.cover_label = RoundedImageLabel(radius=4) # Радиус 4px для маленьких иконок
        self.cover_label.setFixedSize(40, 40)
        self.cover_label.setAlignment(Qt.AlignCenter)
        self.cover_label.setStyleSheet("""
            QLabel {
                background: #222222;
                border-radius: 4px;
            }
        """)
        # Иконка PLAY поверх обложки
        self.play_icon_label = QLabel(self.cover_label)
        self.play_icon_label.setFixedSize(40, 40)
        self.play_icon_label.setAlignment(Qt.AlignCenter)
        self.play_icon_label.setStyleSheet("background: transparent;")
        self.play_icon_label.move(0, 0)
        self.play_icon_label.hide()

        # Кэш для размытого изображения
        self._blurred_pixmap = None
        
        # Читаем метаданные
        meta = MetadataReader.get_metadata(track_path)
        cover_pixmap = self._load_cover_pixmap(meta, track_path)
        self.cover_label.setPixmap(cover_pixmap)
        # Сохраняем оригинальный пиксмап для восстановления после hover и для блюра
        self._original_pixmap = cover_pixmap
                
        # Текст
        text_layout = QVBoxLayout()
        text_layout.setSpacing(2)
        text_layout.setContentsMargins(0, 0, 0, 0)
        
        # Цвет текста зависит от того, является ли трек текущим
        title_color = "#1DB954" if self.is_current else "#FFFFFF"
        artist_color = "#1DB954" if self.is_current else "#AAAAAA"
        
        self.title_label = BodyLabel(meta.get('title', track_path.stem))
        self.title_label.setStyleSheet(f"color: {title_color}; font-weight: bold; background: transparent;")

        self.artist_label = BodyLabel(meta.get('artist', 'Unknown Artist'))
        self.artist_label.setStyleSheet(f"color: {artist_color}; font-size: 12px; background: transparent;")
        
        text_layout.addWidget(self.title_label)
        text_layout.addWidget(self.artist_label)
        text_layout.addStretch() # Прижимаем текст к верху
        
        h_layout.addWidget(self.cover_label)
        # ВАЖНО: stretch=1 заставляет text_layout занять всё свободное место.
        # Это ограничивает ширину MarqueeLabel, запуская анимацию бегущей строки,
        # и позволяет paintEvent рисовать фон на всю ширину виджета.
        h_layout.addLayout(text_layout, stretch=1) 
        
    def paintEvent(self, event):
        """Кастомная отрисовка фона и рамки для текущего трека."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        rect = QRectF(self.rect())
        path = QPainterPath()
        path.addRoundedRect(rect, 6, 6)
        
        if self.is_current:
            bg_color = QColor("#1A3A2A")  # Темно-зеленый фон
            border_color = QColor("#1DB954")
        else:
            bg_color = QColor("#111111")
            border_color = QColor("transparent")
            
        painter.fillPath(path, QBrush(bg_color))
        if self.is_current:
            pen = QPen(border_color, 1.5)
            painter.setPen(pen)
            painter.drawPath(path)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drag_start_pos = event.pos()
            self.is_dragging = False
            self.setCursor(Qt.ClosedHandCursor)

    def mouseMoveEvent(self, event):
        if not (event.buttons() & Qt.LeftButton):
            return
        if not self.is_dragging:
            if (event.pos() - self.drag_start_pos).manhattanLength() < QApplication.startDragDistance():
                return
            self.is_dragging = True
            self.drag_started.emit(self)
        
        self.drag_moved.emit(self, event.globalPos())

    def mouseReleaseEvent(self, event):
        if self.is_dragging:
            self.drag_finished.emit(self)
        self.is_dragging = False
        self.setCursor(Qt.ArrowCursor)

    def mouseDoubleClickEvent(self, event):
        """Обработка двойного клика ЛКМ для запуска трека."""
        if event.button() == Qt.LeftButton:
            self.track_double_clicked.emit(self.track_path)
        super().mouseDoubleClickEvent(event)

    def enterEvent(self, event):
        super().enterEvent(event)
        play_pixmap = FIF.PLAY.icon(Theme.DARK).pixmap(20, 20) 
        self.play_icon_label.setPixmap(play_pixmap)
        self.play_icon_label.show()
        
        blurred = self._get_blurred_pixmap()
        if blurred and not blurred.isNull():
            self.cover_label.setPixmap(blurred)

    def leaveEvent(self, event):
        super().leaveEvent(event)
        self.play_icon_label.hide()
        
        # Возвращаем оригинальную обложку/иконку
        if self._original_pixmap and not self._original_pixmap.isNull():
            self.cover_label.setPixmap(self._original_pixmap)

    def _get_blurred_pixmap(self) -> QPixmap:
        """Возвращает размытую версию текущей обложки (с кэшированием)."""
        if self._blurred_pixmap is None:
            self._blurred_pixmap = blur_pixmap(self._original_pixmap, radius=6)
        return self._blurred_pixmap

    def _update_text_colors(self):
        """Обновляет цвет текста в зависимости от is_current."""
        title_color = "#1DB954" if self.is_current else "#FFFFFF"
        artist_color = "#1DB954" if self.is_current else "#AAAAAA"
        self.title_label.setStyleSheet(f"color: {title_color}; font-weight: bold; background: transparent;")
        self.artist_label.setStyleSheet(f"color: {artist_color}; font-size: 12px; background: transparent;")

    def _load_cover_pixmap(self, meta: dict, track_path: Path) -> QPixmap:
        """
        Возвращает QPixmap размером 40x40: либо обложку альбома, 
        либо дефолтную иконку ноты по центру.
        """
        # Создаем целевой pixmap 40x40
        target_pixmap = QPixmap(40, 40)
        target_pixmap.fill(Qt.transparent) # Прозрачный фон

        if meta.get('cover_data'):
            pixmap = QPixmap()
            if pixmap.loadFromData(meta['cover_data']) and not pixmap.isNull():
                # Масштабируем обложку под 40x40
                scaled_cover = pixmap.scaled(40, 40, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
                painter = QPainter(target_pixmap)
                painter.drawPixmap(0, 0, scaled_cover)
                painter.end()
                return target_pixmap
        
        # Берем иконку размером 24x24 (стандартный размер для Fluent Icons выглядит четко)
        icon_size = 24
        icon_pixmap = FIF.MUSIC.icon(Theme.DARK).pixmap(icon_size, icon_size)
        
        if not icon_pixmap.isNull():
            painter = QPainter(target_pixmap)
            painter.setRenderHint(QPainter.Antialiasing)
            painter.setRenderHint(QPainter.SmoothPixmapTransform)
            
            # Вычисляем координаты для центрирования
            x = (40 - icon_size) // 2
            y = (40 - icon_size) // 2
            
            painter.drawPixmap(x, y, icon_pixmap)
            painter.end()
            
        return target_pixmap


class QueueListContainer(QWidget):
    """Контейнер для списка треков. Управляет их порядком."""
    order_changed = pyqtSignal(list)
    track_double_clicked = pyqtSignal(Path)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background: transparent;")
        self.setAttribute(Qt.WA_TranslucentBackground)

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(4, 4, 4, 4) # Небольшие отступы, чтобы треки не прилипали к краям
        self.layout.setSpacing(4)
        self.items = []
        self.dragged_item = None
        
        # Важно: позволяет контейнеру растягиваться по ширине внутри ScrollArea
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.setMinimumWidth(200) # Минимальная ширина для корректной работы MarqueeLabel
        
    def set_tracks(self, tracks: list[Path], current_track: Path):
        """Очищает и заполняет список треков."""
        # Удаляем ВСЕ элементы перед обновлением
        while self.layout.count() > 0:
            item = self.layout.takeAt(0)
            if item.widget():
                item.widget().setParent(None)
        
        self.items.clear()
        for track in tracks:
            item = QueueTrackItem(track, track == current_track)
            item.drag_started.connect(self._on_drag_started)
            item.drag_moved.connect(self._on_drag_moved)
            item.drag_finished.connect(self._on_drag_finished)
            item.track_double_clicked.connect(self._on_track_double_clicked)  # <-- ДОБАВИТЬ ЭТУ СТРОКУ
            self.layout.addWidget(item)
            self.items.append(item)
        self.layout.addStretch()
            
    def _on_drag_started(self, item):
        self.dragged_item = item
        
    def _on_drag_moved(self, item, global_pos):
        """
        Меняет элементы местами только когда курсор пересекает СЕРЕДИНУ соседнего элемента.
        Это предотвращает 'дребезг' и случайные перемещения.
        """
        local_pos = self.mapFromGlobal(global_pos)
        current_index = self.items.index(item)
        
        for i, other_item in enumerate(self.items):
            if other_item is item:
                continue
            
            other_rect = other_item.geometry()
            other_center_y = other_rect.center().y()
            
            # Проверяем, находится ли курсор в вертикальном диапазоне другого элемента
            if other_rect.contains(local_pos):
                # Если тащим вниз и пересекли середину нижнего элемента
                if current_index < i and local_pos.y() > other_center_y:
                    self.items.remove(item)
                    self.items.insert(i, item)
                    self._rebuild_layout()
                    break
                # Если тащим вверх и пересекли середину верхнего элемента
                elif current_index > i and local_pos.y() < other_center_y:
                    self.items.remove(item)
                    self.items.insert(i, item)
                    self._rebuild_layout()
                    break
                
    def _on_drag_finished(self, item):
        if self.dragged_item:
            new_order = [item.track_path for item in self.items]
            self.order_changed.emit(new_order)
            self.dragged_item = None
            
    def _on_track_double_clicked(self, track_path: Path):
        """Пробрасывает сигнал двойного клика вверх."""
        self.track_double_clicked.emit(track_path)

    def _rebuild_layout(self):
        while self.layout.count() > 0:
            item = self.layout.takeAt(0)
            if item.widget():
                item.widget().setParent(None)

        for item in self.items:
            self.layout.addWidget(item)
        
        self.layout.addStretch()

    def _update_current_highlight(self, current_path: Path):
        """Обновляет подсветку is_current у всех элементов списка."""
        for item in self.items:
            old_is_current = item.is_current
            item.is_current = (item.track_path == current_path)
            if old_is_current != item.is_current:
                item._update_text_colors()  # Обновляем цвет текста
                item.update()  # Перерисовать для обновления фона/рамки


class QueueWindow(QWidget):
    """Главное окно очереди."""
    queue_reordered = pyqtSignal(list)
    play_track_requested = pyqtSignal(Path)

    def __init__(self, app_state: AppState, parent=None):
        super().__init__(parent)
        self.app_state = app_state
        self.setObjectName("QueueWindow")
        self.setAttribute(Qt.WA_StyledBackground, True)
        
        # Стилизуем САМ QueueWindow, чтобы фон и скругление покрывали ВСЁ окно (и info, и scroll)
        self.setStyleSheet("""
            #QueueWindow {
                background-color: #111111;
                border-radius: 10px;
            }
        """)
        
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(8,12,8,12) # Отступы внутри окна
        self.main_layout.setSpacing(12)
        
        # --- Верхняя часть: Инфо о текущем треке ---
        self.info_layout = QVBoxLayout()
        self.info_layout.setSpacing(0)
        self.info_layout.setContentsMargins(5,0,5,0)
        self.info_layout.setAlignment(Qt.AlignCenter)
        
        self.cover_label = RoundedImageLabel(radius=6)
        self.cover_label.setFixedSize(225, 225)
        self.cover_label.setAlignment(Qt.AlignCenter)
        self.cover_label.setStyleSheet("""
            QLabel {
                background: #222222;
                border-radius: 8px;
            }
        """)
        
        self.title_label = MarqueeLabel("No track selected")
        self.title_label.setStyleSheet("color: #FFFFFF; font-size: 16px; font-weight: bold; background: transparent;")
        self.title_label.setAlignment(Qt.AlignLeft)
        
        self.artist_label = MarqueeLabel("Unknown Artist")
        self.artist_label.setStyleSheet("color: #AAAAAA; font-size: 14px; background: transparent;")
        self.artist_label.setAlignment(Qt.AlignLeft)
        
        self.info_layout.addWidget(self.cover_label, alignment=Qt.AlignCenter)
        self.info_layout.addSpacing(5)
        self.info_layout.addWidget(self.title_label)
        self.info_layout.addSpacing(5)
        self.info_layout.addWidget(self.artist_label)
        
        self.main_layout.addLayout(self.info_layout)
        
        # --- Нижняя часть: ScrollArea с очередью (qfluentwidgets) ---
        self.queue_scroll = ScrollArea()
        self.queue_scroll.setWidgetResizable(True)
        # self.queue_scroll.enableTransparentBackground() # Делает фон прозрачным, чтобы был виден фон QueueWindow
        self.queue_scroll.setStyleSheet("""
            ScrollArea, ScrollArea::viewport, ScrollArea > QWidget > QWidget {
                background-color: transparent;
                border: none;
            }
        """)
        
        self.queue_list = QueueListContainer()
        self.queue_list.order_changed.connect(self._on_order_changed)
        self.queue_list.track_double_clicked.connect(self._on_track_double_clicked)
        
        self.queue_scroll.setWidget(self.queue_list)
        
        self.main_layout.addWidget(self.queue_scroll, stretch=1)
        
        # Инициализация данных
        self.update_current_track()
        self.update_queue()
        
    def update_current_track(self):
        """Обновляет верхнюю панель."""
        current_path = self.app_state.current_track_path
        if current_path and current_path.exists():
            meta = MetadataReader.get_metadata(current_path)
            self.title_label.setText(meta.get('title', current_path.stem))
            self.artist_label.setText(meta.get('artist', 'Unknown Artist'))
            
            if meta.get('cover_data'):
                pixmap = QPixmap()
                if pixmap.loadFromData(meta['cover_data']) and not pixmap.isNull():
                    # Убираем .scaled(...), класс RoundedImageLabel сделает это сам
                    self.cover_label.setPixmap(pixmap)
                else:
                    self.cover_label.clear()
            else:
                self.cover_label.clear()
        else:
            self.title_label.setText("No track selected")
            self.artist_label.setText("Unknown Artist")
            self.cover_label.clear()
            
    def update_queue(self):
        """Обновляет список треков."""
        tracks = self.app_state.playlist_paths
        current_track = self.app_state.current_track_path
        self.queue_list.set_tracks(tracks, current_track)
        
    def _on_order_changed(self, new_order: list[Path]):
        self.app_state.playlist_paths = new_order
        self.queue_reordered.emit(new_order)
        
    def on_track_changed(self, title: str, artist: str, album: str, cover_data: object):
        """Вызывается при смене трека через плеер."""
        # Обновляем верхнюю панель (Cover, Title, Artist)
        self.title_label.setText(title)
        self.artist_label.setText(artist)
        
        if cover_data:
            pixmap = QPixmap()
            if pixmap.loadFromData(cover_data) and not pixmap.isNull():
                self.cover_label.setPixmap(pixmap)
            else:
                self._set_no_cover_pixmap()
        else:
            self._set_no_cover_pixmap()
        
        # Берем актуальные данные из app_state, так как индекс мог измениться
        self.queue_list._update_current_highlight(self.app_state.current_track_path)
        self.update_queue()
    
    def _on_track_double_clicked(self, track_path: Path):
        """Обработка двойного клика по треку в очереди."""
        self.play_track_requested.emit(track_path)

    def _set_no_cover_pixmap(self):
        """Создает QPixmap с надписью 'No Cover' и устанавливает его в label."""
        # Создаем пустой pixmap размером 225x225
        pixmap = QPixmap(225, 225)
        pixmap.fill(QColor("#222222")) # Цвет фона как у QLabel
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.TextAntialiasing)
        
        # Настраиваем шрифт
        font = painter.font()
        font.setBold(True)
        font.setPointSize(14)
        painter.setFont(font)
        painter.setPen(QColor("#555555")) # Цвет текста
        
        # Рисуем текст по центру
        text = "No Cover"
        rect = QRectF(0, 0, 225, 225)
        painter.drawText(rect, Qt.AlignCenter, text)
        
        painter.end()
        
        self.cover_label.setPixmap(pixmap)
