from core.logger import log, BASE_DIR
from integrations.helpers.aes import AESCBC
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Encrypt .env file values with a command."

    def add_arguments(self, parser):
        parser.add_argument("aeskey", nargs="+", type=str)

    def handle(self, *args, **options):
        assert (
            len(options["aeskey"]) == 1
        ), "aeskey must be 1 full string ex: a-super-secret-key"

        aes_cbc = AESCBC(options["aeskey"][0])

        envpath = BASE_DIR / ".env"
        encrypted_env_path = BASE_DIR / ".env.encrypted"

        with open(envpath, "r") as f:
            env_lines = f.readlines()

        encrypted_lines = []
        for line in env_lines:
            if "=" in line:
                key, value = line.strip().split("=", 1)
                encrypted_value = aes_cbc.encrypt(value)
                encrypted_lines.append(f"{key}={encrypted_value}\n")
            else:
                encrypted_lines.append(line)

        with open(encrypted_env_path, "w") as f:
            f.writelines(encrypted_lines)

        log.info(f"Encrypted .env saved to {encrypted_env_path}")
