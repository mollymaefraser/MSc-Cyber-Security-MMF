from abc import ABC, abstractmethod


# Car interface/abstract class
class Car(ABC):
    @abstractmethod
    def drive(self):
        pass


# Concrete car classes
class Sedan(Car):
    def drive(self):
        return "Driving a Sedan: smooth handling, ideal for daily commutes."


class SUV(Car):
    def drive(self):
        return "Driving an SUV: higher ground clearance, built for rough terrain."


class Hatchback(Car):
    def drive(self):
        return "Driving a Hatchback: compact and easy to manoeuvre in cities."


# CarFactory abstract class
class CarFactory(ABC):
    @abstractmethod
    def create_car(self):
        pass


# Concrete factories
class SedanFactory(CarFactory):
    def create_car(self):
        return Sedan()


class SUVFactory(CarFactory):
    def create_car(self):
        return SUV()


class HatchbackFactory(CarFactory):
    def create_car(self):
        return Hatchback()


# Demonstration
if __name__ == "__main__":
    factories = [SedanFactory(), SUVFactory(), HatchbackFactory()]

    for factory in factories:
        car = factory.create_car()
        print(car.drive())
