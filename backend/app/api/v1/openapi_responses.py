"""Aide à remplir le paramètre ``responses=`` des décorateurs de route (OpenAPI / Swagger)."""


def openapi_http_error(status_code: int, description: str, detail_example: str) -> dict[int, dict]:
    """
    Retourne un fragment ``{status_code: {...}}`` pour documenter une réponse d'erreur
    au format FastAPI ``{"detail": "..."}``.
    """
    return {
        status_code: {
            "description": description,
            "content": {
                "application/json": {
                    "example": {"detail": detail_example},
                },
            },
        },
    }
