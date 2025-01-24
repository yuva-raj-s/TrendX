import sys
import requests
from bs4 import BeautifulSoup
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QLabel, QPushButton, QTextEdit, QComboBox, QFrame, QSplitter)
from PyQt5.QtGui import QFont, QIcon, QPixmap, QPainter, QColor, QLinearGradient
from PyQt5.QtCore import Qt, QPropertyAnimation, QEasingCurve, QTimer, QThread, pyqtSignal
from PyQt5.QtChart import QChart, QChartView, QPieSeries, QBarSeries, QBarSet
from PyQt5.QtGui import QPixmap, QImage, qRgb
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from wordcloud import WordCloud
import numpy as np

class TrendingTopicsFetcher(QThread):
    topics_fetched = pyqtSignal(list)

    def __init__(self, url):
        super().__init__()
        self.url = url

    def run(self):
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                          '(KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

        try:
            response = requests.get(self.url, headers=headers)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')
            trending_topics = soup.select('ol.trend-card__list a')

            topics = [topic.text.strip() for topic in trending_topics[:30]]
            self.topics_fetched.emit(topics)
        except Exception as e:
            print(f"Failed to fetch trending topics: {e}")
            self.topics_fetched.emit([])

class GradientWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.gradient = QLinearGradient(0, 0, 0, self.height())
        self.gradient.setColorAt(0, QColor("#4a148c"))
        self.gradient.setColorAt(1, QColor("#7c43bd"))

    def paintEvent(self, event):
        painter = QPainter(self)
        self.gradient.setFinalStop(0, self.height())
        painter.fillRect(self.rect(), self.gradient)

class AnimatedButton(QPushButton):
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.setStyleSheet("""
            QPushButton {
                background-color: #6200ea;
                color: white;
                border: none;
                padding: 10px 20px;
                font-size: 14px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #7c43bd;
            }
        """)
        self.animation = QPropertyAnimation(self, b"geometry")
        self.animation.setDuration(100)
        self.animation.setEasingCurve(QEasingCurve.OutQuad)

    def enterEvent(self, event):
        self.animation.setStartValue(self.geometry())
        self.animation.setEndValue(self.geometry().adjusted(-2, -2, 2, 2))
        self.animation.start()

    def leaveEvent(self, event):
        self.animation.setStartValue(self.geometry())
        self.animation.setEndValue(self.geometry().adjusted(2, 2, -2, -2))
        self.animation.start()

class TrendAnalyzerApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle('TrendX - Twitter Trend Analyzer')
        self.setGeometry(100, 100, 1200, 800)
        self.setWindowIcon(QIcon('icon.png'))

        central_widget = GradientWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)

        # Header
        header_widget = QWidget()
        header_layout = QHBoxLayout(header_widget)

        logo_label = QLabel()
        logo_pixmap = QPixmap('logo_white.png').scaledToWidth(300, Qt.SmoothTransformation)  # Adjust width as needed
        logo_label.setPixmap(logo_pixmap)
        header_layout.addWidget(logo_label)

        header_label = QLabel('TrendX - Twitter Trend Analyzer')
        header_label.setStyleSheet("""
            font-size: 24px;
            color: white;
            padding: 20px;
            background-color: rgba(0, 0, 0, 0.2);
            border-radius: 10px;
        """)
        header_label.setAlignment(Qt.AlignCenter)
        header_layout.addWidget(header_label)

        main_layout.addWidget(header_widget)

        # Content
        content = QSplitter(Qt.Horizontal)
        main_layout.addWidget(content)

        # Left panel
        left_panel = QFrame()
        left_panel.setStyleSheet("""
            QFrame {
                background-color: rgba(255, 255, 255, 0.9);
                border-radius: 10px;
                padding: 10px;
            }
        """)
        left_layout = QVBoxLayout(left_panel)

        self.location_combo = QComboBox()
        self.location_combo.addItems(['Worldwide', 'India'])
        self.location_combo.setStyleSheet("""
            QComboBox {
                font-size: 16px;
                padding: 5px;
                border: 1px solid #ccc;
                border-radius: 5px;
            }
        """)
        left_layout.addWidget(self.location_combo)

        self.fetch_button = AnimatedButton('Fetch Trending Topics')
        self.fetch_button.clicked.connect(self.fetch_trending_topics)
        left_layout.addWidget(self.fetch_button)

        self.topics_text = QTextEdit()
        self.topics_text.setReadOnly(True)
        self.topics_text.setStyleSheet("""
            QTextEdit {
                font-size: 14px;
                border: none;
                background-color: transparent;
            }
        """)
        left_layout.addWidget(self.topics_text)

        content.addWidget(left_panel)

        # Right panel
        right_panel = QFrame()
        right_panel.setStyleSheet("""
            QFrame {
                background-color: rgba(255, 255, 255, 0.9);
                border-radius: 10px;
                padding: 10px;
            }
        """)
        right_layout = QVBoxLayout(right_panel)

        self.chart_view = QChartView()
        self.chart_view.setRenderHint(QPainter.Antialiasing)
        right_layout.addWidget(self.chart_view)

        self.wordcloud_canvas = FigureCanvas(plt.figure(figsize=(5, 5)))
        right_layout.addWidget(self.wordcloud_canvas)

        content.addWidget(right_panel)

        # Footer
        footer = QLabel('Created by Sooraj GV and Yuvaraj S')
        footer.setStyleSheet("""
            font-size: 20px;
            color: white;
            padding: 10px;
        """)
        footer.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(footer)
        self.fetcher = None

    def fetch_trending_topics(self):
        location = self.location_combo.currentText()
        url = "https://trends24.in/india" if location == "India" else "https://trends24.in"
        
        self.fetcher = TrendingTopicsFetcher(url)
        self.fetcher.topics_fetched.connect(self.display_topics)
        self.fetcher.start()

        self.fetch_button.setEnabled(False)
        QTimer.singleShot(2000, lambda: self.fetch_button.setEnabled(True))

    def display_topics(self, topics):
        if topics:
            self.topics_text.clear()
            for idx, topic in enumerate(topics, start=1):
                self.topics_text.append(f"{idx}. {topic}")
            
            self.update_chart(topics[:10])
            self.update_wordcloud(topics)
        else:
            self.topics_text.setText("No trending topics found.")

    def update_chart(self, topics):
        series = QPieSeries()
        for topic in topics:
            series.append(topic, 1)

        chart = QChart()
        chart.addSeries(series)
        chart.setTitle("Top 10 Trending Topics")
        chart.setAnimationOptions(QChart.SeriesAnimations)

        self.chart_view.setChart(chart)

    def update_wordcloud(self, topics):
        text = ' '.join(topics)
        wordcloud = WordCloud(width=400, height=400, background_color='white').generate(text)

        self.wordcloud_canvas.figure.clear()
        ax = self.wordcloud_canvas.figure.add_subplot(111)
        ax.imshow(wordcloud, interpolation='bilinear')
        ax.axis('off')
        self.wordcloud_canvas.draw()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = TrendAnalyzerApp()
    ex.show()
    sys.exit(app.exec_())