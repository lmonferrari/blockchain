# utxo
# são as transações que ainda não foram gastas

# toda transação tem um input e um output
# input: é o endereço de onde vem o dinheiro
# output: é o endereço para onde vai o dinheiro

# se uma transação tem "troco", eu que tenho que calcular
# o troco e enviar para o meu endereço.
# se eu tenho 10 e quero enviar 5,
# eu envio 5 para o endereço do destinatário e 5 para o meu endereço.
# tem a taxa de transação, que é o valor que eu pago para o minerador
# para ele colocar a minha transação no bloco.

from datetime import datetime


class Transaction:
    def __init__(self, sender, receiver, amount):
        self.sender = sender
        self.receiver = receiver
        self.amount = amount
        self.timestamp = datetime.now()

    def to_json(self):
        return {
            "sender": self.sender,
            "receiver": self.receiver,
            "amount": self.amount,
            "timestamp": self.timestamp.strftime("%d/%m/%Y, %H:%M:%S"),
        }

    @classmethod
    def from_json(cls, js_t):
        return cls(
            sender=js_t["sender"],
            receiver=js_t["receiver"],
            amount=js_t["amount"],
        )
