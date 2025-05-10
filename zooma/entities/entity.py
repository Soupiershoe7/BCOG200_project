from abc import ABC, abstractmethod

class Entity(ABC):

    def __init__(self):
        pass

    def update(self):
        pass
    
    @abstractmethod
    def draw(self, screen):
        """ Draw the entity on the screen """
        pass