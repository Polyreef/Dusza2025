from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QHBoxLayout, QLabel, QWidget

from game.widgets.background import BackgroundWidget


class BattleAnimationPage(BackgroundWidget):
    def __init__(self, game):
        super().__init__("Assets/Images/Backgrounds/egyszeru.png", game)
        self.game = game

        self.log = []
        self.index = 0

        self.player_label = QLabel(self)
        self.enemy_label = QLabel(self)
        self.player_hp_label = QLabel(self)
        self.enemy_hp_label = QLabel(self)

        self.player_current = None
        self.enemy_current = None

        self.player_hp = 0
        self.enemy_hp = 0

        self._current_attack_anim = None

        self._build_ui()

    def get_any_card_from_world(self, world, name):
        if name in world.simple_cards:
            return world.simple_cards[name]

        if name in world.leader_cards:
            return world.leader_cards[name]

        return None

    def _build_ui(self):
        layout = self.get_container()
        layout.setContentsMargins(20, 20, 20, 20)

        title = QLabel("Harc kezdődik…")
        title.setStyleSheet("color: white; font-size: 24px; font-weight: bold;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title_label = title
        layout.addWidget(title)

        field = QWidget()
        f = QHBoxLayout(field)
        f.setContentsMargins(0, 40, 0, 40)
        f.setSpacing(80)

        self.player_label.setScaledContents(True)
        self.player_label.setFixedSize(260, 300)
        f.addWidget(
            self.player_label,
            alignment=Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignBottom,
        )

        self.enemy_label.setScaledContents(True)
        self.enemy_label.setFixedSize(260, 300)
        f.addWidget(
            self.enemy_label,
            alignment=Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignBottom,
        )

        layout.addWidget(field)

        hp = QHBoxLayout()
        self.player_hp_label.setStyleSheet("color: white; font-size: 18px;")
        self.enemy_hp_label.setStyleSheet("color: white; font-size: 18px;")

        hp.addWidget(self.player_hp_label, alignment=Qt.AlignmentFlag.AlignLeft)
        hp.addWidget(self.enemy_hp_label, alignment=Qt.AlignmentFlag.AlignRight)
        layout.addLayout(hp)

    def start_battle(self, dungeon, result, reward_msg):
        window = self.window()
        if hasattr(window, "sound"):
            window.sound.play("door")

        self.log = list(result.log_lines)
        self.index = 0
        self.result = result
        self.reward_msg = reward_msg

        bg = {
            "egyszeru": "Assets/Images/Backgrounds/egyszeru.png",
            "kis": "Assets/Images/Backgrounds/kis.png",
            "nagy": "Assets/Images/Backgrounds/nagy.png",
        }.get(dungeon.kind, "Assets/Images/Backgrounds/egyszeru.png")
        self.set_background(bg)

        self.player_current = None
        self.enemy_current = None
        self.player_hp = 0
        self.enemy_hp = 0

        self._preprocess_initial_cards()

        if self.player_current:
            self.load_character_sprite(self.player_label, self.player_current)
        if self.enemy_current:
            self.load_character_sprite(self.enemy_label, self.enemy_current)

        self.update_hp_labels()

        QTimer.singleShot(3000, self.next_step)

    def _preprocess_initial_cards(self):
        for line in self.log:
            parts = line.split(";")
            if len(parts) < 6:
                continue

            actor = parts[1]
            action = parts[2]
            if action != "kijatszik":
                continue

            name = parts[3]
            try:
                hp = int(parts[5])
            except ValueError:
                continue

            if actor == "jatekos" and not self.player_current:
                self.player_current = name
                self.player_hp = hp
            elif actor == "kazamata" and not self.enemy_current:
                self.enemy_current = name
                self.enemy_hp = hp

            if self.player_current and self.enemy_current:
                return

    def load_character_sprite(self, label, card_name):
        world = self.game.environment.world
        card = self.get_any_card_from_world(world, card_name)

        if not card:
            pix = QPixmap("Assets/Images/Characters/Fold1.png")
        else:
            elem = card.element.capitalize()
            style = world.simple_styles.get(card.name) or world.leader_styles.get(
                card.name, 1
            )
            path = f"Assets/Images/Characters/{elem}{style}.png"
            pix = QPixmap(path)
            if pix.isNull():
                pix = QPixmap("Assets/Images/Characters/Fold1.png")

        label.setPixmap(
            pix.scaled(
                label.width(),
                label.height(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
        )

    def update_hp_labels(self):
        self.player_hp_label.setText(f"❤️ {self.player_hp}")
        self.enemy_hp_label.setText(f"❤️ {self.enemy_hp}")

    def next_step(self):
        if self.index >= len(self.log):
            self.finish_battle()
            return

        line = self.log[self.index]
        self.index += 1

        parts = line.split(";")
        if not parts:
            QTimer.singleShot(10, self.next_step)
            return

        if parts[0].startswith("harc kezdodik"):
            QTimer.singleShot(10, self.next_step)
            return

        if len(parts) < 3:
            QTimer.singleShot(10, self.next_step)
            return

        actor = parts[1]
        action = parts[2]

        if action == "kijatszik":
            if len(parts) < 6:
                QTimer.singleShot(10, self.next_step)
                return

            name = parts[3]
            try:
                hp = int(parts[5])
            except ValueError:
                QTimer.singleShot(10, self.next_step)
                return

            if actor == "jatekos":
                self.player_current = name
                self.player_hp = hp
                self.load_character_sprite(self.player_label, name)
            else:
                self.enemy_current = name
                self.enemy_hp = hp
                self.load_character_sprite(self.enemy_label, name)

            self.update_hp_labels()
            QTimer.singleShot(400, self.next_step)
            return

        if action == "tamad":
            dmg = int(parts[4])
            attacker = "enemy" if actor == "kazamata" else "player"
            self.animate_attack(attacker, dmg)
            return

        QTimer.singleShot(300, self.next_step)

    def animate_attack(self, attacker, dmg):
        from PySide6.QtCore import (
            QPropertyAnimation,
            QPoint,
            QEasingCurve,
            QSequentialAnimationGroup,
        )

        if attacker == "player":
            card_name = self.player_current
        else:
            card_name = self.enemy_current

        world = self.game.environment.world
        card = self.get_any_card_from_world(world, card_name)

        if card:
            elem = card.element.lower()

            sound_map = {
                "fold": "strike",
                "levego": "arrow",
                "viz": "whoosh",
                "tuz": "throw",
            }

            sound_name = sound_map.get(elem)
            if sound_name:
                self.game.sound.play(sound_name)

        if attacker == "player":
            mover = self.player_label
            target = self.enemy_label
        else:
            mover = self.enemy_label
            target = self.player_label

        start = mover.pos()
        hit = start + QPoint(200 if attacker == "player" else -200, -10)

        anim1 = QPropertyAnimation(mover, b"pos")
        anim1.setDuration(200)
        anim1.setEndValue(hit)
        anim1.setEasingCurve(QEasingCurve.Type.OutQuad)

        shake = QPropertyAnimation(target, b"pos")
        shake.setDuration(160)
        shake.setKeyValueAt(0.3, target.pos() + QPoint(8, -4))
        shake.setKeyValueAt(0.6, target.pos() + QPoint(-8, 4))
        shake.setEndValue(target.pos())

        anim2 = QPropertyAnimation(mover, b"pos")
        anim2.setDuration(200)
        anim2.setEndValue(start)
        anim2.setEasingCurve(QEasingCurve.Type.InQuad)

        grp = QSequentialAnimationGroup(self)
        grp.addAnimation(anim1)
        grp.addAnimation(shake)
        grp.addAnimation(anim2)

        self._current_attack_anim = grp

        grp.finished.connect(lambda: self._on_attack_anim_finished(attacker, dmg, grp))
        grp.start()

    def _on_attack_anim_finished(self, attacker, dmg, grp):
        self._current_attack_anim = None
        grp.deleteLater()
        self.apply_damage(attacker, dmg)

    def apply_damage(self, attacker, dmg):
        if attacker == "player":
            self.enemy_hp -= dmg
            if self.enemy_hp <= 0:
                self.enemy_hp = 0
                self.kill_character(self.enemy_label)
        else:
            self.player_hp -= dmg
            if self.player_hp <= 0:
                self.player_hp = 0
                self.kill_character(self.player_label)

        self.update_hp_labels()
        QTimer.singleShot(600, self.next_step)

    def kill_character(self, label):
        from PySide6.QtCore import QPropertyAnimation

        fade = QPropertyAnimation(label, b"windowOpacity", label)
        fade.setDuration(600)
        fade.setEndValue(0)
        fade.start()

    def finish_battle(self):
        outcome = self.result.outcome
        self.game.show_battle_end_screen(outcome, self.reward_msg)
