from abc import ABC, abstractmethod

class Entity(ABC):

    def __init__(self):
        pass

    def with_id(self, id):
        self.id = id
        return self

    def update(self):
        pass
    
    @abstractmethod
    def draw(self, screen):
        """ Draw the entity on the screen """
        pass