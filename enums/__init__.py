import enum

class TemplateStatus(str, enum.Enum):
    ACTIVE = "active"
    HIDDEN = "hidden"
    TEST = "test"

class GenerationStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class PaymentStatus(str, enum.Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    FAILED = "failed"

class ActionType(str, enum.Enum):
    COMMAND = "command"
    CALLBACK = "callback"
    MESSAGE = "message"
    PHOTO = "photo"
