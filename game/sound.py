from PySide6.QtMultimedia import QSoundEffect
from PySide6.QtCore import QUrl


class SoundManager:
    def __init__(self):
        self.sounds = {}

    def load(self, name: str, path: str, volume: float = 0.7, loop: bool = False):
        eff = QSoundEffect()
        eff.setSource(QUrl.fromLocalFile(path))
        eff.setVolume(volume)
        if loop:
            eff.setLoopCount(100000)  # haha
        self.sounds[name] = eff

    def play(self, name: str):
        sound = self.sounds.get(name)
        if sound:
            sound.play()
