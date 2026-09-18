"""
Тесты для модуля audio_file
"""
import unittest
from pathlib import Path
from music_manager.audio_file import AudioFile


class TestAudioFile(unittest.TestCase):
    """Тесты для класса AudioFile"""
    
    def test_organized_path(self):
        """Тест генерации организованного пути"""
        audio_file = AudioFile(
            path=Path("/test/music.mp3"),
            title="Test Song",
            artist="Test Artist",
            album="Test Album",
            year="2024",
            track_number="05"
        )
        
        base_dir = Path("/output")
        organized_path = audio_file.get_organized_path(base_dir)
        
        expected = base_dir / "Test Artist" / "2024 - Test Album" / "05 - Test Song.mp3"
        self.assertEqual(organized_path, expected)
    
    def test_organized_path_with_unknown_tags(self):
        """Тест организации с отсутствующими тегами"""
        audio_file = AudioFile(
            path=Path("/test/music.mp3")
        )
        
        base_dir = Path("/output")
        organized_path = audio_file.get_organized_path(base_dir)
        
        expected = base_dir / "Unknown Artist" / "0000 - Unknown Album" / "00 - music.mp3"
        self.assertEqual(organized_path, expected)


if __name__ == '__main__':
    unittest.main()
