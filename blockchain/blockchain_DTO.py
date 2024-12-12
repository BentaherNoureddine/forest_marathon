from pydantic import BaseModel


# define the data model for the transaction

class TransactionRequest(BaseModel):
    sender: str
    receiver: str
    amount: float




# define the data model for a balance


class BalanceRequest(BaseModel):
    receiver: str
    amount: float


