import random
import cv2
import numpy as np

from collision_detection import hitCriticalMass
from block import Block
import os


class Challenge():
    def __init__(self, name, image, observer=None):
        self.name = name
        self.image = image
        self.observer = observer
        self.expired = False


class PunchChallenge(Challenge):
    END_SIZE = int(os.getenv("FRAME_WIDTH", "400")) // 3
    BASE_IMG = cv2.imread("assets/glove.png")

    def __init__(self, x: int, y: int, startSize: int = 50, timeToLive=3, observer=None, multiplayerPunch=False):
        super().__init__("Punch Challenge", PunchChallenge.BASE_IMG, observer)
        self.x = x
        self.y = y
        self.size = startSize
        self.timeToLive = timeToLive
        self.growthRate = ((self.END_SIZE - startSize) // timeToLive) + 1
        self.multiplayerPunch = multiplayerPunch

    def update(self, landmarks):
        self.size += self.growthRate
        self.image = cv2.resize(PunchChallenge.BASE_IMG,
                                (self.size, self.size))
        self.timeToLive -= 1
        if self.timeToLive == 0:
            self.checkCollision(landmarks)
            self.expired = True

    def overlayChallenge(self, frame):
        # too lazy to refactor vars
        x = self.x
        y = self.y
        size = self.size

        self.image = cv2.resize(PunchChallenge.BASE_IMG,
                                (size, size))
        adjustmentPixel = 1 if size % 2 != 0 else 0
        frame[y - size // 2: y + size // 2 + adjustmentPixel, x - size // 2: x + size // 2 + adjustmentPixel] = cv2.addWeighted(
            frame[y - size // 2: y + size // 2 + adjustmentPixel, x - size // 2: x + size // 2 + adjustmentPixel], 1.0, self.image, 1.0, 1)

        # red if generated, green if multiplayer
        outlineColor = (
            255, 0, 0) if not self.multiplayerPunch else (0, 255, 0)
        cv2.circle(frame, (x, y), (PunchChallenge.END_SIZE - 10) //
                   2, outlineColor, 2)

    def checkCollision(self, landmarks):
        block = Block()
        if hitCriticalMass(landmarks, (self.x, self.y), self.size // 2) and not block.detectBlock(landmarks):
            self.expired = True
            if self.observer:
                self.observer.notify(self)


class ChallengeManager():
    def __init__(self):
        self.challenges: list[PunchChallenge] = []

    def update_challenges(self, landmarks):
        # Get value field from protobuf
        if landmarks and landmarks.landmark:
            landmarks = landmarks.landmark
        else:
            print(f"Warning: Challenge {self} did not receive landmarks")
            return
        for challenge in self.challenges:
            challenge.update(landmarks)
            if challenge.expired:
                self.challenges.remove(challenge)
        # handle collisions

    def generatePunchChallenge(self, frameWidth=1920, frameHeight=1080, startSize=50, timeToLive=5, observer=None):
        endSize = frameWidth // 4
        x = random.randint((endSize) // 2 + 1,
                           frameWidth - endSize)
        y = random.randint(endSize // 2 + 1,
                           frameHeight - endSize)
        challenge = PunchChallenge(x, y, startSize, timeToLive, observer)
        self.challenges.append(challenge)
        return challenge

    def addPunchChallenge(self, normalizedPunchLocation, multiplayerPunch=False):
        x = int(normalizedPunchLocation[0] *
                int(os.getenv("FRAME_WIDTH", 1920)))
        y = int(normalizedPunchLocation[1] *
                int(os.getenv("FRAME_HEIGHT", 1080)))
        challenge = PunchChallenge(x, y, multiplayerPunch=multiplayerPunch)
        self.challenges.append(challenge)

    def drawChallenges(self, frame):
        for challenge in self.challenges:
            challenge.overlayChallenge(frame)

    def checkCollision(self, landmarks):
        for challenge in self.challenges:
            challenge.checkCollision(landmarks)
