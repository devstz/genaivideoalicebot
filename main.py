import uvicorn
from config.settings import get_settings


def main():
    settings = get_settings()
    uvicorn.run(
        "presentation.bootstrap:create_app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=False,
        factory=True,
    )


if __name__ == '__main__':
    main()