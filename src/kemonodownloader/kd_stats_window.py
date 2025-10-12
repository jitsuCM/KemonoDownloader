"""
Statistics window with comprehensive charts and analytics for downloaded files
"""

import os
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget,
    QLabel, QWidget, QScrollArea, QGridLayout, QGroupBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from datetime import datetime
import sqlite3
import numpy as np

try:
    import matplotlib
    matplotlib.use('Qt5Agg')
    from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
    from matplotlib.figure import Figure
    import matplotlib.pyplot as plt
    from matplotlib.colors import LogNorm
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False

from kemonodownloader.kd_stats import StatsDatabase
from kemonodownloader.kd_language import translate


class StatsWindow(QDialog):
    """Main statistics window with multiple tabs for comprehensive analytics"""

    def __init__(self, parent, base_folder):
        super().__init__(parent)
        self.base_folder = base_folder
        self.stats_db_path = os.path.join(base_folder, "Cache", "stats.db")
        self.stats_db = StatsDatabase(self.stats_db_path)

        self.setWindowTitle(translate("statistics_window_title"))
        self.setGeometry(150, 150, 1400, 900)
        self.setModal(False)

        self.setup_ui()
        self.load_all_data()

    def setup_ui(self):
        """Setup the UI with tab widget"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)

        # Apply dark theme
        self.setStyleSheet("""
            QDialog {
                background-color: #1A2A44;
            }
            QLabel {
                color: white;
            }
            QGroupBox {
                color: white;
                border: 2px solid #3A4B6A;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
                font-weight: bold;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """)

        # Tab widget
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane {
                border: none;
                background: #1A2A44;
            }
            QTabBar::tab {
                background: #3A4B6A;
                color: white;
                padding: 10px 20px;
                margin-right: 2px;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                min-width: 100px;
            }
            QTabBar::tab:selected {
                background: #4A5B7A;
                color: white;
            }
            QTabBar::tab:!selected {
                margin-top: 2px;
            }
        """)

        # Add all tabs
        if HAS_MATPLOTLIB:
            self.general_tab = self.create_general_tab()
            self.tabs.addTab(self.general_tab, translate("stats_general_tab"))

            self.images_tab = self.create_images_tab()
            self.tabs.addTab(self.images_tab, translate("stats_images_tab"))

            self.animations_tab = self.create_animations_tab()
            self.tabs.addTab(self.animations_tab, "Animations")

            self.videos_tab = self.create_videos_tab()
            self.tabs.addTab(self.videos_tab, translate("stats_videos_tab"))

            self.audio_tab = self.create_audio_tab()
            self.tabs.addTab(self.audio_tab, "Audio")

            self.creators_tab = self.create_creators_tab()
            self.tabs.addTab(self.creators_tab, translate("stats_creators_tab"))

            self.advanced_tab = self.create_advanced_tab()
            self.tabs.addTab(self.advanced_tab, "Advanced")
        else:
            # Fallback if matplotlib not installed
            fallback_tab = QWidget()
            fallback_layout = QVBoxLayout(fallback_tab)
            label = QLabel("Install matplotlib for comprehensive statistics: pip install matplotlib")
            label.setStyleSheet("color: #FF6B6B; font-style: italic; font-size: 14px;")
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            fallback_layout.addWidget(label)
            self.tabs.addTab(fallback_tab, "Statistics")

        layout.addWidget(self.tabs)

    def create_scroll_area(self):
        """Create a styled scroll area"""
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background: transparent;
            }
            QScrollBar:vertical {
                background: #2A3B5A;
                width: 12px;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical {
                background: #4A5B7A;
                border-radius: 6px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                border: none;
                background: none;
            }
            QScrollBar:horizontal {
                background: #2A3B5A;
                height: 12px;
                border-radius: 6px;
            }
            QScrollBar::handle:horizontal {
                background: #4A5B7A;
                border-radius: 6px;
            }
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
                border: none;
                background: none;
            }
        """)
        return scroll

    def create_general_tab(self):
        """Create the general statistics tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(20)

        scroll = self.create_scroll_area()
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setSpacing(20)

        # Summary stats group
        summary_group = QGroupBox("Summary Statistics")
        summary_layout = QGridLayout(summary_group)
        summary_layout.setSpacing(15)

        # Create stat labels
        self.total_files_label = self.create_stat_label("Total Files:", "0")
        self.total_size_label = self.create_stat_label("Total Size:", "0 MB")
        self.total_images_label = self.create_stat_label("Total Images:", "0")
        self.total_videos_label = self.create_stat_label("Total Videos:", "0")
        self.unique_creators_label = self.create_stat_label("Unique Creators:", "0")
        self.unique_posts_label = self.create_stat_label("Unique Posts:", "0")
        self.avg_file_size_label = self.create_stat_label("Avg File Size:", "0 MB")
        self.animated_count_label = self.create_stat_label("Animated Images:", "0")

        # Add to grid
        summary_layout.addWidget(self.total_files_label[0], 0, 0)
        summary_layout.addWidget(self.total_files_label[1], 0, 1)
        summary_layout.addWidget(self.total_size_label[0], 0, 2)
        summary_layout.addWidget(self.total_size_label[1], 0, 3)

        summary_layout.addWidget(self.total_images_label[0], 1, 0)
        summary_layout.addWidget(self.total_images_label[1], 1, 1)
        summary_layout.addWidget(self.total_videos_label[0], 1, 2)
        summary_layout.addWidget(self.total_videos_label[1], 1, 3)

        summary_layout.addWidget(self.unique_creators_label[0], 2, 0)
        summary_layout.addWidget(self.unique_creators_label[1], 2, 1)
        summary_layout.addWidget(self.unique_posts_label[0], 2, 2)
        summary_layout.addWidget(self.unique_posts_label[1], 2, 3)

        summary_layout.addWidget(self.avg_file_size_label[0], 3, 0)
        summary_layout.addWidget(self.avg_file_size_label[1], 3, 1)
        summary_layout.addWidget(self.animated_count_label[0], 3, 2)
        summary_layout.addWidget(self.animated_count_label[1], 3, 3)

        content_layout.addWidget(summary_group)

        # Historical plots group
        plots_group = QGroupBox("Historical Trends")
        plots_layout = QVBoxLayout(plots_group)

        # File count over time
        self.file_count_canvas = FigureCanvas(Figure(figsize=(12, 4)))
        plots_layout.addWidget(self.file_count_canvas)

        # Total size over time
        self.total_size_canvas = FigureCanvas(Figure(figsize=(12, 4)))
        plots_layout.addWidget(self.total_size_canvas)

        content_layout.addWidget(plots_group)

        # Media type distribution
        media_group = QGroupBox("Media Type Distribution")
        media_layout = QHBoxLayout(media_group)

        self.media_pie_canvas = FigureCanvas(Figure(figsize=(6, 5)))
        media_layout.addWidget(self.media_pie_canvas)

        self.file_size_dist_canvas = FigureCanvas(Figure(figsize=(6, 5)))
        media_layout.addWidget(self.file_size_dist_canvas)

        content_layout.addWidget(media_group)

        content_layout.addStretch()
        scroll.setWidget(content_widget)
        layout.addWidget(scroll)

        return tab

    def create_images_tab(self):
        """Create the images statistics tab with comprehensive charts"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        scroll = self.create_scroll_area()
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setSpacing(10)

        # Image stats summary
        stats_group = QGroupBox("Image Statistics")
        stats_layout = QGridLayout(stats_group)

        self.img_count_label = self.create_stat_label("Total Images:", "0")
        self.img_size_label = self.create_stat_label("Total Size:", "0 GB")
        self.img_avg_res_label = self.create_stat_label("Avg Resolution:", "0x0")
        self.img_animated_label = self.create_stat_label("Animated:", "0")

        stats_layout.addWidget(self.img_count_label[0], 0, 0)
        stats_layout.addWidget(self.img_count_label[1], 0, 1)
        stats_layout.addWidget(self.img_size_label[0], 0, 2)
        stats_layout.addWidget(self.img_size_label[1], 0, 3)
        stats_layout.addWidget(self.img_avg_res_label[0], 1, 0)
        stats_layout.addWidget(self.img_avg_res_label[1], 1, 1)
        stats_layout.addWidget(self.img_animated_label[0], 1, 2)
        stats_layout.addWidget(self.img_animated_label[1], 1, 3)

        content_layout.addWidget(stats_group)

        # Resolution heatmap and scatter
        res_group = QGroupBox("Resolution Analysis")
        res_layout = QHBoxLayout(res_group)

        self.img_res_heatmap_canvas = FigureCanvas(Figure(figsize=(7, 6)))
        res_layout.addWidget(self.img_res_heatmap_canvas)

        self.img_res_scatter_canvas = FigureCanvas(Figure(figsize=(7, 6)))
        res_layout.addWidget(self.img_res_scatter_canvas)

        content_layout.addWidget(res_group)

        # Format and color mode
        format_group = QGroupBox("Format & Color Mode Distribution")
        format_layout = QHBoxLayout(format_group)

        self.img_format_canvas = FigureCanvas(Figure(figsize=(6, 5)))
        format_layout.addWidget(self.img_format_canvas)

        self.img_color_canvas = FigureCanvas(Figure(figsize=(6, 5)))
        format_layout.addWidget(self.img_color_canvas)

        content_layout.addWidget(format_group)

        # Size distributions
        size_group = QGroupBox("File Size Distribution")
        size_layout = QVBoxLayout(size_group)

        self.img_size_hist_canvas = FigureCanvas(Figure(figsize=(12, 4)))
        size_layout.addWidget(self.img_size_hist_canvas)

        content_layout.addWidget(size_group)

        content_layout.addStretch()
        scroll.setWidget(content_widget)
        layout.addWidget(scroll)

        return tab

    def create_animations_tab(self):
        """Create the animations statistics tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        scroll = self.create_scroll_area()
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setSpacing(10)

        # Animation stats summary
        stats_group = QGroupBox("Animation Statistics")
        stats_layout = QGridLayout(stats_group)

        self.anim_count_label = self.create_stat_label("Total Animations:", "0")
        self.anim_size_label = self.create_stat_label("Total Size:", "0 MB")
        self.anim_avg_duration_label = self.create_stat_label("Avg Duration:", "0s")
        self.anim_avg_fps_label = self.create_stat_label("Avg FPS:", "0")

        stats_layout.addWidget(self.anim_count_label[0], 0, 0)
        stats_layout.addWidget(self.anim_count_label[1], 0, 1)
        stats_layout.addWidget(self.anim_size_label[0], 0, 2)
        stats_layout.addWidget(self.anim_size_label[1], 0, 3)
        stats_layout.addWidget(self.anim_avg_duration_label[0], 1, 0)
        stats_layout.addWidget(self.anim_avg_duration_label[1], 1, 1)
        stats_layout.addWidget(self.anim_avg_fps_label[0], 1, 2)
        stats_layout.addWidget(self.anim_avg_fps_label[1], 1, 3)

        content_layout.addWidget(stats_group)

        # Duration and FPS distributions
        dist_group = QGroupBox("Duration & Frame Rate")
        dist_layout = QHBoxLayout(dist_group)

        self.anim_duration_canvas = FigureCanvas(Figure(figsize=(6, 5)))
        dist_layout.addWidget(self.anim_duration_canvas)

        self.anim_fps_canvas = FigureCanvas(Figure(figsize=(6, 5)))
        dist_layout.addWidget(self.anim_fps_canvas)

        content_layout.addWidget(dist_group)

        # Frame count distribution
        frames_group = QGroupBox("Frame Count Distribution")
        frames_layout = QVBoxLayout(frames_group)

        self.anim_frames_canvas = FigureCanvas(Figure(figsize=(12, 5)))
        frames_layout.addWidget(self.anim_frames_canvas)

        content_layout.addWidget(frames_group)

        # Format breakdown
        format_group = QGroupBox("Animation Format Distribution")
        format_layout = QHBoxLayout(format_group)

        self.anim_format_canvas = FigureCanvas(Figure(figsize=(6, 5)))
        format_layout.addWidget(self.anim_format_canvas)

        self.anim_size_by_format_canvas = FigureCanvas(Figure(figsize=(6, 5)))
        format_layout.addWidget(self.anim_size_by_format_canvas)

        content_layout.addWidget(format_group)

        content_layout.addStretch()
        scroll.setWidget(content_widget)
        layout.addWidget(scroll)

        return tab

    def create_videos_tab(self):
        """Create the videos statistics tab with comprehensive charts"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        scroll = self.create_scroll_area()
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setSpacing(10)

        # Video stats summary
        stats_group = QGroupBox("Video Statistics")
        stats_layout = QGridLayout(stats_group)

        self.vid_count_label = self.create_stat_label("Total Videos:", "0")
        self.vid_size_label = self.create_stat_label("Total Size:", "0 GB")
        self.vid_duration_label = self.create_stat_label("Avg Duration:", "0s")
        self.vid_with_audio_label = self.create_stat_label("With Audio:", "0")

        stats_layout.addWidget(self.vid_count_label[0], 0, 0)
        stats_layout.addWidget(self.vid_count_label[1], 0, 1)
        stats_layout.addWidget(self.vid_size_label[0], 0, 2)
        stats_layout.addWidget(self.vid_size_label[1], 0, 3)
        stats_layout.addWidget(self.vid_duration_label[0], 1, 0)
        stats_layout.addWidget(self.vid_duration_label[1], 1, 1)
        stats_layout.addWidget(self.vid_with_audio_label[0], 1, 2)
        stats_layout.addWidget(self.vid_with_audio_label[1], 1, 3)

        content_layout.addWidget(stats_group)

        # Resolution heatmap
        res_group = QGroupBox("Video Resolution Heatmap")
        res_layout = QHBoxLayout(res_group)

        self.vid_res_heatmap_canvas = FigureCanvas(Figure(figsize=(7, 6)))
        res_layout.addWidget(self.vid_res_heatmap_canvas)

        self.vid_res_scatter_canvas = FigureCanvas(Figure(figsize=(7, 6)))
        res_layout.addWidget(self.vid_res_scatter_canvas)

        content_layout.addWidget(res_group)

        # Codecs and formats
        codec_group = QGroupBox("Codec & Format Distribution")
        codec_layout = QHBoxLayout(codec_group)

        self.vid_codec_canvas = FigureCanvas(Figure(figsize=(6, 5)))
        codec_layout.addWidget(self.vid_codec_canvas)

        self.vid_container_canvas = FigureCanvas(Figure(figsize=(6, 5)))
        codec_layout.addWidget(self.vid_container_canvas)

        content_layout.addWidget(codec_group)

        # Bitrate analysis
        bitrate_group = QGroupBox("Video Bitrate Distribution")
        bitrate_layout = QVBoxLayout(bitrate_group)

        self.vid_bitrate_hist_canvas = FigureCanvas(Figure(figsize=(12, 5)))
        bitrate_layout.addWidget(self.vid_bitrate_hist_canvas)

        content_layout.addWidget(bitrate_group)

        # Duration and FPS
        perf_group = QGroupBox("Duration & Frame Rate")
        perf_layout = QHBoxLayout(perf_group)

        self.vid_duration_hist_canvas = FigureCanvas(Figure(figsize=(6, 5)))
        perf_layout.addWidget(self.vid_duration_hist_canvas)

        self.vid_fps_hist_canvas = FigureCanvas(Figure(figsize=(6, 5)))
        perf_layout.addWidget(self.vid_fps_hist_canvas)

        content_layout.addWidget(perf_group)

        content_layout.addStretch()
        scroll.setWidget(content_widget)
        layout.addWidget(scroll)

        return tab

    def create_audio_tab(self):
        """Create the audio statistics tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        scroll = self.create_scroll_area()
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setSpacing(10)

        # Audio bitrate
        bitrate_group = QGroupBox("Audio Bitrate Distribution")
        bitrate_layout = QVBoxLayout(bitrate_group)

        self.aud_bitrate_hist_canvas = FigureCanvas(Figure(figsize=(12, 5)))
        bitrate_layout.addWidget(self.aud_bitrate_hist_canvas)

        content_layout.addWidget(bitrate_group)

        # Audio properties
        props_group = QGroupBox("Audio Properties")
        props_layout = QHBoxLayout(props_group)

        self.audio_channels_canvas = FigureCanvas(Figure(figsize=(6, 5)))
        props_layout.addWidget(self.audio_channels_canvas)

        self.audio_sample_rate_canvas = FigureCanvas(Figure(figsize=(6, 5)))
        props_layout.addWidget(self.audio_sample_rate_canvas)

        content_layout.addWidget(props_group)

        content_layout.addStretch()
        scroll.setWidget(content_widget)
        layout.addWidget(scroll)

        return tab

    def create_creators_tab(self):
        """Create the creators statistics tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        scroll = self.create_scroll_area()
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setSpacing(10)

        # Top creators
        top_group = QGroupBox("Top Creators")
        top_layout = QHBoxLayout(top_group)

        self.creators_by_count_canvas = FigureCanvas(Figure(figsize=(7, 6)))
        top_layout.addWidget(self.creators_by_count_canvas)

        self.creators_by_size_canvas = FigureCanvas(Figure(figsize=(7, 6)))
        top_layout.addWidget(self.creators_by_size_canvas)

        content_layout.addWidget(top_group)

        # Distribution
        dist_group = QGroupBox("Files per Creator Distribution")
        dist_layout = QVBoxLayout(dist_group)

        self.files_per_creator_canvas = FigureCanvas(Figure(figsize=(12, 5)))
        dist_layout.addWidget(self.files_per_creator_canvas)

        content_layout.addWidget(dist_group)

        # Average file size per creator
        avg_group = QGroupBox("Average File Size by Creator")
        avg_layout = QVBoxLayout(avg_group)

        self.avg_size_per_creator_canvas = FigureCanvas(Figure(figsize=(12, 5)))
        avg_layout.addWidget(self.avg_size_per_creator_canvas)

        content_layout.addWidget(avg_group)

        content_layout.addStretch()
        scroll.setWidget(content_widget)
        layout.addWidget(scroll)

        return tab

    def create_advanced_tab(self):
        """Create advanced analytics tab with correlations"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        scroll = self.create_scroll_area()
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setSpacing(10)

        # File size vs resolution correlation
        corr_group = QGroupBox("Size vs Resolution Correlation")
        corr_layout = QHBoxLayout(corr_group)

        self.size_vs_pixels_canvas = FigureCanvas(Figure(figsize=(7, 6)))
        corr_layout.addWidget(self.size_vs_pixels_canvas)

        self.size_vs_res_heatmap_canvas = FigureCanvas(Figure(figsize=(7, 6)))
        corr_layout.addWidget(self.size_vs_res_heatmap_canvas)

        content_layout.addWidget(corr_group)

        # Video bitrate vs duration
        vid_corr_group = QGroupBox("Video: Bitrate vs Duration")
        vid_corr_layout = QHBoxLayout(vid_corr_group)

        self.bitrate_vs_duration_canvas = FigureCanvas(Figure(figsize=(7, 6)))
        vid_corr_layout.addWidget(self.bitrate_vs_duration_canvas)

        self.bitrate_vs_size_canvas = FigureCanvas(Figure(figsize=(7, 6)))
        vid_corr_layout.addWidget(self.bitrate_vs_size_canvas)

        content_layout.addWidget(vid_corr_group)

        # Downloads over time by media type
        timeline_group = QGroupBox("Download Timeline by Media Type")
        timeline_layout = QVBoxLayout(timeline_group)

        self.timeline_stacked_canvas = FigureCanvas(Figure(figsize=(12, 5)))
        timeline_layout.addWidget(self.timeline_stacked_canvas)

        content_layout.addWidget(timeline_group)

        # Aspect ratio distribution
        aspect_group = QGroupBox("Aspect Ratio Distribution")
        aspect_layout = QVBoxLayout(aspect_group)

        self.aspect_ratio_canvas = FigureCanvas(Figure(figsize=(12, 5)))
        aspect_layout.addWidget(self.aspect_ratio_canvas)

        content_layout.addWidget(aspect_group)

        content_layout.addStretch()
        scroll.setWidget(content_widget)
        layout.addWidget(scroll)

        return tab

    def create_stat_label(self, title, value):
        """Create a pair of labels for displaying a statistic"""
        title_label = QLabel(title)
        title_label.setFont(QFont("Poppins", 12))
        title_label.setStyleSheet("color: #A0B0C0;")

        value_label = QLabel(value)
        value_label.setFont(QFont("Poppins", 16, QFont.Weight.Bold))
        value_label.setStyleSheet("color: #FFFFFF;")

        return (title_label, value_label)

    def load_all_data(self):
        """Load and display all statistics data"""
        if not HAS_MATPLOTLIB:
            return

        self.load_general_data()
        self.load_images_data()
        self.load_animations_data()
        self.load_videos_data()
        self.load_audio_data()
        self.load_creators_data()
        self.load_advanced_data()

    def load_general_data(self):
        """Load general statistics"""
        stats = self.stats_db.get_global_stats()

        if stats:
            self.total_files_label[1].setText(f"{stats['total_files']:,}")
            self.total_size_label[1].setText(self.format_bytes(stats['total_size']))
            self.total_images_label[1].setText(f"{stats['image_count']:,}")
            self.total_videos_label[1].setText(f"{stats['video_count']:,}")
            self.unique_creators_label[1].setText(f"{stats['unique_creators']:,}")
            self.unique_posts_label[1].setText(f"{stats['unique_posts']:,}")
            self.avg_file_size_label[1].setText(self.format_bytes(stats['avg_file_size']))
            self.animated_count_label[1].setText(f"{stats['animated_count']:,}")

        self.plot_file_count_history()
        self.plot_total_size_history()
        self.plot_media_type_pie()
        self.plot_file_size_distribution()

    def load_images_data(self):
        """Load image statistics and create visualizations"""
        # Get image stats
        with sqlite3.connect(self.stats_db_path) as conn:
            cursor = conn.execute("""
                SELECT COUNT(*), SUM(file_size), AVG(width), AVG(height),
                       COUNT(CASE WHEN is_animated = 1 THEN 1 END)
                FROM file_metadata
                WHERE media_type = 'image'
            """)
            img_stats = cursor.fetchone()

        if img_stats and img_stats[0] > 0:
            self.img_count_label[1].setText(f"{img_stats[0]:,}")
            self.img_size_label[1].setText(self.format_bytes(img_stats[1] or 0))
            avg_w = int(img_stats[2] or 0)
            avg_h = int(img_stats[3] or 0)
            self.img_avg_res_label[1].setText(f"{avg_w}x{avg_h}")
            self.img_animated_label[1].setText(f"{img_stats[4]:,}")

        self.plot_image_resolution_heatmap()
        self.plot_image_resolution_scatter()
        self.plot_image_format_distribution()
        self.plot_image_color_mode()
        self.plot_image_size_histogram()

    def load_animations_data(self):
        """Load animation statistics and create visualizations"""
        anim_stats = self.stats_db.get_animation_stats()

        if anim_stats and anim_stats['total_animations'] > 0:
            self.anim_count_label[1].setText(f"{anim_stats['total_animations']:,}")
            self.anim_size_label[1].setText(self.format_bytes(anim_stats['total_size']))
            self.anim_avg_duration_label[1].setText(f"{anim_stats['avg_duration']:.2f}s")
            self.anim_avg_fps_label[1].setText(f"{anim_stats['avg_fps']:.1f}")

        self.plot_animation_duration()
        self.plot_animation_fps()
        self.plot_animation_frame_count()
        self.plot_animation_format_distribution()
        self.plot_animation_size_by_format()

    def load_videos_data(self):
        """Load video statistics and create visualizations"""
        vid_stats = self.stats_db.get_video_stats()

        if vid_stats and vid_stats['total_videos'] > 0:
            self.vid_count_label[1].setText(f"{vid_stats['total_videos']:,}")
            self.vid_size_label[1].setText(self.format_bytes(vid_stats['total_size']))
            self.vid_duration_label[1].setText(f"{vid_stats['avg_duration']:.1f}s")
            self.vid_with_audio_label[1].setText(f"{vid_stats['videos_with_audio']:,}")

        self.plot_video_resolution_heatmap()
        self.plot_video_resolution_scatter()
        self.plot_video_codec_distribution()
        self.plot_video_container_distribution()
        self.plot_video_bitrate_histogram()
        self.plot_video_duration_histogram()
        self.plot_video_fps_histogram()

    def load_audio_data(self):
        """Load audio statistics and create visualizations"""
        self.plot_audio_bitrate_histogram()
        self.plot_audio_channels()
        self.plot_audio_sample_rate()

    def load_creators_data(self):
        """Load creator statistics"""
        self.plot_top_creators_by_count()
        self.plot_top_creators_by_size()
        self.plot_files_per_creator_distribution()
        self.plot_avg_size_per_creator()

    def load_advanced_data(self):
        """Load advanced analytics"""
        self.plot_size_vs_pixels()
        self.plot_size_vs_resolution_heatmap()
        self.plot_bitrate_vs_duration()
        self.plot_bitrate_vs_size()
        self.plot_timeline_stacked()
        self.plot_aspect_ratio_distribution()

    def format_bytes(self, bytes_size):
        """Format bytes into human-readable size"""
        if bytes_size == 0 or bytes_size is None:
            return "0 B"

        units = ['B', 'KB', 'MB', 'GB', 'TB']
        unit_index = 0
        size = float(bytes_size)

        while size >= 1024 and unit_index < len(units) - 1:
            size /= 1024
            unit_index += 1

        return f"{size:.2f} {units[unit_index]}"

    # ==================== GENERAL TAB PLOTS ====================

    def plot_file_count_history(self):
        """Plot historical file count over time"""
        with sqlite3.connect(self.stats_db_path) as conn:
            cursor = conn.execute("""
                SELECT DATE(download_timestamp) as date, COUNT(*) as count
                FROM file_metadata
                WHERE download_timestamp IS NOT NULL
                GROUP BY DATE(download_timestamp)
                ORDER BY date
            """)
            data = cursor.fetchall()

        if not data:
            return

        dates = [datetime.strptime(row[0], '%Y-%m-%d') for row in data]
        counts = [row[1] for row in data]
        cumulative_counts = np.cumsum(counts)

        fig = self.file_count_canvas.figure
        fig.clear()
        ax = fig.add_subplot(111)
        ax.plot(dates, cumulative_counts, color='#4A9EFF', linewidth=2.5, marker='o', markersize=5)
        ax.fill_between(dates, cumulative_counts, alpha=0.3, color='#4A9EFF')
        ax.set_title('Total Files Downloaded Over Time', color='white', fontsize=14, pad=15, fontweight='bold')
        ax.set_xlabel('Date', color='white', fontsize=11)
        ax.set_ylabel('Total Files', color='white', fontsize=11)
        ax.grid(True, alpha=0.2, color='white', linestyle='--')
        ax.tick_params(colors='white', labelsize=9)
        fig.patch.set_facecolor('#1A2A44')
        ax.set_facecolor('#2A3B5A')
        fig.autofmt_xdate()
        fig.tight_layout(pad=2.0, rect=[0, 0, 1, 0.96])
        self.file_count_canvas.draw()

    def plot_total_size_history(self):
        """Plot historical total size over time"""
        with sqlite3.connect(self.stats_db_path) as conn:
            cursor = conn.execute("""
                SELECT DATE(download_timestamp) as date, SUM(file_size) as total_size
                FROM file_metadata
                WHERE download_timestamp IS NOT NULL AND file_size IS NOT NULL
                GROUP BY DATE(download_timestamp)
                ORDER BY date
            """)
            data = cursor.fetchall()

        if not data:
            return

        dates = [datetime.strptime(row[0], '%Y-%m-%d') for row in data]
        sizes = [row[1] for row in data]
        cumulative_sizes_gb = np.cumsum(sizes) / (1024**3)

        fig = self.total_size_canvas.figure
        fig.clear()
        ax = fig.add_subplot(111)
        ax.plot(dates, cumulative_sizes_gb, color='#FF6B9D', linewidth=2.5, marker='o', markersize=5)
        ax.fill_between(dates, cumulative_sizes_gb, alpha=0.3, color='#FF6B9D')
        ax.set_title('Total Downloaded Size Over Time', color='white', fontsize=14, pad=15, fontweight='bold')
        ax.set_xlabel('Date', color='white', fontsize=11)
        ax.set_ylabel('Total Size (GB)', color='white', fontsize=11)
        ax.grid(True, alpha=0.2, color='white', linestyle='--')
        ax.tick_params(colors='white', labelsize=9)
        fig.patch.set_facecolor('#1A2A44')
        ax.set_facecolor('#2A3B5A')
        fig.autofmt_xdate()
        fig.tight_layout(pad=2.0, rect=[0, 0, 1, 0.96])
        self.total_size_canvas.draw()

    def plot_media_type_pie(self):
        """Plot media type distribution pie chart"""
        with sqlite3.connect(self.stats_db_path) as conn:
            cursor = conn.execute("""
                SELECT media_type, COUNT(*) as count
                FROM file_metadata
                GROUP BY media_type
            """)
            data = cursor.fetchall()

        if not data:
            return

        labels = [row[0].capitalize() if row[0] else 'Unknown' for row in data]
        sizes = [row[1] for row in data]
        colors = ['#4A9EFF', '#FF6B9D', '#4ECDC4', '#FFD93D', '#95E1D3']

        fig = self.media_pie_canvas.figure
        fig.clear()
        ax = fig.add_subplot(111)
        wedges, texts, autotexts = ax.pie(sizes, labels=labels, autopct='%1.1f%%',
                                           colors=colors, startangle=90)
        for text in texts:
            text.set_color('white')
            text.set_fontsize(11)
        for autotext in autotexts:
            autotext.set_color('white')
            autotext.set_fontsize(10)
            autotext.set_weight('bold')
        ax.set_title('Media Type Distribution', color='white', fontsize=13, pad=15, fontweight='bold')
        fig.patch.set_facecolor('#1A2A44')
        fig.tight_layout(pad=2.0, rect=[0, 0, 1, 0.96])
        self.media_pie_canvas.draw()

    def plot_file_size_distribution(self):
        """Plot file size distribution histogram"""
        with sqlite3.connect(self.stats_db_path) as conn:
            cursor = conn.execute("""
                SELECT file_size
                FROM file_metadata
                WHERE file_size IS NOT NULL AND file_size > 0
            """)
            sizes = [row[0] / (1024**2) for row in cursor.fetchall()]  # Convert to MB

        if not sizes:
            return

        fig = self.file_size_dist_canvas.figure
        fig.clear()
        ax = fig.add_subplot(111)
        ax.hist(sizes, bins=50, color='#9B59B6', alpha=0.7, edgecolor='white')
        ax.set_title('File Size Distribution', color='white', fontsize=13, pad=15, fontweight='bold')
        ax.set_xlabel('File Size (MB)', color='white', fontsize=11)
        ax.set_ylabel('Count', color='white', fontsize=11)
        ax.grid(True, alpha=0.2, color='white', linestyle='--', axis='y')
        ax.tick_params(colors='white', labelsize=9)
        fig.patch.set_facecolor('#1A2A44')
        ax.set_facecolor('#2A3B5A')
        fig.tight_layout(pad=2.0, rect=[0, 0, 1, 0.96])
        self.file_size_dist_canvas.draw()

    # ==================== IMAGES TAB PLOTS ====================

    def plot_image_resolution_heatmap(self):
        """Plot 2D histogram heatmap of image resolutions"""
        with sqlite3.connect(self.stats_db_path) as conn:
            cursor = conn.execute("""
                SELECT width, height
                FROM file_metadata
                WHERE media_type = 'image' AND width IS NOT NULL AND height IS NOT NULL
            """)
            data = cursor.fetchall()

        if not data:
            return

        widths = [row[0] for row in data]
        heights = [row[1] for row in data]

        fig = self.img_res_heatmap_canvas.figure
        fig.clear()
        ax = fig.add_subplot(111)

        h, xedges, yedges = np.histogram2d(widths, heights, bins=50)
        im = ax.imshow(h.T, origin='lower', aspect='auto', cmap='hot',
                      extent=[xedges[0], xedges[-1], yedges[0], yedges[-1]],
                      interpolation='gaussian', norm=LogNorm())

        ax.set_title('Image Resolution Heatmap', color='white', fontsize=13, pad=15, fontweight='bold')
        ax.set_xlabel('Width (px)', color='white', fontsize=11)
        ax.set_ylabel('Height (px)', color='white', fontsize=11)
        ax.tick_params(colors='white', labelsize=9)

        cbar = fig.colorbar(im, ax=ax, format='%.0f')
        cbar.set_label('Count', color='white', fontsize=10)
        cbar.ax.tick_params(colors='white', labelsize=8)

        fig.patch.set_facecolor('#1A2A44')
        ax.set_facecolor('#2A3B5A')
        fig.tight_layout(pad=2.0, rect=[0, 0, 1, 0.96])
        self.img_res_heatmap_canvas.draw()

    def plot_image_resolution_scatter(self):
        """Plot scatter of image resolutions"""
        with sqlite3.connect(self.stats_db_path) as conn:
            cursor = conn.execute("""
                SELECT width, height, file_size
                FROM file_metadata
                WHERE media_type = 'image' AND width IS NOT NULL AND height IS NOT NULL
            """)
            data = cursor.fetchall()

        if not data:
            return

        widths = [row[0] for row in data]
        heights = [row[1] for row in data]
        sizes = [row[2] / (1024**2) if row[2] else 1 for row in data]  # MB

        fig = self.img_res_scatter_canvas.figure
        fig.clear()
        ax = fig.add_subplot(111)
        scatter = ax.scatter(widths, heights, c=sizes, cmap='viridis', alpha=0.6, s=20, vmin=0, vmax=30)
        ax.set_title('Image Resolution Scatter (colored by file size)', color='white',
                    fontsize=13, pad=15, fontweight='bold')
        ax.set_xlabel('Width (px)', color='white', fontsize=11)
        ax.set_ylabel('Height (px)', color='white', fontsize=11)
        ax.grid(True, alpha=0.2, color='white', linestyle='--')
        ax.tick_params(colors='white', labelsize=9)

        cbar = fig.colorbar(scatter, ax=ax)
        cbar.set_label('Size (MB)', color='white', fontsize=10)
        cbar.ax.tick_params(colors='white', labelsize=8)

        fig.patch.set_facecolor('#1A2A44')
        ax.set_facecolor('#2A3B5A')
        fig.tight_layout(pad=2.0, rect=[0, 0, 1, 0.96])
        self.img_res_scatter_canvas.draw()

    def plot_image_format_distribution(self):
        """Plot image format distribution"""
        with sqlite3.connect(self.stats_db_path) as conn:
            cursor = conn.execute("""
                SELECT image_format, COUNT(*) as count
                FROM file_metadata
                WHERE media_type = 'image' AND image_format IS NOT NULL
                GROUP BY image_format
                ORDER BY count DESC
                LIMIT 10
            """)
            data = cursor.fetchall()

        if not data:
            return

        formats = [row[0] for row in data]
        counts = [row[1] for row in data]
        colors = plt.cm.Set3(np.linspace(0, 1, len(formats)))

        fig = self.img_format_canvas.figure
        fig.clear()
        ax = fig.add_subplot(111)
        bars = ax.bar(formats, counts, color=colors, edgecolor='white', linewidth=1.5)
        ax.set_title('Image Format Distribution', color='white', fontsize=13, pad=15, fontweight='bold')
        ax.set_xlabel('Format', color='white', fontsize=11)
        ax.set_ylabel('Count', color='white', fontsize=11)
        ax.tick_params(colors='white', labelsize=9)
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha='right')
        fig.patch.set_facecolor('#1A2A44')
        ax.set_facecolor('#2A3B5A')
        fig.tight_layout(pad=2.0, rect=[0, 0, 1, 0.96])
        self.img_format_canvas.draw()

    def plot_image_color_mode(self):
        """Plot color mode distribution"""
        with sqlite3.connect(self.stats_db_path) as conn:
            cursor = conn.execute("""
                SELECT color_mode, COUNT(*) as count
                FROM file_metadata
                WHERE media_type = 'image' AND color_mode IS NOT NULL
                GROUP BY color_mode
                ORDER BY count DESC
            """)
            data = cursor.fetchall()

        if not data:
            return

        modes = [row[0] for row in data]
        counts = [row[1] for row in data]
        colors = ['#E74C3C', '#3498DB', '#2ECC71', '#F39C12', '#9B59B6']

        fig = self.img_color_canvas.figure
        fig.clear()
        ax = fig.add_subplot(111)
        wedges, texts, autotexts = ax.pie(counts, labels=modes, autopct='%1.1f%%',
                                           colors=colors, startangle=90)
        for text in texts:
            text.set_color('white')
            text.set_fontsize(10)
        for autotext in autotexts:
            autotext.set_color('white')
            autotext.set_fontsize(9)
            autotext.set_weight('bold')
        ax.set_title('Color Mode Distribution', color='white', fontsize=13, pad=15, fontweight='bold')
        fig.patch.set_facecolor('#1A2A44')
        fig.tight_layout(pad=2.0, rect=[0, 0, 1, 0.96])
        self.img_color_canvas.draw()

    def plot_image_size_histogram(self):
        """Plot image file size histogram"""
        with sqlite3.connect(self.stats_db_path) as conn:
            cursor = conn.execute("""
                SELECT file_size
                FROM file_metadata
                WHERE media_type = 'image' AND file_size IS NOT NULL AND file_size > 0
            """)
            sizes = [row[0] / (1024**2) for row in cursor.fetchall()]  # MB

        if not sizes:
            return

        fig = self.img_size_hist_canvas.figure
        fig.clear()
        ax = fig.add_subplot(111)
        ax.hist(sizes, bins=50, color='#3498DB', alpha=0.7, edgecolor='white')
        ax.set_title('Image File Size Distribution', color='white', fontsize=13, pad=15, fontweight='bold')
        ax.set_xlabel('File Size (MB)', color='white', fontsize=11)
        ax.set_ylabel('Count', color='white', fontsize=11)
        ax.grid(True, alpha=0.2, color='white', linestyle='--', axis='y')
        ax.tick_params(colors='white', labelsize=9)
        fig.patch.set_facecolor('#1A2A44')
        ax.set_facecolor('#2A3B5A')
        fig.tight_layout(pad=2.0, rect=[0, 0, 1, 0.96])
        self.img_size_hist_canvas.draw()

    def plot_animation_duration(self):
        """Plot animation duration histogram"""
        with sqlite3.connect(self.stats_db_path) as conn:
            cursor = conn.execute("""
                SELECT duration
                FROM file_metadata
                WHERE is_animated = 1 AND duration IS NOT NULL AND duration > 0
            """)
            durations = [row[0] for row in cursor.fetchall()]

        if not durations:
            return

        fig = self.anim_duration_canvas.figure
        fig.clear()
        ax = fig.add_subplot(111)
        ax.hist(durations, bins=30, color='#E74C3C', alpha=0.7, edgecolor='white')
        ax.set_title('Animation Duration Distribution', color='white', fontsize=8, pad=10, fontweight='bold')
        ax.set_xlabel('Duration (seconds)', color='white', fontsize=8)
        ax.set_ylabel('Count', color='white', fontsize=8)
        ax.grid(True, alpha=0.2, color='white', linestyle='--', axis='y')
        ax.tick_params(colors='white', labelsize=6)
        fig.patch.set_facecolor('#1A2A44')
        ax.set_facecolor('#2A3B5A')
        fig.tight_layout(pad=1.0, rect=[0, 0, 1, 0.99])
        self.anim_duration_canvas.draw()

    def plot_animation_fps(self):
        """Plot animation FPS histogram"""
        with sqlite3.connect(self.stats_db_path) as conn:
            cursor = conn.execute("""
                SELECT frame_rate
                FROM file_metadata
                WHERE is_animated = 1 AND frame_rate IS NOT NULL AND frame_rate > 0
            """)
            fps_values = [row[0] for row in cursor.fetchall()]

        if not fps_values:
            return

        fig = self.anim_fps_canvas.figure
        fig.clear()
        ax = fig.add_subplot(111)
        ax.hist(fps_values, bins=30, color='#2ECC71', alpha=0.7, edgecolor='white')
        ax.set_title('Animation Frame Rate Distribution', color='white', fontsize=8, pad=10, fontweight='bold')
        ax.set_xlabel('Frame Rate (FPS)', color='white', fontsize=8)
        ax.set_ylabel('Count', color='white', fontsize=8)
        ax.grid(True, alpha=0.2, color='white', linestyle='--', axis='y')
        ax.tick_params(colors='white', labelsize=6)
        fig.patch.set_facecolor('#1A2A44')
        ax.set_facecolor('#2A3B5A')
        fig.tight_layout(pad=1.0, rect=[0, 0, 1, 0.99])
        self.anim_fps_canvas.draw()

    def plot_animation_frame_count(self):
        """Plot animation frame count histogram"""
        with sqlite3.connect(self.stats_db_path) as conn:
            cursor = conn.execute("""
                SELECT frame_count
                FROM file_metadata
                WHERE is_animated = 1 AND frame_count IS NOT NULL AND frame_count > 0
            """)
            frame_counts = [row[0] for row in cursor.fetchall()]

        if not frame_counts:
            return

        fig = self.anim_frames_canvas.figure
        fig.clear()
        ax = fig.add_subplot(111)
        ax.hist(frame_counts, bins=40, color='#9B59B6', alpha=0.7, edgecolor='white')
        ax.set_title('Animation Frame Count Distribution', color='white', fontsize=8, pad=10, fontweight='bold')
        ax.set_xlabel('Frame Count', color='white', fontsize=8)
        ax.set_ylabel('Count', color='white', fontsize=8)
        ax.grid(True, alpha=0.2, color='white', linestyle='--', axis='y')
        ax.tick_params(colors='white', labelsize=6)
        fig.patch.set_facecolor('#1A2A44')
        ax.set_facecolor('#2A3B5A')
        fig.tight_layout(pad=1.0, rect=[0, 0, 1, 0.99])
        self.anim_frames_canvas.draw()

    def plot_animation_format_distribution(self):
        """Plot animation format distribution"""
        with sqlite3.connect(self.stats_db_path) as conn:
            cursor = conn.execute("""
                SELECT image_format, COUNT(*) as count
                FROM file_metadata
                WHERE is_animated = 1 AND image_format IS NOT NULL
                GROUP BY image_format
                ORDER BY count DESC
            """)
            data = cursor.fetchall()

        if not data:
            return

        formats = [row[0] for row in data]
        counts = [row[1] for row in data]
        colors = ['#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0']

        fig = self.anim_format_canvas.figure
        fig.clear()
        ax = fig.add_subplot(111)
        wedges, texts, autotexts = ax.pie(counts, labels=formats, autopct='%1.1f%%',
                                           colors=colors, startangle=90)
        for text in texts:
            text.set_color('white')
            text.set_fontsize(11)
        for autotext in autotexts:
            autotext.set_color('white')
            autotext.set_fontsize(10)
            autotext.set_weight('bold')
        ax.set_title('Animation Format Distribution', color='white', fontsize=8, pad=10, fontweight='bold')
        fig.patch.set_facecolor('#1A2A44')
        fig.tight_layout(pad=1.0, rect=[0, 0, 1, 0.99])
        self.anim_format_canvas.draw()

    def plot_animation_size_by_format(self):
        """Plot average animation file size by format"""
        with sqlite3.connect(self.stats_db_path) as conn:
            cursor = conn.execute("""
                SELECT image_format, AVG(file_size) as avg_size, COUNT(*) as count
                FROM file_metadata
                WHERE is_animated = 1 AND image_format IS NOT NULL AND file_size IS NOT NULL
                GROUP BY image_format
                ORDER BY avg_size DESC
            """)
            data = cursor.fetchall()

        if not data:
            return

        formats = [row[0] for row in data]
        avg_sizes = [row[1] / (1024**2) for row in data]  # MB
        colors = plt.cm.coolwarm(np.linspace(0, 1, len(formats)))

        fig = self.anim_size_by_format_canvas.figure
        fig.clear()
        ax = fig.add_subplot(111)
        bars = ax.barh(formats, avg_sizes, color=colors, edgecolor='white', linewidth=1.5)
        ax.set_title('Average File Size by Format', color='white', fontsize=8, pad=10, fontweight='bold')
        ax.set_xlabel('Average File Size (MB)', color='white', fontsize=8)
        ax.set_ylabel('Format', color='white', fontsize=8)
        ax.tick_params(colors='white', labelsize=6)
        fig.patch.set_facecolor('#1A2A44')
        ax.set_facecolor('#2A3B5A')
        fig.tight_layout(pad=1.0, rect=[0, 0, 1, 0.99])
        self.anim_size_by_format_canvas.draw()

    # ==================== VIDEOS TAB PLOTS ====================

    def plot_video_resolution_heatmap(self):
        """Plot 2D histogram heatmap of video resolutions"""
        with sqlite3.connect(self.stats_db_path) as conn:
            cursor = conn.execute("""
                SELECT width, height
                FROM file_metadata
                WHERE media_type = 'video' AND width IS NOT NULL AND height IS NOT NULL
            """)
            data = cursor.fetchall()

        if not data:
            return

        widths = [row[0] for row in data]
        heights = [row[1] for row in data]

        fig = self.vid_res_heatmap_canvas.figure
        fig.clear()
        ax = fig.add_subplot(111)

        h, xedges, yedges = np.histogram2d(widths, heights, bins=40)
        im = ax.imshow(h.T, origin='lower', aspect='auto', cmap='plasma',
                      extent=[xedges[0], xedges[-1], yedges[0], yedges[-1]],
                      interpolation='gaussian', norm=LogNorm() if h.max() > 0 else None)

        ax.set_title('Video Resolution Heatmap', color='white', fontsize=13, pad=15, fontweight='bold')
        ax.set_xlabel('Width (px)', color='white', fontsize=11)
        ax.set_ylabel('Height (px)', color='white', fontsize=11)
        ax.tick_params(colors='white', labelsize=9)

        cbar = fig.colorbar(im, ax=ax, format='%.0f')
        cbar.set_label('Count', color='white', fontsize=10)
        cbar.ax.tick_params(colors='white', labelsize=8)

        fig.patch.set_facecolor('#1A2A44')
        ax.set_facecolor('#2A3B5A')
        fig.tight_layout(pad=2.0, rect=[0, 0, 1, 0.96])
        self.vid_res_heatmap_canvas.draw()

    def plot_video_resolution_scatter(self):
        """Plot scatter of video resolutions"""
        with sqlite3.connect(self.stats_db_path) as conn:
            cursor = conn.execute("""
                SELECT width, height, duration
                FROM file_metadata
                WHERE media_type = 'video' AND width IS NOT NULL AND height IS NOT NULL
            """)
            data = cursor.fetchall()

        if not data:
            return

        widths = [row[0] for row in data]
        heights = [row[1] for row in data]
        durations = [row[2] if row[2] else 1 for row in data]

        fig = self.vid_res_scatter_canvas.figure
        fig.clear()
        ax = fig.add_subplot(111)
        scatter = ax.scatter(widths, heights, c=durations, cmap='cool', alpha=0.6, s=30)
        ax.set_title('Video Resolution Scatter (colored by duration)', color='white',
                    fontsize=13, pad=15, fontweight='bold')
        ax.set_xlabel('Width (px)', color='white', fontsize=11)
        ax.set_ylabel('Height (px)', color='white', fontsize=11)
        ax.grid(True, alpha=0.2, color='white', linestyle='--')
        ax.tick_params(colors='white', labelsize=9)

        cbar = fig.colorbar(scatter, ax=ax)
        cbar.set_label('Duration (s)', color='white', fontsize=10)
        cbar.ax.tick_params(colors='white', labelsize=8)

        fig.patch.set_facecolor('#1A2A44')
        ax.set_facecolor('#2A3B5A')
        fig.tight_layout(pad=2.0, rect=[0, 0, 1, 0.96])
        self.vid_res_scatter_canvas.draw()

    def plot_video_codec_distribution(self):
        """Plot video codec distribution"""
        codec_dist = self.stats_db.get_codec_distribution()

        if not codec_dist:
            return

        codecs = list(codec_dist.keys())[:10]  # Top 10
        counts = [codec_dist[c] for c in codecs]
        colors = plt.cm.Spectral(np.linspace(0, 1, len(codecs)))

        fig = self.vid_codec_canvas.figure
        fig.clear()
        ax = fig.add_subplot(111)
        bars = ax.barh(codecs, counts, color=colors, edgecolor='white', linewidth=1.5)
        ax.set_title('Video Codec Distribution', color='white', fontsize=13, pad=15, fontweight='bold')
        ax.set_xlabel('Count', color='white', fontsize=11)
        ax.set_ylabel('Codec', color='white', fontsize=11)
        ax.tick_params(colors='white', labelsize=9)
        fig.patch.set_facecolor('#1A2A44')
        ax.set_facecolor('#2A3B5A')
        fig.tight_layout(pad=2.0, rect=[0, 0, 1, 0.96])
        self.vid_codec_canvas.draw()

    def plot_video_container_distribution(self):
        """Plot container format distribution"""
        with sqlite3.connect(self.stats_db_path) as conn:
            cursor = conn.execute("""
                SELECT container_format, COUNT(*) as count
                FROM file_metadata
                WHERE media_type = 'video' AND container_format IS NOT NULL
                GROUP BY container_format
                ORDER BY count DESC
                LIMIT 10
            """)
            data = cursor.fetchall()

        if not data:
            return

        formats = [row[0] for row in data]
        counts = [row[1] for row in data]
        colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#FFA07A', '#98D8C8', '#F7DC6F']

        fig = self.vid_container_canvas.figure
        fig.clear()
        ax = fig.add_subplot(111)
        wedges, texts, autotexts = ax.pie(counts, labels=formats, autopct='%1.1f%%',
                                           colors=colors, startangle=90)
        for text in texts:
            text.set_color('white')
            text.set_fontsize(10)
        for autotext in autotexts:
            autotext.set_color('white')
            autotext.set_fontsize(9)
            autotext.set_weight('bold')
        ax.set_title('Container Format Distribution', color='white', fontsize=13, pad=15, fontweight='bold')
        fig.patch.set_facecolor('#1A2A44')
        fig.tight_layout(pad=2.0, rect=[0, 0, 1, 0.96])
        self.vid_container_canvas.draw()

    def plot_video_bitrate_histogram(self):
        """Plot video bitrate histogram"""
        with sqlite3.connect(self.stats_db_path) as conn:
            cursor = conn.execute("""
                SELECT video_bitrate
                FROM file_metadata
                WHERE media_type = 'video' AND video_bitrate IS NOT NULL AND video_bitrate > 0
            """)
            bitrates = [row[0] / 1000000 for row in cursor.fetchall()]  # Mbps

        if not bitrates:
            return

        fig = self.vid_bitrate_hist_canvas.figure
        fig.clear()
        ax = fig.add_subplot(111)
        ax.hist(bitrates, bins=40, color='#FF6B9D', alpha=0.7, edgecolor='white')
        ax.set_title('Video Bitrate Distribution', color='white', fontsize=13, pad=15, fontweight='bold')
        ax.set_xlabel('Bitrate (Mbps)', color='white', fontsize=11)
        ax.set_ylabel('Count', color='white', fontsize=11)
        ax.grid(True, alpha=0.2, color='white', linestyle='--', axis='y')
        ax.tick_params(colors='white', labelsize=9)
        fig.patch.set_facecolor('#1A2A44')
        ax.set_facecolor('#2A3B5A')
        fig.tight_layout(pad=2.0, rect=[0, 0, 1, 0.96])
        self.vid_bitrate_hist_canvas.draw()

    def plot_audio_bitrate_histogram(self):
        """Plot audio bitrate histogram"""
        with sqlite3.connect(self.stats_db_path) as conn:
            cursor = conn.execute("""
                SELECT audio_bitrate
                FROM file_metadata
                WHERE media_type = 'video' AND audio_bitrate IS NOT NULL AND audio_bitrate > 0
            """)
            bitrates = [row[0] / 1000 for row in cursor.fetchall()]  # Kbps

        if not bitrates:
            return

        fig = self.aud_bitrate_hist_canvas.figure
        fig.clear()
        ax = fig.add_subplot(111)
        ax.hist(bitrates, bins=30, color='#4ECDC4', alpha=0.7, edgecolor='white')
        ax.set_title('Audio Bitrate Distribution', color='white', fontsize=13, pad=15, fontweight='bold')
        ax.set_xlabel('Bitrate (Kbps)', color='white', fontsize=11)
        ax.set_ylabel('Count', color='white', fontsize=11)
        ax.grid(True, alpha=0.2, color='white', linestyle='--', axis='y')
        ax.tick_params(colors='white', labelsize=9)
        fig.patch.set_facecolor('#1A2A44')
        ax.set_facecolor('#2A3B5A')
        fig.tight_layout(pad=2.0, rect=[0, 0, 1, 0.96])
        self.aud_bitrate_hist_canvas.draw()

    def plot_video_duration_histogram(self):
        """Plot video duration histogram"""
        with sqlite3.connect(self.stats_db_path) as conn:
            cursor = conn.execute("""
                SELECT duration
                FROM file_metadata
                WHERE media_type = 'video' AND duration IS NOT NULL AND duration > 0
            """)
            durations = [row[0] for row in cursor.fetchall()]

        if not durations:
            return

        fig = self.vid_duration_hist_canvas.figure
        fig.clear()
        ax = fig.add_subplot(111)
        ax.hist(durations, bins=40, color='#9B59B6', alpha=0.7, edgecolor='white')
        ax.set_title('Video Duration Distribution', color='white', fontsize=13, pad=15, fontweight='bold')
        ax.set_xlabel('Duration (seconds)', color='white', fontsize=11)
        ax.set_ylabel('Count', color='white', fontsize=11)
        ax.grid(True, alpha=0.2, color='white', linestyle='--', axis='y')
        ax.tick_params(colors='white', labelsize=9)
        fig.patch.set_facecolor('#1A2A44')
        ax.set_facecolor('#2A3B5A')
        fig.tight_layout(pad=2.0, rect=[0, 0, 1, 0.96])
        self.vid_duration_hist_canvas.draw()

    def plot_video_fps_histogram(self):
        """Plot video FPS histogram"""
        with sqlite3.connect(self.stats_db_path) as conn:
            cursor = conn.execute("""
                SELECT frame_rate
                FROM file_metadata
                WHERE media_type = 'video' AND frame_rate IS NOT NULL AND frame_rate > 0
            """)
            fps_values = [row[0] for row in cursor.fetchall()]

        if not fps_values:
            return

        fig = self.vid_fps_hist_canvas.figure
        fig.clear()
        ax = fig.add_subplot(111)
        ax.hist(fps_values, bins=30, color='#F39C12', alpha=0.7, edgecolor='white')
        ax.set_title('Video Frame Rate Distribution', color='white', fontsize=13, pad=15, fontweight='bold')
        ax.set_xlabel('Frame Rate (FPS)', color='white', fontsize=11)
        ax.set_ylabel('Count', color='white', fontsize=11)
        ax.grid(True, alpha=0.2, color='white', linestyle='--', axis='y')
        ax.tick_params(colors='white', labelsize=9)
        fig.patch.set_facecolor('#1A2A44')
        ax.set_facecolor('#2A3B5A')
        fig.tight_layout(pad=2.0, rect=[0, 0, 1, 0.96])
        self.vid_fps_hist_canvas.draw()

    def plot_audio_channels(self):
        """Plot audio channel distribution"""
        with sqlite3.connect(self.stats_db_path) as conn:
            cursor = conn.execute("""
                SELECT audio_channels, COUNT(*) as count
                FROM file_metadata
                WHERE media_type = 'video' AND audio_channels IS NOT NULL
                GROUP BY audio_channels
                ORDER BY audio_channels
            """)
            data = cursor.fetchall()

        if not data:
            return

        channels = [f"{row[0]} ch" for row in data]
        counts = [row[1] for row in data]
        colors = plt.cm.tab10(np.linspace(0, 1, len(channels)))

        fig = self.audio_channels_canvas.figure
        fig.clear()
        ax = fig.add_subplot(111)
        bars = ax.bar(channels, counts, color=colors, edgecolor='white', linewidth=1.5)
        ax.set_title('Audio Channels Distribution', color='white', fontsize=13, pad=15, fontweight='bold')
        ax.set_xlabel('Channels', color='white', fontsize=11)
        ax.set_ylabel('Count', color='white', fontsize=11)
        ax.tick_params(colors='white', labelsize=9)
        fig.patch.set_facecolor('#1A2A44')
        ax.set_facecolor('#2A3B5A')
        fig.tight_layout(pad=2.0, rect=[0, 0, 1, 0.96])
        self.audio_channels_canvas.draw()

    def plot_audio_sample_rate(self):
        """Plot audio sample rate distribution"""
        with sqlite3.connect(self.stats_db_path) as conn:
            cursor = conn.execute("""
                SELECT audio_sample_rate, COUNT(*) as count
                FROM file_metadata
                WHERE media_type = 'video' AND audio_sample_rate IS NOT NULL
                GROUP BY audio_sample_rate
                ORDER BY count DESC
                LIMIT 10
            """)
            data = cursor.fetchall()

        if not data:
            return

        rates = [f"{row[0]/1000:.1f} kHz" for row in data]
        counts = [row[1] for row in data]
        colors = plt.cm.rainbow(np.linspace(0, 1, len(rates)))

        fig = self.audio_sample_rate_canvas.figure
        fig.clear()
        ax = fig.add_subplot(111)
        bars = ax.barh(rates, counts, color=colors, edgecolor='white', linewidth=1.5)
        ax.set_title('Audio Sample Rate Distribution', color='white', fontsize=13, pad=15, fontweight='bold')
        ax.set_xlabel('Count', color='white', fontsize=11)
        ax.set_ylabel('Sample Rate', color='white', fontsize=11)
        ax.tick_params(colors='white', labelsize=9)
        fig.patch.set_facecolor('#1A2A44')
        ax.set_facecolor('#2A3B5A')
        fig.tight_layout(pad=2.0, rect=[0, 0, 1, 0.96])
        self.audio_sample_rate_canvas.draw()

    # ==================== CREATORS TAB PLOTS ====================

    def plot_top_creators_by_count(self):
        """Plot top creators by file count"""
        with sqlite3.connect(self.stats_db_path) as conn:
            cursor = conn.execute("""
                SELECT creator_id, COUNT(*) as count
                FROM file_metadata
                WHERE creator_id IS NOT NULL
                GROUP BY creator_id
                ORDER BY count DESC
                LIMIT 15
            """)
            data = cursor.fetchall()

        if not data:
            return

        creators = [row[0][:20] for row in data]  # Truncate long names
        counts = [row[1] for row in data]
        colors = plt.cm.viridis(np.linspace(0, 1, len(creators)))

        fig = self.creators_by_count_canvas.figure
        fig.clear()
        ax = fig.add_subplot(111)
        bars = ax.barh(creators, counts, color=colors, edgecolor='white', linewidth=1.5)
        ax.set_title('Top 15 Creators by File Count', color='white', fontsize=13, pad=15, fontweight='bold')
        ax.set_xlabel('File Count', color='white', fontsize=11)
        ax.set_ylabel('Creator ID', color='white', fontsize=11)
        ax.tick_params(colors='white', labelsize=9)
        fig.patch.set_facecolor('#1A2A44')
        ax.set_facecolor('#2A3B5A')
        fig.tight_layout(pad=2.0, rect=[0, 0, 1, 0.96])
        self.creators_by_count_canvas.draw()

    def plot_top_creators_by_size(self):
        """Plot top creators by total size"""
        with sqlite3.connect(self.stats_db_path) as conn:
            cursor = conn.execute("""
                SELECT creator_id, SUM(file_size) as total_size
                FROM file_metadata
                WHERE creator_id IS NOT NULL AND file_size IS NOT NULL
                GROUP BY creator_id
                ORDER BY total_size DESC
                LIMIT 15
            """)
            data = cursor.fetchall()

        if not data:
            return

        creators = [row[0][:20] for row in data]
        sizes = [row[1] / (1024**3) for row in data]  # GB
        colors = plt.cm.plasma(np.linspace(0, 1, len(creators)))

        fig = self.creators_by_size_canvas.figure
        fig.clear()
        ax = fig.add_subplot(111)
        bars = ax.barh(creators, sizes, color=colors, edgecolor='white', linewidth=1.5)
        ax.set_title('Top 15 Creators by Total Size', color='white', fontsize=13, pad=15, fontweight='bold')
        ax.set_xlabel('Total Size (GB)', color='white', fontsize=11)
        ax.set_ylabel('Creator ID', color='white', fontsize=11)
        ax.tick_params(colors='white', labelsize=9)
        fig.patch.set_facecolor('#1A2A44')
        ax.set_facecolor('#2A3B5A')
        fig.tight_layout(pad=2.0, rect=[0, 0, 1, 0.96])
        self.creators_by_size_canvas.draw()

    def plot_files_per_creator_distribution(self):
        """Plot distribution of files per creator"""
        with sqlite3.connect(self.stats_db_path) as conn:
            cursor = conn.execute("""
                SELECT COUNT(*) as file_count
                FROM file_metadata
                WHERE creator_id IS NOT NULL
                GROUP BY creator_id
            """)
            counts = [row[0] for row in cursor.fetchall()]

        if not counts:
            return

        fig = self.files_per_creator_canvas.figure
        fig.clear()
        ax = fig.add_subplot(111)
        ax.hist(counts, bins=50, color='#E67E22', alpha=0.7, edgecolor='white')
        ax.set_title('Files per Creator Distribution', color='white', fontsize=13, pad=15, fontweight='bold')
        ax.set_xlabel('Number of Files', color='white', fontsize=11)
        ax.set_ylabel('Number of Creators', color='white', fontsize=11)
        ax.grid(True, alpha=0.2, color='white', linestyle='--', axis='y')
        ax.tick_params(colors='white', labelsize=9)
        fig.patch.set_facecolor('#1A2A44')
        ax.set_facecolor('#2A3B5A')
        fig.tight_layout(pad=2.0, rect=[0, 0, 1, 0.96])
        self.files_per_creator_canvas.draw()

    def plot_avg_size_per_creator(self):
        """Plot average file size by creator"""
        with sqlite3.connect(self.stats_db_path) as conn:
            cursor = conn.execute("""
                SELECT creator_id, AVG(file_size) as avg_size, COUNT(*) as count
                FROM file_metadata
                WHERE creator_id IS NOT NULL AND file_size IS NOT NULL
                GROUP BY creator_id
                HAVING count >= 5
                ORDER BY avg_size DESC
                LIMIT 20
            """)
            data = cursor.fetchall()

        if not data:
            return

        creators = [row[0][:20] for row in data]
        avg_sizes = [row[1] / (1024**2) for row in data]  # MB
        colors = plt.cm.coolwarm(np.linspace(0, 1, len(creators)))

        fig = self.avg_size_per_creator_canvas.figure
        fig.clear()
        ax = fig.add_subplot(111)
        bars = ax.barh(creators, avg_sizes, color=colors, edgecolor='white', linewidth=1.5)
        ax.set_title('Average File Size by Creator (min 5 files)', color='white',
                    fontsize=13, pad=15, fontweight='bold')
        ax.set_xlabel('Average File Size (MB)', color='white', fontsize=11)
        ax.set_ylabel('Creator ID', color='white', fontsize=11)
        ax.tick_params(colors='white', labelsize=9)
        fig.patch.set_facecolor('#1A2A44')
        ax.set_facecolor('#2A3B5A')
        fig.tight_layout(pad=2.0, rect=[0, 0, 1, 0.96])
        self.avg_size_per_creator_canvas.draw()

    # ==================== ADVANCED TAB PLOTS ====================

    def plot_size_vs_pixels(self):
        """Plot file size vs pixel count correlation"""
        with sqlite3.connect(self.stats_db_path) as conn:
            cursor = conn.execute("""
                SELECT width * height as pixels, file_size
                FROM file_metadata
                WHERE media_type = 'image' AND width IS NOT NULL AND height IS NOT NULL
                      AND file_size IS NOT NULL AND file_size > 0
            """)
            data = cursor.fetchall()

        if not data:
            return

        pixels = [row[0] / 1000000 for row in data]  # Megapixels
        sizes = [row[1] / (1024**2) for row in data]  # MB

        fig = self.size_vs_pixels_canvas.figure
        fig.clear()
        ax = fig.add_subplot(111)
        ax.scatter(pixels, sizes, alpha=0.5, s=10, color='#3498DB')
        ax.set_title('File Size vs Resolution (Images)', color='white', fontsize=13, pad=15, fontweight='bold')
        ax.set_xlabel('Resolution (Megapixels)', color='white', fontsize=11)
        ax.set_ylabel('File Size (MB)', color='white', fontsize=11)
        ax.grid(True, alpha=0.2, color='white', linestyle='--')
        ax.tick_params(colors='white', labelsize=9)
        fig.patch.set_facecolor('#1A2A44')
        ax.set_facecolor('#2A3B5A')
        fig.tight_layout(pad=2.0, rect=[0, 0, 1, 0.96])
        self.size_vs_pixels_canvas.draw()

    def plot_size_vs_resolution_heatmap(self):
        """Plot 2D heatmap of size vs resolution"""
        with sqlite3.connect(self.stats_db_path) as conn:
            cursor = conn.execute("""
                SELECT width * height as pixels, file_size
                FROM file_metadata
                WHERE media_type = 'image' AND width IS NOT NULL AND height IS NOT NULL
                      AND file_size IS NOT NULL AND file_size > 0
            """)
            data = cursor.fetchall()

        if not data:
            return

        pixels = [row[0] / 1000000 for row in data]
        sizes = [row[1] / (1024**2) for row in data]

        fig = self.size_vs_res_heatmap_canvas.figure
        fig.clear()
        ax = fig.add_subplot(111)

        h, xedges, yedges = np.histogram2d(pixels, sizes, bins=50)
        im = ax.imshow(h.T, origin='lower', aspect='auto', cmap='inferno',
                      extent=[xedges[0], xedges[-1], yedges[0], yedges[-1]],
                      interpolation='gaussian')

        ax.set_title('Size vs Resolution Heatmap', color='white', fontsize=13, pad=15, fontweight='bold')
        ax.set_xlabel('Resolution (Megapixels)', color='white', fontsize=11)
        ax.set_ylabel('File Size (MB)', color='white', fontsize=11)
        ax.tick_params(colors='white', labelsize=9)

        cbar = fig.colorbar(im, ax=ax)
        cbar.set_label('Count', color='white', fontsize=10)
        cbar.ax.tick_params(colors='white', labelsize=8)

        fig.patch.set_facecolor('#1A2A44')
        ax.set_facecolor('#2A3B5A')
        fig.tight_layout(pad=2.0, rect=[0, 0, 1, 0.96])
        self.size_vs_res_heatmap_canvas.draw()

    def plot_bitrate_vs_duration(self):
        """Plot video bitrate vs duration scatter"""
        with sqlite3.connect(self.stats_db_path) as conn:
            cursor = conn.execute("""
                SELECT duration, video_bitrate
                FROM file_metadata
                WHERE media_type = 'video' AND duration IS NOT NULL AND video_bitrate IS NOT NULL
                      AND duration > 0 AND video_bitrate > 0
            """)
            data = cursor.fetchall()

        if not data:
            return

        durations = [row[0] for row in data]
        bitrates = [row[1] / 1000000 for row in data]  # Mbps

        fig = self.bitrate_vs_duration_canvas.figure
        fig.clear()
        ax = fig.add_subplot(111)
        ax.scatter(durations, bitrates, alpha=0.5, s=20, color='#E74C3C')
        ax.set_title('Video Bitrate vs Duration', color='white', fontsize=13, pad=15, fontweight='bold')
        ax.set_xlabel('Duration (seconds)', color='white', fontsize=11)
        ax.set_ylabel('Bitrate (Mbps)', color='white', fontsize=11)
        ax.grid(True, alpha=0.2, color='white', linestyle='--')
        ax.tick_params(colors='white', labelsize=9)
        fig.patch.set_facecolor('#1A2A44')
        ax.set_facecolor('#2A3B5A')
        fig.tight_layout(pad=2.0, rect=[0, 0, 1, 0.96])
        self.bitrate_vs_duration_canvas.draw()

    def plot_bitrate_vs_size(self):
        """Plot video bitrate vs file size"""
        with sqlite3.connect(self.stats_db_path) as conn:
            cursor = conn.execute("""
                SELECT file_size, video_bitrate
                FROM file_metadata
                WHERE media_type = 'video' AND file_size IS NOT NULL AND video_bitrate IS NOT NULL
                      AND file_size > 0 AND video_bitrate > 0
            """)
            data = cursor.fetchall()

        if not data:
            return

        sizes = [row[0] / (1024**2) for row in data]  # MB
        bitrates = [row[1] / 1000000 for row in data]  # Mbps

        fig = self.bitrate_vs_size_canvas.figure
        fig.clear()
        ax = fig.add_subplot(111)
        ax.scatter(sizes, bitrates, alpha=0.5, s=20, color='#2ECC71')
        ax.set_title('Video Bitrate vs File Size', color='white', fontsize=13, pad=15, fontweight='bold')
        ax.set_xlabel('File Size (MB)', color='white', fontsize=11)
        ax.set_ylabel('Bitrate (Mbps)', color='white', fontsize=11)
        ax.grid(True, alpha=0.2, color='white', linestyle='--')
        ax.tick_params(colors='white', labelsize=9)
        fig.patch.set_facecolor('#1A2A44')
        ax.set_facecolor('#2A3B5A')
        fig.tight_layout(pad=2.0, rect=[0, 0, 1, 0.96])
        self.bitrate_vs_size_canvas.draw()

    def plot_timeline_stacked(self):
        """Plot stacked area chart of downloads by media type over time"""
        with sqlite3.connect(self.stats_db_path) as conn:
            cursor = conn.execute("""
                SELECT DATE(download_timestamp) as date, media_type, COUNT(*) as count
                FROM file_metadata
                WHERE download_timestamp IS NOT NULL
                GROUP BY DATE(download_timestamp), media_type
                ORDER BY date, media_type
            """)
            data = cursor.fetchall()

        if not data:
            return

        # Organize data by media type
        from collections import defaultdict
        by_date = defaultdict(lambda: defaultdict(int))

        for row in data:
            by_date[row[0]][row[1]] = row[2]

        dates = sorted(by_date.keys())
        media_types = ['image', 'video', 'audio', 'other']

        date_objs = [datetime.strptime(d, '%Y-%m-%d') for d in dates]

        # Build series for each media type
        series = {mt: [] for mt in media_types}
        for date in dates:
            for mt in media_types:
                series[mt].append(by_date[date].get(mt, 0))

        # Calculate cumulative
        for mt in media_types:
            series[mt] = np.cumsum(series[mt])

        fig = self.timeline_stacked_canvas.figure
        fig.clear()
        ax = fig.add_subplot(111)

        colors = ['#4A9EFF', '#FF6B9D', '#4ECDC4', '#FFD93D']
        ax.stackplot(date_objs, [series[mt] for mt in media_types],
                    labels=[mt.capitalize() for mt in media_types],
                    colors=colors, alpha=0.8)

        ax.set_title('Download Timeline by Media Type', color='white', fontsize=13, pad=15, fontweight='bold')
        ax.set_xlabel('Date', color='white', fontsize=11)
        ax.set_ylabel('Cumulative Count', color='white', fontsize=11)
        ax.legend(loc='upper left', facecolor='#2A3B5A', edgecolor='white', labelcolor='white')
        ax.grid(True, alpha=0.2, color='white', linestyle='--')
        ax.tick_params(colors='white', labelsize=9)
        fig.patch.set_facecolor('#1A2A44')
        ax.set_facecolor('#2A3B5A')
        fig.autofmt_xdate()
        fig.tight_layout(pad=2.0, rect=[0, 0, 1, 0.96])
        self.timeline_stacked_canvas.draw()

    def plot_aspect_ratio_distribution(self):
        """Plot aspect ratio distribution"""
        with sqlite3.connect(self.stats_db_path) as conn:
            cursor = conn.execute("""
                SELECT aspect_ratio, COUNT(*) as count
                FROM file_metadata
                WHERE aspect_ratio IS NOT NULL
                GROUP BY aspect_ratio
                ORDER BY count DESC
                LIMIT 15
            """)
            data = cursor.fetchall()

        if not data:
            return

        ratios = [row[0] for row in data]
        counts = [row[1] for row in data]
        colors = plt.cm.tab20(np.linspace(0, 1, len(ratios)))

        fig = self.aspect_ratio_canvas.figure
        fig.clear()
        ax = fig.add_subplot(111)
        bars = ax.barh(ratios, counts, color=colors, edgecolor='white', linewidth=1.5)
        ax.set_title('Top 15 Aspect Ratios', color='white', fontsize=13, pad=15, fontweight='bold')
        ax.set_xlabel('Count', color='white', fontsize=11)
        ax.set_ylabel('Aspect Ratio', color='white', fontsize=11)
        ax.tick_params(colors='white', labelsize=9)
        fig.patch.set_facecolor('#1A2A44')
        ax.set_facecolor('#2A3B5A')
        fig.tight_layout(pad=2.0, rect=[0, 0, 1, 0.96])
        self.aspect_ratio_canvas.draw()
