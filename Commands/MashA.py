#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#Poke Controller 互換性チェック


from Keys import Button, Stick, Direction, Hat
from PythonCommandBase import PythonCommand


# Mash a button A
# A連打
class MashA(PythonCommand):
    NAME = 'A連打'

    def __init__(self):
        super().__init__()

    def do(self):
        while True:
            self.wait(0.5)
            self.press(Button.A)
