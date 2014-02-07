from django.dispatch import Signal


class_ready = Signal(providing_args=["class"])
