"""
Statistics and metadata tracking for downloaded files
"""

import sqlite3
import os
import threading
from datetime import datetime
from PIL import Image
import mimetypes

try:
    import av
    HAS_PYAV = True
except ImportError:
    HAS_PYAV = False


class StatsDatabase:
    """
    SQLite-based statistics database for tracking downloaded file metadata.

    Stores comprehensive metadata about images and videos including dimensions,
    encoding, bitrate, duration, and more for analytics and organization.
    """

    def __init__(self, db_path):
        """
        Initialize stats database.

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self.lock = threading.Lock()
        self._init_db()

    def _init_db(self):
        """Create database schema if it doesn't exist."""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)

        with sqlite3.connect(self.db_path) as conn:
            # Main file metadata table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS file_metadata (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    file_path TEXT NOT NULL UNIQUE,
                    file_hash TEXT,
                    file_url TEXT,
                    creator_id TEXT,
                    post_id TEXT,

                    -- File basic info
                    file_size INTEGER,
                    file_extension TEXT,
                    mime_type TEXT,
                    media_type TEXT,  -- 'image', 'video', 'audio', 'other'

                    -- Common metadata
                    width INTEGER,
                    height INTEGER,

                    -- Image-specific
                    image_format TEXT,  -- JPEG, PNG, GIF, WEBP, etc.
                    color_mode TEXT,  -- RGB, RGBA, CMYK, Grayscale
                    bit_depth INTEGER,
                    dpi_x INTEGER,
                    dpi_y INTEGER,
                    is_animated BOOLEAN,
                    frame_count INTEGER,

                    -- Video-specific
                    duration REAL,  -- seconds
                    video_codec TEXT,  -- H.264, H.265, VP9, etc.
                    video_bitrate INTEGER,  -- bits per second
                    frame_rate REAL,  -- FPS
                    aspect_ratio TEXT,  -- 16:9, 4:3, etc.
                    container_format TEXT,  -- MP4, MKV, WEBM, etc.

                    -- Audio metadata (for videos)
                    has_audio BOOLEAN,
                    audio_codec TEXT,
                    audio_bitrate INTEGER,
                    audio_channels INTEGER,
                    audio_sample_rate INTEGER,

                    -- Timestamps
                    download_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    file_modified_timestamp TIMESTAMP,

                    -- Status
                    metadata_extracted BOOLEAN DEFAULT FALSE,
                    extraction_error TEXT
                )
            """)

            # Indexes for faster queries
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_creator_id
                ON file_metadata(creator_id)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_post_id
                ON file_metadata(post_id)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_media_type
                ON file_metadata(media_type)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_file_hash
                ON file_metadata(file_hash)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_download_timestamp
                ON file_metadata(download_timestamp)
            """)

            conn.commit()

    def add_file(self, file_path, file_hash=None, file_url=None, creator_id=None, post_id=None):
        """
        Add a file to the stats database with basic information.

        Args:
            file_path: Full path to the file
            file_hash: MD5 hash of file content
            file_url: Original download URL
            creator_id: Creator/user ID
            post_id: Post ID

        Returns:
            ID of the inserted record, or None on error
        """
        if not os.path.exists(file_path):
            return None

        try:
            file_size = os.path.getsize(file_path)
            file_extension = os.path.splitext(file_path)[1].lower()
            mime_type = mimetypes.guess_type(file_path)[0]
            file_modified = datetime.fromtimestamp(os.path.getmtime(file_path))

            # Determine media type
            media_type = 'other'
            if mime_type:
                if mime_type.startswith('image/'):
                    media_type = 'image'
                elif mime_type.startswith('video/'):
                    media_type = 'video'
                elif mime_type.startswith('audio/'):
                    media_type = 'audio'

            with self.lock:
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.execute("""
                        INSERT OR REPLACE INTO file_metadata
                        (file_path, file_hash, file_url, creator_id, post_id,
                         file_size, file_extension, mime_type, media_type,
                         file_modified_timestamp)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (file_path, file_hash, file_url, creator_id, post_id,
                          file_size, file_extension, mime_type, media_type,
                          file_modified))
                    conn.commit()
                    return cursor.lastrowid

        except Exception:
            return None

    def extract_image_metadata(self, file_id, file_path):
        """
        Extract and store metadata for an image file using PIL.
        Handles both static and animated images (GIF, APNG, WEBP).

        Args:
            file_id: Database ID of the file record
            file_path: Path to the image file

        Returns:
            True on success, False on error
        """
        try:
            with Image.open(file_path) as img:
                width, height = img.size
                image_format = img.format
                color_mode = img.mode

                # Check if animated (GIF, PNG, WEBP with multiple frames)
                is_animated = hasattr(img, 'n_frames') and img.n_frames > 1
                frame_count = getattr(img, 'n_frames', 1) if is_animated else 1

                # Get DPI if available
                dpi_x, dpi_y = img.info.get('dpi', (None, None))

                # Calculate bit depth
                bit_depth = None
                if img.mode in ('1', 'L', 'P'):
                    bit_depth = 8
                elif img.mode in ('RGB', 'YCbCr', 'LAB', 'HSV'):
                    bit_depth = 24
                elif img.mode in ('RGBA', 'CMYK', 'I', 'F'):
                    bit_depth = 32

                # Extract animation metadata if animated
                duration = None
                frame_rate = None
                if is_animated:
                    duration, frame_rate = self._extract_animation_metadata(img)

                with self.lock:
                    with sqlite3.connect(self.db_path) as conn:
                        conn.execute("""
                            UPDATE file_metadata
                            SET width = ?, height = ?, image_format = ?,
                                color_mode = ?, bit_depth = ?, dpi_x = ?, dpi_y = ?,
                                is_animated = ?, frame_count = ?,
                                duration = ?, frame_rate = ?,
                                metadata_extracted = TRUE
                            WHERE id = ?
                        """, (width, height, image_format, color_mode, bit_depth,
                              dpi_x, dpi_y, is_animated, frame_count,
                              duration, frame_rate, file_id))
                        conn.commit()

                return True

        except Exception as e:
            # Store error
            with self.lock:
                with sqlite3.connect(self.db_path) as conn:
                    conn.execute("""
                        UPDATE file_metadata
                        SET extraction_error = ?, metadata_extracted = FALSE
                        WHERE id = ?
                    """, (str(e), file_id))
                    conn.commit()
            return False

    def _extract_animation_metadata(self, img):
        """
        Extract animation-specific metadata from an animated image.

        Args:
            img: PIL Image object (already opened)

        Returns:
            Tuple of (total_duration_seconds, average_frame_rate)
        """
        try:
            total_duration_ms = 0
            frame_durations = []

            # Iterate through all frames to get durations
            for frame_num in range(getattr(img, 'n_frames', 1)):
                img.seek(frame_num)

                # Get frame duration in milliseconds
                # GIF uses 'duration', some formats use 'delay'
                frame_duration = img.info.get('duration', None)
                if frame_duration is None:
                    frame_duration = img.info.get('delay', 100)  # Default 100ms

                frame_durations.append(frame_duration)
                total_duration_ms += frame_duration

            # Reset to first frame
            img.seek(0)

            # Calculate total duration in seconds
            total_duration = total_duration_ms / 1000.0 if total_duration_ms > 0 else None

            # Calculate average frame rate
            frame_rate = None
            if total_duration and total_duration > 0:
                frame_rate = len(frame_durations) / total_duration

            return total_duration, frame_rate

        except Exception:
            # If animation metadata extraction fails, return None values
            return None, None

    def extract_video_metadata(self, file_id, file_path):
        """
        Extract and store metadata for a video file using PyAV.

        Note: Requires PyAV (av) package to be installed.
        Falls back gracefully if not available.

        Args:
            file_id: Database ID of the file record
            file_path: Path to the video file

        Returns:
            True on success, False on error
        """
        if not HAS_PYAV:
            # Mark as not extracted if PyAV not available
            try:
                with self.lock:
                    with sqlite3.connect(self.db_path) as conn:
                        conn.execute("""
                            UPDATE file_metadata
                            SET metadata_extracted = FALSE,
                                extraction_error = 'PyAV not installed'
                            WHERE id = ?
                        """, (file_id,))
                        conn.commit()
            except Exception:
                pass
            return False

        try:
            with av.open(file_path) as container:
                # Get container/format info
                duration = container.duration / av.time_base if container.duration else None
                container_format = container.format.name if container.format else None

                # Initialize metadata variables
                width = height = None
                video_codec = None
                video_bitrate = None
                frame_rate = None
                aspect_ratio = None

                has_audio = False
                audio_codec = None
                audio_bitrate = None
                audio_channels = None
                audio_sample_rate = None

                # Extract video stream info
                video_stream = None
                for stream in container.streams.video:
                    video_stream = stream
                    width = stream.width
                    height = stream.height
                    video_codec = stream.codec_context.name if stream.codec_context else None
                    video_bitrate = stream.bit_rate if stream.bit_rate else None

                    # Frame rate
                    if stream.average_rate:
                        frame_rate = float(stream.average_rate)

                    # Aspect ratio
                    if width and height:
                        from math import gcd
                        divisor = gcd(width, height)
                        aspect_w = width // divisor
                        aspect_h = height // divisor
                        aspect_ratio = f"{aspect_w}:{aspect_h}"

                    break  # Use first video stream

                # Extract audio stream info
                for stream in container.streams.audio:
                    has_audio = True
                    audio_codec = stream.codec_context.name if stream.codec_context else None
                    audio_bitrate = stream.bit_rate if stream.bit_rate else None
                    audio_channels = stream.channels if hasattr(stream, 'channels') else None
                    audio_sample_rate = stream.sample_rate if hasattr(stream, 'sample_rate') else None
                    break  # Use first audio stream

                # Store metadata
                with self.lock:
                    with sqlite3.connect(self.db_path) as conn:
                        conn.execute("""
                            UPDATE file_metadata
                            SET width = ?, height = ?,
                                duration = ?, video_codec = ?, video_bitrate = ?,
                                frame_rate = ?, aspect_ratio = ?, container_format = ?,
                                has_audio = ?, audio_codec = ?, audio_bitrate = ?,
                                audio_channels = ?, audio_sample_rate = ?,
                                metadata_extracted = TRUE
                            WHERE id = ?
                        """, (width, height, duration, video_codec, video_bitrate,
                              frame_rate, aspect_ratio, container_format,
                              has_audio, audio_codec, audio_bitrate,
                              audio_channels, audio_sample_rate, file_id))
                        conn.commit()

                return True

        except Exception as e:
            # Store error
            with self.lock:
                with sqlite3.connect(self.db_path) as conn:
                    conn.execute("""
                        UPDATE file_metadata
                        SET extraction_error = ?, metadata_extracted = FALSE
                        WHERE id = ?
                    """, (str(e), file_id))
                    conn.commit()
            return False

    def get_file_metadata(self, file_path):
        """
        Get metadata for a specific file.

        Args:
            file_path: Path to the file

        Returns:
            Dict with metadata or None if not found
        """
        with self.lock:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute("""
                    SELECT * FROM file_metadata WHERE file_path = ?
                """, (file_path,))
                row = cursor.fetchone()

                if row:
                    return dict(row)
                return None

    def get_creator_stats(self, creator_id):
        """
        Get statistics for a specific creator.

        Args:
            creator_id: Creator/user ID

        Returns:
            Dict with statistics
        """
        with self.lock:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT
                        COUNT(*) as total_files,
                        SUM(file_size) as total_size,
                        COUNT(CASE WHEN media_type = 'image' THEN 1 END) as image_count,
                        COUNT(CASE WHEN media_type = 'video' THEN 1 END) as video_count,
                        AVG(file_size) as avg_file_size,
                        MIN(download_timestamp) as first_download,
                        MAX(download_timestamp) as last_download
                    FROM file_metadata
                    WHERE creator_id = ?
                """, (creator_id,))
                row = cursor.fetchone()

                if row:
                    return {
                        'total_files': row[0] or 0,
                        'total_size': row[1] or 0,
                        'image_count': row[2] or 0,
                        'video_count': row[3] or 0,
                        'avg_file_size': row[4] or 0,
                        'first_download': row[5],
                        'last_download': row[6]
                    }
                return None

    def get_global_stats(self):
        """
        Get global statistics across all downloads.

        Returns:
            Dict with global statistics
        """
        with self.lock:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT
                        COUNT(*) as total_files,
                        SUM(file_size) as total_size,
                        COUNT(DISTINCT creator_id) as unique_creators,
                        COUNT(DISTINCT post_id) as unique_posts,
                        COUNT(CASE WHEN media_type = 'image' THEN 1 END) as image_count,
                        COUNT(CASE WHEN media_type = 'video' THEN 1 END) as video_count,
                        COUNT(CASE WHEN is_animated = 1 THEN 1 END) as animated_count,
                        AVG(file_size) as avg_file_size,
                        AVG(CASE WHEN is_animated = 1 THEN duration END) as avg_animation_duration
                    FROM file_metadata
                """)
                row = cursor.fetchone()

                if row:
                    return {
                        'total_files': row[0] or 0,
                        'total_size': row[1] or 0,
                        'unique_creators': row[2] or 0,
                        'unique_posts': row[3] or 0,
                        'image_count': row[4] or 0,
                        'video_count': row[5] or 0,
                        'animated_count': row[6] or 0,
                        'avg_file_size': row[7] or 0,
                        'avg_animation_duration': row[8] or 0
                    }
                return None

    def get_animation_stats(self):
        """
        Get statistics specifically for animated images.

        Returns:
            Dict with animation statistics
        """
        with self.lock:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT
                        COUNT(*) as total_animations,
                        AVG(frame_count) as avg_frames,
                        MAX(frame_count) as max_frames,
                        AVG(duration) as avg_duration,
                        MAX(duration) as max_duration,
                        AVG(frame_rate) as avg_fps,
                        SUM(file_size) as total_size,
                        AVG(file_size) as avg_file_size,
                        COUNT(CASE WHEN image_format = 'GIF' THEN 1 END) as gif_count,
                        COUNT(CASE WHEN image_format = 'PNG' THEN 1 END) as apng_count,
                        COUNT(CASE WHEN image_format = 'WEBP' THEN 1 END) as webp_count
                    FROM file_metadata
                    WHERE is_animated = 1
                """)
                row = cursor.fetchone()

                if row:
                    return {
                        'total_animations': row[0] or 0,
                        'avg_frames': round(row[1], 1) if row[1] else 0,
                        'max_frames': row[2] or 0,
                        'avg_duration': round(row[3], 2) if row[3] else 0,
                        'max_duration': round(row[4], 2) if row[4] else 0,
                        'avg_fps': round(row[5], 1) if row[5] else 0,
                        'total_size': row[6] or 0,
                        'avg_file_size': row[7] or 0,
                        'gif_count': row[8] or 0,
                        'apng_count': row[9] or 0,
                        'webp_count': row[10] or 0
                    }
                return None

    def get_animations_by_format(self, image_format='GIF'):
        """
        Get list of animated images by format.

        Args:
            image_format: Format to filter (GIF, PNG, WEBP)

        Returns:
            List of file metadata dicts
        """
        with self.lock:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute("""
                    SELECT file_path, frame_count, duration, frame_rate, file_size
                    FROM file_metadata
                    WHERE is_animated = 1 AND image_format = ?
                    ORDER BY frame_count DESC
                """, (image_format,))

                return [dict(row) for row in cursor.fetchall()]

    def get_video_stats(self):
        """
        Get statistics specifically for videos.

        Returns:
            Dict with video statistics
        """
        with self.lock:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT
                        COUNT(*) as total_videos,
                        AVG(duration) as avg_duration,
                        MAX(duration) as max_duration,
                        AVG(video_bitrate) as avg_bitrate,
                        AVG(frame_rate) as avg_fps,
                        SUM(file_size) as total_size,
                        AVG(file_size) as avg_file_size,
                        COUNT(CASE WHEN has_audio = 1 THEN 1 END) as videos_with_audio,
                        AVG(width) as avg_width,
                        AVG(height) as avg_height
                    FROM file_metadata
                    WHERE media_type = 'video'
                """)
                row = cursor.fetchone()

                if row:
                    return {
                        'total_videos': row[0] or 0,
                        'avg_duration': round(row[1], 2) if row[1] else 0,
                        'max_duration': round(row[2], 2) if row[2] else 0,
                        'avg_bitrate': row[3] or 0,
                        'avg_fps': round(row[4], 1) if row[4] else 0,
                        'total_size': row[5] or 0,
                        'avg_file_size': row[6] or 0,
                        'videos_with_audio': row[7] or 0,
                        'avg_width': round(row[8]) if row[8] else 0,
                        'avg_height': round(row[9]) if row[9] else 0
                    }
                return None

    def get_videos_by_codec(self, video_codec='h264'):
        """
        Get list of videos by codec.

        Args:
            video_codec: Codec to filter (h264, hevc, vp9, etc.)

        Returns:
            List of file metadata dicts
        """
        with self.lock:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute("""
                    SELECT file_path, duration, video_bitrate, frame_rate,
                           width, height, file_size, has_audio
                    FROM file_metadata
                    WHERE media_type = 'video' AND video_codec = ?
                    ORDER BY duration DESC
                """, (video_codec,))

                return [dict(row) for row in cursor.fetchall()]

    def get_codec_distribution(self):
        """
        Get distribution of video codecs used.

        Returns:
            Dict mapping codec names to counts
        """
        with self.lock:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT video_codec, COUNT(*) as count
                    FROM file_metadata
                    WHERE media_type = 'video' AND video_codec IS NOT NULL
                    GROUP BY video_codec
                    ORDER BY count DESC
                """)

                return {row[0]: row[1] for row in cursor.fetchall()}

    def add_file_complete(self, file_path, file_hash=None, file_url=None, creator_id=None, post_id=None):
        """
        Add a file and extract metadata in one call.

        Args:
            file_path: Full path to the file
            file_hash: MD5 hash of file content
            file_url: Original download URL
            creator_id: Creator/user ID
            post_id: Post ID

        Returns:
            True on success, False on error
        """
        file_id = self.add_file(file_path, file_hash, file_url, creator_id, post_id)
        if file_id is None:
            return False

        # Get media type to decide what metadata to extract
        metadata = self.get_file_metadata(file_path)
        if metadata:
            if metadata['media_type'] == 'image':
                return self.extract_image_metadata(file_id, file_path)
            elif metadata['media_type'] == 'video':
                return self.extract_video_metadata(file_id, file_path)

        # For audio and other types, just mark as complete without detailed metadata
        return True
