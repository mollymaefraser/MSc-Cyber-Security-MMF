# Collaborative Discussion: Structural Design Patterns

**Unit:** Formative Collaborative Discussion (starts and ends in this unit week)
**Note:** Not assessed — informal tutor feedback only.


## Task 1: Adapter Pattern

**Scenario:** A modern e-commerce platform expects RESTful JSON responses, but a legacy payment system only exposes an old SOAP-style interface returning XML-like objects. Rewriting the legacy system isn't feasible, so an Adapter translates between the two.

**Explanation:** The Adapter wraps the legacy system and exposes the interface the modern platform expects. The e-commerce code only ever talks to the adapter's interface, never touching the legacy system directly, so both sides stay decoupled and the legacy system doesn't need to change at all.

```python
from abc import ABC, abstractmethod

# Interface the modern platform expects
class PaymentGateway(ABC):
    @abstractmethod
    def process_payment(self, amount):
        pass

# Legacy system with an incompatible interface
class LegacySOAPPaymentSystem:
    def make_soap_payment(self, amount_in_pence):
        print(f"Legacy SOAP system processing {amount_in_pence} pence")
        return {"status": "SUCCESS", "amount": amount_in_pence}

# Adapter bridges the two
class LegacyPaymentAdapter(PaymentGateway):
    def __init__(self, legacy_system: LegacySOAPPaymentSystem):
        self.legacy_system = legacy_system

    def process_payment(self, amount):
        pence = int(amount * 100)
        result = self.legacy_system.make_soap_payment(pence)
        return {"success": result["status"] == "SUCCESS", "amount_charged": amount}


# Client code only knows about PaymentGateway
def checkout(gateway: PaymentGateway, amount):
    response = gateway.process_payment(amount)
    print(f"Payment result: {response}")


if __name__ == "__main__":
    adapter = LegacyPaymentAdapter(LegacySOAPPaymentSystem())
    checkout(adapter, 49.99)
```

The client's `checkout()` function depends only on `PaymentGateway`, so swapping the legacy system for a different one later requires no changes to the checkout logic — just a new adapter.


---

## Task 2: Bridge Pattern

**Scenario:** A company sells devices (TV, Radio) and remote controls (Basic, Advanced) in various combinations. Without the Bridge Pattern, you'd need a separate class for every device/remote pairing (`BasicTVRemote`, `AdvancedTVRemote`, `BasicRadioRemote`...), which explodes combinatorially as either side grows.

**Explanation:** The Bridge Pattern splits this into two independent hierarchies — `RemoteControl` (abstraction) and `Device` (implementation) — connected by composition rather than inheritance. Any remote can control any device, and each hierarchy can grow independently.

```python
from abc import ABC, abstractmethod

# Implementation hierarchy
class Device(ABC):
    @abstractmethod
    def turn_on(self):
        pass

    @abstractmethod
    def turn_off(self):
        pass


class TV(Device):
    def turn_on(self):
        print("TV is now ON")

    def turn_off(self):
        print("TV is now OFF")


class Radio(Device):
    def turn_on(self):
        print("Radio is now ON")

    def turn_off(self):
        print("Radio is now OFF")


# Abstraction hierarchy
class RemoteControl:
    def __init__(self, device: Device):
        self.device = device

    def toggle_on(self):
        self.device.turn_on()

    def toggle_off(self):
        self.device.turn_off()


class AdvancedRemoteControl(RemoteControl):
    def mute(self):
        print("Muting device")


if __name__ == "__main__":
    basic_remote = RemoteControl(TV())
    basic_remote.toggle_on()

    advanced_remote = AdvancedRemoteControl(Radio())
    advanced_remote.toggle_on()
    advanced_remote.mute()
```

Adding a new device (e.g. `SmartSpeaker`) or a new remote type requires no changes to the other hierarchy — they vary independently, which is exactly what Bridge is for.


---

## Task 3: Composite Pattern

**Scenario:** A file system contains both individual files and folders, and folders can contain more files and folders recursively. Code that displays or calculates the size of a file system shouldn't need special-case logic depending on whether it's looking at a file or a folder.

**Explanation:** The Composite Pattern defines a common `FileSystemComponent` interface that both `File` (leaf) and `Folder` (composite) implement. Client code calls the same methods regardless of whether it's holding a single file or an entire folder tree, since a `Folder` just delegates to its children.

```python
from abc import ABC, abstractmethod

class FileSystemComponent(ABC):
    @abstractmethod
    def show(self, indent=0):
        pass

    @abstractmethod
    def size(self):
        pass


class File(FileSystemComponent):
    def __init__(self, name, file_size):
        self.name = name
        self.file_size = file_size

    def show(self, indent=0):
        print(" " * indent + f"- {self.name} ({self.file_size}KB)")

    def size(self):
        return self.file_size


class Folder(FileSystemComponent):
    def __init__(self, name):
        self.name = name
        self.children = []

    def add(self, component: FileSystemComponent):
        self.children.append(component)

    def show(self, indent=0):
        print(" " * indent + f"+ {self.name}/")
        for child in self.children:
            child.show(indent + 2)

    def size(self):
        return sum(child.size() for child in self.children)


if __name__ == "__main__":
    root = Folder("root")
    root.add(File("resume.pdf", 120))

    docs = Folder("docs")
    docs.add(File("notes.txt", 5))
    docs.add(File("essay.docx", 45))
    root.add(docs)

    root.show()
    print(f"Total size: {root.size()}KB")
```

Whether `size()` is called on a lone `File` or an entire `Folder` tree, the interface is identical — the client never needs to check types.

