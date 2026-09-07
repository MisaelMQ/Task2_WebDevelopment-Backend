import argparse
from getpass import getpass

from pydantic import ValidationError

from app.core.security import hash_password
from app.db.application import (
    initialize_application_database,
    open_application_database,
)
from app.repositories.users_repository import (
    create_user,
    get_user_by_username,
)
from app.schemas.user import UserCreate

def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Crear un usuario para "
            "BCP Tablero NPS API."
        )
    )

    parser.add_argument(
        "--username",
        required=True,
        help="Nombre utilizado para iniciar sesión.",
    )

    parser.add_argument(
        "--name",
        required=True,
        dest="nombre",
        help="Nombre visible del usuario.",
    )

    parser.add_argument(
        "--role",
        choices=["admin", "lector"],
        default="lector",
        dest="rol",
        help="Rol de autorización.",
    )

    return parser.parse_args()

def main() -> int:
    arguments = parse_arguments()

    try:
        user = UserCreate(
            username=arguments.username,
            nombre=arguments.nombre,
            rol=arguments.rol,
            activo=True,
        )
    except ValidationError as error:
        print("Los datos del usuario no son válidos:")
        print(error)
        return 1

    initialize_application_database()
    connection = open_application_database()

    try:
        existing_user = get_user_by_username(
            connection,
            user.username,
        )

        if existing_user is not None:
            print(
                f"El usuario '{user.username}' "
                f"ya existe."
            )
            return 1

        password = getpass(
            "Contraseña: "
        )

        password_confirmation = getpass(
            "Confirmar contraseña: "
        )

        if password != password_confirmation:
            print("Las contraseñas no coinciden.")
            return 1

        if len(password) < 8:
            print(
                "La contraseña debe tener "
                "al menos 8 caracteres."
            )
            return 1

        created_user = create_user(
            connection,
            user,
            hash_password(password),
        )

        print("Usuario creado correctamente:")
        print(
            f"ID: {created_user['id']}"
        )
        print(
            f"Usuario: {created_user['username']}"
        )
        print(
            f"Nombre: {created_user['nombre']}"
        )
        print(
            f"Rol: {created_user['rol']}"
        )

        return 0
    finally:
        connection.close()

if __name__ == "__main__":
    raise SystemExit(main())