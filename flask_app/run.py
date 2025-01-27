from app import create_app
from config import CurrentConfig

app = create_app(CurrentConfig)

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=8000)