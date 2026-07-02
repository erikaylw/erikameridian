from solders.keypair import Keypair
import base58

pk = base58.b58decode('25TqACJfaAKaCwVvKwer1AYqTnvLM2bmEqxpJsjJQy65Hso7kcBDh7dVxX6FEuT3QqRyxCCBR7ijvNQfdGBT1agz')
kp = Keypair.from_bytes(pk)
print(kp.pubkey())
